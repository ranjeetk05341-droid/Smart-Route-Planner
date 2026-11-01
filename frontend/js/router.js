// Router & Comparison Cards Manager — Google Maps Edition
class RouteController {
  constructor() {
    this.origin = null;        // { lat, lng, name }
    this.destination = null;   // { lat, lng, name }
    this.waypoints = [];       // [ { lat, lng, name } ]
    this.transportMode = 'car'; // 'car' | 'bicycle' | 'walking'
    this.optimizationMode = 'fastest'; // 'fastest' | 'shortest' | 'economical'
    this.vehicleType = 'petrol';
    this.fuelPrice = 1.50;
    this.fuelEfficiency = 15.0;
    this.routes = [];
    this.selectedRouteIndex = 0;
  }

  setOrigin(lat, lng, name = 'Starting Point') {
    this.origin = { lat, lng, name };
    mapManager.setOrigin([lat, lng], name);
  }

  setDestination(lat, lng, name = 'Destination') {
    this.destination = { lat, lng, name };
    mapManager.setDestination([lat, lng], name);
  }

  setTransportMode(mode) {
    this.transportMode = mode;
    if (this.origin && this.destination) {
      this.calculateAndRender();
    }
  }

  setOptimizationMode(mode) {
    this.optimizationMode = mode;
    if (this.origin && this.destination) {
      this.calculateAndRender();
    }
  }

  addWaypoint(lat, lng, name = 'Stop') {
    if (this.waypoints.length >= CONFIG.MAX_WAYPOINTS) {
      alert(`Maximum of ${CONFIG.MAX_WAYPOINTS} stops allowed.`);
      return false;
    }
    this.waypoints.push({ lat, lng, name });
    mapManager.addWaypoint([lat, lng], name);
    return true;
  }

  removeWaypoint(index) {
    this.waypoints.splice(index, 1);
    this.refreshWaypointsOnMap();
  }

  refreshWaypointsOnMap() {
    mapManager.clearWaypoints();
    this.waypoints.forEach((wp, idx) => {
      mapManager.addWaypoint([wp.lat, wp.lng], wp.name || `Stop ${idx + 1}`);
    });
  }

  getCoordinatesList() {
    if (!this.origin || !this.destination) return null;
    const list = [[this.origin.lat, this.origin.lng]];
    this.waypoints.forEach(wp => list.push([wp.lat, wp.lng]));
    list.push([this.destination.lat, this.destination.lng]);
    return list;
  }

  async calculateAndRender() {
    const coords = this.getCoordinatesList();
    if (!coords) {
      alert("Please select both a Starting Point and a Destination.");
      return;
    }

    const loader = document.getElementById('route-loading');
    const cardsContainer = document.getElementById('route-cards-container');
    if (loader) loader.classList.remove('hidden');

    try {
      const user = window.currentUser || null;
      const response = await api.calculateRoute({
        coordinates: coords,
        transport_mode: this.transportMode,
        mode: this.optimizationMode,
        vehicle_type: this.vehicleType,
        fuel_price: this.fuelPrice,
        fuel_efficiency: this.fuelEfficiency,
        source_name: this.origin.name || 'Origin',
        dest_name: this.destination.name || 'Destination',
        user_id: user ? user.id : null
      });

      this.routes = response.routes || [];
      this.selectedRouteIndex = 0;

      // Update Map Polylines (Google Blue)
      mapManager.renderRoutes(this.routes, 0);

      // Render Google Maps Comparison Cards
      this.renderRouteComparisonCards();

      // Trigger Algorithm Benchmark in benchmark tab
      if (window.visualizer) {
        window.visualizer.loadBenchmark(coords);
      }

      if (loader) loader.classList.add('hidden');
    } catch (err) {
      if (loader) loader.classList.add('hidden');
      alert(`Route Calculation Failed: ${err.message}`);
    }
  }

  renderRouteComparisonCards() {
    const container = document.getElementById('route-cards-container');
    if (!container) return;

    if (!this.routes || this.routes.length === 0) {
      container.innerHTML = `
        <div class="p-6 text-center text-slate-500 bg-white rounded-xl border border-slate-200">
          <p class="text-xs">No viable routes found for this journey.</p>
        </div>`;
      return;
    }

    let html = '';
    this.routes.forEach((route, idx) => {
      const isSelected = idx === this.selectedRouteIndex;
      const isFastest = route.is_fastest;
      const isShortest = route.is_shortest;

      let badgeHtml = '';
      if (isFastest && isShortest) {
        badgeHtml = `<span class="route-badge-pill badge-fastest">Fastest & Shortest</span>`;
      } else if (isFastest) {
        badgeHtml = `<span class="route-badge-pill badge-fastest">Fastest Route</span>`;
      } else if (isShortest) {
        badgeHtml = `<span class="route-badge-pill badge-shortest">Shortest Distance</span>`;
      } else {
        badgeHtml = `<span class="route-badge-pill badge-alt">Alternative Route</span>`;
      }

      const modeIcon = this.transportMode === 'walking' ? '🚶' : (this.transportMode === 'bicycle' ? '🚲' : '🚗');

      html += `
        <div class="route-card ${isSelected ? 'active' : ''} ${isFastest ? 'fastest' : ''}"
             onclick="window.routeController.selectRoute(${idx})">
          
          <div class="flex items-start justify-between mb-1.5">
            <div>
              <div class="flex items-center gap-2 mb-1">
                ${badgeHtml}
                <span class="text-[11px] text-slate-500">${modeIcon} ${route.transport_mode ? route.transport_mode.toUpperCase() : 'CAR'}</span>
              </div>
              <div class="font-bold text-slate-900 text-sm">
                ${route.name}
              </div>
            </div>

            <div class="text-right">
              <div class="route-duration-hero ${isFastest ? 'text-emerald-700' : 'text-slate-900'}">
                ${route.duration_text || `${Math.round(route.duration_min)} min`}
              </div>
              <div class="route-dist-hero">
                ${route.distance_km} km
              </div>
            </div>
          </div>

          <div class="text-xs text-slate-500 mb-2">
            ${route.mode_details || 'Standard traffic flow'}
          </div>

          <!-- Action bar -->
          <div class="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
            ${this.transportMode === 'car' ? `
              <span class="text-[11px] text-slate-600 font-mono">
                ⛽ $${route.fuel_cost} &bull; ${route.co2_emissions_kg || 0} kg CO2
              </span>
            ` : `
              <span class="text-[11px] text-emerald-600 font-medium">
                🌱 Eco-Friendly Travel
              </span>
            `}

            <button class="text-[#1a73e8] hover:underline font-semibold flex items-center gap-1"
                    onclick="event.stopPropagation(); window.routeController.toggleSteps(${idx})">
              Details ▼
            </button>
          </div>

          <!-- Turn-by-Turn Steps Accordion -->
          <div id="route-steps-${idx}" class="hidden mt-3 pt-3 border-t border-slate-100 max-h-48 overflow-y-auto">
            <h5 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Turn-by-Turn Navigation</h5>
            ${(route.steps && route.steps.length > 0) ? route.steps.map((st, sidx) => `
              <div class="maneuver-item text-xs">
                <span class="text-slate-400 font-mono w-4">${sidx + 1}.</span>
                <span class="flex-1 text-slate-700 font-medium">${st.instruction}</span>
                <span class="text-slate-500 font-mono text-[11px]">${st.distance_m}m</span>
              </div>
            `).join('') : '<p class="text-xs text-slate-400">Proceed along main corridor toward destination.</p>'}
            
            <button class="w-full mt-2.5 py-1.5 px-3 rounded-lg bg-[#e8f0fe] text-[#1a73e8] text-xs font-semibold hover:bg-blue-100 transition"
                    onclick="event.stopPropagation(); window.routeController.saveAsFavorite(${idx})">
              ⭐ Save Route to Favorites
            </button>
          </div>

        </div>
      `;
    });

    container.innerHTML = html;
  }

  selectRoute(index) {
    this.selectedRouteIndex = index;
    mapManager.selectRoute(index);
    this.renderRouteComparisonCards();
  }

  toggleSteps(index) {
    const el = document.getElementById(`route-steps-${index}`);
    if (el) {
      el.classList.toggle('hidden');
    }
  }

  async saveAsFavorite(index) {
    const route = this.routes[index];
    if (!route) return;

    const user = window.currentUser;
    if (!user) {
      alert("Please login or create an account to save favorite routes!");
      return;
    }

    try {
      await api.saveFavoriteRoute({
        user_id: user.id,
        route_name: `${this.origin.name} to ${this.destination.name}`,
        source_name: this.origin.name,
        source_lat: this.origin.lat,
        source_lng: this.origin.lng,
        dest_name: this.destination.name,
        dest_lat: this.destination.lat,
        dest_lng: this.destination.lng,
        waypoints: this.waypoints,
        distance_km: route.distance_km,
        duration_min: route.duration_min,
        route_mode: `${this.transportMode}_${this.optimizationMode}`
      });
      alert("Route added to your Favorites!");
    } catch (err) {
      alert(`Could not save favorite: ${err.message}`);
    }
  }
}

const routeController = new RouteController();
window.routeController = routeController;
