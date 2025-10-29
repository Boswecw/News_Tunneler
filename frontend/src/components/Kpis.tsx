import { createMemo } from 'solid-js'
import { useStore } from '../lib/store'

export default function Kpis() {
  const store = useStore()

  const stats = createMemo(() => {
    const now = new Date()
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000)

    const last24hAlerts = store.articles.filter(
      (a) => new Date(a.published_at) > oneDayAgo && (a.score || 0) >= (store.settings?.min_alert_score || 12)
    )

    const avgScore =
      last24hAlerts.length > 0
        ? (last24hAlerts.reduce((sum, a) => sum + (a.score || 0), 0) / last24hAlerts.length).toFixed(1)
        : '0'

    const topTickers = new Map<string, number>()
    store.articles.forEach((a) => {
      if (a.ticker_guess) {
        topTickers.set(a.ticker_guess, (topTickers.get(a.ticker_guess) || 0) + 1)
      }
    })

    const topTickersList = Array.from(topTickers.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([ticker]) => ticker)

    return {
      last24hAlerts: last24hAlerts.length,
      avgScore,
      topTickers: topTickersList,
    }
  })

  return (
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 animate-fade-in">
      {/* Last 24h Alerts Card */}
      <div class="card hover-lift group">
        <div class="flex items-center justify-between mb-3">
          <div class="text-gray-600 dark:text-gray-400 text-sm font-semibold uppercase tracking-wide">
            Last 24h Alerts
          </div>
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg shadow-blue-500/30 group-hover:shadow-blue-500/50 transition-all">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
          </div>
        </div>
        <div class="text-5xl font-bold text-gradient-primary mt-2 mb-1">
          {stats().last24hAlerts}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">
          High-scoring articles
        </div>
      </div>

      {/* Average Score Card */}
      <div class="card hover-lift group">
        <div class="flex items-center justify-between mb-3">
          <div class="text-gray-600 dark:text-gray-400 text-sm font-semibold uppercase tracking-wide">
            Average Score
          </div>
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/30 group-hover:shadow-purple-500/50 transition-all">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
        <div class="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-500 to-purple-700 mt-2 mb-1">
          {stats().avgScore}
        </div>
        <div class="text-xs text-gray-500 dark:text-gray-400 font-medium">
          Quality metric
        </div>
      </div>

      {/* Top Tickers Card */}
      <div class="card hover-lift group">
        <div class="flex items-center justify-between mb-3">
          <div class="text-gray-600 dark:text-gray-400 text-sm font-semibold uppercase tracking-wide">
            Top Tickers
          </div>
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:shadow-green-500/50 transition-all">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
        </div>
        <div class="flex flex-wrap gap-2 mt-3">
          {stats().topTickers.length > 0 ? (
            stats().topTickers.map((ticker) => (
              <span class="badge-primary hover:scale-105 transition-transform cursor-default">
                {ticker}
              </span>
            ))
          ) : (
            <span class="text-sm text-gray-500 dark:text-gray-400 italic">
              No tickers yet
            </span>
          )}
        </div>
      </div>
    </div>
  )
}