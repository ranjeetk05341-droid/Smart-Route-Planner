import unittest
import json
from backend.app import create_app
from backend.database.db import db

class TestAPIRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_health_endpoint(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_location_search(self):
        resp = self.client.get('/api/locations/search?q=Delhi')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('results', data)
        self.assertGreater(len(data['results']), 0)

    def test_route_calculation(self):
        payload = {
            'coordinates': [[28.6315, 77.2167], [28.5562, 77.1000]],  # Connaught Place to IGI Airport
            'mode': 'fastest',
            'vehicle_type': 'petrol'
        }
        resp = self.client.post('/api/routes/calculate', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['routes']), 0)
        self.assertTrue(data['routes'][0]['is_recommended'])
        # Verify traffic transparency requirement: does not pretend to be live
        self.assertIn('traffic_status', data['routes'][0])
        self.assertFalse(data['routes'][0].get('live_traffic_available', True))

    def test_pois_endpoint(self):
        resp = self.client.get('/api/locations/pois?lat=28.6315&lon=77.2167&radius=2000&category=restaurant')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('pois', data)
        self.assertGreaterEqual(len(data['pois']), 1)
        self.assertEqual(data['pois'][0]['category'], 'restaurant')
        self.assertIn('name', data['pois'][0])
        self.assertIn('address', data['pois'][0])

    def test_pois_all_categories(self):
        resp = self.client.get('/api/locations/pois?lat=28.6315&lon=77.2167&radius=2500&category=all')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        categories = {p['category'] for p in data['pois']}
        self.assertGreater(len(categories), 1)

    def test_simulation_incident_lifecycle(self):
        # 1. Add closure incident
        inc_payload = {
            'type': 'closure',
            'lat': 28.6000,
            'lon': 77.1500,
            'radius_km': 0.5,
            'description': 'Bridge Maintenance Closure'
        }
        resp = self.client.post('/api/simulation/incidents', data=json.dumps(inc_payload), content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        inc_data = resp.get_json()['incident']
        inc_id = inc_data['id']

        # 2. Verify in list
        get_resp = self.client.get('/api/simulation/incidents')
        incidents = get_resp.get_json()['incidents']
        self.assertTrue(any(i['id'] == inc_id for i in incidents))

        # 3. Remove incident
        del_resp = self.client.delete(f'/api/simulation/incidents/{inc_id}')
        self.assertEqual(del_resp.status_code, 200)

    def test_algorithm_benchmark(self):
        payload = {
            'coordinates': [[28.6315, 77.2167], [28.5562, 77.1000]]
        }
        resp = self.client.post('/api/routes/benchmark', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIn('dijkstra', data['benchmark'])
        self.assertIn('a_star', data['benchmark'])

    def test_maps_config_security(self):
        """Verifies maps config never leaks the server key and returns valid client config."""
        resp = self.client.get('/api/config/maps')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('google_maps_browser_key', data)
        self.assertIn('google_maps_enabled', data)
        self.assertIn('has_server_key', data)
        # CRITICAL SECURITY CHECK: Ensure server key is NEVER leaked in client config
        self.assertNotIn('google_maps_server_key', data)
        self.assertNotIn('server_key', data)

    def test_google_maps_diagnostics(self):
        """Verifies diagnostics endpoint provides structured billing and API reporting."""
        resp = self.client.get('/api/diagnostics/google-maps')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('browser_key_configured', data)
        self.assertIn('server_key_configured', data)
        self.assertIn('billing_status', data)
        self.assertIn('recommendations', data)

    def test_multi_modal_transport_modes(self):
        """Verifies route calculation succeeds across Car, Bicycle, and Walking."""
        coords = [[28.6315, 77.2167], [28.5562, 77.1000]]
        for mode in ['car', 'bicycle', 'walking']:
            resp = self.client.post('/api/routes/calculate', data=json.dumps({
                'coordinates': coords,
                'transport_mode': mode
            }), content_type='application/json')
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data['success'])
            self.assertGreater(len(data['routes']), 0)
            self.assertEqual(data['routes'][0]['transport_mode'], mode)

if __name__ == '__main__':
    unittest.main()

