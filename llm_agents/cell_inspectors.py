
import os
from langchain.tools.base import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from db.excel_manager import ExcelDatabase

from utils.excel import get_excel_tile_data
from utils.graph import ComputeGraph

from typing import List, Dict, Any, Tuple
import asyncio
from dotenv import load_dotenv
import pickle
import yaml
from langfuse.callback import CallbackHandler

class ExcelVariableAgent:
    def __init__(self,
                 spread_sheet_path: str,
                 system_prompt: str| None = None,
                 openai_model: str = "gpt-4.1-mini",
                 trace_with_langfuse: bool = False
                 ):
        
        self.load_db(spread_sheet_path)
        self.project_dir = os.path.dirname(os.path.abspath(spread_sheet_path))

        self.construct_system_prompt(system_prompt)
        self.openai_model = openai_model

        self.build_tools()
        self.build_agent()
        self.initialize_variable_database()
        self.trace_with_langfuse = trace_with_langfuse

    def construct_system_prompt(self,custom_prompt:str|None=None):
        if custom_prompt is None:
            with open("prompts/cell_inspector.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)
            self.system_prompt = system_prompt["prompt"]
        else:
            self.system_prompt = custom_prompt

    def load_db(self,spread_sheet_path):
        """load processed mongo spreadsheet database"""
        self.spreadsheet_name = spread_sheet_path.split("/")[-1].split(".")[0]
        self.db = ExcelDatabase(spread_sheet_path)
        self.db.reparse_spreadsheet(name=self.spreadsheet_name)
        self.db.load_spreadsheet()

    def initialize_variable_database(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """Initialize the variable database for different layers of the compute graph."""
        # Initialize
        spreadsheet_data = self.db.get_spreadsheet_data(name=self.spreadsheet_name, as_dict=True)
        self.graph = ComputeGraph(spreadsheet_data, self.db)
        # Build the graph and create layers
        self.graph.build_graph()
        self.graph.create_layers()
        self.layers = self.graph.layers
        self.variable_db = {}
        for layer in self.layers:
            for key in layer:
                self.variable_db[key] = {}
        return self.variable_db
        
    def build_tools(self):
        """Build the tools that the agent can use."""
        self.agent_tools =[
            StructuredTool.from_function(self.update_variable_database)
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

    def get_cell_tile_data(self,cell_id:str, sheetname:str) -> str:
        """
        This tool is used to look at a cell and its neighbors in an excel spreadsheet.                 
        Returns:
        str: A Markdown formatted table of the cell and its neighbors.
        """
        return get_excel_tile_data(cell_id, sheetname, self.db,self.spreadsheet_name,distance=5)

    def update_variable_database(self, 
                             cell_id:str,
                             sheetname:str,
                             variable_name:str,
                             variable_desr:str,
                             python_code:str) -> None:
        """This tool is used to update the variable data in the variable database.
        cell_id: str - The ID of the cell to update.
        sheetname: str - The name of the sheet where the cell is located.
        variable_name: str - The name that the AI assitant selected for the variable name in python.
        variable_desr: str - The description of the variable AI assitant selected.
        python_code: str - The python code generated by the AI assistant for the contents in the 
        
        """
        cell_key = (sheetname, cell_id)
        # print(f"Updating variable database for cell {cell_id} in sheet {sheetname}.")
        self.variable_db[cell_key]["variable_name"] = variable_name
        self.variable_db[cell_key]["variable_desr"] = variable_desr
        self.variable_db[cell_key]["python_code"] = python_code
        
    def build_cell_processing_prompt(self, cell_id: str, sheetname: str) -> str:
        cell_data = self.db.get_cell_data(cell_id, sheetname)
        cell_type = cell_data['cell_type']
        if cell_type == 'formula':
            context = self.extract_formula_cell_context(cell_id, sheetname)
        elif cell_type == 'value':
            context = self.extract_value_cell_context(cell_id, sheetname)
        elif cell_type == 'valuelist':
            context = self.extract_valuelist_cell_context(cell_id, sheetname)
        else:
            raise ValueError(f"Unknown cell type: {cell_type}")
        context+= "\n"
        context += self.extract_cell_tile_context(cell_id, sheetname)
        return context

    def extract_cell_tile_context(self, cell_id: str, sheetname: str) -> str:
        tile_context = f"The cell tile data for cell {cell_id} in sheet '{sheetname}' is as follows:\n"
        tile_data = get_excel_tile_data(cell_id, sheetname, self.db, self.spreadsheet_name, distance=5)
        tile_context += tile_data
        return tile_context

    def extract_formula_cell_context(self, cell_id: str, sheetname: str) -> str:
        """creates a description of formula cell and its dependent cells."""
        cell_data = self.db.get_cell_data(cell_id, sheetname)
        formula = cell_data.get('formula', '')
        context = f"Cell {cell_id} in sheet '{sheetname}' contains the formula: {formula}. "
        context += "Dependent cell information is as follows:\n"
        # add a header 
        context += "| Precedent Cell ID | Sheet Name | Variable Name | Variable Description | Python Code |\n"
        for d_cell in cell_data['precedent_cells']:
            precedent_cell_id = d_cell['cell_ref']
            precedent_sheetname = d_cell['sheet_name']
            key = (precedent_sheetname, precedent_cell_id)
            variable_name = self.variable_db[key]['variable_name'] 
            variable_desr = self.variable_db[key]['variable_desr']
            python_code = self.variable_db[key]['python_code']
            context += f"| {precedent_cell_id} | {precedent_sheetname} | {variable_name} | {variable_desr} | {python_code} |\n"
        return context
    
    def extract_value_cell_context(self, cell_id: str, sheetname: str) -> str:
        """creates a description of value cell and its dependent cells."""
        cell_data = self.db.get_cell_data(cell_id, sheetname)
        value = cell_data['value']
        context = f"Cell {cell_id} in sheet '{sheetname}' contains the contast value: {value['raw']}. "
        return context
    
    def extract_valuelist_cell_context(self, cell_id: str, sheetname: str) -> str:
        """creates a description of valuelist cell and its dependent cells."""
        cell_data = self.db.get_cell_data(cell_id, sheetname)
        context = f"Cell {cell_id} in sheet '{sheetname}' can have a finite set of input values defined as follows:"
        # add header
        context += "\n| Value |\n"
        for cell in cell_data['value_list']:
            cell_id = cell['cell_ref']
            sheetname = cell['sheet_name']
            value = self.db.get_cell_data(cell_id, sheetname)['value']['raw']
            context += f"| {value} |\n"
        return context
                   
    async def ainvoke(self, cell_id,sheetname, thread_id="test"):
        config = {"configurable": {"thread_id": thread_id}}
        if self.trace_with_langfuse:
            config["callbacks"] = [CallbackHandler()]

        user_query = self.build_cell_processing_prompt(cell_id, sheetname)
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

    async def process_layer(self, layer) -> List[Any]:
        """
        Process a layer of cells by invoking ainvoke concurrently for each cell in the layer.
        """
        tasks = [
            self.ainvoke(cell_id, sheetname, f"{sheetname}!{cell_id}")
            for sheetname, cell_id in layer
        ]
        return await asyncio.gather(*tasks)

    async def orchestrate_variable_extraction(self,save_db:bool=True):
        for i,layer in enumerate(self.layers):
            print(f"processing layer {i} with {len(layer)} cells")
            await self.process_layer(layer)
        if save_db:
            with open(f"{self.project_dir}/variable_db_{self.spreadsheet_name}.pkl", "wb") as f:
                pickle.dump(self.variable_db, f)

    def load_variable_db(self,spreadsheet_name:str):
        with open(f"{self.project_dir}/variable_db_{spreadsheet_name}.pkl", "rb") as f:
            self.variable_db = pickle.load(f)
        return self.variable_db