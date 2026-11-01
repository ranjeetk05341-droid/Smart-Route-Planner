import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth in kilometers.
    Used for physical distance estimation and A* heuristic calculation.
    """
    R = 6371.0  # Earth's radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class Node:
    def __init__(self, node_id, lat, lon, label=None):
        self.id = node_id
        self.lat = float(lat)
        self.lon = float(lon)
        self.label = label or str(node_id)

    def to_dict(self):
        return {
            'id': self.id,
            'lat': self.lat,
            'lon': self.lon,
            'label': self.label
        }


class Edge:
    def __init__(self, u, v, distance_km, speed_limit_kmh=50.0, road_type='primary', bidirectional=True):
        self.u = u
        self.v = v
        self.distance_km = float(distance_km)
        self.speed_limit_kmh = max(5.0, float(speed_limit_kmh))
        # Base travel time in minutes: (distance / speed) * 60
        self.base_time_min = (self.distance_km / self.speed_limit_kmh) * 60.0
        self.road_type = road_type
        self.traffic_multiplier = 1.0  # 1.0 = normal, 1.5 = moderate, 2.5 = heavy
        self.is_closed = False
        self.bidirectional = bidirectional

    @property
    def travel_time_min(self):
        if self.is_closed:
            return float('inf')
        return self.base_time_min * self.traffic_multiplier

    def get_weight(self, metric='distance'):
        if self.is_closed:
            return float('inf')
        if metric == 'distance':
            return self.distance_km
        elif metric == 'time':
            return self.travel_time_min
        elif metric == 'traffic':
            return self.travel_time_min * (self.traffic_multiplier ** 1.5)
        return self.distance_km


class Graph:
    def __init__(self):
        self.nodes = {}  # node_id -> Node
        self.adj = {}    # node_id -> list of Edge

    def add_node(self, node_id, lat, lon, label=None):
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(node_id, lat, lon, label)
            self.adj[node_id] = []
        return self.nodes[node_id]

    def add_edge(self, u, v, distance_km=None, speed_limit_kmh=50.0, road_type='primary', bidirectional=True):
        if u not in self.nodes or v not in self.nodes:
            raise ValueError(f"Nodes {u} and {v} must be added to graph before adding edge.")

        if distance_km is None:
            # Calculate from geographic coordinates
            node_u = self.nodes[u]
            node_v = self.nodes[v]
            distance_km = haversine_distance(node_u.lat, node_u.lon, node_v.lat, node_v.lon)

        edge_forward = Edge(u, v, distance_km, speed_limit_kmh, road_type, bidirectional)
        self.adj[u].append(edge_forward)

        if bidirectional:
            edge_backward = Edge(v, u, distance_km, speed_limit_kmh, road_type, bidirectional)
            self.adj[v].append(edge_backward)

    def set_edge_traffic(self, u, v, multiplier):
        if u in self.adj:
            for edge in self.adj[u]:
                if edge.v == v:
                    edge.traffic_multiplier = max(1.0, float(multiplier))
        if v in self.adj:
            for edge in self.adj[v]:
                if edge.v == u:
                    edge.traffic_multiplier = max(1.0, float(multiplier))

    def set_edge_closure(self, u, v, is_closed=True):
        if u in self.adj:
            for edge in self.adj[u]:
                if edge.v == v:
                    edge.is_closed = is_closed
        if v in self.adj:
            for edge in self.adj[v]:
                if edge.v == u:
                    edge.is_closed = is_closed

    def get_neighbors(self, node_id):
        return self.adj.get(node_id, [])

    def to_dict(self):
        nodes_list = [n.to_dict() for n in self.nodes.values()]
        edges_list = []
        visited_pairs = set()
        for u, edges in self.adj.items():
            for e in edges:
                pair = tuple(sorted([e.u, e.v]))
                if pair not in visited_pairs:
                    visited_pairs.add(pair)
                    edges_list.append({
                        'from': e.u,
                        'to': e.v,
                        'distance_km': round(e.distance_km, 3),
                        'travel_time_min': round(e.travel_time_min, 2),
                        'speed_limit_kmh': e.speed_limit_kmh,
                        'traffic_multiplier': e.traffic_multiplier,
                        'is_closed': e.is_closed,
                        'road_type': e.road_type
                    })
        return {
            'nodes': nodes_list,
            'edges': edges_list
        }

