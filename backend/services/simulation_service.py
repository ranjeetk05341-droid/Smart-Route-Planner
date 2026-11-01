import math
from backend.algorithms.graph import haversine_distance

class IncidentManager:
    """
    Manages real-time / simulated road incidents including:
    - Road closures (accidents, construction, floods)
    - High-density traffic bottlenecks
    """
    def __init__(self):
        # In-memory storage for active incidents
        self.incidents = []
        self._next_id = 1

    def add_incident(self, incident_type, lat, lon, radius_km=0.3, description='', multiplier=2.5):
        """
        incident_type: 'closure' or 'traffic'
        """
        incident = {
            'id': self._next_id,
            'type': incident_type,  # 'closure' or 'traffic'
            'lat': float(lat),
            'lon': float(lon),
            'radius_km': max(0.05, float(radius_km)),
            'description': description or ('Road Blocked / Closed' if incident_type == 'closure' else 'Severe Traffic Congestion'),
            'multiplier': float(multiplier) if incident_type == 'traffic' else float('inf')
        }
        self._next_id += 1
        self.incidents.append(incident)
        return incident

    def remove_incident(self, incident_id):
        self.incidents = [inc for inc in self.incidents if inc['id'] != incident_id]
        return True

    def clear_all(self):
        self.incidents = []

    def get_all(self):
        return self.incidents

    def evaluate_route_incidents(self, coordinates):
        """
        Evaluates a polyline list of [lat, lon] coordinates against active incidents.
        Returns:
            has_closure: bool
            max_traffic_multiplier: float
            affected_incidents: list
        """
        has_closure = False
        max_multiplier = 1.0
        affected = []

        if not self.incidents or not coordinates:
            return {
                'has_closure': False,
                'traffic_multiplier': 1.0,
                'affected_incidents': []
            }

        for inc in self.incidents:
            inc_lat = inc['lat']
            inc_lon = inc['lon']
            inc_radius = inc['radius_km']
            is_affected = False

            # Check minimum distance from any polyline coordinate
            for coord in coordinates:
                c_lat, c_lon = coord[0], coord[1]
                dist = haversine_distance(c_lat, c_lon, inc_lat, inc_lon)
                if dist <= inc_radius:
                    is_affected = True
                    break

            if is_affected:
                affected.append(inc)
                if inc['type'] == 'closure':
                    has_closure = True
                elif inc['type'] == 'traffic':
                    if inc['multiplier'] > max_multiplier:
                        max_multiplier = inc['multiplier']

        return {
            'has_closure': has_closure,
            'traffic_multiplier': max_multiplier,
            'affected_incidents': affected
        }

# Global singleton
incident_manager = IncidentManager()

