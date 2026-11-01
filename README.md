# SMART ROUTE PLANNER
### An Intelligent Route Optimization System for Real-World Transportation Problems
*College Final-Year Capstone Project*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com/)
[![Leaflet](https://img.shields.io/badge/GIS-Leaflet.js-brightgreen.svg)](https://leafletjs.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 🌟 Overview
**Smart Route Planner** is a state-of-the-art navigation and route optimization platform engineered to solve real-world urban transit bottlenecks. It replaces opaque single-metric routing by providing a **Multi-Objective Weighted Cost Optimization Engine** that balances:
- ⏱ **Travel Time** (Traffic avoidance & highway utilization)
- 📏 **Physical Distance** (Shortest path minimization)
- ⛽ **Fuel / Energy Costs** (Vehicle-specific consumption & carbon emissions)
- 🚧 **Road Closures & Real-Time Hazards** (Dynamic detour rerouting)

It features both **Dijkstra's Algorithm** and **A\* Search (with Haversine Heuristics)** with side-by-side performance benchmarking.

---

## 🚀 Key Features
1. **100% Free OpenStreetMap Cartography (Zero API Key Required)**: Powered by official **Leaflet.js** and `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, providing clean road hierarchies, highways, streets, and locality labels with zero third-party API keys or rate-limit watermarks.
2. **Real OSM Points of Interest (POIs) via Overpass API**:
   - Filter by: 🍽 Restaurants, 🏨 Hotels, 🏥 Hospitals, 💊 Pharmacies, ⛽ Petrol Pumps, 🏧 ATMs & Banks, 🛍 Malls, 🏫 Schools, 🎓 Colleges, 🚆 Train Stations, and 🚌 Bus Stops.
   - Distinct custom color-coded map pins with icons.
   - Rich Google Maps-inspired place details popup (name, category, address, coordinates, opening hours, cuisine, direct directions buttons).
3. **Compliant OpenStreetMap Search**:
   - Powered by **Photon (Komoot OSM Geocoder)**, strictly respecting Nominatim autocomplete policies with 300ms debouncing, memory caching, and instant Enter-key search.
4. **Transparent Traffic Policy**:
   - Clearly identifies when live real-time traffic is unavailable on the public free OSM tier rather than displaying fabricated data.
   - Distinctly tags user-injected scenario delays in the Road Hazard Simulator.
5. **Multi-Stop Route Planning**: Add intermediate delivery or commute waypoints.
6. **Four Optimization Modes**:
   - ⚡ **Fastest Route**: Minimizes estimated travel duration.
   - 📏 **Shortest Route**: Minimizes total physical kilometers.
   - 💰 **Economical Route**: Minimizes fuel/energy consumption and toll expenses.
   - ⚖ **Balanced Route**: Multi-criteria Pareto compromise between distance, time, and cost.
7. **Smart Route Comparison Cards**: Displays distance, duration, fuel expense, carbon emissions ($CO_2$), efficiency percentage badges, and turn-by-turn navigation steps.
8. **Dynamic Road Incident Simulator**: Click anywhere on the map to inject simulated road closures or heavy traffic congestion zones and observe real-time rerouting.
9. **Academic Algorithm Visualizer**: Side-by-side node exploration counts, search space reduction, and execution latency ($ms$) between Dijkstra and A*.
10. **Vehicle Profiles**: Petrol cars, Diesel SUVs, Electric Vehicles (EV), Hybrids, Two-wheelers, and Commercial Trucks.
11. **Relational Persistence**: User accounts, password hashing, saved locations, route history, and favorite routes stored in SQLite.

---

## 🛠 Tech Stack
- **Frontend**: HTML5, CSS3, Tailwind CSS (CDN), Vanilla JavaScript (ES6+), Leaflet.js, Lucide Icons.
- **Backend**: Python 3.14 / 3.10+, Flask, Flask-CORS, Flask-SQLAlchemy, Werkzeug, Requests.
- **GIS & Mapping**: OpenStreetMap (OSM) Tiles, OSRM Public Routing API, CartoDB Positron / Voyager.
- **Database**: SQLite3 with SQLAlchemy ORM.
- **Algorithms**: Priority-Queue Dijkstra, A* Search with Haversine Heuristic, Multi-Objective Cost Engine.

---

## 📂 Project Structure
```
smart-route-planner/
│
├── backend/
│   ├── app.py                      # Flask Application entry point & gateway
│   ├── requirements.txt            # Python dependencies
│   ├── smart_route.db              # SQLite Database (auto-generated)
│   ├── database/
│   │   ├── db.py                   # SQLAlchemy database setup
│   │   └── seed_data.py            # Sample demo user & seed routes
│   ├── models/
│   │   ├── user.py                 # User & UserPreferences models
│   │   ├── location.py             # SavedLocation model
│   │   └── route.py                # RouteHistory & FavoriteRoute models
│   ├── algorithms/
│   │   ├── graph.py                # Directed weighted graph implementation
│   │   ├── dijkstra.py             # Dijkstra algorithm with metrics
│   │   ├── a_star.py               # A* search with Haversine heuristic
│   │   └── optimizer.py            # Multi-objective weighted scoring engine
│   ├── services/
│   │   ├── osrm_service.py         # OSRM public API integration with fallback
│   │   ├── geocoding_service.py    # Nominatim search & reverse geocoding
│   │   ├── fuel_calculator.py      # Fuel consumption & CO2 emission engine
│   │   └── simulation_service.py   # Traffic congestion & road closure simulation
│   └── routes/
│       ├── auth_routes.py          # /api/auth
│       ├── route_routes.py         # /api/routes
│       ├── location_routes.py      # /api/locations
│       └── simulation_routes.py    # /api/simulation
│
├── frontend/
│   ├── index.html                  # Landing page & feature showcase
│   ├── dashboard.html              # Main interactive route planning command center
│   ├── login.html                  # User login page
│   ├── register.html               # User registration page
│   ├── css/
│   │   └── style.css               # Custom theme styles & animations
│   └── js/
│       ├── config.js               # Global configuration & constants
│       ├── api.js                  # Centralized HTTP request client
│       ├── map.js                  # Leaflet map manager
│       ├── router.js               # Route calculation & comparison cards
│       ├── simulation.js           # Traffic & road closure simulator
│       ├── visualizer.js           # Dijkstra vs A* benchmark visualizer
│       └── app.js                  # Dashboard controller & event binders
│
├── tests/
│   ├── test_algorithms.py          # Unit tests for Dijkstra, A*, and Optimizer
│   └── test_api.py                 # API integration tests for Flask endpoints
│
└── PROJECT_DOCUMENTATION.md        # Comprehensive College Project Documentation Report
```

---

## 💻 Installation & Setup Instructions

### Prerequisites
- Python 3.10 or higher installed ([Download Python](https://www.python.org/downloads/)).
- Git (optional).

### 1. Navigate to the Project Directory
```powershell
cd smart-route-planner
```

### 2. Install Required Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 3. Run Automated Tests
Verify that all algorithms and API routes pass:
```powershell
python -m unittest tests/test_algorithms.py
python -m unittest tests/test_api.py
```

### 4. Start the Application Server
```powershell
python backend/app.py
```

### 5. Access the Web Application
Open your web browser and navigate to:
- **Project Landing Page**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Main Command Center**: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)

---

## 🔑 Pre-Seeded Demo Account
For instant college project evaluation without manual registration, use:
- **Username**: `demo`
- **Password**: `password123`
- *(Or click the "Auto Fill" button directly on the `/login` page).*

---

## 📡 Key REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Authenticate user |
| `GET` | `/api/locations/search?q=query` | Autocomplete geocoding search |
| `POST` | `/api/routes/calculate` | Compute multi-objective route alternatives |
| `POST` | `/api/routes/benchmark` | Compare Dijkstra vs A* on road graph |
| `GET` | `/api/routes/history` | Retrieve route optimization history |
| `POST` | `/api/routes/favorite` | Bookmark route to favorites |
| `GET` | `/api/simulation/incidents` | List active closures and traffic jams |
| `POST` | `/api/simulation/incidents` | Inject road closure or traffic bottleneck |
| `POST` | `/api/simulation/clear` | Clear all active simulated hazards |

---

## 🎓 Academic Presentation Notes
- **Dijkstra vs. A\***: In the dashboard, click the **"Algorithms"** tab to demonstrate how A* with the Haversine heuristic prunes 50%+ of graph vertex expansions while arriving at identical optimal distance.
- **Dynamic Detour**: In the **"Road Hazards"** tab, click "Add Road Closure" and drop a hazard pin onto the primary route. The system immediately re-evaluates the network and computes a detour around the obstruction.
- **Pareto Trade-offs**: Switch between **Fastest** and **Economical** modes to illustrate how fuel savings alter route recommendations.

---

## 📄 License
This project is open-source and released under the **MIT License**.

