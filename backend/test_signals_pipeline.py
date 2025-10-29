#!/usr/bin/env python3
"""
Test script for the complete signals pipeline.

Tests:
1. Signal ingestion
2. Signal retrieval
3. Signal labeling
4. Model training
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"


def test_ingest_signals():
    """Test signal ingestion endpoint."""
    print("\n" + "="*60)
    print("TEST 1: Signal Ingestion")
    print("="*60)
    
    # Create test signals
    now_ms = int(datetime.now().timestamp() * 1000)
    
    signals = [
        {
            "symbol": "AAPL",
            "t": now_ms - 86400000,  # 1 day ago
            "features": {
                "sentiment": 0.7,
                "magnitude": 0.8,
                "novelty": 0.9,
                "credibility": 0.85,
                "ret_1d": 0.02,
                "vol_z": 2.5,
                "vwap_dev": 0.005,
                "gap_pct": 0.01,
                "sector_momo_pct": 0.65,
                "earnings_in_days": 3,
            }
        },
        {
            "symbol": "NVDA",
            "t": now_ms - 43200000,  # 12 hours ago
            "features": {
                "sentiment": 0.85,
                "magnitude": 0.9,
                "novelty": 0.95,
                "credibility": 0.9,
                "ret_1d": 0.035,
                "vol_z": 3.2,
                "vwap_dev": 0.008,
                "gap_pct": 0.015,
                "sector_momo_pct": 0.75,
                "earnings_in_days": 1,
            }
        },
        {
            "symbol": "TSLA",
            "t": now_ms,  # now
            "features": {
                "sentiment": -0.6,
                "magnitude": 0.7,
                "novelty": 0.8,
                "credibility": 0.75,
                "ret_1d": -0.025,
                "vol_z": 1.8,
                "vwap_dev": -0.012,
                "gap_pct": -0.02,
                "sector_momo_pct": 0.45,
                "earnings_in_days": 15,
            }
        },
    ]
    
    payload = {"signals": signals}
    
    response = requests.post(f"{BASE_URL}/signals/ingest", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Ingested {result['count']} signals")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_get_top_signals():
    """Test getting top signals."""
    print("\n" + "="*60)
    print("TEST 2: Get Top Signals")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/signals/top?limit=10")
    
    if response.status_code == 200:
        signals = response.json()
        print(f"\n✅ Retrieved {len(signals)} signals\n")
        
        for sig in signals[:5]:
            print(f"{sig['symbol']:6s} | Score: {sig['score']:5.1f} | Label: {sig['label']}")
            print(f"         Reasons: {len(sig['reasons'])} components")
            if sig['reasons']:
                top_reason = sig['reasons'][0]
                print(f"         Top: {top_reason['k']} = {top_reason['v']} → +{top_reason['+']}")
            print()
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_get_latest_signal():
    """Test getting latest signal for a ticker."""
    print("\n" + "="*60)
    print("TEST 3: Get Latest Signal for AAPL")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/signals/AAPL/latest")
    
    if response.status_code == 200:
        signal = response.json()
        print(f"\n✅ Retrieved signal for {signal['symbol']}\n")
        print(f"Timestamp: {datetime.fromtimestamp(signal['t']/1000)}")
        print(f"Score: {signal['score']:.1f}")
        print(f"Label: {signal['label']}")
        print(f"Forward Return: {signal.get('y_ret_1d', 'Not labeled yet')}")
        print(f"Beat Index: {signal.get('y_beat', 'Not labeled yet')}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_labeling():
    """Test signal labeling."""
    print("\n" + "="*60)
    print("TEST 4: Signal Labeling")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/admin/label")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Labeled {result['labeled_count']} signals")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


def test_training():
    """Test model training."""
    print("\n" + "="*60)
    print("TEST 5: Model Training")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/admin/train")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Training pipeline complete\n")
        print(f"Labeled: {result['labeled_count']} signals")
        
        if result['training_result']:
            tr = result['training_result']
            print(f"\nModel Version: {tr['version']}")
            print(f"Accuracy: {tr['metrics']['accuracy']:.3f}")
            print(f"Training Samples: {tr['metrics']['n_rows']}")
            print(f"\nTop Feature Weights:")
            weights = sorted(tr['weights'].items(), key=lambda x: abs(x[1]), reverse=True)
            for feat, weight in weights[:5]:
                print(f"  {feat:20s}: {weight:6.2f}")
        else:
            print(f"\n⚠️  {result['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")


if __name__ == "__main__":
    print("\n🚀 Signals Pipeline Test Suite")
    print("="*60)
    
    try:
        test_ingest_signals()
        test_get_top_signals()
        test_get_latest_signal()
        test_labeling()
        test_training()
        
        print("\n" + "="*60)
        print("✅ All tests complete!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}\n")

