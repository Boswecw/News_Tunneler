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
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="card">
        <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Last 24h Alerts</div>
        <div class="text-4xl font-bold text-blue-600 dark:text-blue-400 mt-2">{stats().last24hAlerts}</div>
      </div>

      <div class="card">
        <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Average Score</div>
        <div class="text-4xl font-bold text-purple-600 dark:text-purple-400 mt-2">{stats().avgScore}</div>
      </div>

      <div class="card">
        <div class="text-gray-600 dark:text-gray-400 text-sm font-medium">Top Tickers</div>
        <div class="flex flex-wrap gap-2 mt-2">
          {stats().topTickers.map((ticker) => (
            <span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full text-sm font-medium">
              {ticker}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}