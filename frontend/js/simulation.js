// Real-World Simulation Controller (Closures & Traffic Jam injection) — Google Maps Edition
class SimulationManager {
  constructor() {
    this.incidents = [];
    this.activeTool = null; // 'closure' | 'traffic' | null
  }

  async loadIncidents() {
    try {
      const res = await api.getIncidents();
      this.incidents = res.incidents || [];
      mapManager.renderIncidents(this.incidents);
      this.renderIncidentList();
    } catch (err) {
      console.warn("Could not load simulation incidents:", err);
    }
  }

  setSimulationTool(toolType) {
    if (this.activeTool === toolType) {
      this.activeTool = null;
      mapManager.clickMode = null;
    } else {
      this.activeTool = toolType;
      mapManager.clickMode = toolType;
    }
    this.updateToolButtons();
  }

  updateToolButtons() {
    const closureBtn = document.getElementById('tool-closure-btn');
    const trafficBtn = document.getElementById('tool-traffic-btn');

    if (closureBtn) {
      if (this.activeTool === 'closure') {
        closureBtn.classList.add('ring-2', 'ring-red-500', 'bg-red-50');
      } else {
        closureBtn.classList.remove('ring-2', 'ring-red-500', 'bg-red-50');
      }
    }

    if (trafficBtn) {
      if (this.activeTool === 'traffic') {
        trafficBtn.classList.add('ring-2', 'ring-amber-500', 'bg-amber-50');
      } else {
        trafficBtn.classList.remove('ring-2', 'ring-amber-500', 'bg-amber-50');
      }
    }
  }

  async addIncident(type, lat, lon) {
    try {
      const description = type === 'closure' 
        ? prompt("Enter road closure reason (e.g. Flash Flood, Construction, Accident):", "Road Maintenance / Closure")
        : prompt("Enter traffic congestion level (e.g. Rush Hour Peak, Bottleneck):", "Heavy Rush Hour Jam");

      if (description === null) return;

      await api.addIncident({
        type: type,
        lat: lat,
        lon: lon,
        radius_km: 0.4,
        description: description || (type === 'closure' ? 'Road Closure' : 'Traffic Congestion'),
        multiplier: type === 'traffic' ? 2.5 : 999.0
      });

      this.activeTool = null;
      mapManager.clickMode = null;
      this.updateToolButtons();

      await this.loadIncidents();

      if (routeController.origin && routeController.destination) {
        routeController.calculateAndRender();
      }
    } catch (err) {
      alert(`Failed to add incident: ${err.message}`);
    }
  }

  async removeIncident(id) {
    try {
      await api.removeIncident(id);
      await this.loadIncidents();
      if (routeController.origin && routeController.destination) {
        routeController.calculateAndRender();
      }
    } catch (err) {
      alert(`Failed to remove incident: ${err.message}`);
    }
  }

  async clearAll() {
    if (!confirm("Clear all active simulated road closures and traffic obstacles?")) return;
    try {
      await api.clearIncidents();
      await this.loadIncidents();
      if (routeController.origin && routeController.destination) {
        routeController.calculateAndRender();
      }
    } catch (err) {
      alert(`Failed to clear incidents: ${err.message}`);
    }
  }

  renderIncidentList() {
    const listEl = document.getElementById('simulation-incidents-list');
    if (!listEl) return;

    if (this.incidents.length === 0) {
      listEl.innerHTML = `<p class="text-xs text-slate-400 italic">No active road hazards or closures. Click "Road Closure" or "Traffic Jam" to place an incident on the map.</p>`;
      return;
    }

    listEl.innerHTML = this.incidents.map(inc => `
      <div class="flex items-center justify-between p-2.5 rounded-lg border border-slate-200 bg-white text-xs mb-1.5 shadow-sm">
        <div class="flex items-center gap-2">
          <span class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-white text-[10px] ${inc.type === 'closure' ? 'bg-red-500' : 'bg-amber-500'}">
            ${inc.type === 'closure' ? '✕' : '⚠'}
          </span>
          <div>
            <div class="font-semibold text-slate-800">${inc.description}</div>
            <div class="text-slate-400 text-[10px] font-mono">Radius: ${inc.radius_km} km | Lat: ${inc.lat.toFixed(3)}, Lng: ${inc.lon.toFixed(3)}</div>
          </div>
        </div>
        <button onclick="window.simulationManager.removeIncident(${inc.id})" class="text-red-500 hover:text-red-700 font-bold px-2 py-1">
          ✕
        </button>
      </div>
    `).join('');
  }
}

const simulationManager = new SimulationManager();
window.simulationManager = simulationManager;
window.removeSimIncident = (id) => simulationManager.removeIncident(id);
