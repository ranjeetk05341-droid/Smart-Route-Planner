// Leaflet Map Controller — Google Maps Inspired Edition
// Features: OpenStreetMap 100% Free basemap, Google Blue routes,
// Clean Google teardrop pins, Overpass POIs, and responsive controls

class MapManager {
  constructor(containerId = 'map') {
    this.containerId = containerId;
    this.map = null;
    this.tileLayer = null;
    this.markers = {
      origin: null,
      destination: null,
      waypoints: []
    };
    this.routeLayers = [];     // Foreground route polylines
    this.routeCasings = [];    // White outline casing for active route
    this.incidentLayers = [];
    this.poiLayers = {};       // Category -> L.layerGroup
    this.activeCategoryFilter = 'all';
    this.activeRouteIndex = 0;
    this.clickMode = null;     // null | 'origin' | 'destination' | 'waypoint' | 'closure' | 'traffic'
  }

  init() {
    if (this.map) return;

    // Working Leaflet + OpenStreetMap configuration (Zero API Key Required)
    this.map = L.map(this.containerId, {
      zoomControl: false,
      attributionControl: true
    }).setView(CONFIG.DEFAULT_CENTER, CONFIG.DEFAULT_ZOOM);

    // Zoom controls placed at bottom-right (Google Maps style)
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // Active 100% Free OpenStreetMap Tile Layer
    this.tileLayer = L.tileLayer(CONFIG.MAP_TILES.OSM_URL, {
      attribution: CONFIG.MAP_TILES.ATTRIBUTION,
      maxZoom: CONFIG.MAP_TILES.MAX_ZOOM
    }).addTo(this.map);

    // Invalidate size on load & resize
    setTimeout(() => {
      if (this.map) this.map.invalidateSize();
    }, 250);

    window.addEventListener('resize', () => {
      if (this.map) this.map.invalidateSize();
    });

    // Initialize POI layer groups for each category
    Object.keys(CONFIG.POI_CATEGORIES).forEach(cat => {
      this.poiLayers[cat] = L.layerGroup().addTo(this.map);
    });

    // Map Click Listener
    this.map.on('click', (e) => this.handleMapClick(e));

    // Map Move Listener for "Search this area" trigger
    this.map.on('moveend', () => {
      const searchAreaBtn = document.getElementById('search-this-area-btn');
      if (searchAreaBtn && this.map.getZoom() >= 13) {
        searchAreaBtn.classList.remove('hidden');
      }
    });

    // Initial load of POIs around default center
    setTimeout(() => {
      this.fetchAndDisplayPOIsInView('all');
    }, 600);
  }

  setTheme(isDark) {
    if (!this.tileLayer) return;
  }

  setBasemap(styleName) {
    if (!this.tileLayer) return;
    this.tileLayer.setUrl(CONFIG.MAP_TILES.OSM_URL);
  }

  enableGoogleBasemap(browserKey) {
    if (!this.map || !browserKey) return;
    try {
      if (!this.googleTileLayer) {
        this.googleTileLayer = L.tileLayer(
          `https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${encodeURIComponent(browserKey)}`,
          { maxZoom: 20, attribution: '© Google Maps Platform' }
        );
      }
      if (!this.map.hasLayer(this.googleTileLayer)) {
        this.googleTileLayer.addTo(this.map);
      }
      if (this.tileLayer && this.map.hasLayer(this.tileLayer)) {
        this.map.removeLayer(this.tileLayer);
      }
      console.log("[Google Maps] Active basemap upgraded to Google Maps Roadmap tiles.");
    } catch (e) {
      console.warn("[Google Maps Tile Warning] Preserving OpenStreetMap basemap:", e);
    }
  }

  fallbackToOSM() {
    if (!this.map) return;
    if (this.googleTileLayer && this.map.hasLayer(this.googleTileLayer)) {
      this.map.removeLayer(this.googleTileLayer);
    }
    if (this.tileLayer && !this.map.hasLayer(this.tileLayer)) {
      this.tileLayer.addTo(this.map);
    }
    console.log("[OpenStreetMap] Active basemap safely restored to OpenStreetMap.");
  }

  handleMapClick(e) {
    const lat = e.latlng.lat;
    const lng = e.latlng.lng;

    if (this.clickMode === 'origin') {
      this.setOrigin([lat, lng]);
      window.dispatchEvent(new CustomEvent('map:origin-selected', { detail: { lat, lng } }));
      this.clickMode = null;
    } else if (this.clickMode === 'destination') {
      this.setDestination([lat, lng]);
      window.dispatchEvent(new CustomEvent('map:destination-selected', { detail: { lat, lng } }));
      this.clickMode = null;
    } else if (this.clickMode === 'waypoint') {
      this.addWaypoint([lat, lng]);
      window.dispatchEvent(new CustomEvent('map:waypoint-selected', { detail: { lat, lng } }));
      this.clickMode = null;
    } else if (this.clickMode === 'closure' || this.clickMode === 'traffic') {
      window.dispatchEvent(new CustomEvent('map:incident-dropped', { detail: { type: this.clickMode, lat, lng } }));
      this.clickMode = null;
    }
  }

  // Google Maps Style Markers
  createOriginIcon() {
    return L.divIcon({
      className: 'custom-pin-wrapper',
      html: `<div class="pin-gmap-origin" title="Starting Point"></div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12],
      popupAnchor: [0, -12]
    });
  }

  createDestinationIcon() {
    return L.divIcon({
      className: 'custom-pin-wrapper',
      html: `
        <div class="pin-gmap-destination" title="Destination">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9C5 14.25 12 22 12 22C12 22 19 14.25 19 9C19 5.13 15.87 2 12 2Z" fill="#EA4335" stroke="#B31412" stroke-width="1"/>
            <circle cx="12" cy="9" r="3.2" fill="#FFFFFF"/>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    });
  }

  createWaypointIcon(num) {
    return L.divIcon({
      className: 'custom-pin-wrapper',
      html: `<div class="pin-gmap-waypoint">${num}</div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11],
      popupAnchor: [0, -11]
    });
  }

  createPOIMarkerIcon(category) {
    const catConfig = CONFIG.POI_CATEGORIES[category] || {
      color: '#1a73e8',
      icon: 'map-pin',
      label: 'Place'
    };

    const iconSymbols = {
      restaurant: '🍽',
      hotel: '🏨',
      hospital: '🏥',
      pharmacy: '💊',
      school: '🏫',
      college: '🎓',
      mall: '🛍',
      petrol: '⛽',
      atm: '🏧',
      railway: '🚆',
      bus_stop: '🚌'
    };

    const symbol = iconSymbols[category] || '📍';

    return L.divIcon({
      className: 'poi-marker-wrapper',
      html: `
        <div style="background-color: ${catConfig.color}; width: 28px; height: 28px; border-radius: 50%; border: 2px solid #ffffff; box-shadow: 0 2px 6px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 13px;">
          ${symbol}
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 14],
      popupAnchor: [0, -14]
    });
  }

  setOrigin(coords, label = 'Starting Point') {
    if (this.markers.origin) {
      this.map.removeLayer(this.markers.origin);
    }
    const icon = this.createOriginIcon();
    this.markers.origin = L.marker(coords, { icon, draggable: true })
      .bindPopup(`
        <div class="gmap-popup-card">
          <div class="flex items-center gap-2 mb-1">
            <span class="w-2.5 h-2.5 rounded-full bg-[#188038]"></span>
            <span class="text-xs font-bold uppercase tracking-wider text-[#188038]">Starting Point</span>
          </div>
          <div class="font-bold text-sm text-[#202124]">${label}</div>
          <div class="text-[11px] font-mono text-[#5f6368] mt-1">${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}</div>
        </div>
      `)
      .addTo(this.map);

    this.markers.origin.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      window.dispatchEvent(new CustomEvent('map:origin-dragged', { detail: { lat: pos.lat, lng: pos.lng } }));
    });
  }

  setDestination(coords, label = 'Destination') {
    if (this.markers.destination) {
      this.map.removeLayer(this.markers.destination);
    }
    const icon = this.createDestinationIcon();
    this.markers.destination = L.marker(coords, { icon, draggable: true })
      .bindPopup(`
        <div class="gmap-popup-card">
          <div class="flex items-center gap-2 mb-1">
            <span class="w-2.5 h-2.5 rounded-full bg-[#EA4335]"></span>
            <span class="text-xs font-bold uppercase tracking-wider text-[#EA4335]">Destination</span>
          </div>
          <div class="font-bold text-sm text-[#202124]">${label}</div>
          <div class="text-[11px] font-mono text-[#5f6368] mt-1">${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}</div>
        </div>
      `)
      .addTo(this.map);

    this.markers.destination.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      window.dispatchEvent(new CustomEvent('map:destination-dragged', { detail: { lat: pos.lat, lng: pos.lng } }));
    });
  }

  addWaypoint(coords, label = 'Stop') {
    const index = this.markers.waypoints.length + 1;
    const icon = this.createWaypointIcon(index);
    const marker = L.marker(coords, { icon, draggable: true })
      .bindPopup(`
        <div class="gmap-popup-card">
          <div class="text-xs font-bold uppercase text-[#f29900] mb-1">Stop ${index}</div>
          <div class="font-bold text-sm text-[#202124]">${label}</div>
          <div class="text-[11px] font-mono text-[#5f6368] mt-1">${coords[0].toFixed(5)}, ${coords[1].toFixed(5)}</div>
        </div>
      `)
      .addTo(this.map);

    marker.on('dragend', (e) => {
      const pos = e.target.getLatLng();
      window.dispatchEvent(new CustomEvent('map:waypoint-dragged', { detail: { index: index - 1, lat: pos.lat, lng: pos.lng } }));
    });

    this.markers.waypoints.push(marker);
    return index - 1;
  }

  clearWaypoints() {
    this.markers.waypoints.forEach(m => this.map.removeLayer(m));
    this.markers.waypoints = [];
  }

  clearRoutes() {
    this.routeCasings.forEach(l => this.map.removeLayer(l));
    this.routeCasings = [];
    this.routeLayers.forEach(l => this.map.removeLayer(l));
    this.routeLayers = [];
  }

  // Google Maps Style Route Polylines
  renderRoutes(routes, activeIndex = 0) {
    this.clearRoutes();
    if (!routes || routes.length === 0) return;

    this.activeRouteIndex = activeIndex;

    routes.forEach((route, idx) => {
      const isActive = idx === activeIndex;
      const isBlocked = route.is_blocked || route.has_road_closure;
      const color = isBlocked ? CONFIG.ROUTE_COLORS.BLOCKED : (isActive ? CONFIG.ROUTE_COLORS.PRIMARY : CONFIG.ROUTE_COLORS.ALTERNATIVE);

      // White casing line for active route (gives crisp Google Maps outline)
      const casing = L.polyline(route.coordinates, {
        color: '#ffffff',
        weight: isActive ? 8 : 0,
        opacity: isActive ? 0.9 : 0,
        lineCap: 'round',
        lineJoin: 'round',
        interactive: false
      }).addTo(this.map);
      this.routeCasings.push(casing);

      // Core foreground line
      const core = L.polyline(route.coordinates, {
        color: color,
        weight: isActive ? 6 : 4.5,
        opacity: isActive ? 0.95 : 0.65,
        lineCap: 'round',
        lineJoin: 'round',
        dashArray: isBlocked ? '6, 8' : null
      }).addTo(this.map);

      core.on('click', () => {
        window.dispatchEvent(new CustomEvent('route:selected', { detail: { index: idx } }));
      });

      this.routeLayers.push(core);
    });

    // Bring active route layer to front and fit bounds
    if (this.routeLayers[activeIndex]) {
      this.routeLayers[activeIndex].bringToFront();
      this.map.fitBounds(this.routeLayers[activeIndex].getBounds(), { padding: [60, 60] });
    }
  }

  selectRoute(index) {
    this.activeRouteIndex = index;
    this.routeLayers.forEach((layer, idx) => {
      const isActive = idx === index;
      layer.setStyle({
        color: isActive ? CONFIG.ROUTE_COLORS.PRIMARY : CONFIG.ROUTE_COLORS.ALTERNATIVE,
        weight: isActive ? 6 : 4.5,
        opacity: isActive ? 0.95 : 0.6
      });
      if (isActive) layer.bringToFront();
    });

    this.routeCasings.forEach((casing, idx) => {
      const isActive = idx === index;
      casing.setStyle({
        weight: isActive ? 8 : 0,
        opacity: isActive ? 0.9 : 0
      });
      if (isActive) casing.bringToFront();
    });
  }

  // Points of Interest (POI)
  async fetchAndDisplayPOIsInView(category = 'all') {
    if (!this.map) return;
    this.activeCategoryFilter = category;

    const bounds = this.map.getBounds();
    const bboxStr = `${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()}`;

    const loadingIndicator = document.getElementById('poi-loading-indicator');
    if (loadingIndicator) loadingIndicator.classList.remove('hidden');

    try {
      const res = await api.getPOIs({
        bbox: bboxStr,
        category: category,
        limit: 50
      });

      const pois = res.pois || [];
      this.renderPOIs(pois, category);
      if (loadingIndicator) loadingIndicator.classList.add('hidden');
    } catch (err) {
      if (loadingIndicator) loadingIndicator.classList.add('hidden');
    }
  }

  renderPOIs(pois, filterCategory = 'all') {
    Object.values(this.poiLayers).forEach(layer => layer.clearLayers());
    if (!pois || pois.length === 0) return;

    pois.forEach(poi => {
      const cat = poi.category || 'restaurant';
      const catConfig = CONFIG.POI_CATEGORIES[cat] || { color: '#1a73e8', label: 'Place', bg: '#e8f0fe' };
      const markerIcon = this.createPOIMarkerIcon(cat);
      const marker = L.marker([poi.lat, poi.lon], { icon: markerIcon });

      const popupContent = `
        <div class="gmap-popup-card">
          <div class="flex items-center justify-between mb-1.5">
            <span class="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full" style="background-color: ${catConfig.bg}; color: ${catConfig.color};">
              ${catConfig.label}
            </span>
            <span class="text-[10px] text-slate-400 font-mono">OSM</span>
          </div>
          <h4 class="font-bold text-sm text-slate-900 leading-tight mb-1">${poi.name}</h4>
          <p class="text-xs text-slate-600 mb-2">📍 ${poi.address}</p>
          <div class="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-100">
            <button class="py-1.5 px-2 bg-[#1a73e8] hover:bg-[#1557b0] text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition"
                    onclick="window.setAsDestination(${poi.lat}, ${poi.lon}, '${poi.name.replace(/'/g, "\\'")}')">
              🚗 Directions
            </button>
            <button class="py-1.5 px-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center justify-center gap-1 transition"
                    onclick="window.setAsOrigin(${poi.lat}, ${poi.lon}, '${poi.name.replace(/'/g, "\\'")}')">
              🚩 From Here
            </button>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent, { maxWidth: 280 });
      if (this.poiLayers[cat]) {
        this.poiLayers[cat].addLayer(marker);
      }
    });

    this.filterCategoryLayer(filterCategory);
  }

  filterCategoryLayer(selectedCategory) {
    this.activeCategoryFilter = selectedCategory;
    Object.keys(this.poiLayers).forEach(cat => {
      const layer = this.poiLayers[cat];
      if (selectedCategory === 'all' || selectedCategory === cat) {
        if (!this.map.hasLayer(layer)) this.map.addLayer(layer);
      } else {
        if (this.map.hasLayer(layer)) this.map.removeLayer(layer);
      }
    });
  }

  renderIncidents(incidents) {
    this.incidentLayers.forEach(l => this.map.removeLayer(l));
    this.incidentLayers = [];
    if (!incidents) return;

    incidents.forEach(inc => {
      const isClosure = inc.type === 'closure';
      const marker = L.marker([inc.lat, inc.lon])
        .bindPopup(`<b>${isClosure ? 'Road Blocked' : 'Congestion'}</b><br>${inc.description}<br><button class="mt-2 text-xs text-red-600 underline" onclick="window.removeSimIncident(${inc.id})">Remove</button>`)
        .addTo(this.map);
      const circle = L.circle([inc.lat, inc.lon], {
        radius: (inc.radius_km || 0.3) * 1000,
        color: isClosure ? '#d93025' : '#f29900',
        fillColor: isClosure ? '#d93025' : '#f29900',
        fillOpacity: 0.25,
        weight: 1.5
      }).addTo(this.map);
      this.incidentLayers.push(marker, circle);
    });
  }

  toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }

  locateUser() {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const coords = [pos.coords.latitude, pos.coords.longitude];
        this.setOrigin(coords, "My Location");
        this.map.setView(coords, 15);
        window.dispatchEvent(new CustomEvent('map:origin-selected', { detail: { lat: coords[0], lng: coords[1], isCurrent: true } }));
        this.fetchAndDisplayPOIsInView(this.activeCategoryFilter);
      },
      (err) => {
        alert("Unable to retrieve location. Please check browser permissions.");
      }
    );
  }
}

const mapManager = new MapManager();
window.mapManager = mapManager;
