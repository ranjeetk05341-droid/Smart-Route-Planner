// Application Main Controller & UI Event Orchestrator — Google Maps Navigation Edition
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Initialize Map
  mapManager.init();

  // 2. Initialize Maps Platform Config (Google Maps vs. OpenStreetMap)
  initMapsPlatformConfig();

  // 3. Check Session / User
  initUserSession();

  // 4. Load Active Incidents
  simulationManager.loadIncidents();

  // 5. Setup Dynamic Location Search Autocomplete (Zero Hardcoded Locations)
  setupAutocomplete('origin-input', 'origin-dropdown', (item) => {
    routeController.setOrigin(item.lat, item.lon, item.display_name.split(',')[0]);
    document.getElementById('origin-input').value = item.display_name.split(',')[0];
  });

  setupAutocomplete('dest-input', 'dest-dropdown', (item) => {
    routeController.setDestination(item.lat, item.lon, item.display_name.split(',')[0]);
    document.getElementById('dest-input').value = item.display_name.split(',')[0];
  });

  // 6. Bind UI Controls
  setupUIEventListeners();

  // 7. Load default starter route for instant verification
  initDemoRoute();
});

async function initMapsPlatformConfig() {
  try {
    const config = await api.getMapsConfig();
    const statusBadge = document.getElementById('map-engine-status-badge');
    const statusText = document.getElementById('map-engine-status-text');
    const pulseDot = document.getElementById('map-engine-pulse-dot');

    if (config.google_maps_browser_key) {
      CONFIG.GOOGLE_MAPS.BROWSER_KEY = config.google_maps_browser_key;

      // Handle Google Maps Authentication Failures (Billing, Referrers, Invalid Key)
      window.gm_authFailure = function() {
        console.warn("[Google Cloud API Alert] Google Maps JavaScript API authentication failed. Verify API key restrictions, activation, or project billing in Google Cloud Console.");
        mapManager.fallbackToOSM();
        if (statusBadge && statusText) {
          statusBadge.classList.remove('hidden');
          if (pulseDot) pulseDot.className = "w-2 h-2 rounded-full bg-amber-500";
          statusText.textContent = "OSM Active (Google Cloud Auth Check)";
          statusBadge.title = "Google Maps JS API key rejected. Falling back seamlessly to OpenStreetMap.";
        }
      };

      // Dynamically load Google Maps JavaScript API with the BROWSER key
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(config.google_maps_browser_key)}&libraries=places,geometry`;
      script.async = true;
      script.defer = true;
      script.onload = () => {
        CONFIG.GOOGLE_MAPS.IS_ENABLED = true;
        mapManager.enableGoogleBasemap(config.google_maps_browser_key);
        initGooglePlacesAutocomplete();
        if (statusBadge && statusText) {
          statusBadge.classList.remove('hidden');
          if (pulseDot) pulseDot.className = "w-2 h-2 rounded-full bg-[#1a73e8] animate-pulse";
          statusText.textContent = "Google Maps & Routes Live";
        }
      };
      script.onerror = () => {
        console.warn("[Google Cloud Network] Could not load Google Maps JavaScript API. Using OpenStreetMap.");
        mapManager.fallbackToOSM();
      };
      document.head.appendChild(script);

    } else {
      if (statusBadge && statusText) {
        statusBadge.classList.remove('hidden');
        if (pulseDot) pulseDot.className = "w-2 h-2 rounded-full bg-[#188038] animate-pulse";
        statusText.textContent = config.has_server_key ? "Google Routes + OSM Live" : "OSRM & OSM Live";
      }
    }
  } catch (e) {
    console.warn("Could not retrieve maps config, using OSM default:", e);
  }
}

function initGooglePlacesAutocomplete() {
  if (!window.google || !window.google.maps || !window.google.maps.places) return;

  const originInput = document.getElementById('origin-input');
  const destInput = document.getElementById('dest-input');
  if (!originInput || !destInput) return;

  try {
    const originAuto = new google.maps.places.Autocomplete(originInput, {
      fields: ['geometry', 'name', 'formatted_address']
    });
    originAuto.addListener('place_changed', () => {
      const place = originAuto.getPlace();
      if (place && place.geometry && place.geometry.location) {
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();
        const name = place.name || place.formatted_address || originInput.value;
        routeController.setOrigin(lat, lng, name);
        originInput.value = name;
        const dropdown = document.getElementById('origin-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
      }
    });

    const destAuto = new google.maps.places.Autocomplete(destInput, {
      fields: ['geometry', 'name', 'formatted_address']
    });
    destAuto.addListener('place_changed', () => {
      const place = destAuto.getPlace();
      if (place && place.geometry && place.geometry.location) {
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();
        const name = place.name || place.formatted_address || destInput.value;
        routeController.setDestination(lat, lng, name);
        destInput.value = name;
        const dropdown = document.getElementById('dest-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
        if (routeController.origin) {
          routeController.calculateAndRender();
        }
      }
    });

    console.log("[Google Places] Real Google Places Autocomplete successfully connected to search fields.");
  } catch (err) {
    console.warn("[Google Places Note]", err);
  }
}

async function initUserSession() {
  const storedUser = localStorage.getItem('srp_user');
  if (storedUser) {
    try {
      window.currentUser = JSON.parse(storedUser);
      updateUserUI();
    } catch (e) {}
  }
}

function updateUserUI() {
  const user = window.currentUser;
  const authNav = document.getElementById('auth-nav-container');
  if (!authNav) return;

  if (user) {
    authNav.innerHTML = `
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 rounded-full bg-[#1a73e8] text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
          ${user.username.charAt(0)}
        </div>
        <div class="hidden sm:block text-left text-xs">
          <div class="font-bold text-slate-800">${user.username}</div>
        </div>
        <button onclick="window.logoutUser()" class="ml-2 text-xs text-slate-500 hover:text-red-600 font-medium transition">
          Logout
        </button>
      </div>
    `;
  } else {
    authNav.innerHTML = `
      <div class="flex items-center gap-2">
        <a href="/login" class="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-100 transition">
          Sign In
        </a>
        <a href="/register" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#1a73e8] hover:bg-[#1557b0] text-white transition shadow-sm">
          Register
        </a>
      </div>
    `;
  }
}

window.logoutUser = () => {
  localStorage.removeItem('srp_user');
  window.currentUser = null;
  updateUserUI();
};

function setupUIEventListeners() {
  // Transport Mode Selector (Driving 🚗, Cycling 🚲, Walking 🚶)
  const modeButtons = document.querySelectorAll('.travel-mode-btn');
  modeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      modeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const transport = btn.dataset.transport;
      const vehicleWrapper = document.getElementById('car-vehicle-wrapper');
      if (vehicleWrapper) {
        vehicleWrapper.style.display = transport === 'car' ? 'flex' : 'none';
      }

      routeController.setTransportMode(transport);
    });
  });

  // Optimization Mode Pills (Fastest, Shortest, Economical)
  const optPills = document.querySelectorAll('.opt-mode-pill');
  optPills.forEach(pill => {
    pill.addEventListener('click', () => {
      optPills.forEach(p => {
        p.classList.remove('active', 'bg-[#e8f0fe]', 'text-[#1a73e8]', 'border-blue-200');
        p.classList.add('bg-slate-100', 'text-slate-600', 'border-transparent');
      });

      pill.classList.add('active', 'bg-[#e8f0fe]', 'text-[#1a73e8]', 'border-blue-200');
      pill.classList.remove('bg-slate-100', 'text-slate-600', 'border-transparent');

      routeController.setOptimizationMode(pill.dataset.opt);
    });
  });

  // Vehicle selection selector
  const vehicleSelect = document.getElementById('vehicle-select');
  if (vehicleSelect) {
    vehicleSelect.addEventListener('change', (e) => {
      routeController.vehicleType = e.target.value;
      if (routeController.origin && routeController.destination) {
        routeController.calculateAndRender();
      }
    });
  }

  // Find Route button
  const calcBtn = document.getElementById('calculate-route-btn');
  if (calcBtn) {
    calcBtn.addEventListener('click', () => {
      routeController.calculateAndRender();
    });
  }

  // Swap Locations button
  const swapBtn = document.getElementById('swap-locations-btn');
  if (swapBtn) {
    swapBtn.addEventListener('click', () => {
      const origInput = document.getElementById('origin-input');
      const destInput = document.getElementById('dest-input');
      const tempVal = origInput.value;
      origInput.value = destInput.value;
      destInput.value = tempVal;

      const tempCoord = routeController.origin;
      routeController.origin = routeController.destination;
      routeController.destination = tempCoord;

      if (routeController.origin) mapManager.setOrigin([routeController.origin.lat, routeController.origin.lng], routeController.origin.name);
      if (routeController.destination) mapManager.setDestination([routeController.destination.lat, routeController.destination.lng], routeController.destination.name);

      if (routeController.origin && routeController.destination) {
        routeController.calculateAndRender();
      }
    });
  }

  // Add Waypoint button
  const addStopBtn = document.getElementById('add-stop-btn');
  if (addStopBtn) {
    addStopBtn.addEventListener('click', () => {
      mapManager.clickMode = 'waypoint';
      alert("Click on the map where you want to add an intermediate delivery stop.");
    });
  }

  // Geolocation button
  const locateBtn = document.getElementById('locate-user-btn');
  if (locateBtn) {
    locateBtn.addEventListener('click', () => {
      mapManager.locateUser();
    });
  }

  // Floating Fullscreen button
  const fsBtn = document.getElementById('fullscreen-toggle-btn');
  if (fsBtn) {
    fsBtn.addEventListener('click', () => mapManager.toggleFullscreen());
  }

  // Floating Locate button on map
  const floatLocBtn = document.getElementById('floating-locate-btn');
  if (floatLocBtn) {
    floatLocBtn.addEventListener('click', () => mapManager.locateUser());
  }

  // "Search this area" Button
  const searchAreaBtn = document.getElementById('search-this-area-btn');
  if (searchAreaBtn) {
    searchAreaBtn.addEventListener('click', () => {
      searchAreaBtn.classList.add('hidden');
      mapManager.fetchAndDisplayPOIsInView(mapManager.activeCategoryFilter);
    });
  }

  // Recenter to default center coordinates button
  const recenterBtn = document.getElementById('recenter-map-btn');
  if (recenterBtn) {
    recenterBtn.addEventListener('click', () => {
      mapManager.map.setView(CONFIG.DEFAULT_CENTER, CONFIG.DEFAULT_ZOOM);
    });
  }

  // POI Category Filter chips
  const categoryChips = document.querySelectorAll('.poi-filter-chip');
  categoryChips.forEach(chip => {
    chip.addEventListener('click', () => {
      categoryChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const category = chip.dataset.category;
      mapManager.fetchAndDisplayPOIsInView(category);
    });
  });

  // Map Listeners
  window.addEventListener('map:origin-selected', (e) => {
    document.getElementById('origin-input').value = e.detail.isCurrent ? "My Current Location" : `Pinned (${e.detail.lat.toFixed(4)}, ${e.detail.lng.toFixed(4)})`;
    routeController.setOrigin(e.detail.lat, e.detail.lng, document.getElementById('origin-input').value);
  });

  window.addEventListener('map:destination-selected', (e) => {
    document.getElementById('dest-input').value = `Pinned (${e.detail.lat.toFixed(4)}, ${e.detail.lng.toFixed(4)})`;
    routeController.setDestination(e.detail.lat, e.detail.lng, document.getElementById('dest-input').value);
  });

  window.addEventListener('map:waypoint-selected', (e) => {
    routeController.addWaypoint(e.detail.lat, e.detail.lng, `Stop ${routeController.waypoints.length + 1}`);
    renderWaypointsList();
  });

  window.addEventListener('map:incident-dropped', (e) => {
    simulationManager.addIncident(e.detail.type, e.detail.lat, e.detail.lng);
  });

  window.addEventListener('route:selected', (e) => {
    routeController.selectRoute(e.detail.index);
  });

  // Tab Switching
  setupTabSwitching();
}

function setupTabSwitching() {
  const tabs = document.querySelectorAll('.nav-tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active', 'text-[#1a73e8]', 'border-[#1a73e8]');
        t.classList.add('text-slate-500', 'border-transparent');
      });
      tab.classList.add('active', 'text-[#1a73e8]', 'border-[#1a73e8]');
      tab.classList.remove('text-slate-500', 'border-transparent');

      const target = tab.dataset.target;
      document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.add('hidden');
      });
      const activePanel = document.getElementById(`panel-${target}`);
      if (activePanel) activePanel.classList.remove('hidden');

      if (target === 'history') loadHistoryTab();
      if (target === 'saved') loadSavedPlacesTab();
      if (target === 'simulation') simulationManager.loadIncidents();
    });
  });
}

function setupAutocomplete(inputId, dropdownId, onSelect) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  if (!input || !dropdown) return;

  let debounceTimer = null;

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = input.value.trim();
    if (query.length < 2) {
      dropdown.classList.add('hidden');
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await api.searchLocations(query);
        const results = res.results || [];
        if (results.length === 0) {
          dropdown.classList.add('hidden');
          return;
        }

        dropdown.innerHTML = results.map(item => `
          <div class="autocomplete-item" data-lat="${item.lat}" data-lon="${item.lon}">
            <span class="text-[#1a73e8] font-bold mt-0.5">📍</span>
            <div class="flex-1 truncate">
              <div class="font-semibold text-slate-800 text-xs truncate">${item.display_name.split(',')[0]}</div>
              <div class="text-[11px] text-slate-500 truncate">${item.display_name}</div>
            </div>
          </div>
        `).join('');
        dropdown.classList.remove('hidden');

        // Bind clicks
        dropdown.querySelectorAll('.autocomplete-item').forEach((div, idx) => {
          div.addEventListener('click', () => {
            onSelect(results[idx]);
            dropdown.classList.add('hidden');
          });
        });
      } catch (e) {
        dropdown.classList.add('hidden');
      }
    }, 280);
  });

  // Enter key press triggers instant geocoding on top result
  input.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      clearTimeout(debounceTimer);
      const firstItem = dropdown.querySelector('.autocomplete-item');
      if (firstItem) {
        firstItem.click();
      } else {
        const query = input.value.trim();
        if (query.length >= 2) {
          try {
            const res = await api.searchLocations(query);
            if (res.results && res.results.length > 0) {
              onSelect(res.results[0]);
              dropdown.classList.add('hidden');
            }
          } catch (err) {}
        }
      }
    }
  });

  // Close dropdown on outside click
  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  });
}

function renderWaypointsList() {
  const container = document.getElementById('waypoints-list-container');
  if (!container) return;

  if (routeController.waypoints.length === 0) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = routeController.waypoints.map((wp, idx) => `
    <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200 text-xs mb-1">
      <div class="flex items-center gap-2">
        <span class="w-4 h-4 rounded-full bg-amber-500 text-white font-bold flex items-center justify-center text-[10px]">
          ${idx + 1}
        </span>
        <span class="text-slate-700 font-medium truncate">${wp.name || `Stop ${idx + 1}`}</span>
      </div>
      <button onclick="window.routeController.removeWaypoint(${idx}); renderWaypointsList();" class="text-slate-400 hover:text-red-600 font-bold px-1">
        ✕
      </button>
    </div>
  `).join('');
}

async function loadHistoryTab() {
  const container = document.getElementById('history-list-container');
  if (!container) return;

  container.innerHTML = `<div class="p-4 text-center text-xs text-slate-500">Loading history...</div>`;
  try {
    const user = window.currentUser;
    const res = await api.getRouteHistory(user ? user.id : null);
    const history = res.history || [];

    if (history.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-xs text-slate-400">No route searches recorded yet. Calculate a route to view history.</div>`;
      return;
    }

    container.innerHTML = history.map(item => `
      <div class="p-3 rounded-xl border border-slate-200 bg-white mb-2 text-xs shadow-sm">
        <div class="flex items-center justify-between font-bold text-slate-800 mb-1">
          <div class="flex items-center gap-1.5 truncate">
            <span>${item.source_name}</span>
            <span class="text-[#1a73e8]">➔</span>
            <span>${item.dest_name}</span>
          </div>
          <span class="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-[#1a73e8] uppercase font-semibold">
            ${item.route_mode}
          </span>
        </div>
        <div class="flex items-center justify-between text-slate-500 text-[11px] mt-1.5 font-mono">
          <span>📏 ${item.distance_km} km</span>
          <span>⏱ ${item.duration_min} min</span>
          <span>⛽ $${item.fuel_cost}</span>
        </div>
        <button class="w-full mt-2 py-1 rounded bg-slate-50 hover:bg-blue-50 text-[#1a73e8] font-semibold text-[11px] transition"
                onclick="window.replayHistoryRoute(${JSON.stringify(item).replace(/"/g, '&quot;')})">
          Reload Route
        </button>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="p-4 text-center text-xs text-red-500">Error loading history: ${e.message}</div>`;
  }
}

window.replayHistoryRoute = (item) => {
  document.getElementById('origin-input').value = item.source_name;
  document.getElementById('dest-input').value = item.dest_name;
  routeController.setOrigin(item.source_coords[0], item.source_coords[1], item.source_name);
  routeController.setDestination(item.dest_coords[0], item.dest_coords[1], item.dest_name);
  
  // Switch back to directions tab
  const routesTab = document.querySelector('[data-target="routes"]');
  if (routesTab) routesTab.click();

  routeController.calculateAndRender();
};

async function loadSavedPlacesTab() {
  const container = document.getElementById('saved-places-container');
  if (!container) return;

  const user = window.currentUser;
  if (!user) {
    container.innerHTML = `
      <div class="p-6 text-center text-xs text-slate-500">
        <p class="mb-2">Sign in to save and manage favorite locations.</p>
        <a href="/login" class="text-[#1a73e8] font-bold underline">Login Here</a>
      </div>`;
    return;
  }

  try {
    const res = await api.getSavedLocations(user.id);
    const locations = res.locations || [];

    if (locations.length === 0) {
      container.innerHTML = `<div class="p-6 text-center text-xs text-slate-400">No saved locations yet. Save home, office, or delivery hubs.</div>`;
      return;
    }

    container.innerHTML = locations.map(loc => `
      <div class="flex items-center justify-between p-3 rounded-xl border border-slate-200 bg-white mb-2 text-xs shadow-sm">
        <div>
          <div class="font-bold text-slate-800 flex items-center gap-1.5">
            <span>📍</span> ${loc.label}
          </div>
          <div class="text-[11px] text-slate-500 truncate max-w-[200px]">${loc.address}</div>
        </div>
        <div class="flex items-center gap-1.5">
          <button onclick="window.useAsOrigin(${loc.latitude}, ${loc.longitude}, '${loc.label}')" class="px-2 py-1 bg-emerald-50 text-[#188038] rounded font-semibold text-[10px]">
            Set Origin
          </button>
          <button onclick="window.useAsDest(${loc.latitude}, ${loc.longitude}, '${loc.label}')" class="px-2 py-1 bg-red-50 text-[#d93025] rounded font-semibold text-[10px]">
            Set Dest
          </button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    container.innerHTML = `<div class="p-4 text-xs text-red-500">Error loading saved places.</div>`;
  }
}

window.useAsOrigin = (lat, lon, label) => {
  document.getElementById('origin-input').value = label;
  routeController.setOrigin(lat, lon, label);
  const routesTab = document.querySelector('[data-target="routes"]');
  if (routesTab) routesTab.click();
};

window.useAsDest = (lat, lon, label) => {
  document.getElementById('dest-input').value = label;
  routeController.setDestination(lat, lon, label);
  const routesTab = document.querySelector('[data-target="routes"]');
  if (routesTab) routesTab.click();
};

// POI Popup Direct Action Handlers
window.setAsDestination = (lat, lon, label) => {
  document.getElementById('dest-input').value = label;
  routeController.setDestination(lat, lon, label);
  const routesTab = document.querySelector('[data-target="routes"]');
  if (routesTab) routesTab.click();
  if (routeController.origin) {
    routeController.calculateAndRender();
  }
};

window.setAsOrigin = (lat, lon, label) => {
  document.getElementById('origin-input').value = label;
  routeController.setOrigin(lat, lon, label);
  const routesTab = document.querySelector('[data-target="routes"]');
  if (routesTab) routesTab.click();
  if (routeController.destination) {
    routeController.calculateAndRender();
  }
};

function initDemoRoute() {
  document.getElementById('origin-input').value = "Bistupur, Jamshedpur";
  document.getElementById('dest-input').value = "Tatanagar Junction Railway Station";
  routeController.setOrigin(22.8046, 86.2029, "Bistupur, Jamshedpur");
  routeController.setDestination(22.7709, 86.2022, "Tatanagar Railway Station");
  routeController.calculateAndRender();
}
