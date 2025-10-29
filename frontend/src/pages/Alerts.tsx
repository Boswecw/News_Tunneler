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
    <div class="animate-fade-in">
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-gradient mb-2">Alerts</h1>
        <p class="text-gray-600 dark:text-gray-400">Search and filter high-scoring articles</p>
      </div>

      <div class="card mb-6">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Filters</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">Refine your search criteria</p>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              🔍 Search
            </label>
            <input
              type="text"
              class="input-glass"
              placeholder="Search title or summary..."
              value={searchQuery()}
              onInput={(e) => setSearchQuery(e.currentTarget.value)}
            />
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              📊 Minimum Score
            </label>
            <div class="flex items-center space-x-3">
              <input
                type="range"
                min="0"
                max="25"
                step="1"
                value={minScore()}
                onChange={(e) => setMinScore(parseInt(e.currentTarget.value))}
                class="flex-1 h-2 bg-gradient-to-r from-blue-200 to-purple-200 dark:from-blue-900 dark:to-purple-900 rounded-full appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, rgb(59, 130, 246) 0%, rgb(168, 85, 247) ${(minScore() / 25) * 100}%, rgb(229, 231, 235) ${(minScore() / 25) * 100}%, rgb(229, 231, 235) 100%)`
                }}
              />
              <div class="w-14 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg">
                <span class="text-lg font-bold text-white">
                  {minScore()}
                </span>
              </div>
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              📈 Ticker
            </label>
            <input
              type="text"
              class="input-glass"
              placeholder="e.g., AAPL"
              value={selectedTicker()}
              onInput={(e) => setSelectedTicker(e.currentTarget.value.toUpperCase())}
            />
          </div>
        </div>

        <div class="mt-6 flex space-x-3">
          <button onClick={loadArticles} class="btn-primary">
            ✓ Apply Filters
          </button>
          <button
            onClick={() => {
              setSearchQuery('')
              setMinScore(store.settings?.min_alert_score || 12)
              setSelectedTicker('')
            }}
            class="btn-secondary"
          >
            ↺ Reset
          </button>
        </div>
      </div>

      <AlertTable articles={store.articles} isLoading={isLoading()} />
    </div>
  )
}

