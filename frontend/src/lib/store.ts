import { create } from 'zustand'

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

interface Store {
  // Articles
  articles: Article[]
  setArticles: (articles: Article[]) => void
  addArticle: (article: Article) => void

  // Live alerts
  liveAlerts: Article[]
  addLiveAlert: (article: Article) => void
  clearLiveAlerts: () => void

  // Settings
  settings: Settings | null
  setSettings: (settings: Settings) => void

  // Filters
  filters: Filters
  setFilters: (filters: Partial<Filters>) => void

  // UI
  darkMode: boolean
  toggleDarkMode: () => void
  isConnected: boolean
  setIsConnected: (connected: boolean) => void
}

export const useStore = create<Store>((set) => ({
  articles: [],
  setArticles: (articles) => set({ articles }),
  addArticle: (article) =>
    set((state) => ({
      articles: [article, ...state.articles].slice(0, 100),
    })),

  liveAlerts: [],
  addLiveAlert: (article) =>
    set((state) => ({
      liveAlerts: [article, ...state.liveAlerts].slice(0, 50),
    })),
  clearLiveAlerts: () => set({ liveAlerts: [] }),

  settings: null,
  setSettings: (settings) => set({ settings }),

  filters: { minScore: 12 },
  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
    })),

  darkMode: false,
  toggleDarkMode: () =>
    set((state) => {
      const newDarkMode = !state.darkMode
      if (newDarkMode) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      localStorage.setItem('darkMode', String(newDarkMode))
      return { darkMode: newDarkMode }
    }),

  isConnected: false,
  setIsConnected: (connected) => set({ isConnected: connected }),
}))

// Initialize dark mode from localStorage
const savedDarkMode = localStorage.getItem('darkMode') === 'true'
if (savedDarkMode) {
  document.documentElement.classList.add('dark')
  useStore.setState({ darkMode: true })
}

