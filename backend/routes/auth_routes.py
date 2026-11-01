from flask import Blueprint, request, jsonify, session
from backend.database.db import db
from backend.models.user import User, UserPreferences

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username is already taken.'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered.'}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    # Create default preferences
    pref = UserPreferences(
        user_id=user.id,
        vehicle_type=data.get('vehicle_type', 'petrol'),
        fuel_price=float(data.get('fuel_price', 1.50)),
        fuel_efficiency=float(data.get('fuel_efficiency', 15.0)),
        default_mode=data.get('default_mode', 'balanced')
    )
    db.session.add(pref)
    db.session.commit()

    return jsonify({
        'message': 'Registration successful.',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    identity = data.get('identity', '').strip()  # username or email
    password = data.get('password', '')

    if not identity or not password:
        return jsonify({'error': 'Please provide username/email and password.'}), 400

    user = User.query.filter((User.username == identity) | (User.email == identity.lower())).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    session['user_id'] = user.id
    return jsonify({
        'message': 'Login successful.',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id') or request.args.get('user_id')
    if not user_id:
        return jsonify({'user': None, 'authenticated': False}), 200

    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'user': None, 'authenticated': False}), 200

    return jsonify({
        'user': user.to_dict(),
        'authenticated': True
    }), 200


@auth_bp.route('/preferences', methods=['PUT', 'POST'])
def update_preferences():
    user_id = session.get('user_id') or request.json.get('user_id')
    if not user_id:
        return jsonify({'error': 'Authentication required to save preferences.'}), 401

    user = db.session.get(User, int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.get_json() or {}
    pref = user.preferences
    if not pref:
        pref = UserPreferences(user_id=user.id)
        db.session.add(pref)

    if 'vehicle_type' in data:
        pref.vehicle_type = data['vehicle_type']
    if 'fuel_price' in data:
        pref.fuel_price = float(data['fuel_price'])
    if 'fuel_efficiency' in data:
        pref.fuel_efficiency = float(data['fuel_efficiency'])
    if 'default_mode' in data:
        pref.default_mode = data['default_mode']
    if 'dark_mode' in data:
        pref.dark_mode = bool(data['dark_mode'])

    db.session.commit()
    return jsonify({
        'message': 'Preferences updated successfully.',
        'preferences': pref.to_dict()
    }), 200

