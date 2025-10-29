#!/bin/bash

# Trading Signals System - Example Workflow
# This script demonstrates the complete signals pipeline

BASE_URL="http://localhost:8000"

echo "🚀 Trading Signals System - Example Workflow"
echo "============================================================"
echo ""

# Step 1: Ingest signals
echo "📥 Step 1: Ingesting signals..."
echo "------------------------------------------------------------"
curl -s -X POST "$BASE_URL/signals/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "signals": [
      {
        "symbol": "AAPL",
        "t": 1730138358674,
        "features": {
          "sentiment": 0.8,
          "magnitude": 0.45,
          "credibility": 0.9,
          "recency": 1.0,
          "volume": 0.7
        }
      },
      {
        "symbol": "NVDA",
        "t": 1730138358674,
        "features": {
          "sentiment": 0.75,
          "magnitude": 0.6,
          "credibility": 0.85,
          "recency": 1.0,
          "volume": 0.8
        }
      },
      {
        "symbol": "TSLA",
        "t": 1730138358674,
        "features": {
          "sentiment": 0.65,
          "magnitude": 0.55,
          "credibility": 0.8,
          "recency": 1.0,
          "volume": 0.75
        }
      }
    ]
  }' | python3 -m json.tool

echo ""
echo ""

# Step 2: Get top signals
echo "📊 Step 2: Retrieving top signals..."
echo "------------------------------------------------------------"
curl -s "$BASE_URL/signals/top?limit=5" | python3 -m json.tool

echo ""
echo ""

# Step 3: Get latest signal for AAPL
echo "🔍 Step 3: Getting latest signal for AAPL..."
echo "------------------------------------------------------------"
curl -s "$BASE_URL/signals/AAPL/latest" | python3 -m json.tool

echo ""
echo ""

# Step 4: Label signals
echo "🏷️  Step 4: Labeling signals with forward returns..."
echo "------------------------------------------------------------"
curl -s -X POST "$BASE_URL/admin/label" | python3 -m json.tool

echo ""
echo ""

# Step 5: Train model (will fail if not enough data)
echo "🎓 Step 5: Training ML model..."
echo "------------------------------------------------------------"
curl -s -X POST "$BASE_URL/admin/train" | python3 -m json.tool

echo ""
echo ""
echo "✅ Workflow complete!"
echo "============================================================"

