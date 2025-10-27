import { createEffect, createSignal } from 'solid-js'
import { Router, Route } from '@solidjs/router'
import { useStore } from './lib/store'
import { getSettings, healthCheck } from './lib/api'
import { connectWebSocket } from './lib/ws'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Sources from './pages/Sources'
import Settings from './pages/Settings'
import Navigation from './components/Navigation'

export default function App() {
  const store = useStore()
  const [isLoading, setIsLoading] = createSignal(true)
  const [error, setError] = createSignal<string | null>(null)

  createEffect(async () => {
    try {
      // Check backend health
      const healthy = await healthCheck()
      if (!healthy) {
        setError('Backend is not responding')
        setIsLoading(false)
        return
      }

      // Load settings
      const settings = await getSettings()
      store.setSettings(settings)

      // Connect WebSocket
      connectWebSocket()

      setIsLoading(false)
    } catch (err) {
      console.error('Failed to initialize app:', err)
      setError('Failed to connect to backend')
      setIsLoading(false)
    }
  })

  return (
    <div class={store.darkMode ? 'dark' : ''}>
      <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Router>
          <Navigation />
          <main class="container mx-auto px-4 py-8">
            {isLoading() && (
              <div class="flex items-center justify-center h-64">
                <div class="text-center">
                  <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p class="text-gray-600 dark:text-gray-400">Loading...</p>
                </div>
              </div>
            )}
            {error() && (
              <div class="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
                <p class="font-bold">Error</p>
                <p>{error()}</p>
              </div>
            )}
            {!isLoading() && !error() && (
              <>
                <Route path="/" component={Dashboard} />
                <Route path="/alerts" component={Alerts} />
                <Route path="/sources" component={Sources} />
                <Route path="/settings" component={Settings} />
              </>
            )}
          </main>
        </Router>
      </div>
    </div>
  )
}

