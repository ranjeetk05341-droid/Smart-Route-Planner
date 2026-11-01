from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    saved_locations = db.relationship('SavedLocation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    route_histories = db.relationship('RouteHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    favorite_routes = db.relationship('FavoriteRoute', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    preferences = db.relationship('UserPreferences', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'preferences': self.preferences.to_dict() if self.preferences else None
        }


class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), default='petrol')  # petrol, diesel, ev, hybrid, bike, truck
    fuel_price = db.Column(db.Float, default=1.50)  # price per Liter or kWh
    fuel_efficiency = db.Column(db.Float, default=15.0)  # km/L or km/kWh
    default_mode = db.Column(db.String(50), default='balanced')  # fastest, shortest, economical, balanced
    dark_mode = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_type': self.vehicle_type,
            'fuel_price': self.fuel_price,
            'fuel_efficiency': self.fuel_efficiency,
            'default_mode': self.default_mode,
            'dark_mode': self.dark_mode
        }

