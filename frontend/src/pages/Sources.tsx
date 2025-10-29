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
    <div class="animate-fade-in">
      <div class="mb-8">
        <h1 class="text-4xl font-bold text-gradient mb-2">News Sources</h1>
        <p class="text-gray-600 dark:text-gray-400">Manage RSS feeds and data sources</p>
      </div>

      <SourceForm onSuccess={loadSources} />

      <div class="card">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-lg shadow-green-500/30">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Active Sources</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">{sources().length} configured</p>
          </div>
        </div>

        {isLoading() && (
          <div class="flex flex-col items-center justify-center py-12">
            <div class="spinner h-12 w-12 mb-4"></div>
            <p class="text-gray-600 dark:text-gray-400 font-medium">Loading sources...</p>
          </div>
        )}

        {!isLoading() && sources().length === 0 && (
          <div class="text-center py-12">
            <div class="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-700 flex items-center justify-center">
              <svg class="w-10 h-10 text-gray-400 dark:text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p class="text-gray-600 dark:text-gray-400 font-medium mb-1">No sources configured yet</p>
            <p class="text-sm text-gray-500 dark:text-gray-500">Add one using the form above!</p>
          </div>
        )}

        {!isLoading() && sources().length > 0 && (
          <div class="space-y-3">
            <For each={sources()}>
              {(source) => (
                <div class="group flex items-center justify-between p-5 bg-white/40 dark:bg-white/5 backdrop-blur-md rounded-2xl border border-white/30 dark:border-white/10 hover:bg-white/60 dark:hover:bg-white/10 hover:shadow-glass transition-all duration-200">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <div class={source.enabled ? 'status-online' : 'status-offline'}></div>
                      <h3 class="font-bold text-gray-900 dark:text-white">
                        {source.name}
                      </h3>
                    </div>
                    <p class="text-sm text-gray-600 dark:text-gray-400 truncate mb-2">
                      {source.url}
                    </p>
                    <div class="flex items-center space-x-2">
                      <span class="badge-primary text-xs">
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
                      class={`px-4 py-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
                        source.enabled
                          ? 'btn-success'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
                      }`}
                    >
                      {source.enabled ? '✓ Enabled' : '○ Disabled'}
                    </button>
                    <button
                      onClick={() => handleDelete(source.id)}
                      class="btn-danger text-sm"
                    >
                      🗑 Delete
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

