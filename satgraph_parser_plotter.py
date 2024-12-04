import networkx as nx
import re
import matplotlib.pyplot as plt

def parse_network_file(filename):
    """Parse network snapshot file and build NetworkX graph."""
    G = nx.Graph()
    
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("Node"):
                node_match = re.match(r"Node (\-?\d+) with links:", line)
                if node_match:
                    node = int(node_match.group(1))
                    G.add_node(node)
            
            link_matches = re.findall(r"Link \((\-?\d+),(\-?\d+)\) \(length ([\d.]+), y value of the midpoint ([\-.\d]+)\)", line)
            for link in link_matches:
                node1, node2, length, y_value = int(link[0]), int(link[1]), float(link[2]), float(link[3])
                G.add_edge(node1, node2, length=length, y_value=y_value)
    
    return G

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

def find_nodes_in_spare_zones(G, spare_zones):
    """
    Find all nodes that fall within the specified spare zones, handling the wrapping behavior.
    
    Args:
        G: NetworkX graph
        spare_zones: List of tuples, each containing (top_left, top_right, bottom_left, bottom_right) node numbers
        
    Returns:
        Dict mapping zone index to list of nodes in that zone
    """
    nodes_in_zones = {i: [] for i in range(len(spare_zones))}
    
    for node in G.nodes():
        if node < 0:  # Skip ground stations
            continue
            
        node_pos = get_node_position(node)
        if not node_pos:
            continue
            
        node_x, node_y = node_pos
        
        # Check each spare zone
        for zone_idx, zone in enumerate(spare_zones):
            top_left, top_right, bottom_left, bottom_right = zone
            
            # Get zone corner positions
            tl_pos = get_node_position(top_left)
            tr_pos = get_node_position(top_right)
            bl_pos = get_node_position(bottom_left)
            br_pos = get_node_position(bottom_right)
            
            # Calculate zone boundaries
            min_y = min(tl_pos[1], bl_pos[1])
            max_y = max(tl_pos[1], bl_pos[1])
            
            # Handle the wrapped x-coordinates
            if tl_pos[0] > tr_pos[0]:  # Zone wraps around
                # Node is in zone if it's either:
                # 1. Greater than or equal to left boundary
                # 2. Less than or equal to right boundary
                in_x_range = (node_x >= tl_pos[0]) or (node_x <= tr_pos[0])
            else:
                # Normal case - node must be between boundaries
                in_x_range = tl_pos[0] <= node_x <= tr_pos[0]
            
            # Check if node falls within zone boundaries
            if in_x_range and min_y <= node_y <= max_y:
                nodes_in_zones[zone_idx].append(node)
    
    return nodes_in_zones

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

def find_multiple_paths(subgraph, source=-1, target=-2):
    """Find three shortest paths between source and target."""
    paths = []
    lengths = []
    G_temp = subgraph.copy()
    
    for i in range(3):
        try:
            path = nx.shortest_path(G_temp, source=source, target=target, weight="length")
            length = sum(G_temp[u][v]['length'] for u, v in zip(path, path[1:]))
            paths.append(path)
            lengths.append(length)
            
            # Remove inner nodes of the found path for next iteration
            if i < 2:  # Don't remove after finding the third path
                G_temp.remove_nodes_from(path[1:-1])
                
        except nx.NetworkXNoPath:
            print(f"No path #{i+1} found between node {source} and node {target}.")
            break
    
    return paths, lengths

def get_node_styling(node, ground_stations, shortest_path):
    """Determine node color and size based on node type."""
    if node in ground_stations:
        return 'red', 400
    elif node in shortest_path:
        return 'royalblue', 300
    else:
        return 'skyblue', 200

def get_edge_styling(edge, shortest_path, ground_stations):
    """Determine edge color, width, and style based on edge type."""
    node1, node2 = edge
    if node1 in shortest_path and node2 in shortest_path:
        return 'black', 2, '-'
    elif node1 in ground_stations or node2 in ground_stations:
        return 'blue', 0.5, '--'
    else:
        return 'gray', 0.5, '-'

def plot_network(subgraph, positions, shortest_path, ground_stations, spare_zones):
    """Plot the network graph with all styling and annotations."""
    plt.figure(figsize=(12, 12))
    
    # Prepare node styling
    node_colors = []
    node_sizes = []
    for node in subgraph.nodes():
        color, size = get_node_styling(node, ground_stations, shortest_path)
        node_colors.append(color)
        node_sizes.append(size)
    
    # Prepare edge styling
    edge_colors = []
    edge_widths = []
    edge_styles = []
    for edge in subgraph.edges():
        color, width, style = get_edge_styling(edge, shortest_path, ground_stations)
        edge_colors.append(color)
        edge_widths.append(width)
        edge_styles.append(style)
    
    # Draw nodes and edges
    nx.draw_networkx_nodes(subgraph, positions, node_size=node_sizes, node_color=node_colors, alpha=0.9)
    nx.draw_networkx_edges(subgraph, positions, edge_color=edge_colors, width=edge_widths, style=edge_styles, alpha=0.7)
    
    # Add labels
    labels = {node: "LDN" if node == -1 else "NYC" if node == -2 else str(node) for node in subgraph.nodes()}
    nx.draw_networkx_labels(subgraph, positions, labels, font_size=8, font_color='black')
    
    # Add edge labels
    edge_labels = nx.get_edge_attributes(subgraph, 'length')
    rounded_edge_labels = {key: round(val, 1) for key, val in edge_labels.items()}
    nx.draw_networkx_edge_labels(subgraph, positions, edge_labels=rounded_edge_labels, font_size=3, 
                                verticalalignment="bottom", alpha=0.9)
    
    # Draw spare zones
    for i, spare_zone in enumerate(spare_zones):
        plot_spare_zone(positions, spare_zone, i)
    
    plt.axis('off')
    plt.show()

def plot_spare_zone(positions, spare_zone, zone_index):
    """Plot a single spare zone with offset box."""
    offset = 0.25
    zone_coords = [
        (positions[spare_zone[0]][0] - 2*offset, positions[spare_zone[0]][1] + offset),
        (positions[spare_zone[1]][0] + offset, positions[spare_zone[1]][1] + offset),
        (positions[spare_zone[3]][0] + 2*offset, positions[spare_zone[3]][1] - offset),
        (positions[spare_zone[2]][0] - offset, positions[spare_zone[2]][1] - offset),
    ]
    
    zone_x, zone_y = zip(*zone_coords)
    zone_x = list(zone_x) + [zone_x[0]]
    zone_y = list(zone_y) + [zone_y[0]]
    
    plt.plot(zone_x, zone_y, 'r--', linewidth=1.0, label=f"Spare Capacity Zone {zone_index+1}")

def main():
    # Constants
    GROUND_STATIONS = [-1, -2]  # LDN and NYC
    SPARE_ZONES = [(269, 328, 334, 393), (467, 522, 532, 587)]
    
    # Build and analyze network
    G = parse_network_file('snapshots/snapshot0.02s.txt')
    positions = calculate_node_positions(G)
    
    # Find nodes in spare zones
    nodes_in_zones = find_nodes_in_spare_zones(G, SPARE_ZONES)
    for zone_idx, nodes in nodes_in_zones.items():
        print(f"\nNodes in Spare Zone {zone_idx + 1}:")
        print(f"Total nodes: {len(nodes)}")
        print(f"Node numbers: {sorted(nodes)}")
    
    subgraph = create_subgraph(G, positions, GROUND_STATIONS)
    
    # Find paths
    paths, lengths = find_multiple_paths(subgraph)
    if paths:
        for i, (path, length) in enumerate(zip(paths, lengths)):
            print(f"Path {i+1}: {path}")
            print(f"Length {i+1}: {length}")
    
    # Plot network
    plot_network(subgraph, positions, paths[0] if paths else [], GROUND_STATIONS, SPARE_ZONES)

if __name__ == "__main__":
    main()