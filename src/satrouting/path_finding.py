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

def find_path_via_spare_zones(G: nx.Graph, positions: Dict, nodes_in_zones: Dict, 
                            source: int = -1, target: int = -2, 
                            excluded_edges: Optional[List] = None) -> List[List[int]]:
    """
    Find path via spare zones using same initial RF link as shortest path,
    ensuring total path weight is at or above 125% of shortest path weight
    """
    G_copy = G.copy()
    
    # Get shortest path and details
    shortest_path = nx.shortest_path(G_copy, source=source, target=target, weight='length')
    shortest_weight = sum(G_copy[u][v]['length'] for u, v in zip(shortest_path, shortest_path[1:]))
    target_weight = shortest_weight * 1.25  # This is our minimum acceptable weight
    initial_sat = shortest_path[1]
    
    # Remove edges from shortest path (except initial RF link)
    edges_to_remove = list(zip(shortest_path[1:-1], shortest_path[2:]))
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
    if best_zone_idx is not None:
        for zone_node in nodes_in_zones[best_zone_idx]:
            try:
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
        print(f"current_weight: {current_weight}")
        
        needed_weight = max(0, target_weight - current_weight)
        print(f"needed_weight: {needed_weight}")
        
        entry_node = best_entry_path[-1]
        exit_node = best_exit_path[-1]
        print(f"entry_node: {entry_node}, exit_node: {exit_node}")
        
        try:
            zone_path = nx.shortest_path(G_copy, entry_node, exit_node, weight='length')
            zone_weight = sum(G_copy[u][v]['length'] for u, v in zip(zone_path, zone_path[1:]))
            total_weight = current_weight + zone_weight
            print(f"zone_path: {zone_path}")
            needed_weight = target_weight - total_weight
            
            while needed_weight > 0:
                available_nodes = [n for n in nodes_in_zones[best_zone_idx] 
                                 if n not in zone_path]
                
                if not available_nodes:
                    break
                    
                best_insertion = None
                best_insertion_weight = float('inf')
                
                for node in available_nodes:
                    for i in range(1, len(zone_path)):
                        try:
                            H = G_copy.copy()
                            used_nodes = set(zone_path) - {zone_path[i-1], zone_path[i]}
                            H.remove_nodes_from(used_nodes)
                            
                            path_to = nx.shortest_path(H, zone_path[i-1], node, weight='length')
                            path_from = nx.shortest_path(H, node, zone_path[i], weight='length')
                            
                            all_nodes = set(path_to[1:-1] + path_from[1:-1])
                            if all_nodes & set(zone_path):
                                continue
                            
                            segment_weight = (sum(G_copy[u][v]['length'] 
                                           for u, v in zip(path_to, path_to[1:])) +
                                           sum(G_copy[u][v]['length'] 
                                           for u, v in zip(path_from, path_from[1:])))
                            
                            original_weight = G_copy[zone_path[i-1]][zone_path[i]]['length']
                            weight_increase = segment_weight - original_weight
                            
                            if weight_increase > 0 and weight_increase < best_insertion_weight:
                                best_insertion = (i, node, path_to, path_from)
                                best_insertion_weight = weight_increase
                                
                        except nx.NetworkXNoPath:
                            continue
                
                if best_insertion:
                    i, node, path_to, path_from = best_insertion
                    zone_path = (zone_path[:i-1] + path_to + 
                               path_from[1:] + zone_path[i+1:])
                    
                    zone_weight += best_insertion_weight
                    total_weight += best_insertion_weight
                    needed_weight -= best_insertion_weight
                    print(f"Added node {node}, new total weight: {total_weight}")
                else:
                    break

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