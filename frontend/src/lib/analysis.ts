/**
 * API client for price analysis and technical indicators
 */

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export interface PriceSummary {
  ticker: string
  date: string | null
  price: number | null
  open: number | null
  high: number | null
  low: number | null
  volume: number | null
  sma20: number | null
  sma50: number | null
  rsi14: number | null
  atr14: number | null
  "from_52w_high_%": number | null
  "from_52w_low_%": number | null
  "volume_vs_avg_%": number | null
  flags: string[]
}

export interface EventReaction {
  ticker: string
  event_date: string
  "gap_%": number | null
  "1d_%": number | null
  "3d_%": number | null
  "5d_%": number | null
}

/**
 * Fetch price summary with technical indicators for a ticker
 */
export async function getSummary(ticker: string): Promise<PriceSummary> {
  const response = await fetch(`${BASE}/api/analysis/summary/${ticker}`)
  
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to fetch summary for ${ticker}: ${error}`)
  }
  
  return response.json()
}

/**
 * Fetch event reaction (forward returns) for a ticker on a specific date
 */
export async function getEvent(ticker: string, date: string): Promise<EventReaction> {
  const response = await fetch(`${BASE}/api/analysis/event/${ticker}?event_date=${date}`)
  
  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Failed to fetch event reaction for ${ticker}: ${error}`)
  }
  
  return response.json()
}

