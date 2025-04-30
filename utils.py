from typing import Any
import logging
# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

def print_user(text: str):
    print(f"{Colors.BRIGHT_GREEN}[USER]{Colors.RESET} {text}")

def print_agent(text: str):
    # if you want to render Markdown you could strip it, or just print raw
    print(f"{Colors.BRIGHT_BLUE}[AGENT]{Colors.RESET} {text}")

def print_tool_call(tool: str, params: dict):
    print(f"{Colors.BRIGHT_YELLOW}[TOOL CALL]{Colors.RESET} {tool} {params!r}")

def print_tool_result(tool: str, result: Any):
    print(f"{Colors.BRIGHT_MAGENTA}[TOOL RESULT]{Colors.RESET}")
    print(f"{Colors.MAGENTA}{result}{Colors.RESET}")


def prompt_user(prompt_text: str) -> str:
    # Show the prompt in green, then reset before the user types
    return input(f"{Colors.BRIGHT_GREEN}{prompt_text}{Colors.RESET}")