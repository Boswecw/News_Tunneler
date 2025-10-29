import { onMount, createSignal, Show, Component } from 'solid-js'
import { Router } from '@solidjs/router'
import { useStore } from './lib/store'
import { getSettings, healthCheck } from './lib/api'
import { connectWebSocket, setStoreRef } from './lib/ws'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import Sources from './pages/Sources'
import Settings from './pages/Settings'
import LiveCharts from './pages/LiveCharts'
import Opportunities from './pages/Opportunities'
import Navigation from './components/Navigation'

const routes = [
  {
    path: '/',
    component: Dashboard,
  },
  {
    path: '/alerts',
    component: Alerts,
  },
  {
    path: '/opportunities',
    component: Opportunities,
  },
  {
    path: '/sources',
    component: Sources,
  },
  {
    path: '/settings',
    component: Settings,
  },
  {
    path: '/live-charts',
    component: LiveCharts,
  },
]

function AppContent(props: { children?: any }) {
  const store = useStore()
  const [isLoading, setIsLoading] = createSignal(true)
  const [error, setError] = createSignal<string | null>(null)

  onMount(async () => {
    try {
      // Set store reference for WebSocket
      setStoreRef(store)

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
        <Navigation />
        <main class="container mx-auto px-4 py-8">
          <Show when={isLoading()}>
            <div class="flex items-center justify-center h-64">
              <div class="text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-gray-600 dark:text-gray-400">Loading...</p>
              </div>
            </div>
          </Show>
          <Show when={error()}>
            <div class="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded mb-4">
              <p class="font-bold">Error</p>
              <p>{error()}</p>
            </div>
          </Show>
          <Show when={!isLoading() && !error()}>
            {props.children}
          </Show>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <Router root={AppContent}>
      {routes}
    </Router>
  )
}

