import { createSignal, onCleanup, onMount, Show, createEffect, createMemo } from "solid-js";
import { SolidApexCharts } from "solid-apexcharts";
import type { ApexOptions } from "apexcharts";
import { priceCache, fetchIntradayCache, type PricePoint } from "../lib/priceCache";
import { getIntradayBounds, type BoundsResponse } from "../lib/api";

type SourceType = "sse" | "ws";
type ViewMode = "full-day" | "live-minute" | "predictive";

interface ChartSource {
  type: SourceType;
  url: string;
}

interface DataPoint {
  symbol: string;
  ts: number;
  value: number;
  error?: string;
  _meta?: string;  // Metadata field (e.g., "after_hours")
}

interface SignalPoint {
  symbol: string;
  ts: number;
  signal: "BUY" | "SELL";
  prob: number;
  price: number;
}

interface RunningLineChartProps {
  symbol: string;
  source: ChartSource;
  maxPoints?: number;
  height?: number;
  title?: string;
  yAxisLabel?: string;
  color?: string;
}

export default function RunningLineChart(props: RunningLineChartProps) {
  const maxPoints = props.maxPoints ?? 300;
  const [series, setSeries] = createSignal<{ name: string; data: [number, number][] }[]>([
    { name: props.symbol, data: [] },
  ]);
  const [running, setRunning] = createSignal(true);
  const [connected, setConnected] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [lastValue, setLastValue] = createSignal<number | null>(null);
  const [dataSource, setDataSource] = createSignal<string | null>(null);
  const [isAfterHours, setIsAfterHours] = createSignal(false);
  const [marketOpen, setMarketOpen] = createSignal<number | null>(null);
  const [marketClose, setMarketClose] = createSignal<number | null>(null);
  const [viewMode, setViewMode] = createSignal<ViewMode>("live-minute");
  const [cacheLoaded, setCacheLoaded] = createSignal(false);
  const [predictedReturn, setPredictedReturn] = createSignal<number | null>(null);
  const [buySignal, setBuySignal] = createSignal<{t: number, time: string, price: number} | null>(null);
  const [sellSignal, setSellSignal] = createSignal<{t: number, time: string, price: number} | null>(null);
  const [predictiveSignals, setPredictiveSignals] = createSignal<SignalPoint[]>([]);

  // Intraday bounds state
  const [showBounds, setShowBounds] = createSignal(false);
  const [boundsHorizon, setBoundsHorizon] = createSignal(5);
  const [boundsData, setBoundsData] = createSignal<BoundsResponse | null>(null);
  const [boundsLoading, setBoundsLoading] = createSignal(false);
  const [boundsError, setBoundsError] = createSignal<string | null>(null);

  // Computed series that includes bounds when available
  const chartSeries = createMemo(() => {
    const baseSeries = series();
    const bounds = boundsData();

    // Only add bounds in non-predictive modes
    if (!showBounds() || !bounds || bounds.points.length === 0 || viewMode() === "predictive") {
      return baseSeries;
    }

    // Create bounds series (area range)
    const boundsSeriesData: [number, number, number][] = bounds.points.map(p => [
      p.ts,
      p.lower,
      p.upper
    ]);

    return [
      ...baseSeries,
      {
        name: `Bounds (${boundsHorizon()}m ahead)`,
        type: 'rangeArea',
        data: boundsSeriesData
      } as any
    ];
  });

  let socket: EventSource | WebSocket | null = null;
  let predictLineSocket: EventSource | null = null;
  let predictSignalsSocket: EventSource | null = null;
  let cachePointsReceived = 0;
  let cacheLoadTimer: number | null = null;

  const push = (msg: DataPoint) => {
    if (msg.error) {
      setError(msg.error);
      return;
    }

    // Check if market is closed (after hours)
    if (msg._meta === "after_hours" || msg.value === -1) {
      console.log(`🌙 After hours detected for ${props.symbol}, switching to predictive mode`);
      setIsAfterHours(true);
      setDataSource("after_hours");
      setConnected(false);
      // Auto-switch to predictive mode
      setViewMode("predictive");
      return;
    }

    const point: [number, number] = [msg.ts, msg.value];
    setLastValue(msg.value);
    setError(null);

    // Add to cache (for price streams)
    priceCache.addLivePoint(props.symbol, msg);

    // Detect initial cache load (burst of points at connection)
    if (!cacheLoaded()) {
      cachePointsReceived++;

      // Clear existing timer
      if (cacheLoadTimer !== null) {
        clearTimeout(cacheLoadTimer);
      }

      // Set timer to mark cache as loaded after 500ms of no new points
      cacheLoadTimer = window.setTimeout(() => {
        if (cachePointsReceived > 50) {  // If we received more than 50 points, it's likely the cache
          setCacheLoaded(true);
          console.log(`Cache loaded with ${cachePointsReceived} points for ${props.symbol}`);
          updateChartFromCache();
        }
        cachePointsReceived = 0;
      }, 500);
    }

    // Update chart based on view mode
    if (viewMode() === "live-minute") {
      // Live minute mode: show only recent points
      setSeries([
        {
          name: props.symbol,
          data: [...series()[0].data.slice(-maxPoints + 1), point],
        },
      ]);
    } else if (cacheLoaded()) {
      // Full day mode: update from cache (only if cache is loaded)
      updateChartFromCache();
    }
  };

  const updateChartFromCache = () => {
    const data = viewMode() === "full-day"
      ? priceCache.getFullDayData(props.symbol)
      : priceCache.getLiveData(props.symbol).slice(-maxPoints);

    const chartData: [number, number][] = data.map(p => [p.ts, p.value]);

    setSeries([{
      name: props.symbol,
      data: chartData
    }]);

    if (data.length > 0) {
      setLastValue(data[data.length - 1].value);
    }
  };

  const fetchPredictionChart = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
      const url = `${API_BASE}/api/signals/predict-tomorrow/${props.symbol}`;

      console.log(`📊 Fetching prediction chart from: ${url}`);

      const response = await fetch(url);
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ Prediction fetch failed (${response.status}):`, errorText);
        throw new Error(`Failed to fetch prediction chart: ${response.status} ${errorText}`);
      }

      const prediction = await response.json();

      console.log(`📊 Loaded prediction chart for ${props.symbol}:`, prediction);
      console.log(`   - Data points: ${prediction.data_points?.length || 0}`);
      console.log(`   - Predicted return: ${prediction.predicted_return}%`);
      console.log(`   - Market open: ${new Date(prediction.market_open).toLocaleString()}`);
      console.log(`   - Market close: ${new Date(prediction.market_close).toLocaleString()}`);

      // Set prediction data
      setPredictedReturn(prediction.predicted_return);
      setLastValue(prediction.current_price);
      setMarketOpen(prediction.market_open);
      setMarketClose(prediction.market_close);

      if (prediction.buy_signal) {
        setBuySignal({
          t: prediction.buy_signal.t,
          time: prediction.buy_signal.time,
          price: prediction.buy_signal.v  // Backend returns 'v' not 'price'
        });
        console.log(`   - Buy signal: ${prediction.buy_signal.time} @ $${prediction.buy_signal.v}`);
      }

      if (prediction.sell_signal) {
        setSellSignal({
          t: prediction.sell_signal.t,
          time: prediction.sell_signal.time,
          price: prediction.sell_signal.v  // Backend returns 'v' not 'price'
        });
        console.log(`   - Sell signal: ${prediction.sell_signal.time} @ $${prediction.sell_signal.v}`);
      }

      // Set static chart data
      if (prediction.data_points && prediction.data_points.length > 0) {
        const chartData = prediction.data_points.map((p: any) => [p.t, p.v]);
        console.log(`   - Chart data sample (first 3):`, chartData.slice(0, 3));
        console.log(`   - Chart data sample (last 3):`, chartData.slice(-3));

        setSeries([{
          name: props.symbol,
          data: chartData
        }]);

        console.log(`✅ Prediction chart loaded successfully: ${chartData.length} data points`);
      } else {
        console.error(`❌ No data points in prediction response`);
        setError("No prediction data available");
      }

    } catch (err) {
      console.error("❌ Error fetching prediction chart:", err);
      setError(`Failed to load prediction chart: ${err}`);
    }
  };

  const loadPredictiveMode = () => {
    console.log(`🔮 loadPredictiveMode() called for ${props.symbol}`);

    // Close existing predictive sockets if any
    if (predictLineSocket) {
      console.log(`   - Closing predictLineSocket`);
      predictLineSocket.close();
      predictLineSocket = null;
    }
    if (predictSignalsSocket) {
      console.log(`   - Closing predictSignalsSocket`);
      predictSignalsSocket.close();
      predictSignalsSocket = null;
    }

    // Close main socket to stop live data
    if (socket) {
      console.log(`   - Closing main socket`);
      if (socket instanceof EventSource) {
        socket.close();
      } else if (socket instanceof WebSocket) {
        socket.close();
      }
      socket = null;
    }

    console.log(`   - Clearing series and setting connected=false`);
    // Clear existing series before loading prediction
    setSeries([]);
    setConnected(false);

    console.log(`   - Calling fetchPredictionChart()`);
    // Load static prediction chart instead of streaming
    fetchPredictionChart();
  };

  const handleMsg = (raw: string) => {
    try {
      const msg: DataPoint = JSON.parse(raw);
      if (running()) {
        push(msg);
      }
    } catch (e) {
      // Try parsing as plain number (fallback for legacy support)
      const num = Number(raw);
      if (!Number.isNaN(num)) {
        push({ symbol: props.symbol, ts: Date.now(), value: num });
      } else {
        console.error("Failed to parse message:", raw, e);
      }
    }
  };

  // Fetch intraday bounds predictions
  const fetchBounds = async () => {
    if (!showBounds()) return;

    setBoundsLoading(true);
    setBoundsError(null);

    try {
      console.log(`📊 Fetching bounds for ${props.symbol} horizon=${boundsHorizon()}`);
      const data = await getIntradayBounds(props.symbol, '1m', boundsHorizon(), 200);
      setBoundsData(data);
      console.log(`✅ Bounds loaded: ${data.points.length} points`);
    } catch (err: any) {
      console.error(`❌ Failed to fetch bounds for ${props.symbol}:`, err);
      setBoundsError(err.message || 'Failed to load bounds');
    } finally {
      setBoundsLoading(false);
    }
  };

  // Effect to fetch bounds when showBounds or horizon changes
  createEffect(() => {
    if (showBounds()) {
      fetchBounds();
    } else {
      setBoundsData(null);
    }
  });

  // Effect to update chart when view mode changes
  createEffect(() => {
    const mode = viewMode();
    console.log(`🔄 View mode changed to: ${mode} (symbol: ${props.symbol})`);

    if (mode === "predictive") {
      console.log(`   ➡️ Triggering loadPredictiveMode()`);
      loadPredictiveMode();
    } else if (cacheLoaded()) {
      console.log(`   ➡️ Triggering updateChartFromCache()`);
      updateChartFromCache();
    } else {
      console.log(`   ➡️ No action (cache not loaded)`);
    }
  });

  onMount(() => {
    const { url, type } = props.source;

    if (type === "sse") {
      const es = new EventSource(url);
      socket = es;

      es.onopen = () => {
        setConnected(true);
        setError(null);
        console.log(`SSE connected: ${url}`);
      };

      es.onmessage = (e) => {
        handleMsg(e.data);
      };

      es.onerror = (e) => {
        // Don't show error if we're in after-hours mode (expected disconnect)
        if (!isAfterHours()) {
          setConnected(false);
          setError("Connection lost");
          console.error("SSE error:", e);
        }
      };
    } else if (type === "ws") {
      const ws = new WebSocket(url);
      socket = ws;

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        console.log(`WebSocket connected: ${url}`);
      };

      ws.onmessage = (e) => {
        handleMsg(e.data);
      };

      ws.onerror = (e) => {
        setConnected(false);
        setError("Connection error");
        console.error("WebSocket error:", e);
      };

      ws.onclose = () => {
        setConnected(false);
        console.log("WebSocket closed");
      };
    }
  });

  onCleanup(() => {
    console.log(`Cleaning up chart for ${props.symbol} (${props.source.type})`);
    if (socket instanceof WebSocket) {
      socket.close();
      console.log(`WebSocket closed for ${props.symbol}`);
    }
    if (socket instanceof EventSource) {
      socket.close();
      console.log(`EventSource closed for ${props.symbol}`);
    }
    socket = null;

    // Close predictive sockets
    if (predictLineSocket) {
      predictLineSocket.close();
      predictLineSocket = null;
    }
    if (predictSignalsSocket) {
      predictSignalsSocket.close();
      predictSignalsSocket = null;
    }

    // Clear cache for this symbol
    priceCache.clearCache(props.symbol);
  });

  const options = createMemo((): ApexOptions => ({
    chart: {
      id: `realtime-${props.symbol}`,
      animations: {
        enabled: viewMode() === "live-minute",
        easing: "linear",
        dynamicAnimation: {
          speed: 1000,
        },
      },
      zoom: { enabled: viewMode() === "full-day" || viewMode() === "predictive" },
      toolbar: { show: viewMode() === "full-day" || viewMode() === "predictive" },
      background: "transparent",
    },
    xaxis: {
      type: "datetime",
      labels: {
        formatter: (value: number) => {
          const date = new Date(value);
          const hours = date.getHours().toString().padStart(2, '0');
          const minutes = date.getMinutes().toString().padStart(2, '0');
          return `${hours}:${minutes}`;
        },
        datetimeUTC: false,
      },
      tickAmount: (viewMode() === "full-day" || viewMode() === "predictive") ? 13 : 6,
      min: (viewMode() === "full-day" || viewMode() === "predictive") ? (marketOpen() || undefined) : undefined,
      max: (viewMode() === "full-day" || viewMode() === "predictive") ? (marketClose() || undefined) : undefined,
    },
    yaxis: {
      decimalsInFloat: 2,
      title: {
        text: props.yAxisLabel || "Value",
      },
      labels: {
        formatter: (val: number) => val.toFixed(2),
      },
    },
    stroke: {
      curve: "smooth",
      width: [2, 0],  // Line for price, no stroke for bounds
    },
    fill: {
      type: ["gradient", "solid"],
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
        stops: [0, 90, 100]
      },
      opacity: [0.4, 0.2],  // Price area opacity, bounds area opacity
    },
    colors: [props.color || "#3b82f6", "#818cf8"],  // Price color, bounds color (indigo)
    grid: {
      strokeDashArray: 3,
      borderColor: "#e5e7eb",
      padding: {
        right: 80,  // Extra padding for end-of-day marker labels
        left: 80,   // Extra padding for start-of-day marker labels
      }
    },
    plotOptions: {
      bar: {
        columnWidth: '60%',
        barHeight: '70%',
      }
    },
    dataLabels: {
      enabled: false
    },
    tooltip: {
      x: {
        format: "HH:mm:ss",
      },
      y: {
        formatter: (val: number, opts?: any) => {
          if (opts && opts.seriesIndex === 1 && showBounds()) {
            // Bounds series - show range
            const dataPoint = boundsData()?.points[opts.dataPointIndex];
            if (dataPoint) {
              const bandWidth = ((dataPoint.upper - dataPoint.lower) / dataPoint.mid * 100).toFixed(1);
              return `${dataPoint.lower.toFixed(2)} - ${dataPoint.upper.toFixed(2)} (±${bandWidth}%)`;
            }
          }
          return val.toFixed(2);
        },
      },
      shared: true,
      intersect: false,
    },
    theme: {
      mode: document.documentElement.classList.contains("dark") ? "dark" : "light",
    },
    // Add annotations for predicted HIGH and LOW points (predictive mode only)
    annotations: {
      points: (viewMode() === "predictive" && buySignal() && sellSignal()) ? [
        // Predicted LOW (Buy Signal)
        {
          x: buySignal()!.t,
          y: buySignal()!.price,
          marker: {
            size: 8,
            fillColor: "#10b981",
            strokeColor: "#fff",
            strokeWidth: 2,
            shape: "circle",
          },
          label: {
            borderColor: "#10b981",
            offsetY: -10,
            style: {
              color: "#fff",
              background: "#10b981",
              fontSize: "12px",
              fontWeight: "bold",
            },
            text: `LOW: $${buySignal()!.price.toFixed(2)} @ ${buySignal()!.time}`,
          },
        },
        // Predicted HIGH (Sell Signal)
        {
          x: sellSignal()!.t,
          y: sellSignal()!.price,
          marker: {
            size: 8,
            fillColor: "#ef4444",
            strokeColor: "#fff",
            strokeWidth: 2,
            shape: "circle",
          },
          label: {
            borderColor: "#ef4444",
            offsetY: -10,
            style: {
              color: "#fff",
              background: "#ef4444",
              fontSize: "12px",
              fontWeight: "bold",
            },
            text: `HIGH: $${sellSignal()!.price.toFixed(2)} @ ${sellSignal()!.time}`,
          },
        },
      ] : [],
    },
  }));

  return (
    <div class="w-full">
      {/* Header */}
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-3 flex-wrap">
          <h3 class="font-semibold text-lg">{props.title || props.symbol}</h3>
          <Show when={lastValue() !== null}>
            <span class="text-sm font-mono bg-blue-100 dark:bg-blue-900 px-2 py-1 rounded">
              {lastValue()!.toFixed(2)}
            </span>
          </Show>
          <Show when={connected() && dataSource() === "intraday"}>
            <span class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
              <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Live
            </span>
          </Show>
          <Show when={isAfterHours() || dataSource() === "after_hours"}>
            <span class="flex items-center gap-1 text-xs text-purple-600 dark:text-purple-400">
              <span class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></span>
              Tomorrow's Prediction
              {predictedReturn() !== null && (
                <span class={`ml-1 font-mono ${predictedReturn()! >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {predictedReturn()! >= 0 ? '+' : ''}{predictedReturn()!.toFixed(2)}%
                </span>
              )}
            </span>
          </Show>
          <Show when={!connected() && !isAfterHours() && dataSource() !== "after_hours"}>
            <span class="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
              <span class="w-2 h-2 bg-red-500 rounded-full"></span>
              Disconnected
            </span>
          </Show>
        </div>

        <div class="flex items-center gap-2 flex-wrap">
          {/* View Mode Toggle */}
          <div class="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded p-1">
            <Show when={cacheLoaded() && !isAfterHours()}>
              <button
                class={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  viewMode() === "full-day"
                    ? "bg-blue-500 text-white"
                    : "bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
                onClick={() => setViewMode("full-day")}
                title="Show full trading day (minute data)"
              >
                📊 Full Day
              </button>
              <button
                class={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  viewMode() === "live-minute"
                    ? "bg-blue-500 text-white"
                    : "bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
                onClick={() => setViewMode("live-minute")}
                title="Show live minute-by-minute updates"
              >
                ⚡ Live
              </button>
            </Show>
            <button
              class={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                viewMode() === "predictive"
                  ? "bg-purple-500 text-white"
                  : "bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
              }`}
              onClick={() => {
                console.log(`🔮 Predictive button clicked for ${props.symbol}`);
                setViewMode("predictive");
              }}
              title="Show next-day predictions with BUY/SELL signals"
            >
              🔮 Predictive
            </button>
          </div>

          {/* Bounds Controls */}
          <Show when={viewMode() !== "predictive"}>
            <div class="flex items-center gap-1 border-l border-gray-300 dark:border-gray-600 pl-2">
              <button
                class={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  showBounds()
                    ? "bg-indigo-500 text-white"
                    : "bg-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700"
                }`}
                onClick={() => setShowBounds(!showBounds())}
                title="Toggle prediction bounds overlay"
              >
                📈 Bounds
              </button>
              <Show when={showBounds()}>
                <select
                  class="px-2 py-1 text-xs rounded bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600"
                  value={boundsHorizon()}
                  onChange={(e) => setBoundsHorizon(parseInt(e.currentTarget.value))}
                  title="Prediction horizon (minutes ahead)"
                >
                  <option value="5">5m</option>
                  <option value="15">15m</option>
                  <option value="30">30m</option>
                </select>
              </Show>
            </div>
          </Show>

          <button
            class="px-3 py-1 text-xs font-medium rounded bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
            onClick={() => setRunning(!running())}
          >
            {running() ? "⏸ Pause" : "▶ Resume"}
          </button>
          <button
            class="px-3 py-1 text-xs font-medium rounded bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors"
            onClick={() => setSeries([{ name: props.symbol, data: [] }])}
          >
            🗑 Clear
          </button>
          <span class="text-xs text-gray-500 dark:text-gray-400">
            {series()[0]?.data?.length || 0} pts
            <Show when={cacheLoaded()}>
              {" "}({viewMode() === "full-day" ? "minute" : "live"})
            </Show>
          </span>
        </div>
      </div>

      {/* Bounds Status */}
      <Show when={showBounds() && boundsLoading()}>
        <div class="mb-3 p-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm rounded">
          ⏳ Loading prediction bounds...
        </div>
      </Show>
      <Show when={showBounds() && boundsError()}>
        <div class="mb-3 p-2 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 text-sm rounded">
          ⚠️ {boundsError()}
        </div>
      </Show>
      <Show when={showBounds() && boundsData() && !boundsLoading()}>
        <div class="mb-3 p-2 bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 text-sm rounded">
          📊 Showing {boundsData()!.points.length} prediction bounds ({boundsHorizon()}m ahead)
        </div>
      </Show>

      {/* Error Display */}
      <Show when={error()}>
        <div class="mb-3 p-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-sm rounded">
          ⚠️ {error()}
        </div>
      </Show>

      {/* Chart */}
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <SolidApexCharts
          type="area"
          height={props.height ?? 300}
          options={options()}
          series={chartSeries()}
        />
      </div>

      {/* Buy/Sell Signals (After Hours - Legacy) */}
      <Show when={isAfterHours() && buySignal() && sellSignal() && viewMode() !== "predictive"}>
        <div class="mt-4 grid grid-cols-2 gap-4">
          <div class="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-green-600 dark:text-green-400 font-semibold">🟢 BUY Signal</span>
            </div>
            <div class="text-sm text-gray-700 dark:text-gray-300">
              <div>Time: <span class="font-mono">{buySignal()!.time}</span></div>
              <div>Price: <span class="font-mono">${buySignal()!.price.toFixed(2)}</span></div>
            </div>
          </div>

          <div class="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 border border-red-200 dark:border-red-800">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-red-600 dark:text-red-400 font-semibold">🔴 SELL Signal</span>
            </div>
            <div class="text-sm text-gray-700 dark:text-gray-300">
              <div>Time: <span class="font-mono">{sellSignal()!.time}</span></div>
              <div>Price: <span class="font-mono">${sellSignal()!.price.toFixed(2)}</span></div>
            </div>
          </div>
        </div>
      </Show>

      {/* Predictive Signals (Predictive Mode) */}
      <Show when={viewMode() === "predictive" && predictiveSignals().length > 0}>
        <div class="mt-4">
          <h4 class="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">
            🔮 Predicted Trading Signals ({predictiveSignals().length} signals)
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-48 overflow-y-auto">
            {predictiveSignals().map((signal, idx) => {
              const time = new Date(signal.ts).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
              });
              const isBuy = signal.signal === "BUY";
              return (
                <div
                  class={`p-2 rounded border text-xs ${
                    isBuy
                      ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                      : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                  }`}
                >
                  <div class="flex items-center justify-between mb-1">
                    <span class={`font-semibold ${isBuy ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {isBuy ? '↑ BUY' : '↓ SELL'}
                    </span>
                    <span class="font-mono text-gray-600 dark:text-gray-400">{time}</span>
                  </div>
                  <div class="flex items-center justify-between text-gray-700 dark:text-gray-300">
                    <span class="font-mono">${signal.price.toFixed(2)}</span>
                    <span class={`font-semibold ${isBuy ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                      {(signal.prob * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Show>
    </div>
  );
}

