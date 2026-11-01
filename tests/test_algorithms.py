import unittest
import math
from backend.algorithms.graph import Graph, haversine_distance
from backend.algorithms.dijkstra import dijkstra_shortest_path
from backend.algorithms.a_star import a_star_search
from backend.algorithms.optimizer import evaluate_and_rank_routes, get_mode_weights
from backend.services.fuel_calculator import FuelCalculator

class TestRoutingAlgorithms(unittest.TestCase):
    def setUp(self):
        # Create a small graph for deterministic testing
        # A(0,0) ---- B(0, 0.01) ---- C(0, 0.02)
        #   \                           /
        #    \------ D(0.01, 0.01) ----/
        self.g = Graph()
        self.g.add_node('A', 0.0, 0.0, 'Origin')
        self.g.add_node('B', 0.0, 0.01, 'Midpoint North')
        self.g.add_node('C', 0.0, 0.02, 'Destination')
        self.g.add_node('D', 0.01, 0.01, 'Midpoint South (Bypass)')

        # Path 1: A -> B -> C (shorter distance)
        self.g.add_edge('A', 'B', distance_km=1.0, speed_limit_kmh=50.0)
        self.g.add_edge('B', 'C', distance_km=1.0, speed_limit_kmh=50.0)

        # Path 2: A -> D -> C (longer distance, higher speed highway)
        self.g.add_edge('A', 'D', distance_km=1.4, speed_limit_kmh=100.0)
        self.g.add_edge('D', 'C', distance_km=1.4, speed_limit_kmh=100.0)

    def test_haversine_distance(self):
        # Known distance: NYC to London ~ 5570 km
        d = haversine_distance(40.7128, -74.0060, 51.5074, -0.1278)
        self.assertTrue(5500 < d < 5650, f"Unexpected Haversine calculation: {d}")

    def test_dijkstra_shortest_distance(self):
        res = dijkstra_shortest_path(self.g, 'A', 'C', metric='distance')
        self.assertTrue(res['found'])
        self.assertEqual(res['path_nodes'], ['A', 'B', 'C'])
        self.assertAlmostEqual(res['total_distance_km'], 2.0, places=1)

    def test_dijkstra_shortest_time(self):
        # A->D->C takes (2.8/100)*60 = 1.68 min, whereas A->B->C takes (2.0/50)*60 = 2.4 min
        res = dijkstra_shortest_path(self.g, 'A', 'C', metric='time')
        self.assertTrue(res['found'])
        self.assertEqual(res['path_nodes'], ['A', 'D', 'C'])
        self.assertLess(res['total_time_min'], 2.0)

    def test_a_star_optimality(self):
        res_dijkstra = dijkstra_shortest_path(self.g, 'A', 'C', metric='distance')
        res_astar = a_star_search(self.g, 'A', 'C', metric='distance')
        self.assertTrue(res_astar['found'])
        self.assertEqual(res_astar['path_nodes'], res_dijkstra['path_nodes'])
        self.assertAlmostEqual(res_astar['total_distance_km'], res_dijkstra['total_distance_km'], places=1)

    def test_road_closure_rerouting(self):
        # Block edge A-B
        self.g.set_edge_closure('A', 'B', is_closed=True)
        res = dijkstra_shortest_path(self.g, 'A', 'C', metric='distance')
        self.assertTrue(res['found'])
        self.assertEqual(res['path_nodes'], ['A', 'D', 'C'], "Algorithm failed to reroute around closed road!")

    def test_multi_objective_optimizer(self):
        candidate_routes = [
            {'id': 1, 'name': 'Highway', 'distance_km': 15.0, 'duration_min': 15.0, 'fuel_cost': 2.0, 'traffic_multiplier': 1.0},
            {'id': 2, 'name': 'City Short', 'distance_km': 10.0, 'duration_min': 30.0, 'fuel_cost': 1.6, 'traffic_multiplier': 1.8}
        ]
        # Under fastest mode, Highway (15 min) should win
        ranked_fastest = evaluate_and_rank_routes(candidate_routes, mode='fastest')
        self.assertEqual(ranked_fastest[0]['name'], 'Highway')

        # Under shortest mode, City Short (10 km) should win
        ranked_shortest = evaluate_and_rank_routes(candidate_routes, mode='shortest')
        self.assertEqual(ranked_shortest[0]['name'], 'City Short')

    def test_fuel_calculator(self):
        calc = FuelCalculator.calculate(distance_km=100.0, vehicle_type='petrol', user_fuel_price=1.5, user_efficiency=15.0)
        self.assertAlmostEqual(calc['units_consumed'], 6.67, places=1)
        self.assertAlmostEqual(calc['fuel_cost'], 10.0, places=1)
        self.assertGreater(calc['co2_emissions_kg'], 10.0)

if __name__ == '__main__':
    unittest.main()

