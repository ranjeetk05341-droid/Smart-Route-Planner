import os
import requests
import time
import urllib.parse

class GeocodingService:
    """
    Real-Time Universal Geocoding & Autocomplete Service.
    
    1. Zero hardcoded locations: Every single result is dynamically resolved.
    2. Dual-Engine support:
       - If GOOGLE_MAPS_API_KEY is configured in environment, queries Google Places Autocomplete & Geocoding.
       - Otherwise, uses Photon by Komoot (Elasticsearch on OpenStreetMap) designed for fast typeahead,
         with a reliable Nominatim fallback.
    3. Multi-language and UTF-8 safe (supports Tokyo, Paris, London, Sydney, Cairo, New York, etc.).
    4. Fast in-memory caching to minimize redundant network traffic.
    """
    PHOTON_URL = "https://photon.komoot.io/api/"
    NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
    NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
    
    HEADERS = {
        'User-Agent': 'SmartRoutePlanner-NavigationPlatform/3.0 (academic.gis.platform@routing.edu)'
    }

    _cache = {}
    _last_nominatim_time = 0

    @classmethod
    def get_server_key(cls):
        """
        Retrieves the server-side API key for Google Geocoding & Places APIs.
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
    def search(cls, query, limit=7):
        """
        Dynamically searches any city, state, country, area, street, or famous landmark worldwide.
        Returns a list of suggestion dicts: { display_name, lat, lon, type, source }
        """
        if not query or len(query.strip()) < 2:
            return []

        q_clean = query.strip()
        cache_key = f"search_{q_clean.lower()}_{limit}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        results = []

        # 1. Check if Google Maps Server API key is configured
        google_server_key = cls.get_server_key()
        if google_server_key:
            results = cls._search_google(q_clean, google_server_key, limit)

        # 2. If no Google key or Google query yielded 0 results, query OSM Photon Autocomplete
        if not results:
            results = cls._search_photon(q_clean, limit)

        # 3. If Photon yielded 0 results, query OSM Nominatim fallback
        if not results:
            results = cls._search_nominatim(q_clean, limit)

        cls._cache[cache_key] = results
        return results

    @classmethod
    def _search_google(cls, query, api_key, limit):
        results = []
        try:
            # 1. Query Google Places Autocomplete API
            auto_url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
            params = {
                'input': query,
                'key': api_key
            }
            resp = requests.get(auto_url, params=params, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get('status')
                if status == 'OK':
                    predictions = data.get('predictions', [])[:limit]
                    for p in predictions:
                        place_id = p.get('place_id')
                        display_name = p.get('description', '')
                        # Resolve coordinates via Geocoding API
                        geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
                        geo_resp = requests.get(geo_url, params={'place_id': place_id, 'key': api_key}, timeout=3.5)
                        if geo_resp.status_code == 200:
                            geo_data = geo_resp.json()
                            geo_results = geo_data.get('results', [])
                            if geo_results:
                                loc = geo_results[0].get('geometry', {}).get('location', {})
                                lat = loc.get('lat')
                                lng = loc.get('lng')
                                if lat is not None and lng is not None:
                                    results.append({
                                        'display_name': display_name,
                                        'lat': float(lat),
                                        'lon': float(lng),
                                        'type': 'google_place',
                                        'source': 'Google Places Platform'
                                    })
                elif status == 'REQUEST_DENIED':
                    err_msg = data.get('error_message', 'Request denied by Google Cloud.')
                    print(f"[Google Cloud Places API] REQUEST_DENIED: {err_msg}")
                    if 'billing' in err_msg.lower():
                        print("[Google Cloud Billing Alert] Billing is not enabled for this Google Cloud Project. Please enable billing at https://console.cloud.google.com/billing")
                    elif 'referer' in err_msg.lower() or 'restriction' in err_msg.lower():
                        print("[Google Cloud Security Alert] GOOGLE_MAPS_SERVER_KEY appears to have HTTP referrer restrictions. Use an unrestricted or IP-restricted key for server requests.")
                elif status not in ('ZERO_RESULTS',):
                    print(f"[Google Cloud Places Notice] Status: {status} - {data.get('error_message', '')}")

            # 2. If Places returned no results, query Google Geocoding API directly
            if not results:
                geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
                geo_resp = requests.get(geo_url, params={'address': query, 'key': api_key}, timeout=3.5)
                if geo_resp.status_code == 200:
                    geo_data = geo_resp.json()
                    status = geo_data.get('status')
                    if status == 'OK':
                        for item in geo_data.get('results', [])[:limit]:
                            loc = item.get('geometry', {}).get('location', {})
                            lat = loc.get('lat')
                            lng = loc.get('lng')
                            if lat is not None and lng is not None:
                                results.append({
                                    'display_name': item.get('formatted_address', query),
                                    'lat': float(lat),
                                    'lon': float(lng),
                                    'type': 'google_geocode',
                                    'source': 'Google Geocoding API'
                                })
                    elif status == 'REQUEST_DENIED':
                        err_msg = geo_data.get('error_message', '')
                        print(f"[Google Cloud Geocoding API] REQUEST_DENIED: {err_msg}")
        except Exception as e:
            print(f"[Google Geocoding Service Error] {e}")

        return results

    @classmethod
    def _search_photon(cls, query, limit):
        results = []
        try:
            params = {
                'q': query,
                'limit': limit
            }
            resp = requests.get(cls.PHOTON_URL, params=params, headers=cls.HEADERS, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                for feature in data.get('features', []):
                    props = feature.get('properties', {})
                    coords = feature.get('geometry', {}).get('coordinates', [])
                    if len(coords) >= 2:
                        lon = float(coords[0])
                        lat = float(coords[1])

                        # Build a rich, natural display name
                        name_parts = []
                        if props.get('name'):
                            name_parts.append(props['name'])
                        if props.get('street') and props.get('street') != props.get('name'):
                            name_parts.append(props['street'])
                        if props.get('city') and props.get('city') != props.get('name'):
                            name_parts.append(props['city'])
                        elif props.get('county'):
                            name_parts.append(props['county'])
                        if props.get('state'):
                            name_parts.append(props['state'])
                        if props.get('country'):
                            name_parts.append(props['country'])

                        display_name = ", ".join(name_parts) if name_parts else props.get('name', query)

                        # Deduplicate by spatial proximity (< 100 meters)
                        if not any(abs(r['lat'] - lat) < 0.001 and abs(r['lon'] - lon) < 0.001 for r in results):
                            results.append({
                                'display_name': display_name,
                                'lat': lat,
                                'lon': lon,
                                'type': props.get('osm_value', 'locality'),
                                'source': 'OpenStreetMap'
                            })
        except Exception:
            pass
        return results

    @classmethod
    def _search_nominatim(cls, query, limit):
        results = []
        now = time.time()
        elapsed = now - cls._last_nominatim_time
        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)
        cls._last_nominatim_time = time.time()

        try:
            params = {
                'q': query,
                'format': 'json',
                'limit': limit,
                'addressdetails': 1
            }
            resp = requests.get(cls.NOMINATIM_SEARCH_URL, params=params, headers=cls.HEADERS, timeout=4.5)
            if resp.status_code == 200:
                items = resp.json()
                for item in items:
                    lat = float(item.get('lat', 0))
                    lon = float(item.get('lon', 0))
                    display_name = item.get('display_name', query)
                    if lat and lon:
                        results.append({
                            'display_name': display_name,
                            'lat': lat,
                            'lon': lon,
                            'type': item.get('type', 'place'),
                            'source': 'OpenStreetMap'
                        })
        except Exception:
            pass
        return results

    @classmethod
    def reverse(cls, lat, lon):
        cache_key = f"rev_{lat:.4f}_{lon:.4f}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Check Google first if key is present
        google_key = cls.get_google_api_key()
        if google_key:
            try:
                geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
                resp = requests.get(geo_url, params={'latlng': f"{lat},{lon}", 'key': google_key}, timeout=3.5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('results'):
                        display_name = data['results'][0].get('formatted_address', f"Location ({lat:.4f}, {lon:.4f})")
                        cls._cache[cache_key] = display_name
                        return display_name
            except Exception:
                pass

        # Nominatim reverse lookup with 1-second rate limit
        now = time.time()
        elapsed = now - cls._last_nominatim_time
        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)
        cls._last_nominatim_time = time.time()

        try:
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'zoom': 18,
                'addressdetails': 1
            }
            resp = requests.get(cls.NOMINATIM_REVERSE_URL, params=params, headers=cls.HEADERS, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                display_name = data.get('display_name', f"Location ({lat:.4f}, {lon:.4f})")
                cls._cache[cache_key] = display_name
                return display_name
        except Exception:
            pass

        fallback = f"Pinned Location ({lat:.4f}, {lon:.4f})"
        cls._cache[cache_key] = fallback
        return fallback
