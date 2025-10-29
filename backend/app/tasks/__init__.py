"""Background tasks package."""
from app.tasks.labeler import label_signals

# Import Celery tasks to register them
try:
    from app.tasks import llm_tasks, rss_tasks, digest_tasks
    __all__ = ["label_signals", "llm_tasks", "rss_tasks", "digest_tasks"]
except ImportError:
    __all__ = ["label_signals"]

