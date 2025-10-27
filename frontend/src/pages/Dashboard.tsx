import { createEffect, createSignal, For } from 'solid-js'
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
    <div>
      <h1 class="text-3xl font-bold mb-8">Dashboard</h1>

      <Kpis />

      <div class="card">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold">Live Alerts</h2>
          <span class="text-sm text-gray-600 dark:text-gray-400">
            {store.liveAlerts.length} new alerts
          </span>
        </div>

        {store.liveAlerts.length === 0 && !isLoading() && (
          <div class="text-center py-8 text-gray-600 dark:text-gray-400">
            No live alerts yet. Waiting for high-scoring articles...
          </div>
        )}

        {store.liveAlerts.length > 0 && (
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead class="bg-gray-100 dark:bg-gray-700">
                <tr>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Title
                  </th>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Score
                  </th>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Ticker
                  </th>
                  <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Source
                  </th>
                </tr>
              </thead>
              <tbody>
                <For each={store.liveAlerts.slice(0, 10)}>
                  {(alert) => (
                    <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td class="px-4 py-3">
                        <a
                          href={alert.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="text-blue-600 dark:text-blue-400 hover:underline font-medium"
                        >
                          {alert.title}
                        </a>
                      </td>
                      <td class="px-4 py-3 font-bold text-green-600 dark:text-green-400">
                        {alert.score?.toFixed(1)}
                      </td>
                      <td class="px-4 py-3">
                        {alert.ticker_guess && (
                          <span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-sm font-medium">
                            {alert.ticker_guess}
                          </span>
                        )}
                      </td>
                      <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {alert.source_name}
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

