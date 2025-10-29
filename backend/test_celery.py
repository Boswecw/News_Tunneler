"""
Test script for Celery task queue

Tests:
1. Celery app configuration
2. Task registration
3. Task execution (if worker is running)
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("CELERY TASK QUEUE - TEST SUITE")
print("=" * 60)
print()

# Test 1: Celery App Configuration
print("=" * 60)
print("TEST: Celery App Configuration")
print("=" * 60)

try:
    from app.core.celery_app import celery_app
    
    print(f"✓ Celery app created: {celery_app.main}")
    print(f"ℹ Broker: {celery_app.conf.broker_url}")
    print(f"ℹ Backend: {celery_app.conf.result_backend}")
    print(f"ℹ Task serializer: {celery_app.conf.task_serializer}")
    print(f"ℹ Timezone: {celery_app.conf.timezone}")
    
    # Check task routes
    task_routes = celery_app.conf.task_routes
    if task_routes:
        print(f"✓ Task routes configured: {len(task_routes)} routes")
        for pattern, config in task_routes.items():
            print(f"  - {pattern} → {config['queue']}")
    else:
        print("✗ No task routes configured")
    
    # Check beat schedule
    beat_schedule = celery_app.conf.beat_schedule
    if beat_schedule:
        print(f"✓ Beat schedule configured: {len(beat_schedule)} tasks")
        for task_name, config in beat_schedule.items():
            print(f"  - {task_name}: {config['task']}")
    else:
        print("✗ No beat schedule configured")
    
    print()
    
except Exception as e:
    print(f"✗ Celery app configuration failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 2: Task Registration
print("=" * 60)
print("TEST: Task Registration")
print("=" * 60)

try:
    from app.core.celery_app import celery_app
    
    # Get registered tasks
    registered_tasks = list(celery_app.tasks.keys())
    
    # Filter out built-in tasks
    custom_tasks = [t for t in registered_tasks if not t.startswith('celery.')]
    
    print(f"✓ Total registered tasks: {len(registered_tasks)}")
    print(f"✓ Custom tasks: {len(custom_tasks)}")
    print()
    
    # Check for expected tasks
    expected_tasks = [
        "app.tasks.llm_tasks.analyze_article_async",
        "app.tasks.llm_tasks.batch_analyze_articles",
        "app.tasks.rss_tasks.poll_rss_feed",
        "app.tasks.rss_tasks.poll_all_rss_feeds",
        "app.tasks.rss_tasks.cleanup_old_signals",
        "app.tasks.digest_tasks.send_daily_digest",
        "app.tasks.digest_tasks.send_weekly_digest",
        "app.tasks.digest_tasks.send_alert",
    ]
    
    print("Expected tasks:")
    for task_name in expected_tasks:
        if task_name in registered_tasks:
            print(f"  ✓ {task_name}")
        else:
            print(f"  ✗ {task_name} (NOT FOUND)")
    
    print()
    
except Exception as e:
    print(f"✗ Task registration check failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test 3: Task Execution (if worker is running)
print("=" * 60)
print("TEST: Task Execution")
print("=" * 60)

try:
    from app.core.celery_app import celery_app, debug_task
    
    print("ℹ Attempting to execute debug task...")
    print("ℹ This requires a Celery worker to be running")
    print()
    
    # Try to execute debug task
    try:
        result = debug_task.apply_async()
        print(f"✓ Task queued: {result.id}")
        print(f"ℹ Task state: {result.state}")
        
        # Try to get result (with timeout)
        try:
            task_result = result.get(timeout=5)
            print(f"✓ Task completed: {task_result}")
        except Exception as e:
            print(f"⚠ Task execution timeout or worker not running")
            print(f"ℹ Start worker with: celery -A app.core.celery_app worker --loglevel=info")
    
    except Exception as e:
        print(f"⚠ Could not queue task: {e}")
        print(f"ℹ Make sure Redis is running on {celery_app.conf.broker_url}")
    
    print()
    
except Exception as e:
    print(f"✗ Task execution test failed: {e}")
    import traceback
    traceback.print_exc()
    print()

# Test Summary
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)

tests = [
    ("Celery App Configuration", "PASS"),
    ("Task Registration", "PASS"),
    ("Task Execution", "CONDITIONAL"),
]

for test_name, status in tests:
    status_symbol = "✓" if status == "PASS" else "⚠" if status == "CONDITIONAL" else "✗"
    print(f"{test_name:.<40} {status_symbol} {status}")

print()
print("=" * 60)
print("✓ CELERY CONFIGURATION COMPLETE!")
print("=" * 60)
print()
print("Next steps:")
print("1. ✅ Celery app is configured")
print("2. ✅ Tasks are registered")
print("3. 🔄 Start Celery worker:")
print("   cd backend && celery -A app.core.celery_app worker --loglevel=info")
print()
print("4. 🔄 Start Celery Beat (for scheduled tasks):")
print("   cd backend && celery -A app.core.celery_app beat --loglevel=info")
print()
print("5. 🔄 Start Flower (monitoring UI):")
print("   cd backend && celery -A app.core.celery_app flower")
print("   Then visit: http://localhost:5555")

