import networkx as nx
import matplotlib.pyplot as plt
from itertools import islice
import numpy as np

def create_inclined_constellation(num_planes=6, sats_per_plane=10, inclination=0.5, excluded_edges=None):
    G = nx.Graph()
    pos = {}

    excluded_edges = excluded_edges or []

    # Create satellites in an inclined grid format
    for plane in range(num_planes):
        for sat in range(sats_per_plane):
            node_id = (plane, sat)
            x = sat + plane * inclination
            y = -plane
            pos[node_id] = (x, y)
            G.add_node(node_id, pos=pos[node_id])

            # Connect to the next satellite in the same plane (horizontal link, weight 1)
            next_sat = (sat + 1) % sats_per_plane
            if (node_id, (plane, next_sat)) not in excluded_edges:
                G.add_edge(node_id, (plane, next_sat), weight=1)  # Horizontal link with weight 1

            # Connect to the satellite directly in the next plane (vertical link, weight 2)
            if plane < num_planes - 1:
                if (node_id, (plane + 1, sat)) not in excluded_edges:
                    G.add_edge(node_id, (plane + 1, sat), weight=2)  # Vertical link with weight 2

    return G, pos

def add_ground_stations_inclined(G, pos, sats_per_plane, num_planes, excluded_edges=None):
    excluded_edges = excluded_edges or []
    
    # Set coordinates for LDN and NYC with custom offsets
    LDN_pos = (sats_per_plane + 1, -1.4)  # Right and slightly above
    NYC_pos = (-0.5, -2.5)                  # Left and slightly below

    # Add ground station nodes
    G.add_node("LDN", pos=LDN_pos)
    G.add_node("NYC", pos=NYC_pos)

    G.add_edge("LDN", (1, 11))
    G.add_edge("NYC", (3, 0))

    # Update the position dictionary with the new positions for LDN and NYC
    pos["LDN"] = LDN_pos
    pos["NYC"] = NYC_pos


def plot_inclined_constellation(G, pos, paths, excluded_edges=None, spare_zones=None):
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

    for i, spare_zone in enumerate(spare_zones):
        # Get the coordinates of the nodes and apply an offset to create a slightly larger box
        offset = 0.3  # Adjust this value to control the offset size
        zone_coords = [
            (pos[spare_zone[0]][0] - 2*offset, pos[spare_zone[0]][1] + offset),  # Top left corner
            (pos[spare_zone[1]][0] + offset, pos[spare_zone[1]][1] + offset),  # Top right corner
            (pos[spare_zone[3]][0] + 2*offset, pos[spare_zone[3]][1] - offset),  # Top-right corner
            (pos[spare_zone[2]][0] - offset, pos[spare_zone[2]][1] - offset),  # Bottom-right corner
        ]

        # Unpack x and y coordinates for plotting
        zone_x, zone_y = zip(*zone_coords)
        
        # Close the quadrilateral by appending the first corner to the end of the lists
        zone_x = list(zone_x) + [zone_x[0]]
        zone_y = list(zone_y) + [zone_y[0]]

        # Draw the offset dotted box around the spare capacity zone
        plt.plot(zone_x, zone_y, 'r--', linewidth=1.5, label=f"Spare Capacity Zone {i+1}")

    # Add satellite position labels
    satellite_labels = {node: f"{node}" for node in G.nodes if isinstance(node, tuple)}
    for node, (x, y) in pos.items():
        if node in satellite_labels:
            plt.text(x-0.1, y - 0.25, satellite_labels[node], fontsize=8, ha="center", color="darkblue")

    plt.title("Inclined 2D Projection of Satellite Constellation with Highlighted Paths")
    plt.legend(loc="upper right")
    plt.show()

def find_multiple_shortest_paths(G, source="LDN", destination="NYC", k=4, excluded_edges=None):
    try:
        # Remove the excluded edges temporarily for pathfinding
        G_copy = G.copy()
        G_copy.remove_edges_from(excluded_edges)
        
        # Find the k shortest paths using the weighted graph
        paths = list(islice(nx.shortest_simple_paths(G_copy, source=source, target=destination, weight="weight"), k))
        return paths
    except nx.NetworkXNoPath:
        print(f"No path found between {source} and {destination}")
        return []
    
def ensure_edge_weights(G, default_horizontal=1, default_vertical=2):
    for u, v, data in G.edges(data=True):
        # Assign default weights if missing
        if "weight" not in data:
            if u[0] == v[0]:  # Horizontal link
                data["weight"] = default_horizontal
            else:  # Vertical link
                data["weight"] = default_vertical

def find_path_via_spare_zones(G, source="LDN", destination="NYC", spare_zones=None, excluded_edges=None):
    spare_zones = spare_zones or []
    excluded_edges = excluded_edges or []

    # Make a copy of the graph and remove excluded edges
    G_copy = G.copy()
    G_copy.remove_edges_from(excluded_edges)

    # # Ensure every edge has a weight
    ensure_edge_weights(G_copy)

    all_paths = []

    for zone in spare_zones:
        # Identify candidate nodes in this spare zone
        zone_nodes = zone

        # For each node in the spare zone, find paths that do not reuse edges
        for zone_node in zone_nodes:
            try:
                # Find shortest path from source to the current spare zone node
                path_to_zone = nx.shortest_path(G_copy, source=source, target=zone_node, weight="weight")
                
                # Remove edges used in path_to_zone from the graph copy to avoid reuse
                G_temp = G_copy.copy()
                G_temp.remove_edges_from(zip(path_to_zone, path_to_zone[1:]))

                # Find shortest path from the spare zone node to the destination in the modified graph
                path_from_zone = nx.shortest_path(G_temp, source=zone_node, target=destination, weight="weight")

                # Combine the two paths
                full_path = path_to_zone + path_from_zone[1:]  # Avoid repeating the spare zone node

                # Add the combined path to all_paths
                all_paths.append(full_path)

            except nx.NetworkXNoPath:
                print(f"No path found from {source} to {destination} via node {zone_node} in zone {zone}")
                continue

    # Sort all paths by their total weight and return the shortest ones
    all_paths = sorted(all_paths, key=lambda path: nx.path_weight(G_copy, path, weight="weight"))
    return all_paths[:1]  # Return the top 4 shortest paths

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
    inclination = 0.53  # Controls the "angle" of each orbital plane

    constellation, positions = create_inclined_constellation(num_planes=num_planes, sats_per_plane=sats_per_plane, inclination=inclination)
    ensure_edge_weights(constellation)

    LDN_x = 4  # X-coordinate near first plane
    NYC_x = 7     # X-coordinate near last plane

    # Excluded edges
    # excluded_edges = [((0, 1), (0, 2)), ((0, 1), (0, 3))]
    # excluded_edges = [((0, 1), (0, 2)), ((4,4), (5,4))]
    # excluded_edges = [((2,3), (3,3)), ((3,3), (4,3))]
    excluded_edges = [((0, 6), (0,7))]

    # Spare capacity nodes (X1, X2, Y1, Y2)
    # spare_zone = [(4, 3), (4, 9), (5, 3), (5, 9)]
    # spare_zone_1 = [(0,0), (0, 11), (1, 0), (1, 11)]
    spare_zone_1 = [(0,0), (0, 11), (0, 0), (0, 11)]
    # spare_zone_2 = [(4, 1), (4, 9), (5, 1), (5, 9)]
    spare_zones = [spare_zone_1]
    # spare_zones = []

    add_ground_stations_inclined(constellation, positions, sats_per_plane, num_planes, excluded_edges)

    # paths = find_multiple_shortest_paths(constellation, source="LDN", destination="NYC", k=4, excluded_edges=excluded_edges)
    paths = find_path_via_spare_zones(constellation, source="LDN", destination="NYC", spare_zones=spare_zones, excluded_edges=excluded_edges)

    ns3_code = generate_ns3_code_for_paths(paths)

    save_ns3_code_to_file(ns3_code)

    plot_inclined_constellation(constellation, positions, paths, excluded_edges, spare_zones)

if __name__ == "__main__":
    main()
