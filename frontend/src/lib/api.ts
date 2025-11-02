import axios from 'axios'
import type { Article, Settings } from './store'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
})

// Articles
export const getArticles = async (params?: {
  q?: string
  min_score?: number
  ticker?: string
  domain?: string
  since?: string
  limit?: number
  offset?: number
}): Promise<Article[]> => {
  const response = await api.get('/api/articles', { params })
  return response.data
}

export const getArticle = async (id: number): Promise<Article> => {
  const response = await api.get(`/api/articles/${id}`)
  return response.data
}

// LLM Analysis
export interface LLMPlan {
  ticker: string
  sector: string
  catalyst_type: string
  stance: string
  thesis: string
  key_facts: string[]
  near_term_window_days: number
  confidence_0to1: number
  risks: string[]
  suggested_setups: Array<{
    style: string
    entry_hint: string
    invalidations: string
    hold_time_days: number
  }>
  simple_explanation?: string
  summary?: string
}

export interface ArticlePlan {
  article_id: number
  strategy_bucket: string | null
  strategy_risk: {
    max_position_pct: number
    stop_guideline: string
    review_in_days: number
    confidence: number
  } | null
  llm_plan: LLMPlan | null
  published_at: string | null
}

export const analyzeArticle = async (id: number): Promise<{ status: string; article_id: number }> => {
  const response = await api.post(`/api/articles/llm/analyze/${id}`)
  return response.data
}

export const fetchPlan = async (id: number): Promise<ArticlePlan> => {
  const response = await api.get(`/api/articles/${id}/plan`)
  return response.data
}

// Sources
export interface Source {
  id: number
  url: string
  name: string
  source_type: string
  enabled: boolean
  created_at: string
  last_fetched_at?: string
}

export const getSources = async (): Promise<Source[]> => {
  const response = await api.get('/api/sources')
  return response.data
}

export const createSource = async (data: {
  url: string
  name: string
  source_type?: string
}): Promise<Source> => {
  const response = await api.post('/api/sources', data)
  return response.data
}

export const updateSource = async (
  id: number,
  data: { enabled?: boolean }
): Promise<Source> => {
  const response = await api.patch(`/api/sources/${id}`, data)
  return response.data
}

export const deleteSource = async (id: number): Promise<void> => {
  await api.delete(`/api/sources/${id}`)
}

// Settings
export const getSettings = async (): Promise<Settings> => {
  const response = await api.get('/api/settings')
  return response.data
}

export const updateSettings = async (data: Partial<Settings>): Promise<Settings> => {
  const response = await api.patch('/api/settings', data)
  return response.data
}

// Health
export const healthCheck = async (): Promise<boolean> => {
  try {
    console.log('Health check: Calling /health endpoint...')
    const response = await api.get('/health')
    console.log('Health check: Response received', response.status)
    return response.status === 200
  } catch (error) {
    console.error('Health check: Failed', error)
    return false
  }
}

// Intraday Bounds Prediction
export interface BoundsPoint {
  ts: number  // milliseconds
  lower: number
  upper: number
  mid: number
  current_price?: number
}

export interface BoundsResponse {
  ticker: string
  interval: string
  horizon: number
  model_version: string
  points: BoundsPoint[]
  metadata: Record<string, any>
}

export const getIntradayBounds = async (
  ticker: string,
  interval: string = '1m',
  horizon: number = 5,
  limit: number = 200
): Promise<BoundsResponse> => {
  const response = await api.get(`/predict/intraday-bounds/${ticker}`, {
    params: { interval, horizon, limit },
    timeout: 30000, // 30 second timeout for ML predictions
  })
  return response.data
}

export const getIntradayBoundsFromDB = async (
  ticker: string,
  interval: string = '1m',
  horizon: number = 5,
  limit: number = 200
): Promise<BoundsResponse> => {
  const response = await api.get(`/predict/intraday-bounds/db/${ticker}`, {
    params: { interval, horizon, limit },
  })
  return response.data
}

export default api

