import { createEffect, createSignal, For } from 'solid-js'
import { formatDistanceToNow } from 'date-fns'
import { useStore } from '../lib/store'
import { getArticles } from '../lib/api'
import Kpis from '../components/Kpis'
import AlertRow from '../components/AlertRow'

export default function Dashboard() {
  const store = useStore()
  const [isLoading, setIsLoading] = createSignal(true)

  createEffect(async () => {
    try {
      const articles = await getArticles({ limit: 50, min_score: store.settings?.min_alert_score || 12 })
      store.setArticles(articles)
    } catch (error) {
      console.error('Failed to load articles:', error)
    } finally {
      setIsLoading(false)
    }
  })

  return (
    <div class="animate-fade-in">
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-gradient mb-2">Dashboard</h1>
        <p class="text-gray-600 dark:text-gray-400">Real-time market intelligence and alerts</p>
      </div>

      <Kpis />

      <div class="card">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-red-500/30">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Live Alerts</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">Real-time high-scoring articles</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <div class="status-online"></div>
            <span class="badge-success text-xs font-bold">
              {store.liveAlerts.length} new
            </span>
          </div>
        </div>

        {store.liveAlerts.length === 0 && !isLoading() && (
          <div class="text-center py-16">
            <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <p class="text-gray-600 dark:text-gray-400 font-medium mb-1">No live alerts yet</p>
            <p class="text-sm text-gray-500 dark:text-gray-500">Waiting for high-scoring articles...</p>
          </div>
        )}

        {store.liveAlerts.length > 0 && (
          <div class="overflow-x-auto scrollbar-thin">
            <table class="w-full">
              <thead class="bg-white/40 dark:bg-white/5 backdrop-blur-md">
                <tr>
                  <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Title
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Score
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Ticker
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Source
                  </th>
                  <th class="px-4 py-4 text-left text-xs font-bold uppercase tracking-wider text-gray-700 dark:text-gray-300">
                    Published
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={store.liveAlerts.slice(0, 10)}>
                  {(alert) => (
                    <tr class="border-b border-white/10 dark:border-white/5 hover:bg-white/40 dark:hover:bg-white/5 transition-all duration-200 group">
                      <td class="px-4 py-4">
                        <a
                          href={alert.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold group-hover:underline transition-all"
                        >
                          {alert.title}
                        </a>
                      </td>
                      <td class="px-4 py-4">
                        <div class="flex items-center gap-1">
                          <span class="text-lg font-bold text-green-600 dark:text-green-400">
                            {alert.score?.toFixed(1)}
                          </span>
                          {(alert.score || 0) >= 18 && <span class="text-xs">🔥</span>}
                        </div>
                      </td>
                      <td class="px-4 py-4">
                        {alert.ticker_guess && (
                          <span class="badge-primary text-xs font-bold">
                            {alert.ticker_guess}
                          </span>
                        )}
                      </td>
                      <td class="px-4 py-4">
                        <span class="badge-glass text-xs">
                          {alert.source_name}
                        </span>
                      </td>
                      <td class="px-4 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {formatDistanceToNow(new Date(alert.published_at), { addSuffix: true })}
                      </td>
                    </tr>
                  )}
                </For>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

