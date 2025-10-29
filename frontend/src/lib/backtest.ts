/**
 * Backtest API client for analyzing historical stock reactions to news events.
 */

const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export interface BacktestWindowStats {
  count: number;
  "avg_%": number;
  "median_%": number;
  "win_rate_%": number;
  "avg_up_%": number;
  "avg_down_%": number;
}

export interface BacktestSample {
  event_date: string;
  "1d_%"?: number;
  "3d_%"?: number;
  "5d_%"?: number;
}

export interface BacktestResult {
  ticker: string;
  catalyst: string;
  events_count: number;
  lookback_days: number;
  windows: {
    "1d"?: BacktestWindowStats;
    "3d"?: BacktestWindowStats;
    "5d"?: BacktestWindowStats;
  };
  samples: BacktestSample[];
}

/**
 * Fetch backtest results for a ticker.
 * 
 * @param ticker - Stock ticker symbol (e.g., "AAPL")
 * @param catalyst - Optional catalyst filter (e.g., "EARNINGS", "FDA")
 * @param lookback - Number of days to look back (default: 365)
 * @returns Backtest results with aggregated statistics and individual samples
 */
export async function getBacktest(
  ticker: string,
  catalyst?: string,
  lookback: number = 365
): Promise<BacktestResult> {
  const params = new URLSearchParams({
    ticker,
    lookback_days: String(lookback),
  });
  
  if (catalyst) {
    params.set("catalyst", catalyst);
  }
  
  const url = `${BASE}/api/analysis/backtest?${params.toString()}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backtest failed: ${errorText}`);
  }
  
  return response.json();
}

