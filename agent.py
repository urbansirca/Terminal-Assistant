import re
import os
import uuid
import shutil
from pathlib import Path
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tools import execute_command 
from langchain_openai import ChatOpenAI
from utils import prompt_user, print_user, print_agent, print_tool_call, print_tool_result
from dotenv import load_dotenv
import subprocess

load_dotenv()


class ShellAgent:
    SYSTEM_PROMPT = """
You are a helpful command-line assistant that executes shell commands on Linux. Always respond with executable commands when the user's request involves shell operations.

CRITICAL RULES:
1. Use EXACTLY ONE "EXECUTE:" or "CONFIRM:" per response - never use multiple command keywords.
2. DO NOT include any explanations or non-executable text before or after your command.
3. For tasks requiring both file creation AND execution, use ONE of these approaches:
   a. For simple files: EXECUTE: echo 'print("hello")' > script.py && python3 script.py
   b. For multi-line files: Use a compound command:
      EXECUTE: { cat << 'EOF' > script.py
def example():
    print("hello")
example()
EOF
} && python3 script.py

You have access to a dedicated Python virtual environment for each session.
- To install packages, use: pip install package_name
- You can install any packages needed for a task without affecting the user's main environment
- Use the python command to run scripts, which will automatically use this session's environment
- The virtualenv is already activated, so you don't need to activate it

When responding, use EXACTLY one of these formats:
- EXECUTE: <shell command>
  (For safe commands - output ONLY this line, no explanations)
- CONFIRM: <shell command>
  (For potentially destructive commands - output ONLY this line, no explanations)
- <regular text response>
  (Only when absolutely no command execution is needed)

Remember to wrap heredoc in curly braces { } when chaining with && to ensure proper syntax.
"""
    RISK_KEYWORDS = ["rm -rf", "shutdown", "mkfs", "dd ", ":(){:|:&};:", "> /dev", "| sudo", "sudo rm"]

    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
        )
        self.history = []
        
        # Create a unique session ID
        self.session_id = str(uuid.uuid4())[:8]
        
        # Setup virtual environment for this session
        self.venv_path = Path(f".venv_agent_{self.session_id}")
        self.setup_virtual_environment()

    def setup_virtual_environment(self):
        """Create a dedicated virtual environment for this agent session"""
        print_agent(f"Setting up virtual environment for session {self.session_id}...")
        
        # Create virtual environment
        result = subprocess.run(
            f"python -m venv {self.venv_path}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_agent(f"Error creating virtual environment: {result.stderr}")
            raise RuntimeError("Failed to create virtual environment")
            
        print_agent(f"Virtual environment created at {self.venv_path}")
        
        # Get paths to Python and pip in the new environment
        self.venv_python = self.venv_path / ("bin" if os.name != "nt" else "Scripts") / "python"
        self.venv_pip = self.venv_path / ("bin" if os.name != "nt" else "Scripts") / "pip"
        
        # Install basic packages
        result = subprocess.run(
            f"{self.venv_pip} install --upgrade pip",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print_agent(f"Warning: Failed to upgrade pip: {result.stderr}")
            
        print_agent("Virtual environment setup complete")

    def execute_in_venv(self, command):
        """Execute a command in the virtual environment"""
        # Modify command to use the venv's Python/pip if it starts with python or pip
        if command.strip().startswith("python "):
            command = f"{self.venv_python} {command[7:]}"
        elif command.strip().startswith("pip "):
            command = f"{self.venv_pip} {command[4:]}"
            
        # Then execute the command
        return execute_command.invoke(command)

    def is_risky(self, cmd: str) -> bool:
        low = cmd.lower()
        return any(kw in low for kw in self.RISK_KEYWORDS)

    def parse_action(self, text: str):
        """Returns ('execute', cmd) or ('confirm', cmd) or ('reply', text)."""
        m = re.match(r"^\s*EXECUTE:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if m:
            return "execute", m.group(1).strip()
        m = re.match(r"^\s*CONFIRM:\s*(.+)$", text, re.IGNORECASE | re.DOTALL)
        if m:
            return "confirm", m.group(1).strip()
        return "reply", text.strip()

    def cleanup(self):
        """Clean up the virtual environment when done"""
        try:
            if self.venv_path.exists():
                print_agent(f"Cleaning up virtual environment at {self.venv_path}...")
                shutil.rmtree(self.venv_path)
                print_agent("Virtual environment removed")
        except Exception as e:
            print_agent(f"Warning: Failed to clean up virtual environment: {str(e)}")

    def run(self):
        print_agent(f"Ready. Type 'exit' to quit. Using virtual environment: {self.venv_path}")
        try:
            while True:
                user_input = prompt_user("[USER] ")

                if user_input.lower() in ("exit", "quit"):
                    break

                # assemble chat history
                msgs = [SystemMessage(content=self.SYSTEM_PROMPT)]
                msgs += [m for m in self.history]
                msgs.append(HumanMessage(content=user_input))

                # ask LLM what to do
                ai_msg: AIMessage = self.llm.invoke(input=msgs)
                decision = ai_msg.content
                # print(f"\nAgent decision: {decision}\n")

                action, payload = self.parse_action(decision)
                if action == "reply":
                    # plain answer
                    print_agent(payload)
                    self.history.append(HumanMessage(content=user_input))
                    self.history.append(AIMessage(content=payload))

                elif action == "confirm":
                    confirm = prompt_user(
                        f"⚠️  Command looks risky: {payload}\nProceed? (yes/no) "
                    )
                    if confirm.strip().lower() == "yes":
                        # 1) Log the impending tool call
                        print_tool_call("execute_command", {"command": payload})
                        out = self.execute_in_venv(payload)
                        # 3) Log the result
                        print_tool_result("execute_command", out)

                        # 4) Record in history
                        self.history.append(HumanMessage(content=user_input))
                        self.history.append(AIMessage(content=decision))
                        self.history.append(AIMessage(content=out))
                    else:
                        print_agent("Command canceled.")
                        self.history.append(HumanMessage(content=user_input))
                        self.history.append(AIMessage(content="Cancelled execution."))

                elif action == "execute":
                    # run directly without extra prompt
                    print_tool_call("execute_command", {"command": payload})
                    out = self.execute_in_venv(payload)
                    print_tool_result("execute_command", out)
                    # print(out)

                    self.history.append(HumanMessage(content=user_input))
                    self.history.append(AIMessage(content=decision))
                    self.history.append(AIMessage(content=out))
        finally:
            # Ensure we clean up no matter how we exit
            self.cleanup()


if __name__ == "__main__":
    agent = ShellAgent()
    agent.run()
