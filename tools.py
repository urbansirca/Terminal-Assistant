import io
import contextlib
import traceback
from langchain_core.tools import tool

from langchain.tools import tool
import subprocess
import shlex
import os
import requests
from typing import Optional, Dict, Any
import os


# from ssh_utils import execute_command, client

@tool
def example_tool(arg_1: str):
    """
    Example tool that takes a string argument and returns it.
    Docstrings are used to provide information about the tool. They are used as a prompt for the agent.

    Args:
        arg_1 (str): A string argument

    Returns:
        str: The same string argument
    """
    return example_tool


@tool
def execute_command(command: str) -> str:
    """
    Execute any shell command in the terminal. This is a universal tool that can run any terminal command,
    including conda commands, file operations, and system utilities.
    
    Args:
        command (str): The shell command to execute (e.g., "ls -la", "conda list", "cat file.txt")
        
    Returns:
        str: The command output (stdout) or error message if the command fails
    """
    try:
        # Check if it's a cd command, which needs special handling
        if command.strip().startswith("cd "):
            # Extract the directory
            directory = command.strip()[3:]
            # Expand user path if needed (e.g., for ~)
            directory = os.path.expanduser(directory)
            
            try:
                # Change directory
                os.chdir(directory)
                return f"Changed directory to {os.getcwd()}"
            except Exception as e:
                return f"Error changing directory: {str(e)}"
        
        # Use shell=True for complex commands (pipes, redirects, etc.)
        # This also enables conda commands to work properly
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        # Return both stdout and stderr if there's an error
        if result.returncode != 0:
            return f"Exit Code: {result.returncode}\nStdout: {result.stdout.strip()}\nStderr: {result.stderr.strip()}"
        
        return result.stdout.strip()
        
    except Exception as e:
        return f"Error executing command: {str(e)}"



tools = [example_tool, execute_command]
