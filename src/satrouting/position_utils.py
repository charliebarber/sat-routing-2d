"""Utilities for handling node positions."""

def get_node_position(node):
    """Calculate the position for a single node, handling the wrapping behavior."""
    if node < 0:
        return None
        
    plane = node // 66  # 66 sats per plane
    index_in_plane = 66 - (node - (66 * plane))
    
    # Handle the wrapping behavior
    if index_in_plane > 32:
        x = index_in_plane - 33
    else:
        x = index_in_plane + 33
    y = -plane
    
    return x, y

def calculate_node_positions(G):
    """Calculate positions for all nodes in the graph."""
    positions = {}
    for node in G.nodes():
        if node >= 0:
            positions[node] = get_node_position(node)
        else:
            # Set ground station positions
            if node == -1:
                positions[node] = (38.5, -5.5)  # LDN
            elif node == -2:
                positions[node] = (25, -6.5)    # NYC
    
    return positions