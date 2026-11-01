from flask import Blueprint, request, jsonify
from backend.services.simulation_service import incident_manager

simulation_bp = Blueprint('simulation', __name__, url_prefix='/api/simulation')

@simulation_bp.route('/incidents', methods=['GET'])
def get_incidents():
    incidents = incident_manager.get_all()
    return jsonify({'incidents': incidents}), 200


@simulation_bp.route('/incidents', methods=['POST'])
def add_incident():
    data = request.get_json() or {}
    incident_type = data.get('type', 'closure')  # 'closure' or 'traffic'
    lat = data.get('lat')
    lon = data.get('lon')
    radius_km = data.get('radius_km', 0.4)
    description = data.get('description', '')
    multiplier = data.get('multiplier', 2.5)

    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude are required.'}), 400

    incident = incident_manager.add_incident(
        incident_type=incident_type,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
        description=description,
        multiplier=multiplier
    )

    return jsonify({
        'message': f"Simulated {incident_type} incident created.",
        'incident': incident
    }), 201


@simulation_bp.route('/incidents/<int:incident_id>', methods=['DELETE'])
def remove_incident(incident_id):
    incident_manager.remove_incident(incident_id)
    return jsonify({'message': f'Incident {incident_id} removed.'}), 200


@simulation_bp.route('/clear', methods=['POST'])
def clear_incidents():
    incident_manager.clear_all()
    return jsonify({'message': 'All simulated incidents cleared.'}), 200

