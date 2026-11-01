import json
from flask import Blueprint, request, jsonify, session
from backend.database.db import db
from backend.models.route import RouteHistory, FavoriteRoute
from backend.models.user import User
from backend.services.osrm_service import OSRMRoutingService
from backend.algorithms.optimizer import evaluate_and_rank_routes, get_mode_weights

route_bp = Blueprint('routes', __name__, url_prefix='/api/routes')

@route_bp.route('/calculate', methods=['POST'])
def calculate_route():
    data = request.get_json() or {}
    coordinates = data.get('coordinates', [])  # list of [lat, lon]
    mode = data.get('mode', 'fastest')
    transport_mode = data.get('transport_mode') or data.get('travel_mode') or 'car'
    custom_weights = data.get('custom_weights')
    vehicle_type = data.get('vehicle_type', 'petrol')
    fuel_price = data.get('fuel_price')
    fuel_efficiency = data.get('fuel_efficiency')
    user_id = data.get('user_id') or session.get('user_id')
    source_name = data.get('source_name', 'Origin')
    dest_name = data.get('dest_name', 'Destination')

    if not coordinates or len(coordinates) < 2:
        return jsonify({'error': 'At least 2 coordinates (source and destination) are required.'}), 400

    try:
        # 1. Fetch route alternatives from Multi-Modal Routing Engine (Google / OSRM)
        routing_res = OSRMRoutingService.get_routes(
            coordinates=coordinates,
            vehicle_type=vehicle_type,
            user_fuel_price=fuel_price,
            user_efficiency=fuel_efficiency,
            transport_mode=transport_mode,
            optimization_mode=mode
        )

        routes = routing_res['routes']

        # 2. Evaluate and Rank routes using Multi-Objective Weighted Scoring
        ranked_routes = evaluate_and_rank_routes(routes, mode=mode, custom_weights=custom_weights)

        # 3. If there is a recommended route and user_id is provided, save to history
        if ranked_routes and user_id:
            try:
                best_route = ranked_routes[0]
                history_entry = RouteHistory(
                    user_id=int(user_id),
                    source_name=source_name,
                    source_lat=coordinates[0][0],
                    source_lng=coordinates[0][1],
                    dest_name=dest_name,
                    dest_lat=coordinates[-1][0],
                    dest_lng=coordinates[-1][1],
                    waypoints_json=json.dumps(coordinates[1:-1]),
                    distance_km=best_route['distance_km'],
                    duration_min=best_route['duration_min'],
                    fuel_cost=best_route['fuel_cost'],
                    route_mode=f"{transport_mode}_{mode}",
                    efficiency_score=best_route.get('efficiency_score', 95.0),
                    route_summary=f"{best_route['name']} ({best_route['distance_km']} km)"
                )
                db.session.add(history_entry)
                db.session.commit()
            except Exception:
                db.session.rollback()

        return jsonify({
            'success': True,
            'mode': mode,
            'transport_mode': transport_mode,
            'weights_used': get_mode_weights(mode) if not custom_weights else custom_weights,
            'routes': ranked_routes,
            'is_live': routing_res.get('is_live', True),
            'waypoints_count': len(coordinates)
        }), 200

    except (ValueError, RuntimeError) as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@route_bp.route('/benchmark', methods=['POST'])
def benchmark_algorithms():
    data = request.get_json() or {}
    coordinates = data.get('coordinates', [])
    if len(coordinates) < 2:
        return jsonify({'error': 'Coordinates required for benchmarking.'}), 400

    try:
        benchmark_res = OSRMRoutingService.benchmark_algorithms(coordinates)
        return jsonify({
            'success': True,
            'benchmark': benchmark_res
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@route_bp.route('/history', methods=['GET'])
def get_history():
    user_id = request.args.get('user_id') or session.get('user_id')
    query = RouteHistory.query
    if user_id:
        query = query.filter_by(user_id=int(user_id))
    history_items = query.order_by(RouteHistory.created_at.desc()).limit(15).all()

    return jsonify({
        'history': [item.to_dict() for item in history_items]
    }), 200


@route_bp.route('/favorite', methods=['POST'])
def save_favorite():
    data = request.get_json() or {}
    user_id = data.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'error': 'User authentication required.'}), 401

    fav = FavoriteRoute(
        user_id=int(user_id),
        route_name=data.get('route_name', 'Favorite Route'),
        source_name=data.get('source_name', 'Source'),
        source_lat=float(data.get('source_lat', 0.0)),
        source_lng=float(data.get('source_lng', 0.0)),
        dest_name=data.get('dest_name', 'Destination'),
        dest_lat=float(data.get('dest_lat', 0.0)),
        dest_lng=float(data.get('dest_lng', 0.0)),
        waypoints_json=json.dumps(data.get('waypoints', [])),
        distance_km=float(data.get('distance_km', 0.0)),
        duration_min=float(data.get('duration_min', 0.0)),
        route_mode=data.get('route_mode', 'balanced')
    )
    db.session.add(fav)
    db.session.commit()

    return jsonify({
        'message': 'Route saved to favorites.',
        'favorite': fav.to_dict()
    }), 201


@route_bp.route('/favorites', methods=['GET'])
def get_favorites():
    user_id = request.args.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({'favorites': []}), 200

    favorites = FavoriteRoute.query.filter_by(user_id=int(user_id)).order_by(FavoriteRoute.created_at.desc()).all()
    return jsonify({
        'favorites': [f.to_dict() for f in favorites]
    }), 200


@route_bp.route('/favorite/<int:fav_id>', methods=['DELETE'])
def delete_favorite(fav_id):
    fav = db.session.get(FavoriteRoute, fav_id)
    if not fav:
        return jsonify({'error': 'Favorite not found.'}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({'message': 'Favorite removed.'}), 200

