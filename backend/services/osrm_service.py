import os
import requests
import math
import random
from backend.algorithms.graph import haversine_distance, Graph
from backend.algorithms.dijkstra import dijkstra_shortest_path
from backend.algorithms.a_star import a_star_search
from backend.services.simulation_service import incident_manager
from backend.services.fuel_calculator import FuelCalculator

class OSRMRoutingService:
    """
    Intelligent Multi-Modal Routing Engine.
    
    Supports:
    - Transport Modes: 'car' (driving), 'bicycle' (cycling), 'walking' (pedestrian)
    - Dual Engine: Google Directions API (if GOOGLE_MAPS_API_KEY configured) OR OSRM OpenStreetMap Engine
    - Distinguishes Fastest Route (minimum duration) and Shortest Route (minimum distance)
    - Full turn-by-turn navigation maneuvers and road coordinates
    """
    OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

    @classmethod
    def get_server_key(cls):
        """
        Retrieves the server-side API key for Google Routes & Directions APIs.
        Prioritizes GOOGLE_MAPS_SERVER_KEY, falls back to GOOGLE_MAPS_API_KEY.
        Ignores placeholder values.
        """
        key = (os.environ.get('GOOGLE_MAPS_SERVER_KEY') or 
               os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip()
        if key in ['YOUR_SERVER_KEY', 'YOUR_BROWSER_KEY', 'your_google_maps_server_key_here', 'your_google_maps_browser_key_here']:
            return ''
        return key

    @classmethod
    def get_google_api_key(cls):
        return cls.get_server_key()

    @classmethod
    def get_routes(cls, coordinates, vehicle_type='petrol', user_fuel_price=None, user_efficiency=None, transport_mode='car', optimization_mode='fastest'):
        """
        Calculates routes between coordinates.
        coordinates: list of [lat, lon] tuples/lists.
        transport_mode: 'car' | 'bicycle' | 'walking'
        optimization_mode: 'fastest' | 'shortest' | 'economical' | 'balanced'
        """
        if len(coordinates) < 2:
            raise ValueError("At least 2 coordinates (source and destination) are required.")

        normalized_mode = transport_mode.lower()
        if normalized_mode not in ['car', 'bicycle', 'walking']:
            normalized_mode = 'car'

        routes = []
        is_live = False

        # 1. Check if Google Maps Server API key is configured
        google_server_key = cls.get_server_key()
        if google_server_key:
            # 1a. Try Google Routes API v2 (computeRoutes)
            routes = cls._fetch_google_routes_api(coordinates, normalized_mode, google_server_key, vehicle_type, user_fuel_price, user_efficiency)
            
            # 1b. If Routes API v2 returned no routes, try Google Directions API v1
            if not routes:
                routes = cls._fetch_google_directions(coordinates, normalized_mode, google_server_key, vehicle_type, user_fuel_price, user_efficiency)

            if routes:
                is_live = True

        # 2. Open-Source Mapping Stack (Google key not configured or billing inactive)
        if not routes:
            if normalized_mode in ['bicycle', 'walking']:
                # Query Valhalla dedicated pedestrian / cycling routing engine
                routes = cls._fetch_valhalla_routes(coordinates, normalized_mode)
                if routes:
                    is_live = True

            # If mode is car OR Valhalla was temporarily unreachable, query OSRM
            if not routes:
                routes = cls._fetch_osrm_routes(coordinates, normalized_mode, vehicle_type, user_fuel_price, user_efficiency)
                if routes:
                    is_live = True

        # 3. If no provider could calculate a route, do NOT create fake routes
        if not routes:
            raise RuntimeError("No viable road route found between the specified coordinates on the road network.")

        # 4. Identify and tag Shortest Route and Fastest Route
        if routes:
            min_duration = min(r['duration_min'] for r in routes)
            min_distance = min(r['distance_km'] for r in routes)

            for r in routes:
                r['is_fastest'] = abs(r['duration_min'] - min_duration) < 0.05
                r['is_shortest'] = abs(r['distance_km'] - min_distance) < 0.05
                
                # Format friendly duration text (e.g. "14 min" or "1 hr 25 min")
                mins = int(round(r['duration_min']))
                if mins >= 60:
                    hrs = mins // 60
                    rem_mins = mins % 60
                    r['duration_text'] = f"{hrs} hr {rem_mins} min" if rem_mins > 0 else f"{hrs} hr"
                else:
                    r['duration_text'] = f"{max(1, mins)} min"

                # Assign clear badge
                if r['is_fastest'] and r['is_shortest']:
                    r['badge'] = 'Fastest & Shortest'
                    r['is_recommended'] = True
                elif r['is_fastest']:
                    r['badge'] = 'Fastest Route'
                    r['is_recommended'] = True
                elif r['is_shortest']:
                    r['badge'] = 'Shortest Distance'
                    r['is_recommended'] = (optimization_mode == 'shortest')
                else:
                    r['badge'] = 'Alternative Route'
                    r['is_recommended'] = False

        return {
            'routes': routes,
            'transport_mode': normalized_mode,
            'is_live': is_live,
            'waypoints_count': len(coordinates)
        }

    @classmethod
    def _fetch_osrm_routes(cls, coordinates, transport_mode, vehicle_type, user_fuel_price, user_efficiency):
        coords_str = ";".join([f"{coord[1]:.6f},{coord[0]:.6f}" for coord in coordinates])
        url = f"{cls.OSRM_BASE_URL}/{coords_str}"
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'alternatives': 'true',
            'steps': 'true'
        }

        routes = []
        try:
            resp = requests.get(url, params=params, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 'Ok' and data.get('routes'):
                    for idx, r in enumerate(data['routes']):
                        geojson_coords = r['geometry']['coordinates']
                        leaflet_coords = [[pt[1], pt[0]] for pt in geojson_coords]

                        dist_km = r['distance'] / 1000.0
                        raw_duration_min = r['duration'] / 60.0

                        # Calculate mode-specific travel duration and metrics
                        if transport_mode == 'walking':
                            # Average pedestrian walking speed: 4.8 km/h (12.5 min/km)
                            duration_min = (dist_km / 4.8) * 60.0
                            calories = int(dist_km * 65)  # ~65 kcal per km
                            mode_details = f"{calories} kcal &bull; {int(dist_km * 1350):,} steps"
                            fuel_cost = 0.0
                            co2_kg = 0.0
                            units_consumed = 0.0
                            unit_label = "L"
                        elif transport_mode == 'bicycle':
                            # Average cycling speed: 16.0 km/h (3.75 min/km)
                            duration_min = (dist_km / 16.0) * 60.0
                            calories = int(dist_km * 32)  # ~32 kcal per km
                            mode_details = f"{calories} kcal burned &bull; Zero emissions"
                            fuel_cost = 0.0
                            co2_kg = 0.0
                            units_consumed = 0.0
                            unit_label = "L"
                        else:
                            # Car (Driving)
                            duration_min = raw_duration_min
                            mode_details = f"Via primary road corridor"
                            fuel_stats = FuelCalculator.calculate(
                                distance_km=dist_km,
                                vehicle_type=vehicle_type,
                                user_fuel_price=user_fuel_price,
                                user_efficiency=user_efficiency,
                                traffic_multiplier=1.0
                            )
                            fuel_cost = fuel_stats['fuel_cost']
                            co2_kg = fuel_stats['co2_emissions_kg']
                            units_consumed = fuel_stats['units_consumed']
                            unit_label = fuel_stats['unit_label']

                        # Extract step maneuvers
                        steps = []
                        for leg in r.get('legs', []):
                            for step in leg.get('steps', []):
                                maneuver = step.get('maneuver', {})
                                steps.append({
                                    'instruction': step.get('name', '') or maneuver.get('type', 'Proceed'),
                                    'type': maneuver.get('type', 'turn'),
                                    'modifier': maneuver.get('modifier', ''),
                                    'distance_m': round(step.get('distance', 0), 1),
                                    'duration_s': round(step.get('duration', 0), 1)
                                })

                        # Identify main corridor / highway name
                        main_road = "Main Corridor"
                        if steps:
                            named_steps = [s['instruction'] for s in steps if s['instruction'] and s['instruction'] not in ['Proceed', 'depart', 'arrive']]
                            if named_steps:
                                main_road = named_steps[0]

                        # Evaluate against active road incidents / closures
                        incident_eval = incident_manager.evaluate_route_incidents(leaflet_coords)
                        has_closure = incident_eval['has_closure']
                        traffic_mult = max(1.0, incident_eval['traffic_multiplier'])

                        route_name = f"Route {idx + 1}"
                        if idx == 0:
                            route_name = f"via {main_road}" if main_road != "Main Corridor" else "Main Route"
                        elif idx == 1:
                            route_name = f"via {main_road} (Alternative)" if main_road != "Main Corridor" else "Alternative 1"
                        else:
                            route_name = f"Alternative {idx + 1}"

                        routes.append({
                            'id': idx + 1,
                            'name': route_name,
                            'main_road': main_road,
                            'transport_mode': transport_mode,
                            'distance_km': round(dist_km, 2),
                            'duration_min': round(duration_min * traffic_mult, 1),
                            'coordinates': leaflet_coords,
                            'steps': steps[:15],
                            'fuel_cost': fuel_cost,
                            'units_consumed': units_consumed,
                            'unit_label': unit_label,
                            'co2_emissions_kg': co2_kg,
                            'mode_details': mode_details,
                            'has_road_closure': has_closure,
                            'traffic_status': 'Standard flow (OSM)',
                            'live_traffic_available': False,
                            'traffic_multiplier': traffic_mult,
                            'source': 'OpenStreetMap OSRM'
                        })
        except Exception:
            pass

        return routes

    @classmethod
    def _decode_valhalla_polyline6(cls, encoded):
        """Decodes a Valhalla polyline6 encoded string into [[lat, lon], ...] at 1e6 precision."""
        inv = 1.0 / 1e6
        decoded = []
        previous = [0, 0]
        i = 0
        length = len(encoded)
        while i < length:
            ll = [0, 0]
            for j in range(2):
                shift = 0
                res = 0
                while True:
                    byte = ord(encoded[i]) - 63
                    i += 1
                    res |= (byte & 0x1f) << shift
                    shift += 5
                    if byte < 0x20:
                        break
                ll[j] = previous[j] + (~(res >> 1) if (res & 1) else (res >> 1))
                previous[j] = ll[j]
            decoded.append([round(ll[0] * inv, 6), round(ll[1] * inv, 6)])
        return decoded

    @classmethod
    def _fetch_valhalla_routes(cls, coordinates, transport_mode):
        """
        Calculates authentic pedestrian or cycling routes using the free OpenStreetMap Valhalla engine.
        Uses real OSM footways, sidewalks, pedestrian bridges, and cycle tracks.
        """
        url = "https://valhalla1.openstreetmap.de/route"
        costing = 'pedestrian' if transport_mode == 'walking' else 'bicycle'
        payload = {
            'locations': [{'lat': float(coord[0]), 'lon': float(coord[1])} for coord in coordinates],
            'costing': costing,
            'units': 'kilometers',
            'directions_options': {
                'units': 'kilometers',
                'language': 'en-US'
            }
        }
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SmartRoutePlanner-NavigationPlatform/3.0'
        }

        routes = []
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                trip = data.get('trip', {})
                if trip and trip.get('legs'):
                    summary = trip.get('summary', {})
                    dist_km = round(summary.get('length', 0), 2)
                    duration_s = summary.get('time', 0)
                    duration_min = round(duration_s / 60.0, 1)

                    leaflet_coords = []
                    steps = []
                    for leg in trip.get('legs', []):
                        shape = leg.get('shape', '')
                        if shape:
                            leg_coords = cls._decode_valhalla_polyline6(shape)
                            if not leaflet_coords:
                                leaflet_coords.extend(leg_coords)
                            else:
                                leaflet_coords.extend(leg_coords[1:])

                        for maneuver in leg.get('maneuvers', []):
                            inst = maneuver.get('instruction', 'Proceed')
                            steps.append({
                                'instruction': inst,
                                'distance_m': round(maneuver.get('length', 0) * 1000.0, 1),
                                'duration_s': round(maneuver.get('time', 0), 1)
                            })

                    if transport_mode == 'walking':
                        calories = int(dist_km * 65)
                        mode_details = f"{calories} kcal &bull; {int(dist_km * 1350):,} steps &bull; OSM Pedestrian Network"
                    else:
                        calories = int(dist_km * 32)
                        mode_details = f"{calories} kcal burned &bull; Zero emissions &bull; OSM Cycling Network"

                    incident_eval = incident_manager.evaluate_route_incidents(leaflet_coords)

                    main_road = "Dedicated Path"
                    if steps:
                        named = [s['instruction'] for s in steps if s['instruction'] and not s['instruction'].startswith('Proceed')]
                        if named:
                            main_road = named[0]

                    routes.append({
                        'id': 1,
                        'name': f"via {main_road}" if main_road != "Dedicated Path" else ("Pedestrian Route" if transport_mode == 'walking' else "Bicycle Route"),
                        'main_road': main_road,
                        'transport_mode': transport_mode,
                        'distance_km': dist_km,
                        'duration_min': round(duration_min * max(1.0, incident_eval['traffic_multiplier']), 1),
                        'coordinates': leaflet_coords,
                        'steps': steps[:15],
                        'fuel_cost': 0.0,
                        'units_consumed': 0.0,
                        'unit_label': 'L',
                        'co2_emissions_kg': 0.0,
                        'mode_details': mode_details,
                        'has_road_closure': incident_eval['has_closure'],
                        'traffic_status': 'Standard flow (OSM)',
                        'live_traffic_available': False,
                        'traffic_multiplier': max(1.0, incident_eval['traffic_multiplier']),
                        'source': 'OpenStreetMap Valhalla'
                    })

                    # If Valhalla genuinely returned alternates, process them (no fake routes!)
                    for alt_idx, alt_trip in enumerate(data.get('alternates', [])):
                        alt_summary = alt_trip.get('trip', {}).get('summary', {})
                        alt_dist = round(alt_summary.get('length', 0), 2)
                        alt_dur = round(alt_summary.get('time', 0) / 60.0, 1)
                        alt_coords = []
                        alt_steps = []
                        for leg in alt_trip.get('trip', {}).get('legs', []):
                            shape = leg.get('shape', '')
                            if shape:
                                leg_c = cls._decode_valhalla_polyline6(shape)
                                if not alt_coords:
                                    alt_coords.extend(leg_c)
                                else:
                                    alt_coords.extend(leg_c[1:])
                            for m in leg.get('maneuvers', []):
                                alt_steps.append({
                                    'instruction': m.get('instruction', 'Proceed'),
                                    'distance_m': round(m.get('length', 0) * 1000.0, 1),
                                    'duration_s': round(m.get('time', 0), 1)
                                })
                        routes.append({
                            'id': alt_idx + 2,
                            'name': f"Alternative {alt_idx + 1}",
                            'main_road': f"Alternative {alt_idx + 1}",
                            'transport_mode': transport_mode,
                            'distance_km': alt_dist,
                            'duration_min': alt_dur,
                            'coordinates': alt_coords,
                            'steps': alt_steps[:15],
                            'fuel_cost': 0.0,
                            'units_consumed': 0.0,
                            'unit_label': 'L',
                            'co2_emissions_kg': 0.0,
                            'mode_details': mode_details,
                            'has_road_closure': False,
                            'traffic_status': 'Standard flow (OSM)',
                            'live_traffic_available': False,
                            'traffic_multiplier': 1.0,
                            'source': 'OpenStreetMap Valhalla'
                        })
        except Exception as e:
            print(f"[Valhalla Routing Notice] {e}")

        return routes

    @classmethod
    def _fetch_google_routes_api(cls, coordinates, transport_mode, api_key, vehicle_type, user_fuel_price, user_efficiency):
        """
        Queries official Google Maps Platform Routes API v2 (computeRoutes).
        Supports: Car (DRIVE), Bicycle (BICYCLE), Walking (WALK), and Two-Wheeler (TWO_WHEELER).
        """
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': api_key,
            'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.description,routes.legs'
        }

        mode_map = {
            'car': 'DRIVE',
            'bicycle': 'BICYCLE',
            'walking': 'WALK'
        }
        travel_mode = mode_map.get(transport_mode, 'DRIVE')

        payload = {
            'origin': {
                'location': {
                    'latLng': {
                        'latitude': coordinates[0][0],
                        'longitude': coordinates[0][1]
                    }
                }
            },
            'destination': {
                'location': {
                    'latLng': {
                        'latitude': coordinates[-1][0],
                        'longitude': coordinates[-1][1]
                    }
                }
            },
            'travelMode': travel_mode,
            'computeAlternativeRoutes': True,
            'languageCode': 'en-US',
            'units': 'METRIC'
        }

        # routingPreference only valid for DRIVE and TWO_WHEELER
        if travel_mode in ['DRIVE', 'TWO_WHEELER']:
            payload['routingPreference'] = 'TRAFFIC_AWARE'

        # Intermediate waypoints
        if len(coordinates) > 2:
            payload['intermediates'] = [
                {'location': {'latLng': {'latitude': pt[0], 'longitude': pt[1]}}}
                for pt in coordinates[1:-1]
            ]

        routes = []
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('routes'):
                    for idx, r in enumerate(data['routes']):
                        dist_m = r.get('distanceMeters', 0)
                        dist_km = dist_m / 1000.0

                        # duration string: e.g. "420s"
                        dur_str = r.get('duration', '0s')
                        try:
                            duration_s = float(str(dur_str).rstrip('s'))
                        except (ValueError, AttributeError):
                            duration_s = 0.0
                        duration_min = duration_s / 60.0

                        # Polyline decoding
                        encoded_poly = r.get('polyline', {}).get('encodedPolyline', '')
                        coords = cls._decode_google_polyline(encoded_poly) if encoded_poly else []

                        # Step maneuvers
                        steps = []
                        for leg in r.get('legs', []):
                            for step in leg.get('steps', []):
                                nav = step.get('navigationInstruction', {})
                                inst = nav.get('instructions') or nav.get('maneuver', 'Proceed')
                                s_dur = 0.0
                                try:
                                    s_dur = float(str(step.get('staticDuration', '0s')).rstrip('s'))
                                except (ValueError, AttributeError):
                                    pass
                                steps.append({
                                    'instruction': inst,
                                    'distance_m': step.get('distanceMeters', 0),
                                    'duration_s': s_dur
                                })

                        if transport_mode == 'car':
                            fuel_stats = FuelCalculator.calculate(dist_km, vehicle_type, user_fuel_price, user_efficiency)
                            fuel_cost = fuel_stats['fuel_cost']
                            co2_kg = fuel_stats['co2_emissions_kg']
                            units = fuel_stats['units_consumed']
                            label = fuel_stats['unit_label']
                            mode_details = "Google Routes API (Live Traffic)"
                        else:
                            fuel_cost = 0.0
                            co2_kg = 0.0
                            units = 0.0
                            label = "L"
                            cal = int(dist_km * (32 if transport_mode == 'bicycle' else 65))
                            mode_details = f"{cal} kcal &bull; Zero emissions"

                        incident_eval = incident_manager.evaluate_route_incidents(coords)
                        has_closure = incident_eval['has_closure']
                        traffic_mult = max(1.0, incident_eval['traffic_multiplier'])

                        summary = r.get('description') or f"Route {idx + 1}"

                        routes.append({
                            'id': idx + 1,
                            'name': f"via {summary}" if summary and not summary.startswith('Route') else f"Route {idx + 1}",
                            'main_road': summary,
                            'transport_mode': transport_mode,
                            'distance_km': round(dist_km, 2),
                            'duration_min': round(duration_min * traffic_mult, 1),
                            'coordinates': coords,
                            'steps': steps[:15],
                            'fuel_cost': fuel_cost,
                            'units_consumed': units,
                            'unit_label': label,
                            'co2_emissions_kg': co2_kg,
                            'mode_details': mode_details,
                            'has_road_closure': has_closure,
                            'traffic_status': 'Live traffic (Google Routes)',
                            'live_traffic_available': True,
                            'traffic_multiplier': traffic_mult,
                            'source': 'Google Routes API'
                        })
            elif resp.status_code in [400, 403, 404]:
                err_info = resp.json().get('error', {})
                err_msg = err_info.get('message', 'Google Routes API error')
                print(f"[Google Cloud Routes API Alert] HTTP {resp.status_code}: {err_msg}")
                if 'billing' in err_msg.lower():
                    print("[Google Cloud Billing Alert] Google Maps Platform requires billing to be enabled: https://console.cloud.google.com/billing")
        except Exception as e:
            print(f"[Google Routes API Service Notice] {e}")

        return routes

    @classmethod
    def _fetch_google_directions(cls, coordinates, transport_mode, api_key, vehicle_type, user_fuel_price, user_efficiency):
        mode_map = {'car': 'driving', 'bicycle': 'bicycling', 'walking': 'walking'}
        gmode = mode_map.get(transport_mode, 'driving')

        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            'origin': f"{coordinates[0][0]},{coordinates[0][1]}",
            'destination': f"{coordinates[-1][0]},{coordinates[-1][1]}",
            'mode': gmode,
            'alternatives': 'true',
            'key': api_key
        }

        # Handle intermediate waypoints
        if len(coordinates) > 2:
            via_pts = "|".join([f"{pt[0]},{pt[1]}" for pt in coordinates[1:-1]])
            params['waypoints'] = via_pts

        routes = []
        try:
            resp = requests.get(url, params=params, timeout=5.5)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status')
                if status == 'OK' and data.get('routes'):
                    for idx, r in enumerate(data['routes']):
                        summary = r.get('summary', f"Route {idx + 1}")
                        legs = r.get('legs', [])
                        total_dist_m = sum(leg.get('distance', {}).get('value', 0) for leg in legs)
                        total_dur_s = sum(leg.get('duration', {}).get('value', 0) for leg in legs)
                        dist_km = total_dist_m / 1000.0
                        duration_min = total_dur_s / 60.0

                        # Decode overview polyline points
                        encoded_polyline = r.get('overview_polyline', {}).get('points', '')
                        coords = cls._decode_google_polyline(encoded_polyline)

                        steps = []
                        for leg in legs:
                            for step in leg.get('steps', []):
                                raw_html = step.get('html_instructions', '')
                                clean_inst = raw_html.replace('<b>', '').replace('</b>', '').replace('<div style="font-size:0.9em">', ' - ').replace('</div>', '')
                                steps.append({
                                    'instruction': clean_inst,
                                    'distance_m': step.get('distance', {}).get('value', 0),
                                    'duration_s': step.get('duration', {}).get('value', 0)
                                })

                        if transport_mode == 'car':
                            fuel_stats = FuelCalculator.calculate(dist_km, vehicle_type, user_fuel_price, user_efficiency)
                            fuel_cost = fuel_stats['fuel_cost']
                            co2_kg = fuel_stats['co2_emissions_kg']
                            units = fuel_stats['units_consumed']
                            label = fuel_stats['unit_label']
                            mode_details = "Google Maps Traffic Engine"
                        else:
                            fuel_cost = 0.0
                            co2_kg = 0.0
                            units = 0.0
                            label = "L"
                            cal = int(dist_km * (32 if transport_mode == 'bicycle' else 65))
                            mode_details = f"{cal} kcal &bull; Zero emissions"

                        incident_eval = incident_manager.evaluate_route_incidents(coords)
                        has_closure = incident_eval['has_closure']
                        traffic_mult = max(1.0, incident_eval['traffic_multiplier'])

                        routes.append({
                            'id': idx + 1,
                            'name': f"via {summary}" if summary else f"Route {idx + 1}",
                            'main_road': summary,
                            'transport_mode': transport_mode,
                            'distance_km': round(dist_km, 2),
                            'duration_min': round(duration_min * traffic_mult, 1),
                            'coordinates': coords,
                            'steps': steps[:15],
                            'fuel_cost': fuel_cost,
                            'units_consumed': units,
                            'unit_label': label,
                            'co2_emissions_kg': co2_kg,
                            'mode_details': mode_details,
                            'has_road_closure': has_closure,
                            'traffic_status': 'Live traffic (Google Maps)',
                            'live_traffic_available': True,
                            'traffic_multiplier': traffic_mult,
                            'source': 'Google Maps Platform'
                        })
                elif status == 'REQUEST_DENIED':
                    err_msg = data.get('error_message', 'Request denied by Google Cloud.')
                    print(f"[Google Cloud Directions API Error] REQUEST_DENIED: {err_msg}")
                    if 'billing' in err_msg.lower():
                        print("[Google Cloud Billing Alert] Google Maps Platform requires billing to be enabled at https://console.cloud.google.com/billing")
                    elif 'referer' in err_msg.lower() or 'restriction' in err_msg.lower():
                        print("[Google Cloud Security Alert] GOOGLE_MAPS_SERVER_KEY appears to have HTTP referrer restrictions. Use an unrestricted or IP-restricted key for server requests.")
                elif status not in ('ZERO_RESULTS',):
                    print(f"[Google Cloud Directions API Notice] Status: {status} - {data.get('error_message', '')}")
        except Exception as e:
            print(f"[Google Directions Service Error] {e}")
        return routes

    @classmethod
    def _decode_google_polyline(cls, point_str):
        """Decodes a Google encoded polyline string into [[lat, lng], ...]."""
        coord_pairs = []
        index, lat, lng = 0, 0, 0
        length = len(point_str)

        while index < length:
            b, shift, result = 0, 0, 0
            while True:
                b = ord(point_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat

            shift, result = 0, 0
            while True:
                b = ord(point_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lng += dlng

            coord_pairs.append([lat / 1e5, lng / 1e5])

        return coord_pairs

    @classmethod
    def benchmark_algorithms(cls, coordinates):
        """Compares Dijkstra and A* search on a topological road grid network."""
        start = coordinates[0]
        end = coordinates[-1]
        graph = Graph()

        rows, cols = 5, 5
        min_lat = min(start[0], end[0])
        max_lat = max(start[0], end[0])
        min_lon = min(start[1], end[1])
        max_lon = max(start[1], end[1])

        d_lat = (max_lat - min_lat) / max(rows - 1, 1) if (max_lat - min_lat) > 1e-5 else 0.01
        d_lon = (max_lon - min_lon) / max(cols - 1, 1) if (max_lon - min_lon) > 1e-5 else 0.01

        for r in range(rows):
            for c in range(cols):
                lat = min_lat + r * d_lat
                lon = min_lon + c * d_lon
                graph.add_node(f"n_{r}_{c}", lat, lon, f"Junction {r},{c}")

        for r in range(rows):
            for c in range(cols):
                u = f"n_{r}_{c}"
                if r + 1 < rows:
                    v = f"n_{r+1}_{c}"
                    graph.add_edge(u, v, speed_limit_kmh=50.0)
                if c + 1 < cols:
                    v = f"n_{r}_{c+1}"
                    graph.add_edge(u, v, speed_limit_kmh=50.0)
                if r + 1 < rows and c + 1 < cols:
                    v = f"n_{r+1}_{c+1}"
                    graph.add_edge(u, v, speed_limit_kmh=60.0)

        start_node = f"n_0_0"
        end_node = f"n_{rows-1}_{cols-1}"

        dijkstra_res = dijkstra_shortest_path(graph, start_node, end_node, metric='distance')
        astar_res = a_star_search(graph, start_node, end_node, metric='distance')

        speedup = 0
        if dijkstra_res.get('nodes_explored', 0) > 0:
            speedup = round(((dijkstra_res['nodes_explored'] - astar_res['nodes_explored']) / dijkstra_res['nodes_explored']) * 100, 1)

        total_edges = sum(len(e) for e in graph.adj.values()) // 2

        return {
            'graph_nodes_count': len(graph.nodes),
            'graph_edges_count': total_edges,
            'dijkstra': dijkstra_res,
            'a_star': astar_res,
            'speedup_percentage': max(0, speedup)
        }
