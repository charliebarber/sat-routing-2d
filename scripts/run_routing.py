"""Main script for satellite routing analysis."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from satrouting.config import (
    GROUND_STATIONS,
    SPARE_ZONES,
)
from satrouting.graph_utils import parse_network_file, create_subgraph
from satrouting.position_utils import calculate_node_positions
from satrouting.path_finding import find_multiple_paths, find_path_via_spare_zones
from satrouting.visualisation import plot_network
from satrouting.zone_utils import find_nodes_in_spare_zones

def main():
    """Main execution function."""
    # Build and analyze network
    try:
        G = parse_network_file('snapshots/snapshot0.02s.txt')
    except FileNotFoundError:
        print("Error: snapshot file not found. Ensure it's in the snapshots directory.")
        return
    
    # Calculate positions
    positions = calculate_node_positions(G)
    
    # Find nodes in spare zones
    nodes_in_zones = find_nodes_in_spare_zones(G, SPARE_ZONES, positions)
    for zone_idx, nodes in nodes_in_zones.items():
        print(f"\nNodes in Spare Zone {zone_idx + 1}:")
        print(f"Total nodes: {len(nodes)}")
        print(f"Node numbers: {sorted(nodes)}")
    
    # Create relevant subgraph
    subgraph = create_subgraph(G, positions, GROUND_STATIONS)
    
    # Find regular shortest paths
    paths, lengths = find_multiple_paths(subgraph)
    if paths:
        print("\nRegular shortest paths:")
        for i, (path, length) in enumerate(zip(paths, lengths)):
            print(f"Path {i+1}: {path}")
            print(f"Length {i+1}: {length}")
    else:
        print("\nNo valid paths found between ground stations.")
        return
    
    # Find path via spare zones
    spare_paths = find_path_via_spare_zones(subgraph, positions, nodes_in_zones)
    if spare_paths:
        print("\nPath via spare zones:")
        for i, path in enumerate(spare_paths):
            print(f"Spare zone path {i+1}: {path}")
            length = sum(subgraph[u][v]['length'] for u, v in zip(path, path[1:]))
            print(f"Length: {length}")
    else:
        print("\nNo valid paths found through spare zones.")
    
    # Plot results
    plot_network(subgraph, positions, 
                shortest_path=paths[0] if paths else [],
                ground_stations=GROUND_STATIONS,
                spare_zones=SPARE_ZONES,
                spare_path=spare_paths[0] if spare_paths else None)

if __name__ == "__main__":
    main()