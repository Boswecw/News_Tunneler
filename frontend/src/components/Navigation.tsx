import { A } from '@solidjs/router'
import { useStore } from '../lib/store'

export default function Navigation() {
  const store = useStore()

  return (
    <nav class="bg-white dark:bg-gray-800 shadow-md">
      <div class="container mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-8">
            <A href="/" class="text-2xl font-bold text-blue-600 dark:text-blue-400">
              📰 News Tunneler
            </A>
            <div class="hidden md:flex space-x-6">
              <A
                href="/"
                class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Dashboard
              </A>
              <A
                href="/alerts"
                class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Alerts
              </A>
              <A
                href="/sources"
                class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Sources
              </A>
              <A
                href="/settings"
                class="text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                Settings
              </A>
            </div>
          </div>

          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <div
                class={`w-3 h-3 rounded-full ${
                  store.isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              ></div>
              <span class="text-sm text-gray-600 dark:text-gray-400">
                {store.isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

            <button
              onClick={() => store.toggleDarkMode()}
              class="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              title="Toggle dark mode"
            >
              {store.darkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}

