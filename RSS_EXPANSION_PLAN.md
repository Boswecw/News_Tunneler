# RSS Feed Expansion Plan for News Tunneler

## 📊 Current Status

### Existing RSS Feeds (10 total)
Your News Tunneler currently has these RSS feeds configured:

| # | Name | URL | Category |
|---|------|-----|----------|
| 1 | SEC EDGAR – Company Filings | `https://www.sec.gov/cgi-bin/browse-edgar?...` | Regulatory |
| 2 | Reuters – Business News | `https://feeds.reuters.com/reuters/businessNews` | General Market |
| 3 | CNBC – Market News | `https://www.cnbc.com/id/100003114/device/rss/rss.html` | General Market |
| 4 | Yahoo Finance – Top Stories | `https://finance.yahoo.com/news/rssindex` | General Market |
| 5 | MarketWatch – Top Stories | `https://feeds.marketwatch.com/marketwatch/topstories/` | General Market |
| 6 | FierceBiotech – Biotech News | `https://www.fiercebiotech.com/rss/xml` | Sector - Biotech |
| 7 | TechCrunch – Startups | `https://techcrunch.com/startups/feed/` | Sector - Tech |
| 8 | CleanTechnica – Renewable Energy | `https://cleantechnica.com/feed/` | Sector - Energy |
| 9 | WaterWorld – Water Industry News | `https://www.waterworld.com/rss` | Sector - Utilities |
| 10 | Federal Reserve – Press Releases | `https://www.federalreserve.gov/feeds/press_all.xml` | Macro - Central Banks |

---

## 🎯 Proposed New RSS Feeds (10 additional)

Based on your table of potential news sources, here are **10 verified RSS feeds** ready to add:

### **General Market News (4 feeds)**

| # | Name | URL | Why Add It |
|---|------|-----|------------|
| 11 | **Seeking Alpha – Market News** | `https://seekingalpha.com/feed.xml` | Excellent for catalyst categorization, sector analysis, and ticker-specific insights |
| 12 | **Investing.com – All News** | `https://www.investing.com/rss/news.rss` | Global market coverage, macro events, commodities |
| 13 | **Bloomberg – Markets News** | `https://feeds.bloomberg.com/markets/news.rss` | Premium institutional-grade market news |
| 14 | **Financial Times – Home** | `https://www.ft.com/rss/home` | International business and economic news |

### **Asset Class Specific (3 feeds)**

| # | Name | URL | Why Add It |
|---|------|-----|------------|
| 15 | **Investing.com – Stock Market News** | `https://www.investing.com/rss/news_25.rss` | Focused stock market coverage |
| 16 | **Investing.com – Forex News** | `https://www.investing.com/rss/news_1.rss` | Currency market news and central bank updates |
| 17 | **Investing.com – Commodities News** | `https://www.investing.com/rss/news_11.rss` | Oil, gold, agriculture, metals coverage |

### **Macro & Economic (2 feeds)**

| # | Name | URL | Why Add It |
|---|------|-----|------------|
| 18 | **Investing.com – Economic Indicators** | `https://www.investing.com/rss/news_95.rss` | GDP, CPI, employment data releases |
| 19 | **Investing.com – Economy News** | `https://www.investing.com/rss/news_14.rss` | Broader economic trends and policy |

### **Premium Analysis (1 feed)**

| # | Name | URL | Why Add It |
|---|------|-----|------------|
| 20 | **Barron's – Market News** | `https://www.barrons.com/feed` | High-quality investment analysis and stock picks |

---

## 📈 Expected Benefits

### **Coverage Expansion**
- **Before**: 10 feeds → **After**: 20 feeds (100% increase)
- **New Asset Classes**: Forex, Commodities, Economic Indicators
- **Geographic Diversity**: More international coverage (FT, Investing.com)
- **Analysis Depth**: Premium sources (Seeking Alpha, Barron's, Bloomberg)

### **LLM Training Improvements**
- More diverse writing styles for better sentiment analysis
- Ticker-specific news from Seeking Alpha
- Macro context from economic indicator feeds
- Better catalyst detection with specialized feeds

### **Signal Quality**
- More data points for ML training
- Better coverage of market-moving events
- Improved ticker extraction from specialized feeds
- Enhanced credibility scoring with premium sources

---

## 🚀 Implementation Plan

### **Step 1: Update Seed File**
Replace `backend/app/seeds/seed_sources.json` with the expanded version:
- ✅ File created: `seed_sources_EXPANDED.json`
- Contains all 20 feeds with category metadata

### **Step 2: Add to Running Database**
Use the API to add new feeds immediately:
```bash
# Example: Add Seeking Alpha feed
curl -X POST http://localhost:8000/api/sources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Seeking Alpha – Market News",
    "url": "https://seekingalpha.com/feed.xml",
    "source_type": "rss"
  }'
```

### **Step 3: Verify Feeds**
Monitor the backend logs to ensure new feeds are fetching successfully:
```bash
tail -f backend/logs/app.log | grep "Fetching feed"
```

### **Step 4: Monitor Performance**
- Check article ingestion rate
- Verify ticker extraction quality
- Monitor LLM analysis coverage
- Track signal generation

---

## 📋 Category Breakdown

The expanded feed list provides balanced coverage across:

| Category | Count | Feeds |
|----------|-------|-------|
| **General Market** | 8 | Reuters, CNBC, Yahoo, MarketWatch, Seeking Alpha, Investing.com All, Bloomberg, FT |
| **Regulatory** | 1 | SEC EDGAR |
| **Stocks** | 1 | Investing.com Stock Market |
| **Forex** | 1 | Investing.com Forex |
| **Commodities** | 1 | Investing.com Commodities |
| **Macro/Economy** | 3 | Fed Press, Investing.com Indicators, Investing.com Economy |
| **Sector - Biotech** | 1 | FierceBiotech |
| **Sector - Tech** | 1 | TechCrunch |
| **Sector - Energy** | 1 | CleanTechnica |
| **Sector - Utilities** | 1 | WaterWorld |
| **Premium Analysis** | 1 | Barron's |

---

## ⚠️ Notes on API-Based Sources

Some sources from your original table require API keys and are **not RSS-based**:

### **Requires API Integration (Future Enhancement)**
1. **NewsAPI.org** - JSON API (100 req/day free)
2. **Finnhub.io** - JSON API (real-time news)
3. **MarketAux.com** - JSON API (100 req/day)
4. **Polygon.io** - JSON API (you already have API key for prices)
5. **FinancialModelingPrep** - JSON API (250 calls/day)

These would require:
- New API client implementations
- Rate limiting logic
- Different data models (JSON vs RSS)
- Separate polling logic

**Recommendation**: Start with RSS feeds first, then add API sources in Phase 2.

---

## 🔧 Technical Details

### **Database Schema**
The `Source` model supports the new feeds without changes:
```python
class Source(Base, TimestampMixin):
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    source_type = Column(String, default="rss")
    enabled = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime, nullable=True)
```

### **Polling Frequency**
- Current: Every 15 minutes (900 seconds)
- With 20 feeds: ~45 seconds per feed per cycle
- No changes needed to scheduler

### **Rate Limiting**
- RSS feeds have no strict rate limits
- Browser-like headers already configured
- Retry logic with exponential backoff in place

---

## ✅ Next Steps

1. **Review the expanded feed list** - Confirm which feeds you want to add
2. **I'll update the seed file** - Replace `seed_sources.json` with expanded version
3. **I'll add feeds to database** - Use API to add feeds immediately
4. **Monitor ingestion** - Verify feeds are working correctly
5. **Adjust if needed** - Disable any problematic feeds

**Ready to proceed?** Let me know if you want to:
- Add all 10 new feeds
- Add only specific feeds (tell me which ones)
- Modify any feed URLs or names
- Add additional feeds not on this list

