import { createSignal } from 'solid-js'
import { createSource } from '../lib/api'

interface SourceFormProps {
  onSuccess?: () => void
}

export default function SourceForm(props: SourceFormProps) {
  const [url, setUrl] = createSignal('')
  const [name, setName] = createSignal('')
  const [sourceType, setSourceType] = createSignal('rss')
  const [isLoading, setIsLoading] = createSignal(false)
  const [error, setError] = createSignal<string | null>(null)
  const [success, setSuccess] = createSignal(false)

  const handleSubmit = async (e: Event) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)

    if (!url() || !name()) {
      setError('Please fill in all fields')
      return
    }

    setIsLoading(true)
    try {
      await createSource({
        url: url(),
        name: name(),
        source_type: sourceType(),
      })
      setSuccess(true)
      setUrl('')
      setName('')
      setSourceType('rss')
      props.onSuccess?.()
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create source')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} class="card mb-6">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/30">
          <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </div>
        <div>
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">Add New Source</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400">Configure a new RSS feed or data source</p>
        </div>
      </div>

      {error() && (
        <div class="bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/20 dark:to-pink-900/20 border-l-4 border-red-500 rounded-r-xl p-4 mb-4 shadow-glass backdrop-blur-sm animate-slide-down">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-red-500 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <p class="text-sm font-medium text-red-800 dark:text-red-200">{error()}</p>
          </div>
        </div>
      )}

      {success() && (
        <div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-l-4 border-green-500 rounded-r-xl p-4 mb-4 shadow-glass backdrop-blur-sm animate-slide-down">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center flex-shrink-0">
              <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p class="text-sm font-medium text-green-800 dark:text-green-200">Source added successfully!</p>
          </div>
        </div>
      )}

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div>
          <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            🔗 Feed URL
          </label>
          <input
            type="url"
            class="input-glass"
            placeholder="https://example.com/feed.xml"
            value={url()}
            onInput={(e) => setUrl(e.currentTarget.value)}
            required
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
            📰 Feed Name
          </label>
          <input
            type="text"
            class="input-glass"
            placeholder="My News Feed"
            value={name()}
            onInput={(e) => setName(e.currentTarget.value)}
            required
          />
        </div>
      </div>

      <div class="mb-6">
        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
          ⚙️ Feed Type
        </label>
        <select
          class="input-glass"
          value={sourceType()}
          onChange={(e) => setSourceType(e.currentTarget.value)}
        >
          <option value="rss">RSS</option>
          <option value="atom">Atom</option>
          <option value="newsapi">NewsAPI</option>
        </select>
      </div>

      <button type="submit" class="btn-primary" disabled={isLoading()}>
        {isLoading() ? (
          <span class="flex items-center gap-2">
            <div class="spinner h-4 w-4"></div>
            Adding...
          </span>
        ) : (
          '+ Add Source'
        )}
      </button>
    </form>
  )
}

