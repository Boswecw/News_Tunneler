import { onMount, createSignal, Show, Component, lazy } from 'solid-js'
import { Router } from '@solidjs/router'
import { useStore } from './lib/store'
import { getSettings, healthCheck } from './lib/api'
import { connectWebSocket, setStoreRef } from './lib/ws'
import Navigation from './components/Navigation'
import InstallPrompt from './components/InstallPrompt'

// Lazy load pages for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Sources = lazy(() => import('./pages/Sources'))
const Settings = lazy(() => import('./pages/Settings'))
const LiveCharts = lazy(() => import('./pages/LiveCharts'))
const Opportunities = lazy(() => import('./pages/Opportunities'))
const FAQ = lazy(() => import('./pages/FAQ'))

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
  {
    path: '/faq',
    component: FAQ,
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

      {/* PWA Install Prompt */}
      <InstallPrompt />
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

