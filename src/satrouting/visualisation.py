"""Visualization utilities for network graphs."""
import matplotlib.pyplot as plt
import networkx as nx
from typing import List, Dict, Tuple, Optional

def get_node_styling(node: int, ground_stations: List[int], 
                    shortest_path: List[int], spare_path: Optional[List[int]] = None) -> Tuple[str, int]:
    """Determine node color and size based on node type."""
    if node in ground_stations:
        return 'red', 400
    elif spare_path and node in spare_path:
        return 'green', 300
    elif node in shortest_path:
        return 'royalblue', 300
    return 'skyblue', 200

def get_edge_styling(edge: Tuple[int, int], shortest_path: List[int], 
                    ground_stations: List[int], spare_path: Optional[List[int]] = None) -> Tuple[str, float, str]:
    """Determine edge color, width, and style based on edge type."""
    node1, node2 = edge
    
    if spare_path:
        for i in range(len(spare_path) - 1):
            if (node1 == spare_path[i] and node2 == spare_path[i + 1]) or \
               (node2 == spare_path[i] and node1 == spare_path[i + 1]):
                return 'green', 2, '-'
    
    if shortest_path:
        for i in range(len(shortest_path) - 1):
            if (node1 == shortest_path[i] and node2 == shortest_path[i + 1]) or \
               (node2 == shortest_path[i] and node1 == shortest_path[i + 1]):
                return 'black', 2, '-'
    
    if node1 in ground_stations or node2 in ground_stations:
        return 'blue', 0.5, '--'
        
    return 'gray', 0.5, '-'

def plot_spare_zone(positions: Dict, spare_zone: Tuple[int, int, int, int], zone_index: int):
    """Plot a single spare zone with offset box."""
    offset = 0.25
    zone_coords = [
        (positions[spare_zone[0]][0] - 2*offset, positions[spare_zone[0]][1] + offset),
        (positions[spare_zone[1]][0] + offset, positions[spare_zone[1]][1] + offset),
        (positions[spare_zone[3]][0] + 2*offset, positions[spare_zone[3]][1] - offset),
        (positions[spare_zone[2]][0] - offset, positions[spare_zone[2]][1] - offset),
    ]
    
    zone_x, zone_y = zip(*zone_coords)
    plt.plot(list(zone_x) + [zone_x[0]], 
            list(zone_y) + [zone_y[0]], 
            'r--', linewidth=1.0, 
            label=f"Spare Capacity Zone {zone_index+1}")

def plot_network(subgraph: nx.Graph, positions: Dict, shortest_path: List[int], 
                ground_stations: List[int], spare_zones: List[Tuple[int, int, int, int]], 
                spare_path: Optional[List[int]] = None):
    """Plot the network graph with all styling and annotations."""
    plt.figure(figsize=(12, 12))
    
    # Style nodes
    node_colors = []
    node_sizes = []
    for node in subgraph.nodes():
        color, size = get_node_styling(node, ground_stations, shortest_path, spare_path)
        node_colors.append(color)
        node_sizes.append(size)
    
    # Style edges
    edge_colors = []
    edge_widths = []
    edge_styles = []
    for edge in subgraph.edges():
        color, width, style = get_edge_styling(edge, shortest_path, ground_stations, spare_path)
        edge_colors.append(color)
        edge_widths.append(width)
        edge_styles.append(style)
    
    # Draw network elements
    nx.draw_networkx_nodes(subgraph, positions, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(subgraph, positions, edge_color=edge_colors, width=edge_widths, style=edge_styles, alpha=0.7)
    
    # Add labels
    labels = {node: "LDN" if node == -1 else "NYC" if node == -2 else str(node) for node in subgraph.nodes()}
    nx.draw_networkx_labels(subgraph, positions, labels, font_size=8, font_color='black')
    
    # Add edge labels
    edge_labels = nx.get_edge_attributes(subgraph, 'length')
    rounded_edge_labels = {key: round(val, 1) for key, val in edge_labels.items()}
    nx.draw_networkx_edge_labels(subgraph, positions, edge_labels=rounded_edge_labels, 
                                font_size=6, verticalalignment="bottom", alpha=0.9)
    
    # Draw spare zones
    for i, spare_zone in enumerate(spare_zones):
        plot_spare_zone(positions, spare_zone, i)
    
    plt.axis('off')
    plt.show()