/**
 * BacktestCard component - displays historical stock reaction analysis
 */
import { createResource, Show, For } from "solid-js";
import { getBacktest, type BacktestResult } from "../lib/backtest";

interface BacktestCardProps {
  ticker: string;
  catalyst?: string;
  lookback?: number;
}

export default function BacktestCard(props: BacktestCardProps) {
  const [bt] = createResource(
    () => ({
      t: props.ticker,
      c: props.catalyst,
      l: props.lookback || 365,
    }),
    ({ t, c, l }) => getBacktest(t, c, l)
  );

  return (
    <div class="rounded-2xl p-4 bg-gradient-to-br from-purple-900/40 via-neutral-900/60 to-blue-900/40 text-white border border-purple-800/30 shadow-lg">
      <div class="flex items-center gap-2 mb-3">
        <span class="text-2xl">📊</span>
        <h3 class="text-sm font-semibold">
          Historical Backtest — {props.ticker}
          {props.catalyst && (
            <span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-purple-500/30 border border-purple-400/30">
              {props.catalyst}
            </span>
          )}
        </h3>
      </div>

      <Show
        when={!bt.loading && bt()}
        fallback={
          <div class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-400"></div>
            <span class="ml-3 text-sm opacity-70">Analyzing historical data...</span>
          </div>
        }
      >
        {(data) => (
          <div class="text-xs space-y-3">
            {/* Summary */}
            <div class="flex items-center gap-4 text-xs opacity-80 pb-2 border-b border-white/10">
              <div>
                <span class="opacity-60">Events analyzed:</span>{" "}
                <b class="text-purple-300">{data().events_count}</b>
              </div>
              <div>
                <span class="opacity-60">Lookback:</span>{" "}
                <b class="text-purple-300">{data().lookback_days}d</b>
              </div>
            </div>

            {/* Window Statistics Grid */}
            <div class="grid grid-cols-3 gap-2">
              <For each={["1d", "3d", "5d"] as const}>
                {(key) => {
                  const windows = data().windows;
                  const stats = windows?.[key];
                  return (
                    <div class="rounded-lg border border-purple-800/40 bg-purple-900/20 p-3 hover:bg-purple-900/30 transition-colors">
                      <div class="uppercase font-semibold text-purple-300 mb-2">
                        {key}
                      </div>
                      <Show
                        when={stats}
                        fallback={
                          <div class="text-xs opacity-50">No data</div>
                        }
                      >
                        <div class="space-y-1">
                          <div class="flex justify-between">
                            <span class="opacity-70">Avg:</span>
                            <b
                              class={
                                (stats?.["avg_%"] ?? 0) > 0
                                  ? "text-green-400"
                                  : (stats?.["avg_%"] ?? 0) < 0
                                  ? "text-red-400"
                                  : ""
                              }
                            >
                              {stats?.["avg_%"] ?? "—"}%
                            </b>
                          </div>
                          <div class="flex justify-between">
                            <span class="opacity-70">Median:</span>
                            <b
                              class={
                                (stats?.["median_%"] ?? 0) > 0
                                  ? "text-green-400"
                                  : (stats?.["median_%"] ?? 0) < 0
                                  ? "text-red-400"
                                  : ""
                              }
                            >
                              {stats?.["median_%"] ?? "—"}%
                            </b>
                          </div>
                          <div class="flex justify-between">
                            <span class="opacity-70">Win rate:</span>
                            <b class="text-blue-300">
                              {stats?.["win_rate_%"] ?? "—"}%
                            </b>
                          </div>
                          <div class="flex justify-between text-[10px] opacity-60">
                            <span>Avg up:</span>
                            <span class="text-green-400">
                              {stats?.["avg_up_%"] ?? "—"}%
                            </span>
                          </div>
                          <div class="flex justify-between text-[10px] opacity-60">
                            <span>Avg down:</span>
                            <span class="text-red-400">
                              {stats?.["avg_down_%"] ?? "—"}%
                            </span>
                          </div>
                        </div>
                      </Show>
                    </div>
                  );
                }}
              </For>
            </div>

            {/* Interpretation */}
            <Show when={data().windows?.["3d"]}>
              {(stats) => (
                <div class="mt-3 p-2 rounded-lg bg-blue-900/20 border border-blue-800/30">
                  <div class="text-[11px] opacity-80">
                    <b>Interpretation:</b>{" "}
                    {stats()["avg_%"] > 2 ? (
                      <span class="text-green-400">
                        Historically bullish — stock tends to rise after similar news
                      </span>
                    ) : stats()["avg_%"] < -2 ? (
                      <span class="text-red-400">
                        Historically bearish — stock tends to fall after similar news
                      </span>
                    ) : (
                      <span class="text-yellow-400">
                        Neutral pattern — mixed historical reactions
                      </span>
                    )}
                  </div>
                </div>
              )}
            </Show>

            {/* Disclaimer */}
            <div class="mt-3 pt-2 border-t border-white/10">
              <p class="text-[10px] opacity-50 text-center">
                ⚠️ Past performance does not guarantee future results. Educational
                only — not investment advice.
              </p>
            </div>
          </div>
        )}
      </Show>

      {/* Error State */}
      <Show when={bt.error}>
        <div class="py-4 text-center">
          <div class="text-red-400 text-sm mb-2">⚠️ Unable to load backtest data</div>
          <div class="text-xs opacity-60">
            {bt.error instanceof Error ? bt.error.message : "Unknown error"}
          </div>
        </div>
      </Show>
    </div>
  );
}

