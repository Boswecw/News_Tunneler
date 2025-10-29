import { createSignal, For, onMount } from "solid-js";
import RunningLineChart from "../components/RunningLineChart";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_BASE = API_BASE.replace("http://", "ws://").replace("https://", "wss://");

interface ChartConfig {
  symbol: string;
  type: "price" | "sentiment";
  sourceType: "sse" | "ws";
  color?: string;
}

interface TopPrediction {
  symbol: string;
  score: number;
  label: string;
  t: number;
}

export default function LiveCharts() {
  const [charts, setCharts] = createSignal<ChartConfig[]>([]);
  const [loading, setLoading] = createSignal(true);

  const [newSymbol, setNewSymbol] = createSignal("");
  const [newType, setNewType] = createSignal<"price" | "sentiment">("price");
  const [newSourceType, setNewSourceType] = createSignal<"sse" | "ws">("sse");

  // Fetch top predictions on mount (using 30 days of data for better ML predictions)
  onMount(async () => {
    try {
      const response = await fetch(`${API_BASE}/signals/top-predictions?limit=5&min_score=50&days=30`);
      if (response.ok) {
        const predictions: TopPrediction[] = await response.json();

        // Create charts for top predicted stocks
        const newCharts: ChartConfig[] = [];
        predictions.forEach((pred) => {
          // Add price chart
          newCharts.push({
            symbol: pred.symbol,
            type: "price",
            sourceType: "sse",
            color: "#3b82f6",
          });
          // Add sentiment chart
          newCharts.push({
            symbol: pred.symbol,
            type: "sentiment",
            sourceType: "sse",
            color: "#10b981",
          });
        });

        setCharts(newCharts);
        console.log(`Auto-loaded ${predictions.length} top predictions`);
      } else {
        console.error("Failed to fetch top predictions");
        // Fallback to default charts
        setCharts([
          { symbol: "AAPL", type: "price", sourceType: "sse", color: "#3b82f6" },
          { symbol: "AAPL", type: "sentiment", sourceType: "sse", color: "#10b981" },
        ]);
      }
    } catch (error) {
      console.error("Error fetching top predictions:", error);
      // Fallback to default charts
      setCharts([
        { symbol: "AAPL", type: "price", sourceType: "sse", color: "#3b82f6" },
        { symbol: "AAPL", type: "sentiment", sourceType: "sse", color: "#10b981" },
      ]);
    } finally {
      setLoading(false);
    }
  });

  const addChart = () => {
    const symbol = newSymbol().trim().toUpperCase();
    if (!symbol) return;

    setCharts([
      ...charts(),
      {
        symbol,
        type: newType(),
        sourceType: newSourceType(),
        color: newType() === "price" ? "#3b82f6" : "#10b981",
      },
    ]);
    setNewSymbol("");
  };

  const removeChart = (index: number) => {
    setCharts(charts().filter((_, i) => i !== index));
  };

  const getChartUrl = (chart: ChartConfig) => {
    const base = chart.sourceType === "sse" ? API_BASE : WS_BASE;
    return `${base}/stream/${chart.sourceType}/${chart.type}/${chart.symbol}`;
  };

  const getChartTitle = (chart: ChartConfig) => {
    return `${chart.symbol} - ${chart.type === "price" ? "Price" : "Sentiment"} (${chart.sourceType.toUpperCase()})`;
  };

  const getYAxisLabel = (chart: ChartConfig) => {
    return chart.type === "price" ? "Price ($)" : "Sentiment Score";
  };

  return (
    <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-slate-900 dark:to-gray-900">
      <div class="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div class="mb-8">
          <div class="flex items-center gap-3 mb-3">
            <div class="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-lg">
              <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
            <div>
              <h1 class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                Live Market Data
              </h1>
              <p class="text-gray-600 dark:text-gray-400 mt-1">
                Real-time price and sentiment streaming for top predicted stocks
              </p>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading() && (
          <div class="flex items-center justify-center py-20">
            <div class="text-center">
              <div class="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-4"></div>
              <span class="text-lg text-gray-600 dark:text-gray-400">Loading top predictions...</span>
            </div>
          </div>
        )}

        {/* Add Chart Form */}
        <div class="mb-8 backdrop-blur-sm bg-white/70 dark:bg-gray-800/70 rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
          <div class="bg-gradient-to-r from-blue-500/10 to-indigo-500/10 dark:from-blue-500/20 dark:to-indigo-500/20 px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 class="text-xl font-semibold flex items-center gap-2">
              <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add New Chart
            </h2>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div class="md:col-span-1">
                <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Symbol</label>
                <input
                  type="text"
                  class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder-gray-400 dark:placeholder-gray-500"
                  placeholder="e.g., AAPL, NVDA, TSLA"
                  value={newSymbol()}
                  onInput={(e) => setNewSymbol(e.currentTarget.value)}
                  onKeyPress={(e) => e.key === "Enter" && addChart()}
                />
              </div>

              <div class="md:col-span-1">
                <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Data Type</label>
                <select
                  class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  value={newType()}
                  onChange={(e) => setNewType(e.currentTarget.value as "price" | "sentiment")}
                >
                  <option value="price">Price</option>
                  <option value="sentiment">Sentiment</option>
                </select>
              </div>

              <div class="md:col-span-1">
                <label class="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">Connection Type</label>
                <select
                  class="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  value={newSourceType()}
                  onChange={(e) => setNewSourceType(e.currentTarget.value as "sse" | "ws")}
                >
                  <option value="sse">SSE (Server-Sent Events)</option>
                  <option value="ws">WebSocket</option>
                </select>
              </div>

              <div class="md:col-span-1 flex items-end">
                <button
                  class="w-full px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium rounded-lg transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
                  onClick={addChart}
                >
                  Add Chart
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div class="grid gap-6 lg:grid-cols-2">
        <For each={charts()}>
          {(chart, index) => (
            <div class="group backdrop-blur-sm bg-white/70 dark:bg-gray-800/70 rounded-2xl shadow-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
              {/* Chart Header */}
              <div class="relative bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-750 px-6 py-3 border-b border-gray-200/50 dark:border-gray-700/50">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <div class={`w-2 h-2 rounded-full ${chart.type === 'price' ? 'bg-blue-500' : 'bg-green-500'} animate-pulse`}></div>
                    <span class="font-semibold text-gray-700 dark:text-gray-200">
                      {chart.symbol}
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                      {chart.type === "price" ? "Price" : "Sentiment"}
                    </span>
                  </div>
                  <button
                    class="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
                    onClick={() => removeChart(index())}
                    title="Remove chart"
                  >
                    <svg
                      class="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Chart Content */}
              <div class="p-6">
                <RunningLineChart
                  symbol={chart.symbol}
                  source={{
                    type: chart.sourceType,
                    url: getChartUrl(chart),
                  }}
                  title={getChartTitle(chart)}
                  yAxisLabel={getYAxisLabel(chart)}
                  color={chart.color}
                  maxPoints={200}
                  height={320}
                />
              </div>
            </div>
          )}
        </For>
        </div>

        {/* Empty State */}
        {!loading() && charts().length === 0 && (
        <div class="text-center py-20">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
            <svg class="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 class="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">No Charts Yet</h3>
          <p class="text-gray-500 dark:text-gray-400">Add a chart above to start tracking stocks</p>
          </div>
        )}

        {/* Info Section */}
        <div class="mt-8 backdrop-blur-sm bg-gradient-to-br from-blue-50/80 to-indigo-50/80 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl border border-blue-200/50 dark:border-blue-700/50 overflow-hidden shadow-lg">
        <div class="bg-gradient-to-r from-blue-500/10 to-indigo-500/10 dark:from-blue-500/20 dark:to-indigo-500/20 px-6 py-4 border-b border-blue-200/50 dark:border-blue-700/50">
          <h3 class="text-lg font-semibold flex items-center gap-2">
            <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            About Live Charts
          </h3>
        </div>
        <div class="p-6">
          <div class="grid md:grid-cols-2 gap-4">
            <div class="space-y-3">
              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-500/20 dark:bg-blue-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">Auto-Loaded Predictions</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    Charts automatically load for the top 5 stocks with highest ML prediction scores from the last 30 days.
                  </p>
                </div>
              </div>

              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-500/20 dark:bg-blue-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">Price Charts (Blue)</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    During market hours (9:30 AM - 4:00 PM ET), shows real-time streaming data. After hours, displays predictions for the next trading session.
                  </p>
                </div>
              </div>

              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-green-500/20 dark:bg-green-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">Sentiment Charts (Green)</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    Shows aggregated sentiment scores from recent news articles, plus ML prediction score and label.
                  </p>
                </div>
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-purple-500/20 dark:bg-purple-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">Add Custom Charts</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    Use the form above to add charts for any symbol you want to track in real-time.
                  </p>
                </div>
              </div>

              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/20 dark:bg-amber-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">Buy/Sell Signals</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    After hours, charts show predicted optimal buy time (low) and sell time (high) for the next trading session.
                  </p>
                </div>
              </div>

              <div class="flex gap-3">
                <div class="flex-shrink-0 w-8 h-8 rounded-lg bg-indigo-500/20 dark:bg-indigo-500/30 flex items-center justify-center">
                  <svg class="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-1">ML Training</h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    Over time, the model learns which patterns predict market-beating returns and improves prediction accuracy.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>
    );
  }

