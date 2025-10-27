import { createEffect, createSignal } from 'solid-js'
import { useStore } from '../lib/store'
import { getArticles } from '../lib/api'
import AlertTable from '../components/AlertTable'

export default function Alerts() {
  const store = useStore()
  const [isLoading, setIsLoading] = createSignal(true)
  const [searchQuery, setSearchQuery] = createSignal('')
  const [minScore, setMinScore] = createSignal(store.settings?.min_alert_score || 12)
  const [selectedTicker, setSelectedTicker] = createSignal('')

  const loadArticles = async () => {
    setIsLoading(true)
    try {
      const articles = await getArticles({
        q: searchQuery() || undefined,
        min_score: minScore(),
        ticker: selectedTicker() || undefined,
        limit: 200,
      })
      store.setArticles(articles)
    } catch (error) {
      console.error('Failed to load articles:', error)
    } finally {
      setIsLoading(false)
    }
  }

  createEffect(() => {
    loadArticles()
  })

  return (
    <div>
      <h1 class="text-3xl font-bold mb-8">Alerts</h1>

      <div class="card mb-6">
        <h2 class="text-lg font-semibold mb-4">Filters</h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="label">Search</label>
            <input
              type="text"
              class="input"
              placeholder="Search title or summary..."
              value={searchQuery()}
              onInput={(e) => setSearchQuery(e.currentTarget.value)}
            />
          </div>

          <div>
            <label class="label">Minimum Score</label>
            <div class="flex items-center space-x-2">
              <input
                type="range"
                min="0"
                max="25"
                step="1"
                value={minScore()}
                onChange={(e) => setMinScore(parseInt(e.currentTarget.value))}
                class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg"
              />
              <span class="text-lg font-bold text-blue-600 dark:text-blue-400 w-12">
                {minScore()}
              </span>
            </div>
          </div>

          <div>
            <label class="label">Ticker</label>
            <input
              type="text"
              class="input"
              placeholder="e.g., AAPL"
              value={selectedTicker()}
              onInput={(e) => setSelectedTicker(e.currentTarget.value.toUpperCase())}
            />
          </div>
        </div>

        <div class="mt-4 flex space-x-2">
          <button onClick={loadArticles} class="btn btn-primary">
            Apply Filters
          </button>
          <button
            onClick={() => {
              setSearchQuery('')
              setMinScore(store.settings?.min_alert_score || 12)
              setSelectedTicker('')
            }}
            class="btn btn-secondary"
          >
            Reset
          </button>
        </div>
      </div>

      <AlertTable articles={store.articles} isLoading={isLoading()} />
    </div>
  )
}

