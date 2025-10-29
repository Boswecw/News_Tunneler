# Adjusted Price Calculation

## Overview

This document explains how the News Tunneler system handles **adjusted close prices** for stock data. Adjusted prices account for corporate actions like stock splits and dividend payments, ensuring accurate historical analysis and backtesting.

## What is Adjusted Close?

**Adjusted Close** is a modified version of the closing price that accounts for:
- **Stock Splits**: When a company splits its stock (e.g., 2:1), historical prices are adjusted downward
- **Dividends**: When cash dividends are paid, historical prices are adjusted downward to reflect the value transfer

### Why It Matters

Without adjustment:
- A stock trading at $100 that does a 2:1 split would show a sudden drop to $50
- Charts would show false "crashes" at split dates
- Returns calculations would be inaccurate

With adjustment:
- Historical prices are retroactively adjusted to maintain continuity
- Charts show true total return (price appreciation + dividends)
- Technical indicators (SMA, RSI, etc.) work correctly across corporate actions

## Implementation

### Core Function: `recompute_adjusted_from_events()`

Located in `backend/app/core/prices.py`, this function rebuilds adjusted prices from raw data:

```python
def recompute_adjusted_from_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recompute adjusted close prices from raw close, dividend, and split data.
    
    Args:
        df: DataFrame with columns:
            - date (datetime): Trading date
            - close (float): Raw closing price
            - dividend (float): Dividend amount (0 if none)
            - split_coeff (float): Split coefficient (1 if none)
    
    Returns:
        DataFrame with additional column:
            - adj_close_rebuilt (float): Recomputed adjusted close price
    """
```

### How It Works

The function applies cumulative adjustment factors **forward** from each event date:

1. **Split Factor**: `1 / split_coefficient`
   - For a 2:1 split (split_coeff = 2.0), factor = 0.5
   - All prior prices are multiplied by 0.5

2. **Dividend Factor**: `(prev_close - dividend) / prev_close`
   - For a $1 dividend on a $100 stock, factor = 99/100 = 0.99
   - All prior prices are multiplied by 0.99

3. **Combined Factor**: Product of all future split and dividend factors
   - Each date's adjusted price = close × (product of all future factors)

### Example

```
Date       Close  Dividend  Split   Adj Close
---------- ------ --------- ------- ----------
2025-01-01 $100   $0        1.0     $49.52  ← Adjusted for both events
2025-01-02 $101   $0        1.0     $50.01
2025-01-03 $102   $0        1.0     $50.51
2025-01-04 $103   $0        1.0     $51.00
2025-01-05 $104   $0        1.0     $51.50
2025-01-06 $103   $1        1.0     $51.50  ← Dividend paid
2025-01-07 $102   $0        1.0     $51.00
2025-01-08 $101   $0        1.0     $50.50
2025-01-09 $50.50 $0        2.0     $50.50  ← 2:1 split
2025-01-10 $51.00 $0        1.0     $51.00  ← No future events
```

## Current Data Source: Yahoo Finance (yfinance)

### ✅ Active Implementation

The system is now using **Yahoo Finance** via the `yfinance` library as the primary data source:

**Advantages:**
- ✅ **Completely free** - No API key required
- ✅ **Includes dividend data** - Captures all dividend payments
- ✅ **Includes split data** - Captures all stock splits
- ✅ **Adjusted close prices** - Automatically calculated from corporate actions
- ✅ **Real-time data** - Up-to-date market prices
- ✅ **No rate limits** - Much more generous than Alpha Vantage free tier

**Data Provided:**
- Open, High, Low, Close prices
- Volume
- Dividend amounts (on ex-dividend dates)
- Split coefficients (on split dates)
- Adjusted close (recomputed using our `recompute_adjusted_from_events()` function)

### Alternative Data Sources

#### Alpha Vantage Free Tier

The free tier API (`TIME_SERIES_DAILY`) **does not include** dividend and split data:
- Only provides: open, high, low, close, volume
- No fields: `7. dividend amount`, `8. split coefficient`
- Rate limited: 25 calls/day, 5 calls/minute

#### Alpha Vantage Premium Tier

The premium API (`TIME_SERIES_DAILY_ADJUSTED`) **includes**:
- All free tier fields
- `5. adjusted close` (vendor-calculated)
- `7. dividend amount`
- `8. split coefficient`
- Cost: $50/month

## Upgrading to Premium or Switching Vendors

### Option 1: Upgrade to Alpha Vantage Premium

Update `backend/app/core/prices.py`:

```python
# Change from TIME_SERIES_DAILY to TIME_SERIES_DAILY_ADJUSTED
url = (
    "https://www.alphavantage.co/query"
    "?function=TIME_SERIES_DAILY_ADJUSTED"  # Changed
    f"&symbol={ticker}&outputsize=compact&apikey={AV_KEY}"
)

# Update field parsing
ts = js.get("Time Series (Daily Adjusted)", {})  # Changed key
for d, o in ts.items():
    rows.append({
        "date": pd.Timestamp(d),
        "open": float(o["1. open"]),
        "high": float(o["2. high"]),
        "low": float(o["3. low"]),
        "close": float(o["4. close"]),
        "adj_close": float(o["5. adjusted close"]),  # Now available
        "volume": int(float(o["6. volume"])),
        "dividend": float(o.get("7. dividend amount", 0.0)),  # Now available
        "split_coeff": float(o.get("8. split coefficient", 1.0)),  # Now available
    })
```

### Option 2: Use Alternative Data Source

Other sources with free dividend/split data:
- **yfinance** (Yahoo Finance): Free, includes adjusted close
- **Finnhub**: Free tier includes some corporate actions
- **Polygon.io**: Free tier includes splits and dividends

Example with yfinance:

```python
import yfinance as yf

def _yfinance_daily(ticker: str) -> pd.DataFrame:
    """Fetch daily price data from Yahoo Finance."""
    stock = yf.Ticker(ticker)
    df = stock.history(period="100d")
    
    # yfinance provides Close and Adj Close
    df = df.reset_index()
    df.columns = df.columns.str.lower()
    df = df.rename(columns={'adj close': 'adj_close'})
    
    # Get dividend and split data
    dividends = stock.dividends
    splits = stock.splits
    
    # Merge into main dataframe
    df['dividend'] = df['date'].map(dividends.to_dict()).fillna(0.0)
    df['split_coeff'] = df['date'].map(splits.to_dict()).fillna(1.0)
    
    return df
```

## Verification

To verify adjusted prices are correct:

1. **Run the test script**:
   ```bash
   cd backend
   python3 test_adjusted_prices.py
   ```

2. **Compare vendor vs rebuilt**:
   ```python
   df = get_daily_prices("AAPL")
   
   # If using premium API with vendor's adjusted close:
   df['diff'] = df['adj_close'] - df['adj_close_rebuilt']
   print(df[['date', 'adj_close', 'adj_close_rebuilt', 'diff']])
   
   # Differences should be tiny (< $0.01) due to rounding
   ```

3. **Check for corporate actions**:
   ```python
   # Find dates with dividends or splits
   events = df[(df['dividend'] > 0) | (df['split_coeff'] != 1.0)]
   print(events[['date', 'close', 'dividend', 'split_coeff', 'adj_close_rebuilt']])
   ```

## Impact on Technical Analysis

### Indicators Using Adjusted Prices

These indicators should use `adj_close` instead of `close`:
- ✅ **SMA (Simple Moving Average)**: Uses adjusted close
- ✅ **RSI (Relative Strength Index)**: Uses adjusted close
- ✅ **ATR (Average True Range)**: Uses adjusted high/low/close
- ✅ **52-week high/low**: Uses adjusted close

### Backtesting

The backtest system (`backend/app/core/backtest.py`) uses adjusted prices:
```python
def forward_returns(prices_df: pd.DataFrame, event_dates, windows=(1,3,5)):
    # Uses 'adj_close' column for return calculations
    start_price = df.loc[d, "adj_close"]
    end_price = df.iloc[idx]["adj_close"]
    fwd_return = (end_price / start_price - 1) * 100.0
```

This ensures:
- Returns are accurate across splits and dividends
- Backtests reflect true total return
- No false signals from corporate actions

## Frontend Display

The `AnalysisCard` component shows a tooltip explaining adjusted prices:

```tsx
<div class="text-center opacity-70">
  Using <b class="text-neutral-400">raw close prices</b>.{' '}
  <span 
    class="underline decoration-dotted cursor-help" 
    title="Adjusted Close rewrites past prices to account for stock splits and cash dividends so charts reflect total return. Free tier data uses raw prices; upgrade to premium for split/dividend-adjusted data."
  >
    What's adjusted close?
  </span>
</div>
```

## Best Practices

1. **Always use adjusted prices for**:
   - Long-term price charts
   - Technical indicators
   - Backtesting
   - Return calculations

2. **Use raw prices for**:
   - Intraday trading (same-day)
   - Order execution (current market price)
   - Real-time quotes

3. **Document your data source**:
   - Note whether using raw or adjusted prices
   - Specify vendor and tier (free vs premium)
   - Include data freshness (cache TTL)

## References

- [yfinance Documentation](https://github.com/ranaroussi/yfinance)
- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/)
- [Investopedia: Adjusted Closing Price](https://www.investopedia.com/terms/a/adjusted_closing_price.asp)
- [Yahoo Finance: Why Adjusted Close?](https://help.yahoo.com/kb/SLN2311.html)

## Summary

- ✅ **Implemented**: `recompute_adjusted_from_events()` function
- ✅ **Active**: Using Yahoo Finance (yfinance) as primary data source
- ✅ **Working**: Dividend and split data is being captured
- ✅ **Verified**: Adjusted close prices are calculated correctly
- ✅ **Documented**: Frontend tooltip explains adjusted prices
- ✅ **Tested**: Test scripts verify calculation accuracy
- ✅ **Free**: No API key required, no rate limits

The system is **portable** and **vendor-agnostic** - you can switch data sources without changing your analysis code.

### Current Status

**Data Source:** Yahoo Finance (yfinance)
- ✅ Free, no API key required
- ✅ Includes dividends and splits
- ✅ Real-time data
- ✅ Adjusted close prices calculated from corporate actions

**Example Output:**
```
✅ Found 1 dividend payment(s):
                     date      close  dividend  adj_close
2025-08-11 00:00:00-04:00 227.179993      0.26 227.179993
```

The News Tunneler now has **full adjusted price support** with free, unlimited access to dividend and split data! 🎉

