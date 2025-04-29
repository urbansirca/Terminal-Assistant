from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.types import Send

from tools import tools
from logger import logger
import datetime
import json

class AIAgent:
    """Example autonomous AI Agent"""

    prompt = f"""You are a helpful assistant that can execute terminal commands on the user's Mac.
                You have access to a tool that can run any shell command. 
                Use this tool to help the user with terminal operations, conda environment management, 
                and file system tasks. Be careful with destructive commands.
    """

    def __init__(self, llm):
        self.llm = llm
        self.agents = {}
        self.memory = MemorySaver()
        self._setup_graph()

    def _setup_graph(self):
        """Setup the LangGraph workflow"""
        # Create the LangGraph workflow
        builder = StateGraph(AgentState)
        agent = create_react_agent(self.llm, tools=tools, prompt=self.prompt, checkpointer=self.memory)
        self.graph = agent

    # Update the process_message method as well
    def process_message(self, message, thread_id=None):
        """Process a user message"""
        # Create a human message
        human_msg = HumanMessage(content=message)

        # Run the graph with the correct config for checkpointer
        events = self.graph.stream(
            {"messages": [human_msg]},
            config={
                "thread_id": thread_id,
                "configurable": {"checkpointer": self.memory},
                "recursion_limit": 10
            },
        )

        # Collect all messages
        messages = []
        for event in events:
            for _, node_output in event.items():
                messages.extend(node_output.get("messages", []))
                
        #return messages

         # Return the last AI message content
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        if ai_messages:
            logger.log_agent_response(
                "Commander", ai_messages[-1].content
            )
            return ai_messages[-1].content
        return "No response from Commander."
