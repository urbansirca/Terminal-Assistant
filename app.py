from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
import sys
import io
import requests
import pandas as pd
import os
from langchain_core.tools import Tool
import asyncio
import uuid
from dotenv import load_dotenv
from agent import AIAgent
load_dotenv()

llm = ChatOpenAI(model='gpt-4o')

ai_agent = AIAgent(llm)
thread_id = str(uuid.uuid4())


def run_demo():
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting demo.")
            break

        print("\n--- Chat Interface ---\n")
        ai_agent.process_message(user_input, thread_id=thread_id)


if __name__ == "__main__":
    run_demo()
