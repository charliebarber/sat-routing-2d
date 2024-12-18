from typing import List, Tuple, Dict

def find_nodes_in_spare_zones(G, spare_zones: List[Tuple[int, int, int, int]], node_positions: Dict) -> Dict[int, List[int]]:
    """
    Find all nodes that fall within the specified spare zones, handling the wrapping behavior.
    
    Args:
        G: NetworkX graph
        spare_zones: List of tuples, each containing (top_left, top_right, bottom_left, bottom_right) node numbers
        node_positions: Dictionary mapping nodes to their (x, y) positions
        
    Returns:
        Dict mapping zone index to list of nodes in that zone
    """
    nodes_in_zones = {i: [] for i in range(len(spare_zones))}
    
    for node in G.nodes():
        if node < 0:  # Skip ground stations
            continue
            
        node_pos = node_positions.get(node)
        if not node_pos:
            continue
            
        node_x, node_y = node_pos
        
        # Check each spare zone
        for zone_idx, zone in enumerate(spare_zones):
            top_left, top_right, bottom_left, bottom_right = zone
            
            # Get zone corner positions
            tl_pos = node_positions[top_left]
            tr_pos = node_positions[top_right]
            bl_pos = node_positions[bottom_left]
            
            # Calculate zone boundaries
            min_y = min(tl_pos[1], bl_pos[1])
            max_y = max(tl_pos[1], bl_pos[1])
            
            # Handle the wrapped x-coordinates
            if tl_pos[0] > tr_pos[0]:  # Zone wraps around
                in_x_range = (node_x >= tl_pos[0]) or (node_x <= tr_pos[0])
            else:
                in_x_range = tl_pos[0] <= node_x <= tr_pos[0]
            
            if in_x_range and min_y <= node_y <= max_y:
                nodes_in_zones[zone_idx].append(node)
    
    return nodes_in_zones