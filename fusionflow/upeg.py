"""UPEG - Unified Polyglot Execution Graph"""

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class UPEGNode:
    """Node in the UPEG graph"""
    id: str
    operation: str
    inputs: List[str]
    outputs: List[str]
    metadata: Dict[str, Any]

class UPEG:
    """Unified Polyglot Execution Graph representation"""
    
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def add_node(self, node: UPEGNode):
        """Add a node to the graph"""
        self.nodes.append(node)
    
    def add_edge(self, from_node: str, to_node: str):
        """Add an edge between nodes"""
        self.edges.append((from_node, to_node))
    
    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            'nodes': [vars(node) for node in self.nodes],
            'edges': self.edges
        }
