#!/usr/bin/env python3
"""
List all RSS feeds in the News Tunneler database.

This script displays all configured RSS feeds with their status.
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import get_db_context
from app.models import Source


def list_sources():
    """List all RSS feeds in the database."""
    print("=" * 80)
    print("News Tunneler - RSS Feed Sources")
    print("=" * 80)
    print()
    
    with get_db_context() as db:
        sources = db.query(Source).order_by(Source.id).all()
        
        if not sources:
            print("No sources found in database.")
            return
        
        print(f"Total Sources: {len(sources)}")
        print()
        
        # Group by status
        enabled = [s for s in sources if s.enabled]
        disabled = [s for s in sources if not s.enabled]
        
        print(f"✅ Enabled: {len(enabled)}")
        print(f"❌ Disabled: {len(disabled)}")
        print()
        print("-" * 80)
        
        for source in sources:
            status = "✅" if source.enabled else "❌"
            last_fetch = "Never"
            if source.last_fetched_at:
                # Calculate time since last fetch
                delta = datetime.utcnow() - source.last_fetched_at
                if delta.total_seconds() < 60:
                    last_fetch = "Just now"
                elif delta.total_seconds() < 3600:
                    mins = int(delta.total_seconds() / 60)
                    last_fetch = f"{mins} min ago"
                elif delta.total_seconds() < 86400:
                    hours = int(delta.total_seconds() / 3600)
                    last_fetch = f"{hours} hr ago"
                else:
                    days = int(delta.total_seconds() / 86400)
                    last_fetch = f"{days} days ago"
            
            print(f"{status} [{source.id:2d}] {source.name}")
            print(f"    URL: {source.url}")
            print(f"    Type: {source.source_type} | Last Fetched: {last_fetch}")
            print()
    
    print("=" * 80)


if __name__ == "__main__":
    list_sources()

