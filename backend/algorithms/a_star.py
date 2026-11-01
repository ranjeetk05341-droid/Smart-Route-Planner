import heapq
import time
from .graph import haversine_distance

def a_star_search(graph, start_id, goal_id, metric='distance'):
    """
    Executes A* Search Algorithm using an admissible Haversine heuristic.
    
    Parameters:
        graph (Graph): In-memory Graph instance.
        start_id: Identifier of the source node.
        goal_id: Identifier of the destination node.
        metric (str): 'distance', 'time', or 'traffic'
        
    Returns:
        dict: Path results and algorithmic benchmarking statistics.
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
            'algorithm': 'A* Search'
        }

    goal_node = graph.nodes[goal_id]
    MAX_SPEED_KMH = 120.0  # Max theoretical speed for admissible time heuristic

    def heuristic(node_id):
        curr_node = graph.nodes[node_id]
        h_dist = haversine_distance(curr_node.lat, curr_node.lon, goal_node.lat, goal_node.lon)
        if metric in ('time', 'traffic'):
            # Minimum time in minutes to reach goal at maximum highway speed
            return (h_dist / MAX_SPEED_KMH) * 60.0
        return h_dist

    # Priority queue stores tuples: (f_score, g_score, node_id)
    pq = []
    initial_h = heuristic(start_id)
    heapq.heappush(pq, (initial_h, 0.0, start_id))

    g_score = {node_id: float('inf') for node_id in graph.nodes}
    g_score[start_id] = 0.0

    came_from = {}
    edge_used = {}
    visited = set()
    nodes_explored = 0

    while pq:
        f, current_g, current_node = heapq.heappop(pq)

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

            tentative_g = current_g + weight
            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current_node
                edge_used[neighbor] = edge
                f_score = tentative_g + heuristic(neighbor)
                heapq.heappush(pq, (f_score, tentative_g, neighbor))

    exec_time_ms = (time.perf_counter() - start_time) * 1000.0

    if g_score[goal_id] == float('inf'):
        return {
            'found': False,
            'error': 'No viable path exists between source and destination.',
            'path_nodes': [],
            'path_coords': [],
            'total_distance_km': 0.0,
            'total_time_min': 0.0,
            'nodes_explored': nodes_explored,
            'execution_time_ms': round(exec_time_ms, 3),
            'algorithm': 'A* Search'
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
        'algorithm': 'A* Search'
    }

