import { createSignal, onCleanup, onMount, Show } from "solid-js";
import { SolidApexCharts } from "solid-apexcharts";
import type { ApexOptions } from "apexcharts";

type SourceType = "sse" | "ws";

interface ChartSource {
  type: SourceType;
  url: string;
}

interface DataPoint {
  symbol: string;
  t: number;
  v: number;
  type?: string;
  count?: number;
  error?: string;
  source?: string;
  prediction_score?: number;
  prediction_label?: string;
  predicted_return?: number;
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
  const maxPoints = props.maxPoints ?? 200;
  const [series, setSeries] = createSignal<{ name: string; data: [number, number][] }[]>([
    { name: props.symbol, data: [] },
  ]);
  const [running, setRunning] = createSignal(true);
  const [connected, setConnected] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [lastValue, setLastValue] = createSignal<number | null>(null);
  const [predictionScore, setPredictionScore] = createSignal<number | null>(null);
  const [predictionLabel, setPredictionLabel] = createSignal<string | null>(null);
  const [dataSource, setDataSource] = createSignal<string | null>(null);
  const [predictedReturn, setPredictedReturn] = createSignal<number | null>(null);
  const [isAfterHours, setIsAfterHours] = createSignal(false);
  const [buySignal, setBuySignal] = createSignal<{t: number, time: string, price: number} | null>(null);
  const [sellSignal, setSellSignal] = createSignal<{t: number, time: string, price: number} | null>(null);
  const [marketOpen, setMarketOpen] = createSignal<number | null>(null);
  const [marketClose, setMarketClose] = createSignal<number | null>(null);

  let socket: EventSource | WebSocket | null = null;

  const push = (msg: DataPoint) => {
    if (msg.error) {
      setError(msg.error);
      return;
    }

    // Check if market is closed (after hours)
    if (msg.source === "after_hours") {
      setIsAfterHours(true);
      setDataSource("after_hours");
      setConnected(false); // Mark as disconnected since stream will close
      // Fetch static prediction chart
      fetchPredictionChart();
      return;
    }

    const point: [number, number] = [msg.t, msg.v];
    setLastValue(msg.v);
    setError(null);

    // Update prediction info if available (from sentiment stream)
    if (msg.prediction_score !== undefined) {
      setPredictionScore(msg.prediction_score);
    }
    if (msg.prediction_label !== undefined) {
      setPredictionLabel(msg.prediction_label);
    }

    // Update data source if available (from price stream)
    if (msg.source !== undefined) {
      setDataSource(msg.source);
    }

    // Update predicted return if available (from price stream after hours)
    if (msg.predicted_return !== undefined) {
      setPredictedReturn(msg.predicted_return);
    }

    setSeries([
      {
        name: props.symbol,
        data: [...series()[0].data.slice(-maxPoints + 1), point],
      },
    ]);
  };

  const fetchPredictionChart = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      const response = await fetch(`${API_BASE}/signals/predict-tomorrow/${props.symbol}`);
      if (!response.ok) {
        throw new Error("Failed to fetch prediction chart");
      }

      const prediction = await response.json();

      // Set prediction data
      setPredictedReturn(prediction.predicted_return);
      setLastValue(prediction.current_price);
      setMarketOpen(prediction.market_open);
      setMarketClose(prediction.market_close);
      setBuySignal({
        t: prediction.buy_signal.t,
        time: prediction.buy_signal.time,
        price: prediction.buy_signal.v
      });
      setSellSignal({
        t: prediction.sell_signal.t,
        time: prediction.sell_signal.time,
        price: prediction.sell_signal.v
      });

      // Set static chart data
      const chartData = prediction.data_points.map((p: any) => [p.t, p.v]);
      setSeries([{
        name: props.symbol,
        data: chartData
      }]);

    } catch (err) {
      console.error("Error fetching prediction chart:", err);
      setError("Failed to load prediction chart");
    }
  };

  const handleMsg = (raw: string) => {
    try {
      const msg: DataPoint = JSON.parse(raw);
      if (running()) {
        push(msg);
      }
    } catch (e) {
      // Try parsing as plain number
      const num = Number(raw);
      if (!Number.isNaN(num)) {
        push({ symbol: props.symbol, t: Date.now(), v: num });
      } else {
        console.error("Failed to parse message:", raw, e);
      }
    }
  };

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
    if (socket instanceof WebSocket) {
      socket.close();
    }
    if (socket instanceof EventSource) {
      socket.close();
    }
  });

  const options: ApexOptions = {
    chart: {
      id: `realtime-${props.symbol}`,
      animations: {
        enabled: true,
        easing: "linear",
        dynamicAnimation: {
          speed: 1000,
        },
      },
      zoom: { enabled: false },
      toolbar: { show: false },
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
        datetimeUTC: false, // Use local timezone
      },
      tickAmount: 13, // 6.5 hours * 2 = 13 half-hour intervals
      min: marketOpen() || undefined,
      max: marketClose() || undefined,
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
      width: 2,
    },
    colors: [props.color || "#3b82f6"],
    grid: {
      strokeDashArray: 3,
      borderColor: "#e5e7eb",
    },
    tooltip: {
      x: {
        format: "HH:mm:ss",
      },
      y: {
        formatter: (val: number) => val.toFixed(2),
      },
    },
    theme: {
      mode: document.documentElement.classList.contains("dark") ? "dark" : "light",
    },
  };

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
          <Show when={predictionScore() !== null && predictionLabel()}>
            <span class={`text-xs px-2 py-1 rounded font-medium ${
              predictionLabel() === "High-Conviction" ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200" :
              predictionLabel() === "Opportunity" ? "bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200" :
              "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
            }`}>
              🎯 {predictionLabel()}: {predictionScore()!.toFixed(1)}
            </span>
          </Show>
        </div>

        <div class="flex items-center gap-2">
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
            {series()[0].data.length}/{maxPoints} pts
          </span>
        </div>
      </div>

      {/* Error Display */}
      <Show when={error()}>
        <div class="mb-3 p-2 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 text-sm rounded">
          ⚠️ {error()}
        </div>
      </Show>

      {/* Chart */}
      <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
        <SolidApexCharts
          type="line"
          height={props.height ?? 300}
          options={options}
          series={series()}
        />
      </div>

      {/* Buy/Sell Signals (After Hours Only) */}
      <Show when={isAfterHours() && buySignal() && sellSignal()}>
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
    </div>
  );
}

