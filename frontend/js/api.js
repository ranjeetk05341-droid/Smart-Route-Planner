// Centralized API Client
class APIClient {
  constructor() {
    this.baseUrl = CONFIG.API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {})
      }
    };

    if (config.body && typeof config.body === 'object') {
      config.body = JSON.stringify(config.body);
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}: Request failed`);
      }
      return data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  }

  // Auth Endpoints
  async register(username, email, password, prefs = {}) {
    return this.request('/auth/register', {
      method: 'POST',
      body: { username, email, password, ...prefs }
    });
  }

  async login(identity, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: { identity, password }
    });
  }

  async getCurrentUser(userId) {
    return this.request(`/auth/me${userId ? `?user_id=${userId}` : ''}`);
  }

  async updatePreferences(prefs) {
    return this.request('/auth/preferences', {
      method: 'PUT',
      body: prefs
    });
  }

  // Location, Geocoding & POI Endpoints
  async searchLocations(query) {
    return this.request(`/locations/search?q=${encodeURIComponent(query)}`);
  }

  async reverseGeocode(lat, lon) {
    return this.request(`/locations/reverse?lat=${lat}&lon=${lon}`);
  }

  async getPOIs(params = {}) {
    const query = new URLSearchParams();
    if (params.lat) query.append('lat', params.lat);
    if (params.lon) query.append('lon', params.lon);
    if (params.radius) query.append('radius', params.radius);
    if (params.bbox) query.append('bbox', params.bbox);
    if (params.category) query.append('category', params.category);
    if (params.limit) query.append('limit', params.limit);
    return this.request(`/locations/pois?${query.toString()}`);
  }

  async getSavedLocations(userId) {
    return this.request(`/locations/saved${userId ? `?user_id=${userId}` : ''}`);
  }

  async saveLocation(data) {
    return this.request('/locations/saved', {
      method: 'POST',
      body: data
    });
  }

  async deleteSavedLocation(locId) {
    return this.request(`/locations/saved/${locId}`, {
      method: 'DELETE'
    });
  }

  // Routing Endpoints
  async calculateRoute(params) {
    return this.request('/routes/calculate', {
      method: 'POST',
      body: params
    });
  }

  async benchmarkAlgorithms(coordinates) {
    return this.request('/routes/benchmark', {
      method: 'POST',
      body: { coordinates }
    });
  }

  async getRouteHistory(userId) {
    return this.request(`/routes/history${userId ? `?user_id=${userId}` : ''}`);
  }

  async saveFavoriteRoute(data) {
    return this.request('/routes/favorite', {
      method: 'POST',
      body: data
    });
  }

  async getFavoriteRoutes(userId) {
    return this.request(`/routes/favorites${userId ? `?user_id=${userId}` : ''}`);
  }

  async deleteFavoriteRoute(favId) {
    return this.request(`/routes/favorite/${favId}`, {
      method: 'DELETE'
    });
  }

  // Simulation Endpoints
  async getIncidents() {
    return this.request('/simulation/incidents');
  }

  async addIncident(data) {
    return this.request('/simulation/incidents', {
      method: 'POST',
      body: data
    });
  }

  async removeIncident(incidentId) {
    return this.request(`/simulation/incidents/${incidentId}`, {
      method: 'DELETE'
    });
  }

  async clearIncidents() {
    return this.request('/simulation/clear', {
      method: 'POST'
    });
  }

  // Google Maps Platform Config & Diagnostics
  async getMapsConfig() {
    return this.request('/config/maps');
  }

  async getGoogleDiagnostics() {
    return this.request('/diagnostics/google-maps');
  }
}

const api = new APIClient();

