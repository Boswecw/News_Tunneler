import { createStore } from 'solid-js/store'

export interface Article {
  id: number
  url: string
  title: string
  summary?: string
  source_name: string
  source_url: string
  source_type: string
  published_at: string
  ticker_guess?: string
  score?: number
}

export interface Settings {
  weight_catalyst: number
  weight_novelty: number
  weight_credibility: number
  weight_sentiment: number
  weight_liquidity: number
  min_alert_score: number
  poll_interval_sec: number
}

export interface Filters {
  q?: string
  minScore: number
  ticker?: string
  domain?: string
  since?: string
}

interface StoreState {
  articles: Article[]
  liveAlerts: Article[]
  settings: Settings | null
  filters: Filters
  darkMode: boolean
  isConnected: boolean
}

// Initialize dark mode from localStorage
const savedDarkMode = localStorage.getItem('darkMode') === 'true'
if (savedDarkMode) {
  document.documentElement.classList.add('dark')
}

const [store, setStore] = createStore<StoreState>({
  articles: [],
  liveAlerts: [],
  settings: null,
  filters: { minScore: 12 },
  darkMode: savedDarkMode,
  isConnected: false,
})

export const useStore = () => ({
  // State
  get articles() { return store.articles },
  get liveAlerts() { return store.liveAlerts },
  get settings() { return store.settings },
  get filters() { return store.filters },
  get darkMode() { return store.darkMode },
  get isConnected() { return store.isConnected },

  // Articles
  setArticles: (articles: Article[]) => {
    setStore('articles', articles)
  },
  addArticle: (article: Article) => {
    setStore('articles', (prev) => [article, ...prev].slice(0, 100))
  },

  // Live alerts
  addLiveAlert: (article: Article) => {
    setStore('liveAlerts', (prev) => [article, ...prev].slice(0, 50))
  },
  clearLiveAlerts: () => {
    setStore('liveAlerts', [])
  },

  // Settings
  setSettings: (settings: Settings) => {
    setStore('settings', settings)
  },

  // Filters
  setFilters: (filters: Partial<Filters>) => {
    setStore('filters', (prev) => ({ ...prev, ...filters }))
  },

  // UI
  toggleDarkMode: () => {
    const newDarkMode = !store.darkMode
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('darkMode', String(newDarkMode))
    setStore('darkMode', newDarkMode)
  },
  setIsConnected: (connected: boolean) => {
    setStore('isConnected', connected)
  },
})

