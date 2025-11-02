"""Check signals in the database."""
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "news.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count total signals
cursor.execute("SELECT COUNT(*) FROM signals")
total = cursor.fetchone()[0]
print(f"Total signals: {total}")

# Show top 10 signals
cursor.execute("""
    SELECT symbol, score, label, confidence, article_id, created_at
    FROM signals
    ORDER BY score DESC
    LIMIT 10
""")
print("\nTop 10 signals:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check signals from last 7 days with score >= 50
cursor.execute("""
    SELECT COUNT(*)
    FROM signals
    WHERE score >= 50.0
    AND created_at >= datetime('now', '-7 days')
""")
recent_high_score = cursor.fetchone()[0]
print(f"\nSignals with score >= 50 in last 7 days: {recent_high_score}")

conn.close()

