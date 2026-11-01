// Algorithm Benchmark & Academic Visualizer Engine — Google Maps Edition
class AlgorithmVisualizer {
  constructor() {
    this.benchmarkData = null;
  }

  async loadBenchmark(coordinates) {
    if (!coordinates || coordinates.length < 2) return;

    try {
      const res = await api.benchmarkAlgorithms(coordinates);
      if (res.success && res.benchmark) {
        this.benchmarkData = res.benchmark;
        this.renderBenchmarkUI();
      }
    } catch (err) {
      console.warn("Algorithm benchmark update error:", err);
    }
  }

  renderBenchmarkUI() {
    const container = document.getElementById('benchmark-results-container');
    if (!container || !this.benchmarkData) return;

    const data = this.benchmarkData;
    const dij = data.dijkstra || {};
    const astar = data.a_star || {};

    const maxNodes = Math.max(dij.nodes_explored || 1, astar.nodes_explored || 1);
    const dijPercent = Math.round((dij.nodes_explored / maxNodes) * 100);
    const astarPercent = Math.round((astar.nodes_explored / maxNodes) * 100);

    container.innerHTML = `
      <div class="rounded-xl p-4 bg-white border border-slate-200 shadow-sm mb-4">
        <div class="flex items-center justify-between mb-3">
          <div>
            <h4 class="font-bold text-slate-900 text-sm">Algorithmic Performance Benchmark</h4>
            <p class="text-[11px] text-slate-500">Dijkstra vs. A* (Haversine Heuristic) on Road Network</p>
          </div>
          <span class="px-2.5 py-1 text-xs font-bold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
            ${data.speedup_percentage}% Search Pruning
          </span>
        </div>

        <div class="grid grid-cols-2 gap-2 mb-3 text-xs">
          <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div class="font-bold text-slate-700 mb-0.5">Graph Network</div>
            <div class="text-slate-500 text-[11px]">Nodes: <b class="text-slate-800 font-mono">${data.graph_nodes_count}</b></div>
            <div class="text-slate-500 text-[11px]">Edges: <b class="text-slate-800 font-mono">${data.graph_edges_count}</b></div>
          </div>
          <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200">
            <div class="font-bold text-slate-700 mb-0.5">Heuristic Engine</div>
            <div class="text-slate-500 text-[11px]">Formula: <b class="text-slate-800">Haversine</b></div>
            <div class="text-slate-500 text-[11px]">Admissibility: <b class="text-emerald-700 font-semibold">Strict (h &le; h*)</b></div>
          </div>
        </div>

        <!-- Node Exploration Comparison -->
        <div class="space-y-2.5 mb-3">
          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-slate-600">Dijkstra (Uniform Cost Search)</span>
              <span class="text-amber-700 font-mono">${dij.nodes_explored} nodes (${dij.execution_time_ms} ms)</span>
            </div>
            <div class="w-full h-2 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div class="h-full bg-amber-500 rounded-full transition-all duration-500" style="width: ${dijPercent}%"></div>
            </div>
          </div>

          <div>
            <div class="flex justify-between text-xs font-semibold mb-1">
              <span class="text-[#1a73e8]">A* Search (Goal-Directed)</span>
              <span class="text-[#1a73e8] font-mono font-bold">${astar.nodes_explored} nodes (${astar.execution_time_ms} ms)</span>
            </div>
            <div class="w-full h-2 rounded-full bg-slate-100 overflow-hidden border border-slate-200">
              <div class="h-full bg-[#1a73e8] rounded-full transition-all duration-500" style="width: ${astarPercent}%"></div>
            </div>
          </div>
        </div>

        <div class="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-600 leading-relaxed">
          <b>Evaluation Result:</b> A* pruned <span class="text-emerald-700 font-bold">${Math.max(0, dij.nodes_explored - astar.nodes_explored)} unpromising branches</span> compared to Dijkstra while preserving exact mathematical distance optimality (${astar.total_distance_km} km).
        </div>
      </div>
    `;
  }
}

const visualizer = new AlgorithmVisualizer();
window.visualizer = visualizer;
