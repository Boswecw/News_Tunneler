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
      <h3 class="text-lg font-semibold mb-4">Add New Source</h3>

      {error() && (
        <div class="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
          {error()}
        </div>
      )}

      {success() && (
        <div class="bg-green-100 dark:bg-green-900 border border-green-400 dark:border-green-700 text-green-700 dark:text-green-200 px-4 py-3 rounded mb-4">
          Source added successfully!
        </div>
      )}

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label class="label">Feed URL</label>
          <input
            type="url"
            class="input"
            placeholder="https://example.com/feed.xml"
            value={url()}
            onInput={(e) => setUrl(e.currentTarget.value)}
            required
          />
        </div>

        <div>
          <label class="label">Feed Name</label>
          <input
            type="text"
            class="input"
            placeholder="My News Feed"
            value={name()}
            onInput={(e) => setName(e.currentTarget.value)}
            required
          />
        </div>
      </div>

      <div class="mb-4">
        <label class="label">Feed Type</label>
        <select
          class="input"
          value={sourceType()}
          onChange={(e) => setSourceType(e.currentTarget.value)}
        >
          <option value="rss">RSS</option>
          <option value="atom">Atom</option>
          <option value="newsapi">NewsAPI</option>
        </select>
      </div>

      <button type="submit" class="btn btn-primary" disabled={isLoading()}>
        {isLoading() ? 'Adding...' : 'Add Source'}
      </button>
    </form>
  )
}

