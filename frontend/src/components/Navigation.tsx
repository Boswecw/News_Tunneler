import { A } from '@solidjs/router'
import { useStore } from '../lib/store'

export default function Navigation() {
  const store = useStore()

  return (
    <nav class="nav-glass sticky top-0 z-50">
      <div class="flex items-center justify-between py-4 pr-4">
        <div class="flex items-center space-x-6">
          <A href="/" class="flex items-center group ml-3">
            <div class="relative">
              <div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl blur-lg opacity-50 group-hover:opacity-75 transition-opacity"></div>
              <img
                src="/logo.webp"
                alt="News Tunneler Logo"
                class="h-20 w-20 rounded-2xl relative z-10 ring-2 ring-white/50 dark:ring-white/20 group-hover:ring-white/70 dark:group-hover:ring-white/30 transition-all group-hover:scale-105"
              />
            </div>
          </A>
          <div class="hidden md:flex space-x-1">
            <A
              href="/"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Dashboard
            </A>
            <A
              href="/opportunities"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Opportunities
            </A>
            <A
              href="/live-charts"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Live Charts
            </A>
            <A
              href="/alerts"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Alerts
            </A>
            <A
              href="/sources"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Sources
            </A>
            <A
              href="/settings"
              class="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white/40 dark:hover:bg-white/10 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-200 backdrop-blur-sm"
              activeClass="bg-white/60 dark:bg-white/10 text-blue-600 dark:text-blue-400 shadow-glass"
            >
              Settings
            </A>
          </div>
        </div>

        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2 px-3 py-2 rounded-xl bg-white/40 dark:bg-white/5 backdrop-blur-md border border-white/30 dark:border-white/10">
              <div
                class={store.isConnected ? 'status-online' : 'status-offline'}
              ></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">
                {store.isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>

          <button
            onClick={() => store.toggleDarkMode()}
            class="p-2.5 rounded-xl bg-white/40 dark:bg-white/5 backdrop-blur-md border border-white/30 dark:border-white/10 text-gray-800 dark:text-gray-200 hover:bg-white/60 dark:hover:bg-white/10 hover:scale-110 transition-all duration-200 shadow-glass"
            title="Toggle dark mode"
          >
            <span class="text-lg">{store.darkMode ? '☀️' : '🌙'}</span>
          </button>
        </div>
      </div>
    </nav>
  )
}

