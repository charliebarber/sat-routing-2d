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
                print(f"Added node {node}")  # Debugging: Print node being added
        
        # Check for links in the line
        # Updated regex to allow for negative numbers (\-?\d+)
        link_matches = re.findall(r"Link \((\-?\d+),(\-?\d+)\) \(length ([\d.]+), y value of the midpoint ([\d.]+)\)", line)
        for link in link_matches:
            node1, node2, length, y_value = int(link[0]), int(link[1]), float(link[2]), float(link[3])
            G.add_edge(node1, node2, length=length, y_value=y_value)  # Add edge with length and y-value
            print(f"Added edge - {node1} -> {node2}")  # Debugging: Print edge being added


# Get the neighbours of nodes -1 and -2
neighbours = set()
for station in ground_stations:
    if station not in G.nodes:
        print(f"Warning: Node {station} is not in the graph.")  # Debugging: Print warning if node is missing
    else:
        # Get direct neighbours (i.e., nodes connected to node -1 and -2)
        for neighbour in G.neighbors(station):
            print(f"Node {station} is connected to Node {neighbour}")  # Debugging: Print connections
            neighbours.add(neighbour)

# Add the ground stations themselves to the neighbours set
neighbours.update(ground_stations)

shortest_path = None

# Find the shortest path from -1 to -2
if -1 in G.nodes and -2 in G.nodes:
    try:
        shortest_path = nx.shortest_path(G, source=-1, target=-2, weight="length")
        print(f"Shortest path from -1 to -2: {shortest_path}")
        
        # Add all the nodes in the shortest path to the neighbours set
        neighbours.update(shortest_path)
        
        # Add nodes that are 1 link away from each node on the shortest path
        for node in shortest_path[1:-1]:
            for neighbour in G.neighbors(node):
                neighbours.add(neighbour)
                for neighbour_neighbour in G.neighbors(neighbour):
                    neighbours.add(neighbour_neighbour)

                    for neighbour_neighbour_neighbour in G.neighbors(neighbour_neighbour):
                       neighbours.add(neighbour_neighbour_neighbour) 

                print(f"Node {node} has neighbour {neighbour} (1 link away)")  # Debugging: Print neighbours of nodes in the path
    except nx.NetworkXNoPath:
        print("No path found between node -1 and node -2.")


# Create a subgraph containing only the ground stations, their neighbours, and the shortest path nodes
subgraph = G.subgraph(neighbours).copy()

edges_to_remove = []
for edge in subgraph.edges():
    node1, node2 = edge
    # Check if either node1 or node2 connects to only one other node
    if len(list(subgraph.neighbors(node1))) <= 1 or len(list(subgraph.neighbors(node2))) <= 1:
        edges_to_remove.append(edge)

# Remove the identified edges
print(f"Edges to remove: {edges_to_remove}")
subgraph.remove_edges_from(edges_to_remove)
                           
isolated_nodes = list(nx.isolates(subgraph))
print(f"Isolated nodes to remove: {isolated_nodes}")
subgraph.remove_nodes_from(isolated_nodes)

# Node coloring and sizing
node_colors = []
node_sizes = []
for node in subgraph.nodes():
    if node in ground_stations:
        node_colors.append('red')  # Ground stations
        node_sizes.append(500)
    elif node in shortest_path:
        node_colors.append('green')  # Shortest path nodes
        node_sizes.append(400)
    else:
        node_colors.append('skyblue')  # Other nodes
        node_sizes.append(200)

# Edge styling: Differentiate shortest path edges
edge_colors = []
edge_widths = []
for edge in subgraph.edges():
    if set(edge).issubset(shortest_path):  # Both nodes are in the shortest path
        edge_colors.append('blue')
        edge_widths.append(2)
    else:
        edge_colors.append('gray')
        edge_widths.append(1)

# Use a less cluttered layout
pos = nx.spring_layout(subgraph, seed=22)  # Increase k to spread nodes more

# Plot the graph
plt.figure(figsize=(10, 10))

# Draw nodes
nx.draw_networkx_nodes(subgraph, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)

# Draw edges
nx.draw_networkx_edges(subgraph, pos, edge_color=edge_colors, width=edge_widths, alpha=0.7)

# Label important nodes only
labels = {node: str(node) for node in subgraph.nodes() if node in ground_stations or node in shortest_path}
nx.draw_networkx_labels(subgraph, pos, labels, font_size=10, font_color='black')

# Add title and display
plt.axis('off')
plt.show()

# Check the nodes and edges of the subgraph
print(f"Subgraph nodes: {list(subgraph.nodes())}")
print(f"Subgraph edges: {list(subgraph.edges())}")

# Now you can visualize or process the filtered subgraph
pos = nx.spring_layout(subgraph, seed=42, weight="length")  # Using spring layout for the visualization

# Plot the subgraph
plt.figure(figsize=(8, 8))
nx.draw_networkx_nodes(subgraph, pos, node_size=300, node_color='skyblue')
nx.draw_networkx_labels(subgraph, pos, font_size=10, font_weight='bold')
nx.draw_networkx_edges(subgraph, pos, width=1, alpha=0.7, edge_color='gray')

plt.axis('off')
plt.show()
