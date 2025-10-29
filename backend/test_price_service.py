#!/usr/bin/env python3
"""
Test script for price fetching service.

Tests both Polygon and Yahoo Finance price sources.
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.prices import get_close, index_ret


def test_intelligent_routing():
    """Test intelligent routing: Polygon for stocks, Yahoo for indices."""
    print("\n" + "="*60)
    print("Testing Intelligent Price Routing")
    print("="*60)
    print("\n📊 Stocks → Polygon.io | Indices → Yahoo Finance\n")

    # Set to use Polygon (but indices will auto-route to Yahoo)
    os.environ["USE_PRICE_SOURCE"] = "polygon"

    test_date = datetime(2025, 10, 27)

    print(f"Fetching prices for {test_date.date()}:\n")

    # Test individual stocks (should use Polygon)
    print("Individual Stocks (via Polygon):")
    symbols = ["AAPL", "NVDA", "TSLA", "MSFT"]
    for symbol in symbols:
        price = get_close(symbol, test_date)
        if price:
            print(f"  ✅ {symbol:6s} ${price:8.2f}")
        else:
            print(f"  ❌ {symbol:6s} Failed to fetch")

    # Test indices (should auto-route to Yahoo)
    print("\nIndices (auto-routed to Yahoo):")
    indices = ["^GSPC", "^DJI", "^IXIC"]
    for symbol in indices:
        price = get_close(symbol, test_date)
        if price:
            print(f"  ✅ {symbol:6s} ${price:8.2f}")
        else:
            print(f"  ❌ {symbol:6s} Failed to fetch")

    # Test index return
    print("\n\nIndex Return Calculation:")
    d0 = datetime(2025, 10, 24)
    d1 = datetime(2025, 10, 27)
    idx_return = index_ret("^GSPC", d0, d1)
    print(f"  S&P 500 ({d0.date()} → {d1.date()}): {idx_return*100:.2f}%")


def test_polygon():
    """Test Polygon.io price fetching."""
    print("\n" + "="*60)
    print("Testing Polygon.io Price Service")
    print("="*60)
    
    # Set to use Polygon
    os.environ["USE_PRICE_SOURCE"] = "polygon"
    
    symbols = ["AAPL", "NVDA", "TSLA", "MSFT"]
    test_date = datetime(2025, 10, 27)
    
    print(f"\nFetching prices for {test_date.date()}:\n")
    
    for symbol in symbols:
        price = get_close(symbol, test_date)
        if price:
            print(f"✅ {symbol:6s} ${price:8.2f}")
        else:
            print(f"❌ {symbol:6s} Failed to fetch")
    
    # Test index return
    print(f"\n\nTesting Index Return Calculation:")
    d0 = datetime(2025, 10, 24)
    d1 = datetime(2025, 10, 27)
    
    idx_return = index_ret("^GSPC", d0, d1)
    print(f"S&P 500 return ({d0.date()} → {d1.date()}): {idx_return*100:.2f}%")


def test_yahoo():
    """Test Yahoo Finance price fetching."""
    print("\n" + "="*60)
    print("Testing Yahoo Finance Price Service")
    print("="*60)
    
    # Set to use Yahoo
    os.environ["USE_PRICE_SOURCE"] = "yahoo"
    
    symbols = ["AAPL", "NVDA", "TSLA", "MSFT"]
    test_date = datetime(2025, 10, 27)
    
    print(f"\nFetching prices for {test_date.date()}:\n")
    
    for symbol in symbols:
        price = get_close(symbol, test_date)
        if price:
            print(f"✅ {symbol:6s} ${price:8.2f}")
        else:
            print(f"❌ {symbol:6s} Failed to fetch")
    
    # Test index return
    print(f"\n\nTesting Index Return Calculation:")
    d0 = datetime(2025, 10, 24)
    d1 = datetime(2025, 10, 27)
    
    idx_return = index_ret("^GSPC", d0, d1)
    print(f"S&P 500 return ({d0.date()} → {d1.date()}): {idx_return*100:.2f}%")


def test_cache():
    """Test price caching."""
    print("\n" + "="*60)
    print("Testing Price Cache")
    print("="*60)
    
    os.environ["USE_PRICE_SOURCE"] = "polygon"
    
    symbol = "AAPL"
    test_date = datetime(2025, 10, 27)
    
    print(f"\nFetching {symbol} price (should hit API)...")
    import time
    start = time.time()
    price1 = get_close(symbol, test_date)
    time1 = time.time() - start
    print(f"✅ First fetch: ${price1:.2f} ({time1:.3f}s)")
    
    print(f"\nFetching {symbol} price again (should use cache)...")
    start = time.time()
    price2 = get_close(symbol, test_date)
    time2 = time.time() - start
    print(f"✅ Second fetch: ${price2:.2f} ({time2:.3f}s)")
    
    if time2 < time1 * 0.5:
        print(f"\n✅ Cache is working! Second fetch was {time1/time2:.1f}x faster")
    else:
        print(f"\n⚠️  Cache may not be working properly")


if __name__ == "__main__":
    print("\n🚀 Price Service Test Suite")
    print("="*60)

    # Test intelligent routing (main test)
    try:
        test_intelligent_routing()
    except Exception as e:
        print(f"\n❌ Intelligent routing test failed: {e}")

    # Test Polygon
    try:
        test_polygon()
    except Exception as e:
        print(f"\n❌ Polygon test failed: {e}")

    # Test Yahoo
    try:
        test_yahoo()
    except Exception as e:
        print(f"\n❌ Yahoo test failed: {e}")

    # Test cache
    try:
        test_cache()
    except Exception as e:
        print(f"\n❌ Cache test failed: {e}")

    print("\n" + "="*60)
    print("✅ Test suite complete!")
    print("="*60 + "\n")

