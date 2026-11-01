from flask import Blueprint, request, jsonify, session
from backend.database.db import db
from backend.models.location import SavedLocation
from backend.services.geocoding_service import GeocodingService
from backend.services.overpass_service import OverpassService

location_bp = Blueprint('locations', __name__, url_prefix='/api/locations')

@location_bp.route('/search', methods=['GET'])
def search_places():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'results': []}), 200

    results = GeocodingService.search(query, limit=6)
    return jsonify({'results': results}), 200


@location_bp.route('/reverse', methods=['GET'])
def reverse_geocode():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if lat is None or lon is None:
        return jsonify({'error': 'lat and lon parameters are required.'}), 400

    address = GeocodingService.reverse(lat, lon)
    return jsonify({
        'address': address,
        'lat': lat,
        'lon': lon
    }), 200


@location_bp.route('/pois', methods=['GET'])
def get_points_of_interest():
    """
    Returns real mapped OpenStreetMap Points of Interest (POIs) via Overpass API.
    Supports: restaurants, hotels, hospitals, pharmacies, schools, colleges,
    malls, petrol pumps, ATMs, railway stations, and bus stops.
    """
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    radius = request.args.get('radius', default=2000, type=int)
    category = request.args.get('category', default='all')
    bbox_param = request.args.get('bbox')  # format: south,west,north,east
    limit = request.args.get('limit', default=50, type=int)

    bounds = None
    if bbox_param:
        try:
            parts = [float(p.strip()) for p in bbox_param.split(',')]
            if len(parts) == 4:
                bounds = parts
        except Exception:
            bounds = None

    pois = OverpassService.get_pois(
        lat=lat,
        lon=lon,
        radius_m=radius,
        bounds=bounds,
        category=category,
        limit=limit
    )

    return jsonify({
        'success': True,
        'count': len(pois),
        'category': category,
        'pois': pois
    }), 200


@location_bp.route('/saved', methods=['GET'])
def get_saved_locations():
    user_id = request.args.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'locations': []}), 200

    locs = SavedLocation.query.filter_by(user_id=int(user_id)).order_by(SavedLocation.created_at.desc()).all()
    return jsonify({'locations': [l.to_dict() for l in locs]}), 200


@location_bp.route('/saved', methods=['POST'])
def save_location():
    data = request.get_json() or {}
    user_id = data.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User authentication required.'}), 401

    label = data.get('label', '').strip()
    address = data.get('address', '').strip()
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not label or not address or lat is None or lon is None:
        return jsonify({'error': 'Label, address, latitude, and longitude are required.'}), 400

    loc = SavedLocation(
        user_id=int(user_id),
        label=label,
        address=address,
        latitude=float(lat),
        longitude=float(lon),
        category=data.get('category', 'custom')
    )
    db.session.add(loc)
    db.session.commit()

    return jsonify({
        'message': 'Location saved successfully.',
        'location': loc.to_dict()
    }), 201


@location_bp.route('/saved/<int:loc_id>', methods=['DELETE'])
def delete_saved_location(loc_id):
    loc = db.session.get(SavedLocation, loc_id)
    if not loc:
        return jsonify({'error': 'Location not found.'}), 404

    db.session.delete(loc)
    db.session.commit()
    return jsonify({'message': 'Saved location removed.'}), 200
