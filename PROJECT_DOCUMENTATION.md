# SMART ROUTE PLANNER
## An Intelligent Route Optimization System for Real-World Transportation Problems
### Final Year Capstone Project Report & Technical Specification

---

## 1. Project Abstract
Rapid urbanization, exponential growth in vehicle density, and fluctuating energy costs present severe logistical and environmental challenges to modern cities. Existing consumer navigation platforms predominantly compute routes optimized solely for travel duration, often directing vehicles onto congested corridors while failing to account for physical distance minimization, fuel economics, customizable multi-stop sequencing, and real-time roadblock avoidance.

**Smart Route Planner** is an intelligent, multi-criteria route optimization and transportation planning platform. It leverages OpenStreetMap GIS data, OSRM road geometries, and classical graph theory algorithms (**Dijkstra's Algorithm** and **A\* Search with Haversine Heuristic**), coupled with a **Multi-Objective Weighted Cost Engine**. The system evaluates distance, duration, fuel/energy expenditure, carbon footprint, and dynamic roadblock hazards (flooding, construction, accidents). The platform features an interactive Leaflet.js dashboard with dark/light themes, multi-stop planning, real-world incident simulations, and an academic algorithm benchmarking visualizer.

---

## 2. Introduction
Navigation and route planning systems are critical components of contemporary intelligent transportation systems (ITS). Whether for daily personal commuting, commercial parcel logistics, or emergency medical services, selecting an optimal path between geographic coordinates requires evaluating competing constraints. 

While classical shortest path algorithms calculate the minimum edge sum across a graph, real-world transit involves trade-offs: the shortest physical route might traverse congested inner-city arterials, while the fastest route may require substantial detours along toll expressways resulting in heightened fuel consumption and emissions.

This project bridges theoretical computer science algorithms with practical full-stack web engineering, creating an open-source, reproducible, and robust decision-support platform for urban transit.

---

## 3. Problem Statement
Commercial navigation tools suffer from three fundamental limitations:
1. **Single-Metric Bias**: Routes are optimized strictly for travel time, neglecting total fuel/energy expenditure and vehicle wear-and-tear.
2. **Opaque Black-Box Heuristics**: Users cannot inspect or customize algorithmic weights (e.g., specifying a preference for distance vs. fuel cost).
3. **Inflexible Dynamic Obstacle Simulation**: Fleet managers and students cannot easily inject simulated localized road hazards (such as bridge closures or flash floods) to test real-time detour resilience.

---

## 4. Project Objectives
1. Implement **Dijkstra's Shortest Path Algorithm** using a priority queue (min-heap) to establish the shortest distance baseline.
2. Implement the **A\* Search Algorithm** utilizing an admissible Haversine great-circle distance heuristic to demonstrate goal-directed search pruning.
3. Formulate a **Multi-Objective Weighted Cost Function** evaluating:
   - Fastest Route (minimizing travel time)
   - Shortest Route (minimizing physical kilometers)
   - Economical Route (minimizing fuel consumption and operational costs)
   - Balanced Route (Pareto compromise between time, distance, and fuel)
4. Integrate real-world **OpenStreetMap** geographic road networks and turn-by-turn routing via the Open Source Routing Machine (OSRM).
5. Build a dynamic **Incident & Road Closure Simulator** capable of invalidating graph edges and recalculating viable detours.
6. Provide an **Algorithm Benchmarking Visualizer** comparing node expansions, execution latency (ms), and search space reduction for academic evaluation.
7. Deliver a responsive, modern UI/UX with dark/light themes, user authentication, saved places, and route history logging.

---

## 5. Existing System vs. Proposed System

| Feature / Dimension | Existing Navigation Systems | Proposed Smart Route Planner |
| :--- | :--- | :--- |
| **Optimization Focus** | Almost exclusively travel time. | Multi-criteria: Time, Distance, Fuel Cost, and Carbon Footprint. |
| **User Transparency** | Proprietary black-box algorithms. | Transparent, customizable weights and mode selections. |
| **Map & Cartography** | Proprietary styled tiles with billing caps. | **Leaflet + OpenStreetMap** (`tile.openstreetmap.org`) pure open-source tiles with zero API keys required. |
| **Points of Interest (POIs)** | Paid proprietary API queries. | **Overpass API** querying real OpenStreetMap features (restaurants, hotels, hospitals, pharmacies, petrol, ATMs, malls, transit). |
| **Search & Autocomplete** | High-cost Google Places API. | **Photon (OSM-based Elasticsearch geocoder)** compliant with third-party usage policies. |
| **Algorithmic Benchmarking** | Unavailable. | Side-by-side Dijkstra vs. A* node visits and execution timing visualizer. |
| **Hazard Simulation** | Read-only; cannot inject hypothetical closures. | Interactive closure & traffic bottleneck injector with instant rerouting. |
| **Vehicle Tailoring** | Generic passenger car assumptions. | Profiles for Petrol, Diesel, EV, Hybrid, Bike, and Commercial Trucks. |
| **Data Privacy & Cost** | Requires proprietary API keys (e.g., Google Maps Billing). | 100% Free & Open-Source: Leaflet, OpenStreetMap, OSRM, Overpass, SQLite (Zero API key required). |

---

## 6. System Requirements

### 6.1 Hardware Requirements
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher (Dual-Core 2.0 GHz+).
- **RAM**: Minimum 4 GB (8 GB recommended).
- **Disk Storage**: 500 MB free hard drive space.
- **Display**: Minimum $1280 \times 720$ resolution (optimized for desktop and mobile viewports).

### 6.2 Software Requirements
- **Operating System**: Windows 10/11, macOS Monterey+, or Linux (Ubuntu 20.04+).
- **Runtime Environment**: Python 3.10+ (tested on Python 3.14).
- **Web Browser**: Modern ECMAScript 6+ browser (Google Chrome, Mozilla Firefox, Microsoft Edge, Safari).
- **Key Python Libraries**: Flask, Flask-CORS, Flask-SQLAlchemy, Requests, Werkzeug.
- **Frontend Libraries**: Leaflet.js 1.9+, Tailwind CSS (CDN), Lucide Icons.

---

## 7. Functional & Non-Functional Requirements

### 7.1 Functional Requirements
1. **User Authentication & Profiles**: Secure registration, login with hashed passwords, and customizable vehicle preferences.
2. **Geocoding & Location Search**: Autocomplete search for starting points, destinations, and intermediate delivery stops.
3. **Interactive Map Operations**: Draggable markers for origin, destination, and waypoints; click-to-pin navigation.
4. **Multi-Criteria Optimization**: Route computation across 4 optimization modes with alternative route evaluation.
5. **Fuel & Carbon Emission Calculator**: Accurate distance-based fuel consumption factoring in traffic idling penalties.
6. **Dynamic Hazard Injection**: Interactive addition/deletion of road closures and traffic jams with instant detour triggering.
7. **Algorithm Benchmark**: Side-by-side performance profiling of Dijkstra vs. A*.
8. **Persistence**: Route history logging and bookmarking of favorite routes.

### 7.2 Non-Functional Requirements
1. **Performance**: Algorithmic route scoring completes in under 250 milliseconds.
2. **Fault Tolerance & Resilience**: If OSRM or Nominatim is unreachable, the system activates internal fallback graph generators without raising unhandled exceptions.
3. **Security**: Passwords hashed using PBKDF2/SHA256 via Werkzeug.
4. **Usability**: Responsive, intuitive UI with feedback indicators, badges, and tooltips.

---

## 8. System Architecture Diagram

```
+---------------------------------------------------------------------------------+
|                                 USER BROWSER                                    |
|   +-------------------------------------------------------------------------+   |
|   |         Presentation Layer (HTML5, Tailwind CSS, Leaflet.js)            |   |
|   |  - Dashboard Control Center       - Search Autocomplete Dropdowns       |   |
|   |  - Route Comparison Cards         - Incident Simulator & Overlay        |   |
|   |  - Algorithm Benchmark Charts     - Saved Places & History Panel        |   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------|-----------------------------------------+
                                        | HTTP / JSON REST APIs
+---------------------------------------v-----------------------------------------+
|                         PYTHON FLASK BACKEND GATEWAY                            |
|   +-------------------+  +-------------------+  +----------------------------+  |
|   |  /api/auth        |  |  /api/routes      |  |  /api/locations            |  |
|   |  - Register/Login |  |  - Calculate Route|  |  - Nominatim Search Proxy  |  |
|   |  - User Profiles  |  |  - Benchmark Algo |  |  - Reverse Geocode         |  |
|   |  - Preferences    |  |  - History/Favs   |  |  - Saved Locations         |  |
|   +-------------------+  +-------------------+  +----------------------------+  |
|   +--------------------------------------------------------------------------+  |
|   |  /api/simulation: Incident Manager (Road Closures & Congestion Zones)    |  |
|   +--------------------------------------------------------------------------+  |
+---------------------------------------|-----------------------------------------+
                                        |
+---------------------------------------v-----------------------------------------+
|                         SERVICES & ALGORITHM ENGINE                             |
|  +-------------------+  +-------------------+  +-----------------------------+  |
|  | Dijkstra Engine   |  | A* Search Engine  |  | Multi-Objective Optimizer   |  |
|  | - Priority Queue  |  | - Haversine $h(n)$|  | - Normalized Weighted Score |  |
|  | - Shortest Dist   |  | - Admissible Prune|  | - Pareto Alternative Rank   |  |
|  +-------------------+  +-------------------+  +-----------------------------+  |
|  +-------------------+  +-------------------+  +-----------------------------+  |
|  | OSRM Gateway      |  | Fuel Calculator   |  | Incident Evaluator          |  |
|  | - Road Geometries |  | - Fuel/kWh Cost   |  | - Polyline Collision Check  |  |
|  | - Turn Steps      |  | - CO2 Emissions   |  | - Detour Re-triggering       |  |
|  +-------------------+  +-------------------+  +-----------------------------+  |
+---------------------------------------|-----------------------------------------+
                                        |
+---------------------------------------v-----------------------------------------+
|                               DATABASE LAYER                                    |
|   SQLite Relational Storage (Users, Preferences, Locations, History, Favorites)  |
+---------------------------------------------------------------------------------+
```

---

## 9. Use Case Diagram

```
                 +---------------------------------------------+
                 |            Smart Route Planner              |
                 +---------------------------------------------+
                 |                                             |
                 |   (1) Search Locations & Autocomplete       |
                 |                     ^                       |
                 |                     |                       |
   [ User /      |   (2) Calculate Multi-Stop Optimal Route    |
    Commuter ] --+                     |                       |
                 |   (3) Select Optimization Mode              |
                 |       (Fastest / Shortest / Economical)     |
                 |                     |                       |
                 |   (4) Compare Alternative Route Cards       |
                 |                     |                       |
                 |   (5) Save Route to Favorites / History     |
                 |                                             |
+----------------+---------------------------------------------+
|                |                                             |
|  [ Evaluator / |   (6) Simulate Road Closure / Traffic Jam   |
|    Student ] --+                     |                       |
|                |   (7) Run Dijkstra vs. A* Benchmark Test    |
|                |                                             |
+----------------+---------------------------------------------+
```

---

## 10. Data Flow Diagram (DFD Level 1)

```
[ User Input: Start, End, Mode ]
              |
              v
     ( Process 1.0: Geocoding & Validation )
              |
              v ( Coordinates: [lat, lon] list )
     ( Process 2.0: Route Retrieval & Incident Check ) <---> [ Incident Manager ]
              |                                                   (Active Hazards)
              v ( Candidate Routes GeoJSON )
     ( Process 3.0: Multi-Objective Cost Engine )
              |
              +---> Calls Dijkstra ($w_d$)
              +---> Calls A* Search ($w_t$ with Haversine)
              +---> Calls Fuel & Emission Calculator ($w_c$)
              |
              v ( Normalized Pareto Scores & Ranks )
     ( Process 4.0: Presentation & Map Rendering )
              |
              +---> Draws Recommended & Alternative Polylines on Leaflet
              +---> Populates Interactive Comparison Cards
              +---> Updates Benchmark Visualizer
              |
              v
[ Persistence: SQLite DB (Route History & Saved Places) ]
```

---

## 11. Entity-Relationship (ER) Diagram & Database Schema

### 11.1 Users Table (`users`)
- `id` (INTEGER, PK, Autoincrement)
- `username` (VARCHAR(80), Unique, Not Null)
- `email` (VARCHAR(120), Unique, Not Null)
- `password_hash` (VARCHAR(256), Not Null)
- `created_at` (DATETIME)

### 11.2 User Preferences Table (`user_preferences`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`, Unique)
- `vehicle_type` (VARCHAR(50), Default 'petrol')
- `fuel_price` (FLOAT, Default 1.50)
- `fuel_efficiency` (FLOAT, Default 15.0)
- `default_mode` (VARCHAR(50), Default 'balanced')
- `dark_mode` (BOOLEAN, Default False)

### 11.3 Saved Locations Table (`saved_locations`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`)
- `label` (VARCHAR(100), Not Null)
- `address` (VARCHAR(255), Not Null)
- `latitude` (FLOAT, Not Null)
- `longitude` (FLOAT, Not Null)
- `category` (VARCHAR(50), Default 'custom')
- `created_at` (DATETIME)

### 11.4 Route History Table (`route_history`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`, Nullable)
- `source_name` (VARCHAR(255))
- `source_lat` (FLOAT)
- `source_lng` (FLOAT)
- `dest_name` (VARCHAR(255))
- `dest_lat` (FLOAT)
- `dest_lng` (FLOAT)
- `waypoints_json` (TEXT)
- `distance_km` (FLOAT)
- `duration_min` (FLOAT)
- `fuel_cost` (FLOAT)
- `route_mode` (VARCHAR(50))
- `efficiency_score` (FLOAT)
- `route_summary` (VARCHAR(255))
- `created_at` (DATETIME)

### 11.5 Favorite Routes Table (`favorite_routes`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`)
- `route_name` (VARCHAR(100))
- `source_name` (VARCHAR(255))
- `dest_name` (VARCHAR(255))
- `waypoints_json` (TEXT)
- `distance_km` (FLOAT)
- `duration_min` (FLOAT)
- `route_mode` (VARCHAR(50))
- `created_at` (DATETIME)

---

## 12. Algorithmic Formulation & Mathematical Models

### 12.1 Dijkstra's Shortest Path Algorithm
Dijkstra's algorithm is a greedy search algorithm that guarantees the optimal shortest path in graphs with non-negative edge weights $w(u, v) \ge 0$.

```python
# Priority Queue Implementation
dist[start] = 0
heapq.heappush(pq, (0, start))
while pq:
    current_cost, u = heapq.heappop(pq)
    if u == goal: break
    for edge in graph.neighbors(u):
        v = edge.v
        new_cost = current_cost + edge.weight
        if new_cost < dist[v]:
            dist[v] = new_cost
            came_from[v] = u
            heapq.heappush(pq, (new_cost, v))
```

- **Time Complexity**: $O((|V| + |E|) \log |V|)$ using binary heap.
- **Space Complexity**: $O(|V|)$ for distance and predecessor tables.

### 12.2 A\* Search Algorithm with Haversine Heuristic
A\* enhances Dijkstra by introducing an evaluation function $f(n) = g(n) + h(n)$:
- $g(n)$: Actual cost incurred from origin to node $n$.
- $h(n)$: Estimated cost from node $n$ to goal $t$.

To guarantee optimality, $h(n)$ must be **admissible** ($h(n) \le h^*(n)$) and **consistent** ($h(u) \le w(u, v) + h(v)$). We employ the **Haversine Great-Circle Distance**:

$$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$

Where $R = 6371.0\text{ km}$. For travel duration heuristics:
$$h_{\text{time}}(n) = \frac{d_{\text{haversine}}(n, t)}{v_{\max}} \times 60$$
where $v_{\max} = 120\text{ km/h}$, ensuring search admissibility.

### 12.3 Multi-Objective Weighted Cost Function
Given a candidate set of routes $\{R_1, R_2, \dots, R_k\}$, each route is evaluated across four normalized dimensions:

$$\text{Score}(R_i) = w_d \cdot \left(\frac{D_i}{D_{\max}}\right) + w_t \cdot \left(\frac{T_i}{T_{\max}}\right) + w_c \cdot \left(\frac{C_i}{C_{\max}}\right) + w_{\text{trf}} \cdot \tau_i + P_{\text{closure}}$$

Where:
- $D_i$: Distance in kilometers.
- $T_i$: Effective travel duration (including congestion factor).
- $C_i$: Fuel or electric charging cost.
- $\tau_i$: Congestion density index ($1.0$ = normal, $2.5$ = severe delay).
- $P_{\text{closure}}$: Road closure penalty ($\infty$ if route intersects a closure zone).
- Normalized Weights: $w_d + w_t + w_c + w_{\text{trf}} = 1.0$.

---

## 13. Testing Documentation & Verification Results

### 13.1 Unit Testing (`tests/test_algorithms.py`)
- `test_haversine_distance`: Validated against known geodetic benchmarks (NYC to London ~5570 km). **Result: PASSED (0.001s)**.
- `test_dijkstra_shortest_distance`: Verified that Dijkstra discovers the shortest distance corridor. **Result: PASSED**.
- `test_dijkstra_shortest_time`: Verified that higher-speed highway corridors win over slower direct roads in travel time mode. **Result: PASSED**.
- `test_a_star_optimality`: Verified A* produces the identical shortest path as Dijkstra with reduced node visits. **Result: PASSED**.
- `test_road_closure_rerouting`: Simulated edge failure; verified algorithm successfully detoured around blocked segment. **Result: PASSED**.
- `test_multi_objective_optimizer`: Tested fastest vs. shortest mode ranking. **Result: PASSED**.
- `test_fuel_calculator`: Verified consumption and emissions calculation across vehicle types. **Result: PASSED**.

### 13.2 Integration Testing (`tests/test_api.py`)
- `test_health_endpoint`: API health status responds with 200 OK. **Result: PASSED**.
- `test_location_search`: Geocoding proxy returns valid structured results. **Result: PASSED**.
- `test_route_calculation`: Multi-objective route calculation returns ranked alternatives with recommendation flags and transparent traffic availability labeling. **Result: PASSED**.
- `test_pois_endpoint`: Overpass POI service returns real mapped OSM features with categories, names, and addresses. **Result: PASSED**.
- `test_pois_all_categories`: Querying all categories returns diverse real mapped places across food, health, transit, and amenities. **Result: PASSED**.
- `test_simulation_incident_lifecycle`: Dynamic creation, listing, and removal of road hazard incidents. **Result: PASSED**.
- `test_algorithm_benchmark`: Live generation of topological road network graph and benchmarking of Dijkstra vs. A*. **Result: PASSED**.

**Total Test Suite: 14/14 automated tests PASSED.**

---

## 14. Future Scope
1. **IoT Edge Sensors**: Direct ingestion of traffic sensor data via MQTT.
2. **Machine Learning Speed Prediction**: Long Short-Term Memory (LSTM) recurrent networks to forecast congestion patterns based on historical traffic cycles.
3. **Multi-Modal Transit Integration**: Incorporating metro rail, bus transit, and pedestrian walking corridors into a unified intermodal graph.
4. **Offline Mobile Application**: Packaging with Progressive Web App (PWA) offline vector tile caching.

---

## 15. Conclusion
The **Smart Route Planner** successfully meets all capstone requirements for an intelligent transportation optimization platform. By synthesizing classical graph theory (Dijkstra and A*), multi-criteria decision making, modern web mapping (Leaflet and OpenStreetMap), and real-time hazard simulation, the system demonstrates how algorithmic engineering can directly mitigate urban traffic congestion, unnecessary fuel expenditure, and transit inefficiencies.

