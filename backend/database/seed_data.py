from backend.database.db import db
from backend.models.user import User, UserPreferences
from backend.models.location import SavedLocation
from backend.models.route import RouteHistory, FavoriteRoute

def seed_sample_data():
    """Seeds sample user and demo data if not already present."""
    if User.query.filter_by(username='demo').first():
        return  # Already seeded

    demo_user = User(
        username='demo',
        email='demo@smartroute.edu'
    )
    demo_user.set_password('password123')
    db.session.add(demo_user)
    db.session.flush()

    # User preferences
    pref = UserPreferences(
        user_id=demo_user.id,
        vehicle_type='petrol',
        fuel_price=1.50,
        fuel_efficiency=16.0,
        default_mode='balanced',
        dark_mode=False
    )
    db.session.add(pref)

    # Saved locations
    loc1 = SavedLocation(
        user_id=demo_user.id,
        label='Home Residence',
        address='Connaught Place, Central Delhi, Delhi, India',
        latitude=28.6315,
        longitude=77.2167,
        category='home'
    )
    loc2 = SavedLocation(
        user_id=demo_user.id,
        label='Tech Hub Office',
        address='Indira Gandhi International Airport, Terminal 3, New Delhi, India',
        latitude=28.5562,
        longitude=77.1000,
        category='work'
    )
    loc3 = SavedLocation(
        user_id=demo_user.id,
        label='Logistics Hub',
        address='New Delhi Railway Station, Delhi, India',
        latitude=28.6431,
        longitude=77.2197,
        category='delivery'
    )
    db.session.add_all([loc1, loc2, loc3])

    # Sample Route History
    hist = RouteHistory(
        user_id=demo_user.id,
        source_name='Connaught Place',
        source_lat=28.6315,
        source_lng=77.2167,
        dest_name='IGI Airport',
        dest_lat=28.5562,
        dest_lng=77.1000,
        waypoints_json='[]',
        distance_km=15.4,
        duration_min=24.5,
        fuel_cost=1.44,
        route_mode='balanced',
        efficiency_score=96.2,
        route_summary='Primary Highway Corridor'
    )
    db.session.add(hist)

    # Sample Favorite Route
    fav = FavoriteRoute(
        user_id=demo_user.id,
        route_name='Daily Office Commute',
        source_name='Connaught Place',
        source_lat=28.6315,
        source_lng=77.2167,
        dest_name='IGI Airport',
        dest_lat=28.5562,
        dest_lng=77.1000,
        distance_km=15.4,
        duration_min=24.5,
        route_mode='fastest'
    )
    db.session.add(fav)

    db.session.commit()
    print("Database seeded with demo account: username 'demo' | password 'password123'")

