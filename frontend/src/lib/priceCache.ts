/**
 * Price Data Cache Manager
 *
 * Manages caching of intraday price data for fast propagation of entire trading day.
 * Collects second-by-second data while allowing switching between full day and minute views.
 *
 * Uses unified data format: {symbol: string, ts: number, value: number}
 */

export interface PricePoint {
  symbol: string;  // Stock ticker symbol
  ts: number;      // timestamp in milliseconds
  value: number;   // price or sentiment value
}

export interface PriceCacheEntry {
  symbol: string;
  data: PricePoint[];
  marketOpen: number;   // timestamp in milliseconds
  marketClose: number;  // timestamp in milliseconds
  fetchedAt: number;    // timestamp in milliseconds
  liveData: PricePoint[]; // Live second-by-second data collected during streaming
}

class PriceCacheManager {
  private cache: Map<string, PriceCacheEntry> = new Map();
  private listeners: Map<string, Set<(entry: PriceCacheEntry) => void>> = new Map();

  /**
   * Initialize cache for a symbol with full day data
   */
  initCache(symbol: string, data: PricePoint[], marketOpen: number, marketClose: number): void {
    const entry: PriceCacheEntry = {
      symbol,
      data,
      marketOpen,
      marketClose,
      fetchedAt: Date.now(),
      liveData: []
    };
    
    this.cache.set(symbol, entry);
    this.notifyListeners(symbol, entry);
    
    console.log(`[PriceCache] Initialized cache for ${symbol} with ${data.length} points`);
  }

  /**
   * Add a live data point (from streaming)
   */
  addLivePoint(symbol: string, point: PricePoint): void {
    const entry = this.cache.get(symbol);
    if (!entry) {
      console.warn(`[PriceCache] No cache entry for ${symbol}, creating new`);
      this.cache.set(symbol, {
        symbol,
        data: [],
        marketOpen: 0,
        marketClose: 0,
        fetchedAt: Date.now(),
        liveData: [point]
      });
      return;
    }

    // Add to live data
    entry.liveData.push(point);
    
    // Keep only last 1000 live points to avoid memory issues
    if (entry.liveData.length > 1000) {
      entry.liveData = entry.liveData.slice(-1000);
    }

    this.notifyListeners(symbol, entry);
  }

  /**
   * Get cache entry for a symbol
   */
  getCache(symbol: string): PriceCacheEntry | undefined {
    return this.cache.get(symbol);
  }

  /**
   * Get full day data (minute-by-minute from cache)
   */
  getFullDayData(symbol: string): PricePoint[] {
    const entry = this.cache.get(symbol);
    return entry?.data || [];
  }

  /**
   * Get live data (second-by-second collected during streaming)
   */
  getLiveData(symbol: string): PricePoint[] {
    const entry = this.cache.get(symbol);
    return entry?.liveData || [];
  }

  /**
   * Get combined data (full day + live updates)
   */
  getCombinedData(symbol: string): PricePoint[] {
    const entry = this.cache.get(symbol);
    if (!entry) return [];

    // Combine cached minute data with live second data
    // Remove duplicates by timestamp
    const combined = [...entry.data, ...entry.liveData];
    const uniqueMap = new Map<number, PricePoint>();

    combined.forEach(point => {
      uniqueMap.set(point.ts, point);
    });

    return Array.from(uniqueMap.values()).sort((a, b) => a.ts - b.ts);
  }

  /**
   * Subscribe to cache updates for a symbol
   */
  subscribe(symbol: string, callback: (entry: PriceCacheEntry) => void): () => void {
    if (!this.listeners.has(symbol)) {
      this.listeners.set(symbol, new Set());
    }
    
    this.listeners.get(symbol)!.add(callback);

    // Return unsubscribe function
    return () => {
      const listeners = this.listeners.get(symbol);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.listeners.delete(symbol);
        }
      }
    };
  }

  /**
   * Notify all listeners for a symbol
   */
  private notifyListeners(symbol: string, entry: PriceCacheEntry): void {
    const listeners = this.listeners.get(symbol);
    if (listeners) {
      listeners.forEach(callback => callback(entry));
    }
  }

  /**
   * Clear cache for a symbol
   */
  clearCache(symbol: string): void {
    this.cache.delete(symbol);
    this.listeners.delete(symbol);
    console.log(`[PriceCache] Cleared cache for ${symbol}`);
  }

  /**
   * Clear all caches
   */
  clearAll(): void {
    this.cache.clear();
    this.listeners.clear();
    console.log(`[PriceCache] Cleared all caches`);
  }

  /**
   * Get cache statistics
   */
  getStats(symbol: string): { minutePoints: number; livePoints: number; totalPoints: number } | null {
    const entry = this.cache.get(symbol);
    if (!entry) return null;

    return {
      minutePoints: entry.data.length,
      livePoints: entry.liveData.length,
      totalPoints: entry.data.length + entry.liveData.length
    };
  }
}

// Singleton instance
export const priceCache = new PriceCacheManager();

/**
 * Fetch and cache full intraday data for a symbol
 *
 * Note: The REST endpoint /stream/intraday/{symbol} still returns the detailed format.
 * This function converts it to the unified format for caching.
 */
export async function fetchIntradayCache(symbol: string, apiBase: string = "http://localhost:8000"): Promise<boolean> {
  try {
    const response = await fetch(`${apiBase}/stream/intraday/${symbol}`);

    if (!response.ok) {
      console.error(`[PriceCache] Failed to fetch intraday data for ${symbol}: ${response.status}`);
      return false;
    }

    const data = await response.json();

    // Convert from detailed format {t, v, o, h, l, volume} to unified format {symbol, ts, value}
    const unifiedData: PricePoint[] = data.data.map((point: any) => ({
      symbol: symbol,
      ts: point.t,
      value: point.v
    }));

    priceCache.initCache(
      symbol,
      unifiedData,
      data.market_open,
      data.market_close
    );

    return true;
  } catch (error) {
    console.error(`[PriceCache] Error fetching intraday data for ${symbol}:`, error);
    return false;
  }
}

