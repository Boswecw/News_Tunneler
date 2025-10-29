"""
Celery Application Configuration

Provides distributed task queue for background processing.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings
from app.core.structured_logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Create Celery app
celery_app = Celery(
    "news_tunneler",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
)

# Configure task autodiscovery
celery_app.autodiscover_tasks([
    "app.tasks.llm_tasks",
    "app.tasks.rss_tasks",
    "app.tasks.digest_tasks",
    "app.tasks.ml_tasks",
], force=True)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Task result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    
    # Worker configuration
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        "app.tasks.llm_tasks.*": {"queue": "llm"},
        "app.tasks.rss_tasks.*": {"queue": "rss"},
        "app.tasks.digest_tasks.*": {"queue": "digest"},
        "app.tasks.ml_tasks.*": {"queue": "llm"},  # ML tasks use LLM queue
    },
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        # Poll RSS feeds every 5 minutes
        "poll-rss-feeds": {
            "task": "app.tasks.rss_tasks.poll_all_rss_feeds",
            "schedule": crontab(minute="*/5"),  # Every 5 minutes
        },
        
        # Send daily digest at 8 AM UTC
        "send-daily-digest": {
            "task": "app.tasks.digest_tasks.send_daily_digest",
            "schedule": crontab(hour=8, minute=0),  # 8:00 AM UTC
        },
        
        # Clean up old signals every day at midnight
        "cleanup-old-signals": {
            "task": "app.tasks.rss_tasks.cleanup_old_signals",
            "schedule": crontab(hour=0, minute=0),  # Midnight UTC
        },

        # Retrain ML models daily at 2 AM UTC
        "retrain-ml-models": {
            "task": "ml.scheduled_retrain",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM UTC
        },
    },
)

logger.info("Celery app configured", extra={
    "broker": celery_app.conf.broker_url,
    "backend": celery_app.conf.result_backend,
    "queues": ["llm", "rss", "digest"],
})


# Task event handlers
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    logger.info(f"Request: {self.request!r}")
    return {"status": "ok", "task_id": self.request.id}


# Celery signals for logging
from celery.signals import (
    task_prerun,
    task_postrun,
    task_failure,
    task_retry,
    task_success,
)


@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    """Log when a task starts."""
    logger.info(
        f"Task started: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100],
        }
    )


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
    """Log when a task completes."""
    logger.info(
        f"Task completed: {task.name}",
        extra={
            "task_id": task_id,
            "task_name": task.name,
            "result": str(retval)[:100] if retval else None,
        }
    )


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **extra):
    """Log when a task fails."""
    logger.error(
        f"Task failed: {sender.name}",
        exc_info=True,
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100],
        }
    )


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, **extra):
    """Log when a task is retried."""
    logger.warning(
        f"Task retry: {sender.name}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "reason": str(reason),
        }
    )


@task_success.connect
def task_success_handler(sender=None, result=None, **extra):
    """Log when a task succeeds."""
    logger.debug(
        f"Task success: {sender.name}",
        extra={
            "task_name": sender.name,
            "result": str(result)[:100] if result else None,
        }
    )


# Import tasks to register them
try:
    from app.tasks import llm_tasks, rss_tasks, digest_tasks, ml_tasks
    logger.info("Tasks imported successfully")
except ImportError as e:
    logger.warning(f"Could not import tasks: {e}")

