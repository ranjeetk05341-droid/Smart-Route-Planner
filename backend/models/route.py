import json
from datetime import datetime
from backend.database.db import db

class RouteHistory(db.Model):
    __tablename__ = 'route_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    source_name = db.Column(db.String(255), nullable=False)
    source_lat = db.Column(db.Float, nullable=False)
    source_lng = db.Column(db.Float, nullable=False)
    dest_name = db.Column(db.String(255), nullable=False)
    dest_lat = db.Column(db.Float, nullable=False)
    dest_lng = db.Column(db.Float, nullable=False)
    waypoints_json = db.Column(db.Text, default='[]')
    distance_km = db.Column(db.Float, nullable=False)
    duration_min = db.Column(db.Float, nullable=False)
    fuel_cost = db.Column(db.Float, default=0.0)
    route_mode = db.Column(db.String(50), default='balanced')
    efficiency_score = db.Column(db.Float, default=0.0)
    route_summary = db.Column(db.String(255), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            waypoints = json.loads(self.waypoints_json) if self.waypoints_json else []
        except Exception:
            waypoints = []

        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_name': self.source_name,
            'source_coords': [self.source_lat, self.source_lng],
            'dest_name': self.dest_name,
            'dest_coords': [self.dest_lat, self.dest_lng],
            'waypoints': waypoints,
            'distance_km': round(self.distance_km, 2),
            'duration_min': round(self.duration_min, 1),
            'fuel_cost': round(self.fuel_cost, 2),
            'route_mode': self.route_mode,
            'efficiency_score': round(self.efficiency_score, 1),
            'route_summary': self.route_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FavoriteRoute(db.Model):
    __tablename__ = 'favorite_routes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    route_name = db.Column(db.String(100), nullable=False)
    source_name = db.Column(db.String(255), nullable=False)
    source_lat = db.Column(db.Float, nullable=False)
    source_lng = db.Column(db.Float, nullable=False)
    dest_name = db.Column(db.String(255), nullable=False)
    dest_lat = db.Column(db.Float, nullable=False)
    dest_lng = db.Column(db.Float, nullable=False)
    waypoints_json = db.Column(db.Text, default='[]')
    distance_km = db.Column(db.Float, nullable=False)
    duration_min = db.Column(db.Float, nullable=False)
    route_mode = db.Column(db.String(50), default='balanced')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        try:
            waypoints = json.loads(self.waypoints_json) if self.waypoints_json else []
        except Exception:
            waypoints = []

        return {
            'id': self.id,
            'user_id': self.user_id,
            'route_name': self.route_name,
            'source_name': self.source_name,
            'source_coords': [self.source_lat, self.source_lng],
            'dest_name': self.dest_name,
            'dest_coords': [self.dest_lat, self.dest_lng],
            'waypoints': waypoints,
            'distance_km': round(self.distance_km, 2),
            'duration_min': round(self.duration_min, 1),
            'route_mode': self.route_mode,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

