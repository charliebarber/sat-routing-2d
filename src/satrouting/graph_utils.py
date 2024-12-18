"""Utilities for graph creation and manipulation."""
import networkx as nx
import re

def parse_network_file(filename):
    """Parse network snapshot file and build NetworkX graph."""
    G = nx.Graph()
    
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("Node"):
                node_match = re.match(r"Node (\-?\d+) with links:", line)
                if node_match:
                    G.add_node(int(node_match.group(1)))
            
            link_matches = re.findall(r"Link \((\-?\d+),(\-?\d+)\) \(length ([\d.]+), y value of the midpoint ([\-.\d]+)\)", line)
            for node1, node2, length, y_value in link_matches:
                G.add_edge(int(node1), int(node2), length=float(length), y_value=float(y_value))
    
    return G

def create_subgraph(G, positions, ground_stations):
    """Create a subgraph containing only relevant nodes."""
    subgraph = G.copy()
    nodes_to_remove = []
    
    for node in subgraph.nodes():
        if node in ground_stations:
            continue
            
        pos = positions[node]
        x, y = pos[0], pos[1]
        if x < 26 or x > 40 or y < -8 or y > -4:
            nodes_to_remove.append(node)
            
    subgraph.remove_nodes_from(nodes_to_remove)
    return subgraph