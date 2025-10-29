import { createResource, For, Show } from "solid-js";
import { createSignal, onCleanup } from "solid-js";

type Reason = {
  k: string;
  v: any;
  "+": number;
};

type Signal = {
  symbol: string;
  article_id: number;
  confidence: number;
  match_type: string;
  features: Record<string, any>;
  score: number;
  label: string;
  reasons: Reason[];
  timestamp: number;
};

const fetchTopSignals = async (): Promise<Signal[]> => {
  const response = await fetch("http://localhost:8000/signals/top?limit=20");
  if (!response.ok) {
    throw new Error("Failed to fetch signals");
  }
  return response.json();
};

export default function OpportunitiesPanel() {
  const [signals, { refetch }] = createResource<Signal[]>(fetchTopSignals);
  const [expandedSymbol, setExpandedSymbol] = createSignal<string | null>(null);

  // Auto-refresh every 30 seconds
  const interval = setInterval(() => {
    refetch();
  }, 30000);

  onCleanup(() => clearInterval(interval));

  const getLabelColor = (label: string) => {
    switch (label) {
      case "High-Conviction":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "Opportunity":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "Watch":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200";
    }
  };

  const formatReasonKey = (key: string) => {
    const labels: Record<string, string> = {
      sentiment: "Sentiment",
      magnitude: "Magnitude",
      novelty: "Novelty",
      credibility: "Credibility",
      ret_1d: "1D Return",
      vol_z: "Volume Z",
      vwap_dev: "VWAP Dev",
      gap_pct: "Gap %",
      earnings_in_days: "Earnings Prox",
      sector_momo_pct: "Sector Momo",
      topic: "Topic",
      risk_halted: "Halted",
      risk_beta: "High Beta",
      risk_atr_pct: "High ATR",
    };
    return labels[key] || key;
  };

  const formatReasonValue = (reason: Reason) => {
    if (typeof reason.v === "boolean") {
      return reason.v ? "Yes" : "No";
    }
    if (typeof reason.v === "number") {
      return reason.v.toFixed(2);
    }
    return String(reason.v);
  };

  return (
    <div class="p-6 space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
          Top Opportunities
        </h2>
        <button
          onClick={() => refetch()}
          class="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Refresh
        </button>
      </div>

      <Show
        when={!signals.loading && signals()}
        fallback={
          <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            Loading signals...
          </div>
        }
      >
        <div class="space-y-3">
          <For
            each={signals()}
            fallback={
              <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                No signals available
              </div>
            }
          >
            {(signal) => (
              <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                {/* Main row */}
                <div
                  class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-750"
                  onClick={() =>
                    setExpandedSymbol(
                      expandedSymbol() === signal.symbol ? null : signal.symbol
                    )
                  }
                >
                  <div class="flex items-center space-x-4">
                    <div class="font-mono text-lg font-bold text-gray-900 dark:text-white">
                      {signal.symbol}
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      {signal.match_type}
                    </div>
                  </div>

                  <div class="flex items-center space-x-4">
                    <div class="text-right">
                      <div class="text-2xl font-bold text-gray-900 dark:text-white">
                        {signal.score.toFixed(1)}
                      </div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        score
                      </div>
                    </div>

                    <span
                      class={`px-3 py-1 text-sm font-medium rounded-full ${getLabelColor(
                        signal.label
                      )}`}
                    >
                      {signal.label}
                    </span>

                    <svg
                      class={`w-5 h-5 text-gray-400 transition-transform ${
                        expandedSymbol() === signal.symbol ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>

                {/* Expanded details */}
                <Show when={expandedSymbol() === signal.symbol}>
                  <div class="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-750">
                    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                      Score Breakdown
                    </h3>
                    <div class="space-y-2">
                      <For each={signal.reasons}>
                        {(reason) => (
                          <div class="flex items-center justify-between text-sm">
                            <div class="flex items-center space-x-2">
                              <span class="text-gray-600 dark:text-gray-400">
                                {formatReasonKey(reason.k)}:
                              </span>
                              <span class="font-mono text-gray-900 dark:text-white">
                                {formatReasonValue(reason)}
                              </span>
                            </div>
                            <span
                              class={`font-mono font-semibold ${
                                reason["+"] > 0
                                  ? "text-green-600 dark:text-green-400"
                                  : "text-red-600 dark:text-red-400"
                              }`}
                            >
                              {reason["+"] > 0 ? "+" : ""}
                              {reason["+"].toFixed(1)}
                            </span>
                          </div>
                        )}
                      </For>
                    </div>

                    <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        Confidence: {(signal.confidence * 100).toFixed(0)}% •
                        Article ID: {signal.article_id} •
                        Updated:{" "}
                        {new Date(signal.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                </Show>
              </div>
            )}
          </For>
        </div>
      </Show>
    </div>
  );
}

