import axios from 'axios'
import type { Article, Settings } from './store'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
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
    const response = await api.get('/health')
    return response.status === 200
  } catch {
    return false
  }
}

export default api

