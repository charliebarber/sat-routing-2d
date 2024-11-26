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

shortest_path = None

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
    elif x < 26 or x > 38:
        nodes_to_remove.append(node)
    elif y < -10 or y > -4:
        nodes_to_remove.append(node)
    # else:
        # print(f"node: {node}, pos: {pos}")

subgraph.remove_nodes_from(nodes_to_remove)

# Node coloring and sizing
node_colors = []
node_sizes = []
for node in subgraph.nodes():
    if node in ground_stations:
        node_colors.append('red')  # Ground stations
        node_sizes.append(400)
    elif node in shortest_path:
        node_colors.append('green')  # Shortest path nodes
        node_sizes.append(300)
    else:
        node_colors.append('skyblue')  # Other nodes
        node_sizes.append(200)

# Edge styling: Differentiate shortest path edges
edge_colors = []
edge_widths = []
for edge in subgraph.edges():
    node1, node2 = edge
    if node1 in (shortest_path) and node2 in (shortest_path):  # Both nodes are in the shortest path
        edge_colors.append('red')
        edge_widths.append(2)
    elif node1 in ground_stations or node2 in ground_stations:  # GS-Sat links
        edge_colors.append("blue")
        edge_widths.append(0.5)
    else:  # Inter-orbit links and intra
        edge_colors.append("gray")
        edge_widths.append(0.5)
# Use a less cluttered layout
# pos = nx.spring_layout(subgraph, seed=22)  # Increase k to spread nodes more

# Plot the graph
plt.figure(figsize=(10, 10))

# Draw nodes
nx.draw_networkx_nodes(subgraph, positions, node_size=node_sizes, node_color=node_colors, alpha=0.9)

# Draw edges
nx.draw_networkx_edges(subgraph, positions, edge_color=edge_colors, width=edge_widths, alpha=0.7)

# Label important nodes only
labels = {node: str(node) for node in subgraph.nodes() }
nx.draw_networkx_labels(G, positions, labels, font_size=5, font_color='black')

# Add title and display
plt.axis('off')
plt.show()