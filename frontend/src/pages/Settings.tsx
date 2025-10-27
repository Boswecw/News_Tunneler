import { createSignal, Show } from 'solid-js'
import { useStore } from '../lib/store'
import { updateSettings } from '../lib/api'
import WeightSliders from '../components/WeightSliders'

export default function Settings() {
  const store = useStore()
  const [isSaving, setIsSaving] = createSignal(false)
  const [message, setMessage] = createSignal<{ type: 'success' | 'error'; text: string } | null>(null)
  const [minAlertScore, setMinAlertScore] = createSignal(store.settings?.min_alert_score || 12)
  const [pollInterval, setPollInterval] = createSignal(store.settings?.poll_interval_sec || 900)

  const handleSave = async () => {
    setIsSaving(true)
    setMessage(null)

    try {
      const updated = await updateSettings({
        weight_catalyst: store.settings?.weight_catalyst || 1,
        weight_novelty: store.settings?.weight_novelty || 1,
        weight_credibility: store.settings?.weight_credibility || 1,
        weight_sentiment: store.settings?.weight_sentiment || 1,
        weight_liquidity: store.settings?.weight_liquidity || 1,
        min_alert_score: minAlertScore(),
        poll_interval_sec: pollInterval(),
      })

      store.setSettings(updated)
      setMessage({ type: 'success', text: 'Settings saved successfully!' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error: any) {
      setMessage({
        type: 'error',
        text: error.response?.data?.detail || 'Failed to save settings',
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleWeightChange = (key: string, value: number) => {
    if (store.settings) {
      store.setSettings({
        ...store.settings,
        [key]: value,
      })
    }
  }

  return (
    <div>
      <h1 class="text-3xl font-bold mb-8">Settings</h1>

      <Show when={message()}>
        {(msg) => (
          <div
            class={`mb-6 px-4 py-3 rounded border ${
              msg().type === 'success'
                ? 'bg-green-100 dark:bg-green-900 border-green-400 dark:border-green-700 text-green-700 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900 border-red-400 dark:border-red-700 text-red-700 dark:text-red-200'
            }`}
          >
            {msg().text}
          </div>
        )}
      </Show>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
          <div class="card mb-6">
            <h2 class="text-lg font-semibold mb-6">Scoring Weights</h2>
            <Show when={store.settings}>
              {(settings) => (
                <WeightSliders settings={settings()} onChange={handleWeightChange} />
              )}
            </Show>
          </div>

          <div class="card">
            <h2 class="text-lg font-semibold mb-4">Alert Threshold</h2>
            <div class="mb-4">
              <label class="label">Minimum Alert Score</label>
              <div class="flex items-center space-x-4">
                <input
                  type="range"
                  min="0"
                  max="25"
                  step="1"
                  value={minAlertScore()}
                  onChange={(e) => setMinAlertScore(parseInt(e.currentTarget.value))}
                  class="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg"
                />
                <span class="text-2xl font-bold text-blue-600 dark:text-blue-400 w-12">
                  {minAlertScore()}
                </span>
              </div>
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Articles with scores below this threshold won't trigger alerts
              </p>
            </div>
          </div>
        </div>

        <div>
          <div class="card">
            <h2 class="text-lg font-semibold mb-4">Polling</h2>

            <div class="mb-4">
              <label class="label">Poll Interval (seconds)</label>
              <input
                type="number"
                min="60"
                max="3600"
                step="60"
                value={pollInterval()}
                onChange={(e) => setPollInterval(parseInt(e.currentTarget.value))}
                class="input"
              />
              <p class="text-sm text-gray-600 dark:text-gray-400 mt-2">
                How often to check feeds for new articles
              </p>
            </div>

            <div class="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded p-3 mb-4">
              <p class="text-sm text-blue-800 dark:text-blue-200">
                <strong>Current interval:</strong> {Math.round(pollInterval() / 60)} minutes
              </p>
            </div>

            <button
              onClick={handleSave}
              disabled={isSaving()}
              class="btn btn-primary w-full"
            >
              {isSaving() ? 'Saving...' : 'Save Settings'}
            </button>
          </div>

          <div class="card mt-6">
            <h2 class="text-lg font-semibold mb-4">Info</h2>
            <div class="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <p>
                <strong>Scoring Formula:</strong>
              </p>
              <p class="text-xs">
                Total = (Catalyst × w_catalyst) + (Novelty × w_novelty) + (Credibility × w_credibility) + (Sentiment × w_sentiment) + (Liquidity × w_liquidity)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

