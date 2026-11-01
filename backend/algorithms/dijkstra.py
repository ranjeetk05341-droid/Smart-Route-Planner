import heapq
import time

def dijkstra_shortest_path(graph, start_id, goal_id, metric='distance'):
    """
    Executes Dijkstra's Shortest Path Algorithm on the provided Graph.
    
    Parameters:
        graph (Graph): In-memory Graph instance.
        start_id: Identifier of the source node.
        goal_id: Identifier of the destination node.
        metric (str): 'distance', 'time', or 'traffic'
        
    Returns:
        dict: {
            'found': bool,
            'path_nodes': list,
            'path_coords': list of [lat, lon],
            'total_distance_km': float,
            'total_time_min': float,
            'nodes_explored': int,
            'execution_time_ms': float,
            'algorithm': 'Dijkstra'
        }
    """
    start_time = time.perf_counter()

    if start_id not in graph.nodes or goal_id not in graph.nodes:
        return {
            'found': False,
            'error': f'Start ({start_id}) or Goal ({goal_id}) node not in graph.',
            'path_nodes': [],
            'path_coords': [],
            'total_distance_km': 0.0,
            'total_time_min': 0.0,
            'nodes_explored': 0,
            'execution_time_ms': 0.0,
            'algorithm': 'Dijkstra'
        }

    # Priority queue holds tuples: (cumulative_cost, node_id)
    pq = []
    heapq.heappush(pq, (0.0, start_id))

    distances = {node_id: float('inf') for node_id in graph.nodes}
    distances[start_id] = 0.0

    came_from = {}
    edge_used = {}
    visited = set()
    nodes_explored = 0

    while pq:
        current_cost, current_node = heapq.heappop(pq)

        if current_node in visited:
            continue
        visited.add(current_node)
        nodes_explored += 1

        if current_node == goal_id:
            break

        for edge in graph.get_neighbors(current_node):
            neighbor = edge.v
            if neighbor in visited or edge.is_closed:
                continue

            weight = edge.get_weight(metric)
            if weight == float('inf'):
                continue

            tentative_cost = current_cost + weight
            if tentative_cost < distances[neighbor]:
                distances[neighbor] = tentative_cost
                came_from[neighbor] = current_node
                edge_used[neighbor] = edge
                heapq.heappush(pq, (tentative_cost, neighbor))

    exec_time_ms = (time.perf_counter() - start_time) * 1000.0

    if distances[goal_id] == float('inf'):
        return {
            'found': False,
            'error': 'No viable path exists between source and destination (road closures may be blocking all routes).',
            'path_nodes': [],
            'path_coords': [],
            'total_distance_km': 0.0,
            'total_time_min': 0.0,
            'nodes_explored': nodes_explored,
            'execution_time_ms': round(exec_time_ms, 3),
            'algorithm': 'Dijkstra'
        }

    # Reconstruct path
    path = []
    curr = goal_id
    total_dist = 0.0
    total_time = 0.0

    while curr in came_from:
        path.append(curr)
        edge = edge_used[curr]
        total_dist += edge.distance_km
        total_time += edge.travel_time_min
        curr = came_from[curr]
    path.append(start_id)
    path.reverse()

    path_coords = [[graph.nodes[n].lat, graph.nodes[n].lon] for n in path]

    return {
        'found': True,
        'path_nodes': path,
        'path_coords': path_coords,
        'total_distance_km': round(total_dist, 3),
        'total_time_min': round(total_time, 2),
        'nodes_explored': nodes_explored,
        'execution_time_ms': round(exec_time_ms, 3),
        'algorithm': 'Dijkstra'
    }

