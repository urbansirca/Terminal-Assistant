# ShellAgent

> A lightweight, conversational CLI agent for executing shell commands safely.

ShellAgent is a Python-based REPL tool that lets you interact with your macOS (or Linux) shell via natural‐language prompts. It leverages an LLM to decide when to run commands, asks for confirmation on risky operations, and colorizes all input/output for a clean terminal experience.

---

## Features

- **Natural‐language decision making**  
  The agent’s system prompt guides the LLM to choose between:
  - `EXECUTE: <command>`  
  - `CONFIRM: <command>`  
  - Plain text replies

- **Risk detection & confirmation**  
  Simple keyword checks (`rm ‐rf`, `shutdown`, `dd`, etc.) trigger “CONFIRM” prompts before destructive commands run.

- **Colorized I/O**  
  User prompts, agent replies, tool calls, and results are all printed in distinct ANSI colors.

- **Command history**  
  In‐session memory retains your conversation so the LLM can refer back to earlier context.

---

## Prerequisites

- Python 3.8+  
- A LangChain-compatible LLM API key (e.g. OpenAI) configured in your environment  
---

## Installation

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/shellagent.git
   cd shellagent
