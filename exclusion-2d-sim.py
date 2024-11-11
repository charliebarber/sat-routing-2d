import networkx as nx
import matplotlib.pyplot as plt
from itertools import islice
import numpy as np

def create_inclined_constellation(num_planes=6, sats_per_plane=10, inclination=0.5, excluded_edges=None):
    G = nx.Graph()
    pos = {}

    # Initialize excluded_edges as an empty list if None
    excluded_edges = excluded_edges or []

    # Create satellites in an inclined grid format
    for plane in range(num_planes):
        for sat in range(sats_per_plane):
            node_id = (plane, sat)
            x = sat + plane * inclination
            y = -plane
            pos[node_id] = (x, y)
            G.add_node(node_id, pos=pos[node_id])

            # Connect to the next satellite in the same plane (wrap around)
            next_sat = (sat + 1) % sats_per_plane
            if (node_id, (plane, next_sat)) not in excluded_edges:
                G.add_edge(node_id, (plane, next_sat))

            # Connect to the satellite directly in the next plane
            if plane < num_planes - 1:
                if (node_id, (plane + 1, sat)) not in excluded_edges:
                    G.add_edge(node_id, (plane + 1, sat))

    return G, pos

def add_ground_stations_inclined(G, pos, LDN_x, NYC_x, sats_per_plane, excluded_edges=None):
    excluded_edges = excluded_edges or []
    G.add_node("LDN", pos=(LDN_x, 1))
    G.add_node("NYC", pos=(NYC_x, -len(pos) // sats_per_plane - 1))

    # Connect LDN to its nearest satellite in the first plane
    if ("LDN", (0, int(LDN_x / (1 + 0.5)))) not in excluded_edges:
        G.add_edge("LDN", (0, int(LDN_x / (1 + 0.5))))

    # Connect NYC to its nearest satellite in the last plane
    if ("NYC", (len(pos) // sats_per_plane - 1, int(NYC_x / (1 + 0.5)))) not in excluded_edges:
        G.add_edge("NYC", (len(pos) // sats_per_plane - 1, int(NYC_x / (1 + 0.5))))

    pos["LDN"] = (LDN_x, 1)
    pos["NYC"] = (NYC_x, -len(pos) // sats_per_plane - 1)

def plot_inclined_constellation(G, pos, paths, excluded_edges=None):
    excluded_edges = excluded_edges or []
    plt.figure(figsize=(14, 10))

    # Draw the entire constellation first with light edges
    nx.draw(G, pos, with_labels=False, node_size=100, node_color="lightblue", edge_color="gray")

    # Edge usage count to track shared edges
    edge_usage = {}

    # Color code for paths (4 paths)
    colors = ["red", "blue", "green", "purple"]

    # Iterate through each path and count the edge usage
    for i, path in enumerate(paths):
        path_edges = list(zip(path, path[1:]))
        
        # Increment usage for each edge in the path
        for edge in path_edges:
            if edge not in edge_usage:
                edge_usage[edge] = 0
            edge_usage[edge] += 1
        
        # Draw the path edges with transparency or varying thickness
        for edge in path_edges:
            # Calculate transparency based on usage (more paths -> more transparency)
            usage = edge_usage[edge]
            alpha = max(0.2, 1 - 0.3 * (usage - 1))  # Set a minimum opacity to avoid complete transparency
            nx.draw_networkx_edges(G, pos, edgelist=[edge], width=2.5, edge_color=colors[i], alpha=alpha)

        nx.draw_networkx_nodes(G, pos, nodelist=path, node_size=150, node_color=colors[i])

        # Log the path to the console
        print(f"Path {i+1}: {path}")

    # Highlight excluded edges (black dashed lines)
    for edge in excluded_edges:
        nx.draw_networkx_edges(G, pos, edgelist=[edge], edge_color="black", width=2, style='dashed')

    # Highlight ground stations
    nx.draw_networkx_nodes(G, pos, nodelist=["LDN"], node_color="red", node_size=300, label="LDN")
    nx.draw_networkx_nodes(G, pos, nodelist=["NYC"], node_color="green", node_size=300, label="NYC")

    # Add labels for ground stations
    nx.draw_networkx_labels(G, pos, labels={"LDN": "LDN", "NYC": "NYC"}, font_size=12, font_color="black")

    # Add satellite position labels
    satellite_labels = {node: f"{node}" for node in G.nodes if isinstance(node, tuple)}
    for node, (x, y) in pos.items():
        if node in satellite_labels:
            plt.text(x, y - 0.25, satellite_labels[node], fontsize=8, ha="center", color="darkblue")

    plt.title("Inclined 2D Projection of Satellite Constellation with Highlighted Paths")
    plt.legend(loc="upper right")
    plt.show()

def find_multiple_shortest_paths(G, source="LDN", destination="NYC", k=4, excluded_edges=None):
    try:
        # Remove the excluded edges temporarily for pathfinding
        G_copy = G.copy()
        G_copy.remove_edges_from(excluded_edges)
        
        # Find the k shortest paths using the modified graph
        paths = list(islice(nx.shortest_simple_paths(G_copy, source=source, target=destination), k))
        return paths
    except nx.NetworkXNoPath:
        print(f"No path found between {source} and {destination}")
        return []

def generate_ns3_code_for_paths(paths, num_satellites=60):
    ns3_code = []
    
    # Set up satellite nodes in NS-3
    ns3_code.append("// Create satellite nodes")
    for i in range(num_satellites):
        ns3_code.append(f"Ptr<Node> satellite_{i} = CreateObject<Node>();")

    ns3_code.append("// Create ground station nodes")
    ns3_code.append("Ptr<Node> ground_LDN = CreateObject<Node>();")
    ns3_code.append("Ptr<Node> ground_NYC = CreateObject<Node>();")

    # For each path, generate the code to connect the satellites
    ns3_code.append("// Set up point-to-point links between satellites for each path")
    for path_index, path in enumerate(paths):
        ns3_code.append(f"// Path {path_index + 1} from LDN to NYC")
        for i in range(len(path) - 1):
            node1 = path[i]
            node2 = path[i + 1]
            
            # Assuming the node names are tuples of (plane, satellite)
            if node1 == "LDN":
                ns3_code.append(f"PointToPointHelper p2p_{path_index}_{i};")
                ns3_code.append(f"p2p_{path_index}_{i}.Install(ground_LDN, satellite_{node2[0] * num_satellites + node2[1]});")
            elif node2 == "NYC":
                ns3_code.append(f"PointToPointHelper p2p_{path_index}_{i};")
                ns3_code.append(f"p2p_{path_index}_{i}.Install(satellite_{node1[0] * num_satellites + node1[1]}, ground_NYC);")
            else:
                ns3_code.append(f"PointToPointHelper p2p_{path_index}_{i};")
                ns3_code.append(f"p2p_{path_index}_{i}.Install(satellite_{node1[0] * num_satellites + node1[1]}, satellite_{node2[0] * num_satellites + node2[1]});")

    return ns3_code

def save_ns3_code_to_file(ns3_code, filename="ns3_configuration.txt"):
    with open(filename, "w") as f:
        for line in ns3_code:
            f.write(line + "\n")

def main():
    # Parameters for the constellation grid
    num_planes = 6
    sats_per_plane = 12
    inclination = 0.9  # Controls the "angle" of each orbital plane

    constellation, positions = create_inclined_constellation(num_planes=num_planes, sats_per_plane=sats_per_plane, inclination=inclination)
    
    LDN_x = 4  # X-coordinate near first plane
    NYC_x = 7     # X-coordinate near last plane

    # Excluded edges
    excluded_edges = [((0, 1), (0, 2)), ((0, 1), (0, 3))]
    # excluded_edges = [((0, 1), (0, 2)), ((4,4), (5,4))]
    # excluded_edges = [((2,3), (3,3)), ((3,3), (4,3))]
    # excluded_edges = []

    add_ground_stations_inclined(constellation, positions, LDN_x, NYC_x, sats_per_plane, excluded_edges)

    paths = find_multiple_shortest_paths(constellation, source="LDN", destination="NYC", k=4, excluded_edges=excluded_edges)

    ns3_code = generate_ns3_code_for_paths(paths)

    save_ns3_code_to_file(ns3_code)

    plot_inclined_constellation(constellation, positions, paths, excluded_edges)

if __name__ == "__main__":
    main()
