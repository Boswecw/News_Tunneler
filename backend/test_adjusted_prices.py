"""
Test script for adjusted price calculation.

This demonstrates how the recompute_adjusted_from_events function works
with sample dividend and split data.
"""
import pandas as pd
import sys
sys.path.insert(0, '/home/charles/projects/Coding2025/news-tunneler/backend')

from app.core.prices import recompute_adjusted_from_events

# Create sample data with a 2:1 stock split and a $1 dividend
# Scenario: Stock trading at $100, then:
# - Day 5: $1 dividend paid (ex-div date)
# - Day 8: 2:1 stock split
data = {
    'date': pd.date_range('2025-01-01', periods=10, freq='D'),
    'close': [100.0, 101.0, 102.0, 103.0, 104.0,  # Days 0-4
              103.0, 102.0, 101.0,                 # Days 5-7 (after dividend)
              50.5, 51.0],                         # Days 8-9 (after 2:1 split)
    'dividend': [0.0, 0.0, 0.0, 0.0, 0.0,
                 1.0,  # $1 dividend on day 5
                 0.0, 0.0, 0.0, 0.0],
    'split_coeff': [1.0, 1.0, 1.0, 1.0, 1.0,
                    1.0, 1.0, 1.0,
                    2.0,  # 2:1 split on day 8 (split_coeff = 2.0)
                    1.0],
}

df = pd.DataFrame(data)

print("=" * 80)
print("ADJUSTED PRICE CALCULATION TEST")
print("=" * 80)
print("\nOriginal Data:")
print(df.to_string(index=False))

# Compute adjusted prices
df_adjusted = recompute_adjusted_from_events(df)

print("\n" + "=" * 80)
print("After Adjustment Calculation:")
print("=" * 80)
print(df_adjusted[['date', 'close', 'dividend', 'split_coeff', 'adj_close_rebuilt']].to_string(index=False))

print("\n" + "=" * 80)
print("EXPLANATION:")
print("=" * 80)
print("""
How adjusted close works:
1. On day 5: $1 dividend is paid
   - All prices BEFORE day 5 are adjusted down by the dividend factor
   - Factor = (prev_close - dividend) / prev_close = (104 - 1) / 104 ≈ 0.9904
   
2. On day 8: 2:1 stock split occurs
   - All prices BEFORE day 8 are adjusted down by the split factor
   - Factor = 1 / split_coeff = 1 / 2.0 = 0.5
   
3. The adjusted close for early days reflects BOTH events:
   - Day 0 adjusted = 100.0 * 0.9904 * 0.5 ≈ 49.52
   - This means if you bought at $100 on day 0, after the dividend and split,
     your position would be worth the equivalent of ~$49.52 per original share
     (but you'd have 2 shares worth ~$50.5 each + $1 dividend received)

This ensures price charts show true total return including corporate actions.
""")

print("\n" + "=" * 80)
print("VERIFICATION:")
print("=" * 80)
print(f"Day 0 close: ${df_adjusted.iloc[0]['close']:.2f}")
print(f"Day 0 adjusted: ${df_adjusted.iloc[0]['adj_close_rebuilt']:.2f}")
print(f"Adjustment factor: {df_adjusted.iloc[0]['adj_close_rebuilt'] / df_adjusted.iloc[0]['close']:.4f}")
print(f"\nDay 9 close: ${df_adjusted.iloc[9]['close']:.2f}")
print(f"Day 9 adjusted: ${df_adjusted.iloc[9]['adj_close_rebuilt']:.2f}")
print(f"Adjustment factor: {df_adjusted.iloc[9]['adj_close_rebuilt'] / df_adjusted.iloc[9]['close']:.4f}")
print("\nNote: Recent prices have factor ≈ 1.0 (no future events to adjust for)")

