"""
SpreadsheetGraph module for building and visualizing dependency graphs from spreadsheet data.
"""

import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple, Union, Any


class ComputeGraph:
    """
    Class for building and visualizing directed acyclic graphs from Excel spreadsheet data.
    
    This class creates a dependency graph based on cell references where:
    - Nodes represent cells in the spreadsheet
    - Edges represent dependencies between cells
    
    The class can:
    - Build a graph representation of the spreadsheet dependencies
    - Create DAG layers for hierarchical visualization
    - Visualize the dependency graph with customizable options
    """
    
    def __init__(self, spreadsheet_data: Dict[str, Any], db):
        """
        Initialize the SpreadsheetGraph with spreadsheet data and database connection.
        
        Args:
            spreadsheet_data: Dictionary containing spreadsheet metadata and cell references
            db: Database instance that provides access to cell data
        """
        self.spreadsheet_data = spreadsheet_data
        self.db = db
        self.graph = nx.DiGraph()
        self.layers = []
        self.positions = {}
        
    def build_graph(self) -> nx.DiGraph:
        """
        Build the directed graph from spreadsheet data.
        
        Returns:
            nx.DiGraph: The constructed graph
        """
        nodes = set()
        for sheet_name in self.spreadsheet_data['cell_references']:
            for cell_ref in self.spreadsheet_data['cell_references'][sheet_name]:
                # Get detailed cell data from the database
                cell_data = self.db.get_cell_data(cell_ref, sheet_name)
                
                if not cell_data:
                    continue
                    
                precedent_cells = cell_data.get('precedent_cells', [])
                dependent_cells = cell_data.get('dependent_cells', [])
                
                # Create a node name that includes the sheet name and cell reference
                node_name = f"{cell_data['sheet']}!{cell_ref}"
                nodes.add(node_name)
                
                # Add node if it has any connections
                if precedent_cells or dependent_cells:
                    self.graph.add_node(node_name, label=node_name)
                    
                # Create edges from each precedent cell to this cell
                for precedent_cell in precedent_cells:
                    precedent_node_name = f"{precedent_cell['sheet_name']}!{precedent_cell['cell_ref']}"
                    if precedent_node_name not in nodes:
                        self.graph.add_node(precedent_node_name, label=precedent_node_name)
                        nodes.add(precedent_node_name)
                    self.graph.add_edge(precedent_node_name, node_name)
        return self.graph
    
    def create_layers(self) -> List[List[str]]:
        """
        Create topological layers of the graph.
        This organizes nodes into layers based on their dependencies.
        
        Returns:
            List[List[str]]: List of layers, where each layer is a list of node names
        """
        # Use topological_generations to get layers of nodes
        self.layers = list(nx.topological_generations(self.graph))
        
        
        # Assign a 'layer' attribute to each node based on its layer index
        for layer_index, layer in enumerate(self.layers):
            for node in layer:
                self.graph.nodes[node]['layer'] = layer_index

        # layers = [
        #                 [
        #                     {"sheet_name": sheet, "cell_ref": cell}
        #                     for sheet, cell in (node.split("!") for node in layer)
        #                 ]
        #                 for layer in self.layers
        #             ]

        layers = [
            {(sheet, cell): {} for sheet, cell in (node.split("!") for node in layer)} for layer in self.layers
        ]

        self.layers = layers
        return self.layers
    
    def compute_layout(self, scale: float = 100) -> Dict[str, Tuple[float, float]]:
        """
        Compute the layout for the graph visualization using multipartite layout.
        
        Args:
            scale: Scale factor for the layout (default: 100)
            
        Returns:
            Dict[str, Tuple[float, float]]: Dictionary mapping node names to coordinates
        """
        # Use multipartite layout which organizes nodes according to their layer
        self.positions = nx.multipartite_layout(self.graph, subset_key="layer", scale=scale)
        return self.positions
        
    def visualize(self, 
                  figsize: Tuple[int, int] = (5, 10),
                  node_color: str = 'skyblue',
                  node_size: int = 1000,
                  font_size: int = 8,
                  scale: float = 0.02,
                  title: str = "Layered Visualization of Dependency Graph",
                  save_path: Optional[str] = None) -> None:
        """
        Visualize the dependency graph.
        
        Args:
            figsize: Figure size as (width, height) in inches
            node_color: Color of the nodes
            node_size: Size of the nodes
            font_size: Size of the font for node labels
            scale: Scale factor for vertical spacing
            title: Title of the graph
            save_path: Path to save the figure (if None, the figure is displayed)
        """
        # Make sure graph is built
        if not self.graph.nodes():
            self.build_graph()
            
        # Create layers if not already created
        if not self.layers:
            self.create_layers()
            
        # Compute layout if not already computed
        if not self.positions:
            self.compute_layout()
            
        # Adjust the y-coordinates for better visibility
        positions = {node: (x, y * scale) for node, (x, y) in self.positions.items()}
        
        # Get the labels set earlier
        labels = nx.get_node_attributes(self.graph, 'label')
        
        # Create a new figure
        plt.figure(figsize=figsize)
        
        # Draw the graph with layered positions
        nx.draw(self.graph, positions, labels=labels, 
                node_color=node_color, node_size=node_size, 
                arrows=True, font_size=font_size)
        
        plt.title(title)
        
        # Save or show the figure
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
            
    def get_graph(self) -> nx.DiGraph:
        """
        Get the constructed graph.
        
        Returns:
            nx.DiGraph: The directed graph
        """
        return self.graph
        
    def get_layers(self) -> List[List[str]]:
        """
        Get the topological layers of the graph.
        
        Returns:
            List[List[str]]: List of layers
        """
        return self.layers
