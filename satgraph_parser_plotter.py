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

def find_path_via_spare_zones(G, positions, nodes_in_zones, source=-1, target=-2, excluded_edges=None):
    """
    Find path via spare zones using same initial RF link as shortest path,
    ensuring total path weight is at or above 125% of shortest path weight
    """
    # Create copy of graph
    G_copy = G.copy()
    
    # Get shortest path and details
    shortest_path = nx.shortest_path(G_copy, source=source, target=target, weight='length')
    shortest_weight = sum(G_copy[u][v]['length'] for u, v in zip(shortest_path, shortest_path[1:]))
    target_weight = shortest_weight * 1.25  # This is our minimum acceptable weight
    initial_sat = shortest_path[1]
    
    # Remove edges from shortest path (except initial RF link)
    edges_to_remove = list(zip(shortest_path[1:-1], shortest_path[2:-1]))
    G_copy.remove_edges_from(edges_to_remove)
    print(f"Edges excluded are: {edges_to_remove}")

    G_copy.remove_edges_from([(initial_sat, source)])
    
    best_path = None
    best_weight = float('inf')
    best_zone_idx = None
    best_entry_path = None
    best_entry_path_weight = float('inf')
    
    # Try to reach a zone from the initial sat
    for zone_idx, zone_nodes in nodes_in_zones.items():
        print(f"\nTrying zone {zone_idx + 1}")
        
        # Find all possible paths through this zone
        for zone_node in zone_nodes:
            try:
                # Find a path to this zone node
                entry_path = nx.shortest_path(G_copy, source=initial_sat, target=zone_node, weight='length')
                
                # Check if it is the shortest path to a zone yet
                entry_path_weight = sum(G_copy[u][v]['length'] for u, v in zip(entry_path, entry_path[1:]))

                if entry_path_weight < best_entry_path_weight:
                    best_entry_path = entry_path
                    best_entry_path_weight = entry_path_weight
                    best_zone_idx = zone_idx
                        
            except nx.NetworkXNoPath:
                continue

    best_exit_path = None
    best_exit_path_weight = float('inf')
    
    # Find best exit path from the chosen zone
    for zone_node in nodes_in_zones[best_zone_idx]:
        try:
            # Find a path to this same zone from the destination
            exit_path = nx.shortest_path(G_copy, source=target, target=zone_node, weight='length')

            exit_path_weight = sum(G_copy[u][v]['length'] for u, v in zip(exit_path, exit_path[1:]))
            if exit_path_weight < best_exit_path_weight:
                best_exit_path = exit_path
                best_exit_path_weight = exit_path_weight
                
        except nx.NetworkXNoPath:
            continue

    print(f"best_entry_path: {best_entry_path}")
    print(f"best_exit_path: {best_exit_path}")

    if best_entry_path and best_exit_path:
        # Calculate current weight without zone path
        rf_weight = G[source][initial_sat]['length']
        current_weight = rf_weight + best_entry_path_weight + best_exit_path_weight
        print(f"best_entry_path: {best_entry_path}")
        print(f"best_exit_path: {best_exit_path}")
        print(f"current_weight: {current_weight}")
        
        # Calculate how much additional weight we need
        needed_weight = max(0, target_weight - current_weight)
        print(f"needed_weight: {needed_weight}")
        
        # Find path between entry and exit nodes that gets us to target weight
        entry_node = best_entry_path[-1]
        exit_node = best_exit_path[-1]
        print(f"entry_node: {entry_node}, exit_node: {exit_node}")
        
        try:
            # First try shortest path through zone
            zone_path = nx.shortest_path(G_copy, entry_node, exit_node, weight='length')
            zone_weight = sum(G_copy[u][v]['length'] for u, v in zip(zone_path, zone_path[1:]))
            total_weight = current_weight + zone_weight
            print(f"zone_path: {zone_path}")
            needed_weight = target_weight - total_weight
            print(f"needed_weight: {needed_weight}")
            
            # keep adding edges until you hit or exceed the target
            while needed_weight > 0:
                # Find all nodes in our zone that aren't in our current path
                available_nodes = [n for n in nodes_in_zones[best_zone_idx] 
                                 if n not in zone_path]
                
                if not available_nodes:
                    break
                    
                # Try inserting each available node at each position in our path
                best_insertion = None
                best_insertion_weight = float('inf')
                
                for node in available_nodes:
                    # Try inserting at each position in the path
                    for i in range(1, len(zone_path)):
                        try:
                            # Create temporary graph excluding used nodes to prevent reuse
                            H = G_copy.copy()
                            used_nodes = set(zone_path) - {zone_path[i-1], zone_path[i]}
                            H.remove_nodes_from(used_nodes)
                            
                            # Get path to and from the insertion point
                            path_to = nx.shortest_path(H, zone_path[i-1], node, weight='length')
                            path_from = nx.shortest_path(H, node, zone_path[i], weight='length')
                            
                            # Verify no nodes are reused in the new paths
                            all_nodes = set(path_to[1:-1] + path_from[1:-1])
                            if all_nodes & set(zone_path):
                                continue
                            
                            # Calculate new path segment weight
                            segment_weight = (sum(G_copy[u][v]['length'] 
                                           for u, v in zip(path_to, path_to[1:])) +
                                           sum(G_copy[u][v]['length'] 
                                           for u, v in zip(path_from, path_from[1:])))
                            
                            # Calculate weight difference from original segment
                            original_weight = G_copy[zone_path[i-1]][zone_path[i]]['length']
                            weight_increase = segment_weight - original_weight
                            
                            # If this gets us closer to our target, store it
                            if weight_increase > 0 and weight_increase < best_insertion_weight:
                                best_insertion = (i, node, path_to, path_from)
                                best_insertion_weight = weight_increase
                                
                        except nx.NetworkXNoPath:
                            continue
                
                if best_insertion:
                    # Insert the best node we found
                    i, node, path_to, path_from = best_insertion
                    zone_path = (zone_path[:i-1] + path_to + 
                               path_from[1:] + zone_path[i+1:])
                    
                    # Update weights
                    zone_weight += best_insertion_weight
                    total_weight += best_insertion_weight
                    needed_weight -= best_insertion_weight
                    print(f"Added node {node}, new total weight: {total_weight}")
                else:
                    break  # No valid insertions found
            
            # final path
            if total_weight >= target_weight:
                complete_path = ([source] + best_entry_path[:-1] + 
                               zone_path + 
                               best_exit_path[:-1][::-1])
                best_path = complete_path
                best_weight = total_weight

        except nx.NetworkXNoPath:
            pass
    
    if best_path:
        print(f"\nFound path through zone {best_zone_idx + 1}")
        print(f"Path weight: {best_weight:.2f} (shortest possible: {shortest_weight:.2f})")
        print(f"Weight increase: {((best_weight/shortest_weight) - 1) * 100:.1f}%")
        return [best_path]
        
    return []

def get_node_styling(node, ground_stations, shortest_path, spare_path=None):
    """Determine node color and size based on node type."""
    if node in ground_stations:
        return 'red', 400
    elif spare_path and node in spare_path:
        return 'green', 300
    elif node in shortest_path:
        return 'royalblue', 300
    else:
        return 'skyblue', 200

def get_edge_styling(edge, shortest_path, ground_stations, spare_path=None):
    """Determine edge color, width, and style based on edge type."""
    node1, node2 = edge
    
    # Check if this edge is actually part of the spare path sequence
    if spare_path:
        for i in range(len(spare_path) - 1):
            if (node1 == spare_path[i] and node2 == spare_path[i + 1]) or \
               (node2 == spare_path[i] and node1 == spare_path[i + 1]):
                return 'green', 2, '-'
    
    # Check if edge is part of shortest path sequence
    if shortest_path:
        for i in range(len(shortest_path) - 1):
            if (node1 == shortest_path[i] and node2 == shortest_path[i + 1]) or \
               (node2 == shortest_path[i] and node1 == shortest_path[i + 1]):
                return 'black', 2, '-'
    
    # Ground station connections
    if node1 in ground_stations or node2 in ground_stations:
        return 'blue', 0.5, '--'
        
    # All other edges
    return 'gray', 0.5, '-'

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

def plot_network(subgraph, positions, shortest_path, ground_stations, spare_zones, spare_path=None):
    """Plot the network graph with all styling and annotations."""
    plt.figure(figsize=(12, 12))
    
    # Prepare node styling
    node_colors = []
    node_sizes = []
    for node in subgraph.nodes():
        color, size = get_node_styling(node, ground_stations, shortest_path, spare_path)
        node_colors.append(color)
        node_sizes.append(size)
    
    # Prepare edge styling
    edge_colors = []
    edge_widths = []
    edge_styles = []
    for edge in subgraph.edges():
        color, width, style = get_edge_styling(edge, shortest_path, ground_stations, spare_path)
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
    
    # Find regular shortest paths
    paths, lengths = find_multiple_paths(subgraph)
    if paths:
        print("\nRegular shortest paths:")
        for i, (path, length) in enumerate(zip(paths, lengths)):
            print(f"Path {i+1}: {path}")
            print(f"Length {i+1}: {length}")
    
    # Find path via spare zones
    spare_paths = find_path_via_spare_zones(subgraph, positions, nodes_in_zones)
    if spare_paths:
        print("\nPath via spare zones:")
        for i, path in enumerate(spare_paths):
            print(f"Spare zone path {i+1}: {path}")
            length = sum(subgraph[u][v]['length'] for u, v in zip(path, path[1:]))
            print(f"Length: {length}")
    
    # Plot network with both regular shortest path and spare zone path
    plot_network(subgraph, positions, 
                shortest_path=paths[0] if paths else [],
                ground_stations=GROUND_STATIONS,
                spare_zones=SPARE_ZONES,
                spare_path=spare_paths[0] if spare_paths else None)

if __name__ == "__main__":
    main()

def get_node_styling(node, ground_stations, shortest_path, spare_path=None):
    """Determine node color and size based on node type."""
    if node in ground_stations:
        return 'red', 400
    elif spare_path and node in spare_path:
        return 'green', 300
    elif node in shortest_path:
        return 'royalblue', 300
    else:
        return 'skyblue', 200

def get_edge_styling(edge, shortest_path, ground_stations, spare_path=None):
    """Determine edge color, width, and style based on edge type."""
    node1, node2 = edge
    
    # Check if this edge is actually part of the spare path sequence
    if spare_path:
        for i in range(len(spare_path) - 1):
            if (node1 == spare_path[i] and node2 == spare_path[i + 1]) or \
               (node2 == spare_path[i] and node1 == spare_path[i + 1]):
                return 'green', 2, '-'
    
    # Check if edge is part of shortest path sequence
    if shortest_path:
        for i in range(len(shortest_path) - 1):
            if (node1 == shortest_path[i] and node2 == shortest_path[i + 1]) or \
               (node2 == shortest_path[i] and node1 == shortest_path[i + 1]):
                return 'black', 2, '-'
    
    # Ground station connections
    if node1 in ground_stations or node2 in ground_stations:
        return 'blue', 0.5, '--'
        
    # All other edges
    return 'gray', 0.5, '-'

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

def plot_network(subgraph, positions, shortest_path, ground_stations, spare_zones, spare_path=None):
    """Plot the network graph with all styling and annotations."""
    plt.figure(figsize=(12, 12))
    
    # Prepare node styling
    node_colors = []
    node_sizes = []
    for node in subgraph.nodes():
        color, size = get_node_styling(node, ground_stations, shortest_path, spare_path)
        node_colors.append(color)
        node_sizes.append(size)
    
    # Prepare edge styling
    edge_colors = []
    edge_widths = []
    edge_styles = []
    for edge in subgraph.edges():
        color, width, style = get_edge_styling(edge, shortest_path, ground_stations, spare_path)
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
    
    # Find regular shortest paths
    paths, lengths = find_multiple_paths(subgraph)
    if paths:
        print("\nRegular shortest paths:")
        for i, (path, length) in enumerate(zip(paths, lengths)):
            print(f"Path {i+1}: {path}")
            print(f"Length {i+1}: {length}")
    
    # Find path via spare zones
    spare_paths = find_path_via_spare_zones(subgraph, positions, nodes_in_zones)
    if spare_paths:
        print("\nPath via spare zones:")
        for i, path in enumerate(spare_paths):
            print(f"Spare zone path {i+1}: {path}")
            length = sum(subgraph[u][v]['length'] for u, v in zip(path, path[1:]))
            print(f"Length: {length}")
    
    # Plot network with both regular shortest path and spare zone path
    plot_network(subgraph, positions, 
                shortest_path=paths[0] if paths else [],
                ground_stations=GROUND_STATIONS,
                spare_zones=SPARE_ZONES,
                spare_path=spare_paths[0] if spare_paths else None)

if __name__ == "__main__":
    main()