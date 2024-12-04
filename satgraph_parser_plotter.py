import networkx as nx
import re
import matplotlib.pyplot as plt

# Initialize the graph
G = nx.Graph()

# Ground stations (nodes -1 and -2)
ground_stations = [-1, -2]

# Parse the file and build the graph
with open('snapshots/snapshot0.02s.txt', 'r') as file:
    for line in file:
        # Check if the line describes a node and its links
        if line.startswith("Node"):
            node_match = re.match(r"Node (\-?\d+) with links:", line)  # Match negative numbers correctly
            if node_match:
                node = int(node_match.group(1))
                G.add_node(node)  # Add the node to the graph
        
        # Check for links in the line
        link_matches = re.findall(r"Link \((\-?\d+),(\-?\d+)\) \(length ([\d.]+), y value of the midpoint ([\-.\d]+)\)", line)
        for link in link_matches:
            node1, node2, length, y_value = int(link[0]), int(link[1]), float(link[2]), float(link[3])
            G.add_edge(node1, node2, length=length, y_value=y_value)  # Add edge with length and y-value
            # print(f"Added edge: {node1} -> {node2} , length = {length}, y_value = {y_value}")

positions = {}
for node in G.nodes():
    if node >= 0:
        plane = node // 66 # 66 sats per plane
        # index_in_plane = node % 25 # 25 orbital plane
        index_in_plane = 66 - (node - (66 * plane))

        # print(f"plane: {plane} index_in_plane: {index_in_plane}")

        if index_in_plane > 32:
            x = index_in_plane - 33
        else:
            x = index_in_plane + 33
        y = -plane
        positions[node] = (x, y)

# Set ground station nodes, -1 = LDN, -2 = NYC
positions[-1] = (38.5, -5.5) # LDN
positions[-2] = (25, -6.5) # NYC

# spare zone is 4-tuple: top left, top right, 
spare_zones = [(269, 328, 334, 393), (467, 522, 532, 587)]

def generate_nodes_from_zone(zone_corners):
    """
    Generate all nodes within the rectangular grid defined by 4 corner nodes.
    Assumes the zone is aligned along axes.
    """
    # Extract min and max coordinates from the zone corners
    x_coords = [corner[0] for corner in zone_corners]
    y_coords = [corner[1] for corner in zone_corners]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # Generate all nodes within the rectangular area
    return [(x, y) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1)]

shortest_path = None
second_shortest = None

# Find the shortest path from -1 to -2
if -1 in G.nodes and -2 in G.nodes:
    try:
        shortest_path = nx.shortest_path(G, source=-1, target=-2, weight="length")
        print(f"Shortest path from -1 to -2: {shortest_path}")
    except nx.NetworkXNoPath:
        print("No path found between node -1 and node -2.")



# Create a subgraph containing nearby nodes to path
subgraph = G.copy()
# subgraph.remove_nodes_from(ground_stations)

edges_to_remove = []
nodes_to_remove = []
for node in subgraph.nodes():
    pos = positions[node]
    x = pos[0]
    y = pos[1]
    if node in ground_stations:
        continue
    elif x < 26 or x > 40:
        nodes_to_remove.append(node)
    elif y < -8 or y > -4:
        nodes_to_remove.append(node)
    # else:
        # print(f"node: {node}, pos: {pos}")

subgraph.remove_nodes_from(nodes_to_remove)

G_copy = subgraph.copy()
G_copy.remove_nodes_from(shortest_path[1:-1])
second_shortest = nx.shortest_path(G_copy, source=-1, target=-2, weight="length")
second_shortest_length = nx.shortest_path_length(G_copy, source=-1, target=-2, weight="length")
print(f"second_shortest: {second_shortest} length: {second_shortest_length}")

second_weight = 0
for u, v in zip(second_shortest, second_shortest[1:]):
    weight = subgraph[u][v]['length']
    print(f" Edge: {u, v} - Weight: {weight}")
    second_weight += weight
print(f"second_weight: {second_weight}")

G_copy2 = G_copy.copy()
G_copy2.remove_nodes_from(second_shortest[1:-1])
third_shortest = nx.shortest_path(G_copy2, source=-1, target=-2, weight="length")
third_shortest_length = nx.shortest_path_length(G_copy2, source=-1, target=-2, weight="length")
print(f"third_shortest: {third_shortest} length: {third_shortest_length}")

third_weight = 0
for u, v in zip(third_shortest, third_shortest[1:]):
    weight = subgraph[u][v]['length']
    print(f" Edge: {u, v} - Weight: {weight}")
    third_weight += weight
print(f"third_weight: {third_weight}")

# Node coloring and sizing
node_colors = []
node_sizes = []
for node in subgraph.nodes():
    if node in ground_stations:
        node_colors.append('red')  # Ground stations
        node_sizes.append(400)
    elif node in shortest_path:
        node_colors.append('royalblue')  # Shortest path nodes
        node_sizes.append(300)
    else:
        node_colors.append('skyblue')  # Other nodes
        node_sizes.append(200)

# Edge styling: Differentiate shortest path edges
edge_colors = []
edge_widths = []
edge_font_color = []
edge_labels = []
edge_styles = []
for edge in subgraph.edges():
    node1, node2 = edge
    if node1 in (shortest_path) and node2 in (shortest_path):  # Both nodes are in the shortest path
        edge_colors.append('black')
        edge_widths.append(2)
        edge_styles.append('-')
    # elif (node1 in (second_shortest) and node2 in (second_shortest)) or (node1 in (third_shortest) and node2 in (third_shortest)):
        # edge_colors.append('green')
        # edge_widths.append(2)
        # edge_styles.append('-')
    elif node1 in ground_stations or node2 in ground_stations:  # GS-Sat links
        edge_colors.append("blue")
        edge_widths.append(0.5)
        edge_styles.append('--')
    else:  # Inter-orbit links and intra
        edge_colors.append("gray")
        edge_widths.append(0.5)
        edge_styles.append('-')
# Use a less cluttered layout
# pos = nx.spring_layout(subgraph, seed=22)  # Increase k to spread nodes more

# Plot the graph
plt.figure(figsize=(12, 12))

# Draw nodes
nx.draw_networkx_nodes(subgraph, positions, node_size=node_sizes, node_color=node_colors, alpha=0.9)

# Draw edges
nx.draw_networkx_edges(subgraph, positions, edge_color=edge_colors, width=edge_widths, style=edge_styles, alpha=0.7)

# Label important nodes
labels = {node: "LDN" if node == -1 else "NYC" if node == -2 else str(node) for node in subgraph.nodes()}
nx.draw_networkx_labels(subgraph, positions, labels, font_size=8, font_color='black')

# Add edge labels to display weights
edge_labels = nx.get_edge_attributes(subgraph, 'length')
# Round the edge labels for better displaying
rounded_edge_labels = {key: round(val, 1) for key, val in edge_labels.items()}
nx.draw_networkx_edge_labels(subgraph, positions, edge_labels=rounded_edge_labels, font_size=3, verticalalignment="bottom", alpha=0.9)

for i, spare_zone in enumerate(spare_zones):
    # Get the coordinates of the nodes and apply an offset to create a slightly larger box
    offset = 0.25  # Adjust this value to control the offset size
    zone_coords = [
        (positions[spare_zone[0]][0] - 2*offset, positions[spare_zone[0]][1] + offset),  # Top left corner
        (positions[spare_zone[1]][0] + offset, positions[spare_zone[1]][1] + offset),  # Top right corner
        (positions[spare_zone[3]][0] + 2*offset, positions[spare_zone[3]][1] - offset),  # Top-right corner
        (positions[spare_zone[2]][0] - offset, positions[spare_zone[2]][1] - offset),  # Bottom-right corner
    ]

    print(f"zone_coords: {zone_coords}")

    # Unpack x and y coordinates for plotting
    zone_x, zone_y = zip(*zone_coords)
    
    # Close the quadrilateral by appending the first corner to the end of the lists
    zone_x = list(zone_x) + [zone_x[0]]
    zone_y = list(zone_y) + [zone_y[0]]

    # Draw the offset dotted box around the spare capacity zone
    plt.plot(zone_x, zone_y, 'r--', linewidth=1.0, label=f"Spare Capacity Zone {i+1}")

# Add title and display
plt.axis('off')
plt.show()