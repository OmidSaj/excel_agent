from enum import Enum

from langchain.tools.base import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from db.excel_manager import ExcelDatabase
from tqdm import tqdm

from utils.excel import get_excel_tile_data
from utils.graph import ComputeGraph

from typing import List, Dict, Any, Tuple
import asyncio
from dotenv import load_dotenv
import pickle
import yaml
import os
import logging

class ProgrammerAgent:
    def __init__(self,
                 spread_sheet_path: str,
                 system_prompt: str| None = None,
                 openai_model: str = "gpt-4.1-mini",
                 ):
        
        self.spreadsheet_name = spread_sheet_path.split("/")[-1].split(".")[0]
        self.project_dir = os.path.dirname(os.path.abspath(spread_sheet_path))
        self.openai_model = openai_model

        self.load_variable_db()
        self.construct_system_prompt(system_prompt)

        self.build_tools()
        self.build_agent()

    def construct_system_prompt(self,custom_prompt:str|None=None):
        if custom_prompt is None:
            with open("prompts/programmer.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)
            self.system_prompt = system_prompt["prompt"]
        else:
            self.system_prompt = custom_prompt

    def load_variable_db(self):
        with open(f"{self.project_dir}/variable_db_{self.spreadsheet_name}.pkl", "rb") as f:
            self.variable_db = pickle.load(f)
        return self.variable_db
        
    def build_tools(self):
        """Build the tools that the agent can use."""
        self.agent_tools =[
            StructuredTool.from_function(self.write_python_code_to_file),
            StructuredTool.from_function(self.write_readme_to_file),
            StructuredTool.from_function(self.create_directory)
        ]
        self.tool_node = ToolNode(
            tools=self.agent_tools
        )
        
    def build_agent(self):
        load_dotenv()
        self.model_with_tools = ChatOpenAI(
                                model=self.openai_model, temperature=0
                            ).bind_tools(self.agent_tools)
        memory = MemorySaver()

        # Specify an ID for the thread
        workflow = StateGraph(MessagesState)
        # Define the two nodes we will cycle between
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", self.should_continue, ["tools", END])
        workflow.add_edge("tools", "agent")
        self.app = workflow.compile(checkpointer=memory)
 
    def should_continue(self,state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    async def call_model(self,state: MessagesState):
        messages = state["messages"]
        response = self.model_with_tools.invoke(messages)
        return {"messages": [response]}


    def write_python_code_to_file(self, 
                             python_code:str,
                             save_path:str) -> None:
        """
        This tool is used to write python code to a file at the specified path.
        """
        absolute_save_path = os.path.join(self.project_dir, save_path)
        with open(absolute_save_path, "w") as f:
            f.write(python_code)
        logging.info(f"Created {absolute_save_path}")
        return f"Created {save_path}"
    
    def write_readme_to_file(self, 
                             readme_content:str,
                             save_path:str) -> None:
        """
        This tool is used to write readme content to a file at the specified path.
        """
        absolute_save_path = os.path.join(self.project_dir, save_path)
        with open(absolute_save_path, "w") as f:
            f.write(readme_content)
        logging.info(f"Created {absolute_save_path}")
        return f"Created {save_path}"
    
    def create_directory(self, directory_path:str) -> None:
        """
        This tool is used to create a directory at the specified path.
        """
        # join the relative directory path with the project directory
        save_directory_path = os.path.join(self.project_dir, directory_path)
        os.makedirs(save_directory_path, exist_ok=True)
        logging.info(f"Created {save_directory_path}")
        return f"Created {directory_path}"
    
    def build_coding_context(self) -> str:
        """This method will collect the information inside the variable database from cell inspectors and 
        returns a combined context for the programmer agent to organize them into a proper and consistent code."""
        context = ""
        for key in self.variable_db:
            variable_name = self.variable_db[key]["variable_name"]
            variable_desr = self.variable_db[key]["variable_desr"]
            python_code = self.variable_db[key]["python_code"] 
            context+=f"\n#{variable_name}:{variable_desr}\n{python_code}"               
        return context
               
    async def initialize_coding_agent(self, thread_id="python_code_generation"):
        config = {"configurable": {"thread_id": thread_id}}
        user_query = self.build_coding_context()
        if "messages" not in self.app.get_state(config).values:
            user_inputs = {"messages": [
                ("system", self.system_prompt), 
                ("human", user_query)
                ]}
        else:
            user_inputs = {"messages": [
                ("human", user_query)
                ]}
        messages = await self.app.ainvoke(user_inputs,config=config)
        return messages 


