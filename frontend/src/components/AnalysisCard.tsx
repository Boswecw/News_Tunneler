import { createResource, Show, For } from 'solid-js'
import { getSummary, getEvent } from '../lib/analysis'

interface AnalysisCardProps {
  ticker: string
  published: string
}

export default function AnalysisCard(props: AnalysisCardProps) {
  const [summary] = createResource(() => props.ticker, getSummary)
  const [eventData] = createResource(
    () => ({ t: props.ticker, d: props.published.split('T')[0] }),
    ({ t, d }) => getEvent(t, d)
  )

  const getFlagLabel = (flag: string): string => {
    const labels: Record<string, string> = {
      oversold_zone: '🔵 Oversold (RSI < 30) — bounces possible',
      overbought_zone: '🔴 Overbought (RSI > 70) — pullback risk',
      uptrend_intact: '📈 Uptrend intact (above SMA20 & SMA50)',
      downtrend_intact: '📉 Downtrend intact (below SMA20 & SMA50)',
      near_52w_high: '🎯 Near 52-week high — breakout watch',
      near_52w_low: '⚠️ Near 52-week low — support test',
      unusual_volume: '📊 Unusual volume (>50% above average)',
    }
    return labels[flag] || flag
  }

  const formatPercent = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  const formatNumber = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    return value.toFixed(2)
  }

  const formatPrice = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    return `$${value.toFixed(2)}`
  }

  const formatVolume = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return '—'
    if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
    if (value >= 1_000) return `${(value / 1_000).toFixed(2)}K`
    return value.toString()
  }

  return (
    <div class="rounded-2xl p-5 bg-gradient-to-br from-neutral-900/80 to-neutral-800/60 text-white border border-neutral-700/50 shadow-xl">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          📊 Market Analysis — {props.ticker}
        </h3>
        <Show when={summary()?.date}>
          <span class="text-xs text-neutral-400">
            As of {summary()!.date}
          </span>
        </Show>
      </div>

      <Show
        when={!summary.loading && summary()}
        fallback={
          <div class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
            <span class="ml-3 text-sm text-neutral-400">Loading market data...</span>
          </div>
        }
      >
        <div class="space-y-4">
          {/* Price & Volume */}
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-neutral-800/50 rounded-lg p-3">
              <div class="text-xs text-neutral-400 mb-1">Current Price</div>
              <div class="text-2xl font-bold text-blue-400">
                {formatPrice(summary()?.price)}
              </div>
            </div>
            <div class="bg-neutral-800/50 rounded-lg p-3">
              <div class="text-xs text-neutral-400 mb-1">Volume</div>
              <div class="text-2xl font-bold text-purple-400">
                {formatVolume(summary()?.volume)}
              </div>
              <Show when={summary()?.["volume_vs_avg_%"] !== null}>
                <div class="text-xs text-neutral-400 mt-1">
                  {formatPercent(summary()?.["volume_vs_avg_%"])} vs avg
                </div>
              </Show>
            </div>
          </div>

          {/* Technical Indicators */}
          <div class="bg-neutral-800/30 rounded-lg p-4">
            <div class="text-sm font-semibold text-neutral-300 mb-3">Technical Indicators</div>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span class="text-neutral-400">SMA(20):</span>
                <span class="ml-2 font-mono text-white">{formatPrice(summary()?.sma20)}</span>
              </div>
              <div>
                <span class="text-neutral-400">SMA(50):</span>
                <span class="ml-2 font-mono text-white">{formatPrice(summary()?.sma50)}</span>
              </div>
              <div>
                <span class="text-neutral-400">RSI(14):</span>
                <span
                  class="ml-2 font-mono font-bold"
                  classList={{
                    'text-green-400': summary()?.rsi14 !== null && summary()!.rsi14! < 30,
                    'text-red-400': summary()?.rsi14 !== null && summary()!.rsi14! > 70,
                    'text-white': summary()?.rsi14 !== null && summary()!.rsi14! >= 30 && summary()!.rsi14! <= 70,
                  }}
                >
                  {formatNumber(summary()?.rsi14)}
                </span>
              </div>
              <div>
                <span class="text-neutral-400">ATR(14):</span>
                <span class="ml-2 font-mono text-white">{formatPrice(summary()?.atr14)}</span>
              </div>
            </div>
          </div>

          {/* 52-Week Range */}
          <div class="bg-neutral-800/30 rounded-lg p-4">
            <div class="text-sm font-semibold text-neutral-300 mb-3">52-Week Range</div>
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span class="text-neutral-400">From High:</span>
                <span
                  class="ml-2 font-mono font-bold"
                  classList={{
                    'text-yellow-400': summary()?.["from_52w_high_%"] !== null && summary()!["from_52w_high_%"]! > -5,
                    'text-white': summary()?.["from_52w_high_%"] !== null && summary()!["from_52w_high_%"]! <= -5,
                  }}
                >
                  {formatPercent(summary()?.["from_52w_high_%"])}
                </span>
              </div>
              <div>
                <span class="text-neutral-400">From Low:</span>
                <span
                  class="ml-2 font-mono font-bold"
                  classList={{
                    'text-yellow-400': summary()?.["from_52w_low_%"] !== null && summary()!["from_52w_low_%"]! < 5,
                    'text-white': summary()?.["from_52w_low_%"] !== null && summary()!["from_52w_low_%"]! >= 5,
                  }}
                >
                  {formatPercent(summary()?.["from_52w_low_%"])}
                </span>
              </div>
            </div>
          </div>

          {/* Event Reaction */}
          <Show when={!eventData.loading && eventData()}>
            <div class="bg-gradient-to-r from-purple-900/30 to-blue-900/30 rounded-lg p-4 border border-purple-700/30">
              <div class="text-sm font-semibold text-neutral-300 mb-3">
                📈 Typical Reaction After News
              </div>
              <div class="grid grid-cols-3 gap-3 text-sm">
                <div class="text-center">
                  <div class="text-xs text-neutral-400 mb-1">1 Day</div>
                  <div
                    class="font-mono font-bold text-lg"
                    classList={{
                      'text-green-400': eventData()!['1d_%'] !== null && eventData()!['1d_%']! > 0,
                      'text-red-400': eventData()!['1d_%'] !== null && eventData()!['1d_%']! < 0,
                      'text-neutral-400': eventData()!['1d_%'] === null,
                    }}
                  >
                    {formatPercent(eventData()!['1d_%'])}
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-xs text-neutral-400 mb-1">3 Days</div>
                  <div
                    class="font-mono font-bold text-lg"
                    classList={{
                      'text-green-400': eventData()!['3d_%'] !== null && eventData()!['3d_%']! > 0,
                      'text-red-400': eventData()!['3d_%'] !== null && eventData()!['3d_%']! < 0,
                      'text-neutral-400': eventData()!['3d_%'] === null,
                    }}
                  >
                    {formatPercent(eventData()!['3d_%'])}
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-xs text-neutral-400 mb-1">5 Days</div>
                  <div
                    class="font-mono font-bold text-lg"
                    classList={{
                      'text-green-400': eventData()!['5d_%'] !== null && eventData()!['5d_%']! > 0,
                      'text-red-400': eventData()!['5d_%'] !== null && eventData()!['5d_%']! < 0,
                      'text-neutral-400': eventData()!['5d_%'] === null,
                    }}
                  >
                    {formatPercent(eventData()!['5d_%'])}
                  </div>
                </div>
              </div>
              <Show when={eventData()?.["gap_%"] !== null}>
                <div class="mt-3 pt-3 border-t border-purple-700/30 text-xs text-neutral-400">
                  Gap on news day: <span class="font-mono text-white">{formatPercent(eventData()?.["gap_%"])}</span>
                </div>
              </Show>
            </div>
          </Show>

          {/* Interpretation Flags */}
          <Show when={summary()?.flags && summary()!.flags.length > 0}>
            <div class="bg-neutral-800/30 rounded-lg p-4">
              <div class="text-sm font-semibold text-neutral-300 mb-3">💡 Key Signals</div>
              <div class="space-y-2">
                <For each={summary()!.flags}>
                  {(flag) => (
                    <div class="text-xs text-neutral-300 bg-neutral-700/30 rounded px-3 py-2">
                      {getFlagLabel(flag)}
                    </div>
                  )}
                </For>
              </div>
            </div>
          </Show>

          {/* Disclaimer */}
          <div class="text-[10px] text-neutral-500 pt-2 border-t border-neutral-700/30 space-y-1">
            <div class="text-center">
              ⚠️ Educational only — not investment advice. Data from {summary()?.date || 'market close'}.
            </div>
            <div class="text-center opacity-70">
              Using <b class="text-green-400">adjusted close prices</b> (includes splits & dividends).{' '}
              <span
                class="underline decoration-dotted cursor-help"
                title="Adjusted Close rewrites past prices to account for stock splits and cash dividends so charts reflect total return. Data from Yahoo Finance (free, no API key required)."
              >
                What's this?
              </span>
            </div>
          </div>
        </div>
      </Show>

      <Show when={summary.error}>
        <div class="bg-red-900/20 border border-red-700/50 rounded-lg p-4 text-sm text-red-300">
          <div class="font-semibold mb-1">⚠️ Failed to load market data</div>
          <div class="text-xs text-red-400">
            {summary.error instanceof Error ? summary.error.message : 'Unknown error'}
          </div>
        </div>
      </Show>
    </div>
  )
}

