"""Path finding algorithms and utilities."""
import networkx as nx
from typing import List, Tuple, Optional, Dict

def find_multiple_paths(G: nx.Graph, source: int = -1, target: int = -2) -> Tuple[List[List[int]], List[float]]:
    """Find three shortest paths between source and target."""
    paths = []
    lengths = []
    G_temp = G.copy()
    
    for i in range(3):
        try:
            path = nx.shortest_path(G_temp, source=source, target=target, weight="length")
            length = sum(G_temp[u][v]['length'] for u, v in zip(path, path[1:]))
            paths.append(path)
            lengths.append(length)
            
            if i < 2:  # Don't remove after finding the third path
                G_temp.remove_nodes_from(path[1:-1])
                
        except nx.NetworkXNoPath:
            print(f"No path #{i+1} found between node {source} and node {target}.")
            break
    
    return paths, lengths

def find_paths_recursive(G, current_node, target, nodes_in_zones, 
                        path_so_far, weight_so_far, target_weight,
                        excluded_edges, visited_zones, paths_found,
                        SATS_PER_PLANE, direction=None):
    """
    Recursive helper to find paths through zones
    
    Args:
        G: NetworkX graph
        current_node: Current satellite node
        target: Target node (ground station)
        nodes_in_zones: Dict mapping zone indices to lists of nodes
        path_so_far: List of nodes in current path
        weight_so_far: Current accumulated path weight
        target_weight: Target total path weight (1.25 * shortest)
        excluded_edges: Set of edges to avoid (from shortest path)
        visited_zones: Set of zone indices already used
        paths_found: List to collect valid complete paths
        SATS_PER_PLANE: Number of satellites per orbital plane
        direction: Current direction (None if first hop, else 1/-1)
    """
    # Try routing to destination if we've hit at least one zone
    if visited_zones:
        try:
            exit_path = nx.shortest_path(G, current_node, target, weight='length')
            # Check if path uses excluded edges
            if not any((u,v) in excluded_edges for u,v in zip(exit_path, exit_path[1:])):
                exit_weight = sum(G[u][v]['length'] for u,v in zip(exit_path, exit_path[1:]))
                total_weight = weight_so_far + exit_weight
                
                if total_weight >= target_weight:
                    complete_path = path_so_far + exit_path[1:]
                    paths_found.append((complete_path, total_weight))
                    print(f"Found valid path with weight {total_weight:.2f}")
                    
        except nx.NetworkXNoPath:
            pass
            
    # Try routing to next zones
    current_plane = current_node // SATS_PER_PLANE
    
    for zone_idx, zone_nodes in nodes_in_zones.items():
        if zone_idx in visited_zones:
            continue
            
        for zone_node in zone_nodes:
            zone_plane = zone_node // SATS_PER_PLANE
            plane_diff = zone_plane - current_plane
            
            # Check direction consistency if direction is established
            if direction is not None and plane_diff * direction < 0:
                continue
                
            try:
                zone_path = nx.shortest_path(G, current_node, zone_node, weight='length')
                # Check if path uses excluded edges
                if any((u,v) in excluded_edges for u,v in zip(zone_path, zone_path[1:])):
                    continue
                    
                zone_weight = sum(G[u][v]['length'] for u,v in zip(zone_path, zone_path[1:]))
                new_weight = weight_so_far + zone_weight
                
                # Set direction based on plane difference
                new_direction = 1 if plane_diff > 0 else -1 if plane_diff < 0 else direction
                
                # Recurse
                find_paths_recursive(
                    G, zone_node, target,
                    nodes_in_zones,
                    path_so_far + zone_path[1:],
                    new_weight,
                    target_weight,
                    excluded_edges,
                    visited_zones | {zone_idx},
                    paths_found,
                    SATS_PER_PLANE,
                    new_direction
                )
                
            except nx.NetworkXNoPath:
                continue

def find_path_via_spare_zones(G: nx.Graph, positions: Dict, nodes_in_zones: Dict, target_weight_factor: float,
                            source: int = -1, target: int = -2) -> List[List[int]]:
    """
    Find paths via spare zones using same initial RF link as shortest path,
    ensuring total path weight is at or above 125% of shortest path weight.
    Will attempt to route through zones maintaining consistent orbital plane direction.
    """
    G_copy = G.copy()
    SATS_PER_PLANE = 66

    # Initial setup
    shortest_path = nx.shortest_path(G_copy, source=source, target=target, weight='length')
    shortest_weight = sum(G_copy[u][v]['length'] for u,v in zip(shortest_path, shortest_path[1:]))
    target_weight = shortest_weight * target_weight_factor
    initial_sat = shortest_path[1]
    
    # Get edges to exclude (from shortest path)
    excluded_edges = set(zip(shortest_path[1:-1], shortest_path[2:]))
    reverse_edges = set((v,u) for u,v in excluded_edges)
    excluded_edges.update(reverse_edges)  # Add reverse edges
    print(f"Edges excluded are: {excluded_edges}")
    
    # Remove shortest path edges from working graph
    G_copy.remove_edges_from(excluded_edges)
    
    # Initialize collections for recursive search
    paths_found = []
    initial_weight = G[source][initial_sat]['length']
    initial_path = [source, initial_sat]
    
    # Start recursive search
    find_paths_recursive(
        G_copy, initial_sat, target,
        nodes_in_zones,
        initial_path,
        initial_weight,
        target_weight,
        excluded_edges,
        set(),  # No zones visited yet
        paths_found,
        SATS_PER_PLANE
    )
    
    if paths_found:
        # Sort by how close the weight is to target_weight
        paths_found.sort(key=lambda x: abs(x[1] - target_weight))
        print(f"\nFound {len(paths_found)} valid paths")
        best_path, best_weight = paths_found[0]
        print(f"\nSelected best path:")
        print(f"Path weight: {best_weight:.2f} (target: {target_weight:.2f}, shortest possible: {shortest_weight:.2f})")
        print(f"Weight increase: {((best_weight/shortest_weight) - 1) * 100:.1f}%")
        print(f"Difference from target: {abs(best_weight - target_weight):.2f}")
        
        # Also show some alternatives if available
        if len(paths_found) > 1:
            print("\nNext best alternatives:")
            for path, weight in paths_found[1:4]:  # Show up to 3 alternatives
                print(f"Weight: {weight:.2f}, Difference from target: {abs(weight - target_weight):.2f}")
        
        return [best_path]  # Return only the best path
        
    print("\nNo valid paths found")
    return []