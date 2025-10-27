import { createEffect, createSignal, For } from 'solid-js'
import { getSources, deleteSource, updateSource } from '../lib/api'
import SourceForm from '../components/SourceForm'
import type { Source } from '../lib/api'

export default function Sources() {
  const [sources, setSources] = createSignal<Source[]>([])
  const [isLoading, setIsLoading] = createSignal(true)

  const loadSources = async () => {
    setIsLoading(true)
    try {
      const data = await getSources()
      setSources(data)
    } catch (error) {
      console.error('Failed to load sources:', error)
    } finally {
      setIsLoading(false)
    }
  }

  createEffect(() => {
    loadSources()
  })

  const handleDelete = async (id: number) => {
    if (confirm('Are you sure you want to delete this source?')) {
      try {
        await deleteSource(id)
        setSources(sources().filter((s) => s.id !== id))
      } catch (error) {
        console.error('Failed to delete source:', error)
      }
    }
  }

  const handleToggle = async (id: number, enabled: boolean) => {
    try {
      await updateSource(id, { enabled: !enabled })
      setSources(
        sources().map((s) => (s.id === id ? { ...s, enabled: !enabled } : s))
      )
    } catch (error) {
      console.error('Failed to update source:', error)
    }
  }

  return (
    <div>
      <h1 class="text-3xl font-bold mb-8">News Sources</h1>

      <SourceForm onSuccess={loadSources} />

      <div class="card">
        <h2 class="text-lg font-semibold mb-4">Active Sources</h2>

        {isLoading() && (
          <div class="text-center py-8 text-gray-600 dark:text-gray-400">
            Loading sources...
          </div>
        )}

        {!isLoading() && sources().length === 0 && (
          <div class="text-center py-8 text-gray-600 dark:text-gray-400">
            No sources configured yet. Add one above!
          </div>
        )}

        {!isLoading() && sources().length > 0 && (
          <div class="space-y-3">
            <For each={sources()}>
              {(source) => (
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div class="flex-1">
                    <h3 class="font-semibold text-gray-900 dark:text-white">
                      {source.name}
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                      {source.url}
                    </p>
                    <div class="flex items-center space-x-2 mt-2">
                      <span class="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs font-medium">
                        {source.source_type.toUpperCase()}
                      </span>
                      {source.last_fetched_at && (
                        <span class="text-xs text-gray-500 dark:text-gray-400">
                          Last fetched: {new Date(source.last_fetched_at).toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleToggle(source.id, source.enabled)}
                      class={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                        source.enabled
                          ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-800'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      {source.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                    <button
                      onClick={() => handleDelete(source.id)}
                      class="btn btn-danger text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}
            </For>
          </div>
        )}
      </div>
    </div>
  )
}

