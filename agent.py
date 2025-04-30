import re
import os
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from tools import execute_command 
from langchain_openai import ChatOpenAI
from utils import prompt_user, print_user, print_agent, print_tool_call, print_tool_result
from dotenv import load_dotenv
load_dotenv()


class ShellAgent:
    SYSTEM_PROMPT = """
You are a helpful assistant that can execute shell commands on a Mac via a tool called `execute_command`.
Whenever you want to run a command, respond in one of these exact formats:
  - EXECUTE: <shell command>
  - CONFIRM: <shell command>  (for potentially destructive commands)
Otherwise, just answer the user in plain language.
"""
    RISK_KEYWORDS = ["rm -rf", "shutdown", "mkfs", "dd ", ":(){:|:&};:"]

    def __init__(self, ):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        self.history = []

    def is_risky(self, cmd: str) -> bool:
        low = cmd.lower()
        return any(kw in low for kw in self.RISK_KEYWORDS)

    def parse_action(self, text: str):
        """Returns ('execute', cmd) or ('confirm', cmd) or ('reply', text)."""
        m = re.match(r"^\s*EXECUTE:\s*(.+)$", text, re.IGNORECASE)
        if m:
            return "execute", m.group(1).strip()
        m = re.match(r"^\s*CONFIRM:\s*(.+)$", text, re.IGNORECASE)
        if m:
            return "confirm", m.group(1).strip()
        return "reply", text.strip()

    def run(self):
        print_agent("Ready. Type 'exit' to quit.")
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
                    out = execute_command.invoke(payload)
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
                out = execute_command.invoke(payload)
                print_tool_result("execute_command", out)
                # print(out)

                self.history.append(HumanMessage(content=user_input))
                self.history.append(AIMessage(content=decision))
                self.history.append(AIMessage(content=out))


if __name__ == "__main__":
    agent = ShellAgent()
    agent.run()
