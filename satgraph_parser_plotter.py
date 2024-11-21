import networkx as nx
import matplotlib.pyplot as plt
import re

# Initialize the graph
G = nx.Graph()

# Parse the file
with open('snapshots/satgraph_time0.02.txt', 'r') as file:
    for line in file:
        if line.startswith("Node"):
            node_match = re.match(r"Node (\d+) with links:", line)
            if node_match:
                node = int(node_match.group(1))
                G.add_node(node)
        
        # Check for links in the line
        link_matches = re.findall(r"Link \((\d+),(\d+)\) \(length ([\d.]+)", line)
        for link in link_matches:
            node1, node2, length = int(link[0]), int(link[1]), float(link[2])
            G.add_edge(node1, node2, length=length)

# Optional: Filter nodes based on degree or some property
# For example, keep only nodes with degree > 2
filtered_nodes = [node for node, degree in dict(G.degree()).items() if degree > 2]
G = G.subgraph(filtered_nodes).copy()

# Use a layout optimized for large graphs
pos = nx.spring_layout(G, k=0.1, seed=42)  # k parameter controls spacing

# Configure plot
plt.figure(figsize=(12, 12))
plt.title("Large Graph with Filtered Nodes and Scaled Edge Widths")
plt.axis('off')

# Draw nodes with scaling based on degree
node_sizes = [100 + 10 * G.degree(node) for node in G.nodes()]
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='skyblue', alpha=0.7)

# Draw edges with transparency and scaled widths based on length
edges = G.edges(data=True)
edge_widths = [min(d['length'] / 500, 2) for (u, v, d) in edges]  # Scale down widths for readability
nx.draw_networkx_edges(G, pos, edgelist=edges, width=edge_widths, alpha=0.3)

# Optionally add labels only for key nodes
nx.draw_networkx_labels(G, pos, font_size=8, font_color="black")

plt.show()
