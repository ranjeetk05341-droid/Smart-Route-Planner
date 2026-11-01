import os
import sys

# Ensure backend root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Load environment variables via python-dotenv if present, with resilient built-in fallback
try:
    from dotenv import load_dotenv
    for env_path in [os.path.join(parent_dir, '.env'), os.path.join(current_dir, '.env')]:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
except ImportError:
    pass

# Resilient built-in .env parser
for env_path in [os.path.join(parent_dir, '.env'), os.path.join(current_dir, '.env')]:
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

import requests
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from backend.database.db import db, init_db
from backend.database.seed_data import seed_sample_data
from backend.routes.auth_routes import auth_bp
from backend.routes.route_routes import route_bp
from backend.routes.location_routes import location_bp
from backend.routes.simulation_routes import simulation_bp

def create_app():
    frontend_folder = os.path.join(parent_dir, 'frontend')
    app = Flask(__name__, static_folder=frontend_folder, static_url_path='')
    CORS(app, supports_credentials=True)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'smart-route-planner-academic-secret-key-2026')
    db_path = os.path.join(current_dir, 'smart_route.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Database
    init_db(app)

    with app.app_context():
        seed_sample_data()

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(route_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(simulation_bp)

    # Client-Safe Maps Config Endpoint
    @app.route('/api/config/maps')
    def maps_config():
        """
        Exposes GOOGLE_MAPS_BROWSER_KEY for frontend Google Maps JS API.
        SECURITY MANDATE: GOOGLE_MAPS_SERVER_KEY is NEVER exposed here or to client-side code.
        """
        browser_key = os.environ.get('GOOGLE_MAPS_BROWSER_KEY', '').strip()
        if browser_key in ['YOUR_BROWSER_KEY', 'your_google_maps_browser_key_here']:
            browser_key = ''
        server_key = (os.environ.get('GOOGLE_MAPS_SERVER_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip()
        if server_key in ['YOUR_SERVER_KEY', 'your_google_maps_server_key_here']:
            server_key = ''
        return jsonify({
            'google_maps_browser_key': browser_key,
            'google_maps_enabled': bool(browser_key),
            'has_server_key': bool(server_key),
            'active_engine': 'Google Maps Platform' if (browser_key or server_key) else 'OpenStreetMap (OSM)'
        })

    # Diagnostic Endpoint to verify Google Cloud Billing, API Activation & Credentials
    @app.route('/api/diagnostics/google-maps')
    def google_maps_diagnostics():
        browser_key = os.environ.get('GOOGLE_MAPS_BROWSER_KEY', '').strip()
        if browser_key in ['YOUR_BROWSER_KEY', 'your_google_maps_browser_key_here']:
            browser_key = ''
        server_key = (os.environ.get('GOOGLE_MAPS_SERVER_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip()
        if server_key in ['YOUR_SERVER_KEY', 'your_google_maps_server_key_here']:
            server_key = ''

        diagnostics = {
            'browser_key_configured': bool(browser_key),
            'server_key_configured': bool(server_key),
            'browser_key_preview': f"{browser_key[:6]}...{browser_key[-4:]}" if len(browser_key) > 10 else None,
            'server_key_preview': f"{server_key[:6]}...{server_key[-4:]}" if len(server_key) > 10 else None,
            'geocoding_api': {'status': 'not_tested'},
            'directions_api': {'status': 'not_tested'},
            'billing_status': 'unknown',
            'recommendations': []
        }

        if not server_key:
            diagnostics['recommendations'].append("No GOOGLE_MAPS_SERVER_KEY configured. System is running on 100% free OpenStreetMap & Photon geocoding.")
            return jsonify(diagnostics), 200

        # 1. Test Google Geocoding API with server key
        try:
            geo_res = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={'address': 'New Delhi', 'key': server_key},
                timeout=4.5
            )
            geo_json = geo_res.json()
            status = geo_json.get('status')
            err_msg = geo_json.get('error_message', '')
            diagnostics['geocoding_api'] = {
                'http_code': geo_res.status_code,
                'status': status,
                'error_message': err_msg
            }
            if status == 'REQUEST_DENIED':
                if 'billing' in err_msg.lower():
                    diagnostics['billing_status'] = 'BILLING_NOT_ENABLED'
                    diagnostics['recommendations'].append("Enable Billing on your Google Cloud Project: https://console.cloud.google.com/billing")
                elif 'referer' in err_msg.lower() or 'restriction' in err_msg.lower():
                    diagnostics['recommendations'].append("GOOGLE_MAPS_SERVER_KEY has HTTP referrer restrictions. Use an unrestricted or IP-restricted key for server requests.")
        except Exception as e:
            diagnostics['geocoding_api'] = {'error': str(e)}

        # 2. Test Google Directions / Routes API with server key
        try:
            dir_res = requests.get(
                "https://maps.googleapis.com/maps/api/directions/json",
                params={'origin': '28.6315,77.2167', 'destination': '28.5562,77.1000', 'key': server_key},
                timeout=4.5
            )
            dir_json = dir_res.json()
            status = dir_json.get('status')
            err_msg = dir_json.get('error_message', '')
            diagnostics['directions_api'] = {
                'http_code': dir_res.status_code,
                'status': status,
                'error_message': err_msg
            }
            if status == 'REQUEST_DENIED':
                if 'billing' in err_msg.lower():
                    diagnostics['billing_status'] = 'BILLING_NOT_ENABLED'
                    if "Enable Billing" not in str(diagnostics['recommendations']):
                        diagnostics['recommendations'].append("Enable Billing on your Google Cloud Project: https://console.cloud.google.com/billing")
                elif 'referer' in err_msg.lower() or 'restriction' in err_msg.lower():
                    if "HTTP referrer" not in str(diagnostics['recommendations']):
                        diagnostics['recommendations'].append("GOOGLE_MAPS_SERVER_KEY has HTTP referrer restrictions. Use an unrestricted or IP-restricted key for backend calls.")
        except Exception as e:
            diagnostics['directions_api'] = {'error': str(e)}

        if diagnostics['geocoding_api'].get('status') == 'OK' and diagnostics['directions_api'].get('status') == 'OK':
            diagnostics['billing_status'] = 'ACTIVE_AND_VERIFIED'
            diagnostics['recommendations'].append("Google Maps Platform APIs are active, verified, and operational.")

        return jsonify(diagnostics), 200

    # API Health Check
    @app.route('/api/health')
    def health():
        server_key_present = bool((os.environ.get('GOOGLE_MAPS_SERVER_KEY') or os.environ.get('GOOGLE_MAPS_API_KEY') or '').strip())
        browser_key_present = bool(os.environ.get('GOOGLE_MAPS_BROWSER_KEY', '').strip())
        return jsonify({
            'status': 'healthy',
            'project': 'Smart Route Planner',
            'version': '1.0.0',
            'database': 'SQLite Connected',
            'google_maps_platform': {
                'browser_key_configured': browser_key_present,
                'server_key_configured': server_key_present
            }
        })

    # Serve Frontend Pages
    @app.route('/')
    def index():
        return send_from_directory(frontend_folder, 'index.html')

    @app.route('/dashboard')
    def dashboard():
        return send_from_directory(frontend_folder, 'dashboard.html')

    @app.route('/login')
    def login_page():
        return send_from_directory(frontend_folder, 'login.html')

    @app.route('/register')
    def register_page():
        return send_from_directory(frontend_folder, 'register.html')

    # Serve static assets
    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(frontend_folder, filename)

    return app

# WSGI Application entry point (Compatible with Vercel Serverless, Gunicorn & Local Flask)
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"================================================================")
    print(f"  SMART ROUTE PLANNER - ACADEMIC FINAL-YEAR CAPSTONE SYSTEM")
    print(f"  Running on: http://127.0.0.1:{port}")
    print(f"  Dashboard:  http://127.0.0.1:{port}/dashboard")
    print(f"================================================================")
    app.run(host='0.0.0.0', port=port, debug=True)

