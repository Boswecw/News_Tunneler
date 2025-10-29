#!/usr/bin/env python3
"""
Add new RSS feeds to the News Tunneler database.

This script adds 10 new RSS feeds to the running database:
- Seeking Alpha
- Investing.com (7 feeds)
- Bloomberg
- Financial Times
- Barron's

Run this script to add feeds immediately without restarting the backend.
"""
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import get_db_context
from app.models import Source
from app.core.logging import logger


# New feeds to add
NEW_FEEDS = [
    {
        "name": "Seeking Alpha – Market News",
        "url": "https://seekingalpha.com/feed.xml",
        "type": "rss"
    },
    {
        "name": "Investing.com – All News",
        "url": "https://www.investing.com/rss/news.rss",
        "type": "rss"
    },
    {
        "name": "Investing.com – Stock Market News",
        "url": "https://www.investing.com/rss/news_25.rss",
        "type": "rss"
    },
    {
        "name": "Investing.com – Forex News",
        "url": "https://www.investing.com/rss/news_1.rss",
        "type": "rss"
    },
    {
        "name": "Investing.com – Commodities News",
        "url": "https://www.investing.com/rss/news_11.rss",
        "type": "rss"
    },
    {
        "name": "Investing.com – Economic Indicators",
        "url": "https://www.investing.com/rss/news_95.rss",
        "type": "rss"
    },
    {
        "name": "Investing.com – Economy News",
        "url": "https://www.investing.com/rss/news_14.rss",
        "type": "rss"
    },
    {
        "name": "Bloomberg – Markets News",
        "url": "https://feeds.bloomberg.com/markets/news.rss",
        "type": "rss"
    },
    {
        "name": "Financial Times – Home",
        "url": "https://www.ft.com/rss/home",
        "type": "rss"
    },
    {
        "name": "Barron's – Market News",
        "url": "https://www.barrons.com/feed",
        "type": "rss"
    }
]


def add_new_feeds():
    """Add new RSS feeds to the database."""
    print("=" * 70)
    print("Adding New RSS Feeds to News Tunneler")
    print("=" * 70)
    print()
    
    added_count = 0
    skipped_count = 0
    
    with get_db_context() as db:
        for feed_data in NEW_FEEDS:
            # Check if already exists
            existing = db.query(Source).filter(Source.url == feed_data["url"]).first()
            
            if existing:
                print(f"⏭️  SKIP: {feed_data['name']}")
                print(f"   Already exists (ID: {existing.id})")
                skipped_count += 1
            else:
                # Add new feed
                source = Source(
                    url=feed_data["url"],
                    name=feed_data["name"],
                    source_type=feed_data["type"],
                    enabled=True,
                )
                db.add(source)
                db.flush()  # Get the ID
                
                print(f"✅ ADDED: {feed_data['name']}")
                print(f"   URL: {feed_data['url']}")
                print(f"   ID: {source.id}")
                added_count += 1
            
            print()
        
        # Commit all changes
        db.commit()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Added: {added_count} new feeds")
    print(f"⏭️  Skipped: {skipped_count} existing feeds")
    print(f"📊 Total feeds in database: {added_count + skipped_count + 10}")
    print()
    print("🎉 Done! New feeds will be polled on the next cycle (every 15 minutes)")
    print()


if __name__ == "__main__":
    try:
        add_new_feeds()
    except Exception as e:
        logger.error(f"Failed to add new feeds: {e}")
        print(f"❌ ERROR: {e}")
        sys.exit(1)

