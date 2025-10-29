"""Test script to manually trigger RSS feed polling."""
import asyncio
import sys
sys.path.insert(0, '/home/charles/projects/Coding2025/news-tunneler/backend')

from app.core.scheduler import poll_feeds

if __name__ == "__main__":
    print("Starting manual poll test...")
    asyncio.run(poll_feeds())
    print("Poll complete!")

