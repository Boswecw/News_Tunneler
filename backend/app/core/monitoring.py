"""Prometheus monitoring and metrics."""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI
from app.core.config import get_settings

settings = get_settings()

# Application info
app_info = Info('news_tunneler_app', 'News Tunneler application information')
app_info.info({
    'version': '1.0.0',
    'environment': settings.env
})

# Request metrics (handled by instrumentator)
# - http_requests_total
# - http_request_duration_seconds
# - http_requests_in_progress

# Custom business metrics
articles_processed = Counter(
    'news_tunneler_articles_processed_total',
    'Total number of articles processed',
    ['source_type']
)

signals_generated = Counter(
    'news_tunneler_signals_generated_total',
    'Total number of trading signals generated',
    ['signal_type']
)

predictions_made = Counter(
    'news_tunneler_predictions_made_total',
    'Total number of predictions made',
    ['ticker', 'horizon']
)

ml_model_inference_duration = Histogram(
    'news_tunneler_ml_inference_duration_seconds',
    'ML model inference duration in seconds',
    ['model_type', 'ticker']
)

cache_hits = Counter(
    'news_tunneler_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'news_tunneler_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

websocket_connections = Gauge(
    'news_tunneler_websocket_connections',
    'Current number of WebSocket connections'
)

database_query_duration = Histogram(
    'news_tunneler_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

api_errors = Counter(
    'news_tunneler_api_errors_total',
    'Total number of API errors',
    ['endpoint', 'error_type']
)

background_jobs_duration = Histogram(
    'news_tunneler_background_job_duration_seconds',
    'Background job duration in seconds',
    ['job_name']
)

background_jobs_success = Counter(
    'news_tunneler_background_jobs_success_total',
    'Total number of successful background jobs',
    ['job_name']
)

background_jobs_failure = Counter(
    'news_tunneler_background_jobs_failure_total',
    'Total number of failed background jobs',
    ['job_name']
)

# System metrics
active_users = Gauge(
    'news_tunneler_active_users',
    'Current number of active users'
)

database_connections = Gauge(
    'news_tunneler_database_connections',
    'Current number of database connections'
)


def setup_monitoring(app: FastAPI) -> None:
    """
    Setup Prometheus monitoring for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    if not settings.prometheus_enabled:
        return
    
    # Initialize instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )
    
    # Add custom metrics
    instrumentator.add(
        lambda info: info.modified_duration,
        metric_name="http_request_duration_seconds",
        metric_doc="HTTP request duration in seconds",
        metric_namespace="news_tunneler",
    )
    
    # Instrument the app
    instrumentator.instrument(app)
    
    # Expose metrics endpoint
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)


# Context managers for tracking metrics
class track_ml_inference:
    """Context manager to track ML inference duration."""
    
    def __init__(self, model_type: str, ticker: str):
        self.model_type = model_type
        self.ticker = ticker
        self.timer = None
    
    def __enter__(self):
        self.timer = ml_model_inference_duration.labels(
            model_type=self.model_type,
            ticker=self.ticker
        ).time()
        return self.timer.__enter__()
    
    def __exit__(self, *args):
        return self.timer.__exit__(*args)


class track_database_query:
    """Context manager to track database query duration."""
    
    def __init__(self, query_type: str):
        self.query_type = query_type
        self.timer = None
    
    def __enter__(self):
        self.timer = database_query_duration.labels(
            query_type=self.query_type
        ).time()
        return self.timer.__enter__()
    
    def __exit__(self, *args):
        return self.timer.__exit__(*args)


class track_background_job:
    """Context manager to track background job execution."""
    
    def __init__(self, job_name: str):
        self.job_name = job_name
        self.timer = None
    
    def __enter__(self):
        self.timer = background_jobs_duration.labels(
            job_name=self.job_name
        ).time()
        return self.timer.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            background_jobs_success.labels(job_name=self.job_name).inc()
        else:
            background_jobs_failure.labels(job_name=self.job_name).inc()
        return self.timer.__exit__(exc_type, exc_val, exc_tb)


# Helper functions
def record_article_processed(source_type: str) -> None:
    """Record that an article was processed."""
    articles_processed.labels(source_type=source_type).inc()


def record_signal_generated(signal_type: str) -> None:
    """Record that a signal was generated."""
    signals_generated.labels(signal_type=signal_type).inc()


def record_prediction_made(ticker: str, horizon: str) -> None:
    """Record that a prediction was made."""
    predictions_made.labels(ticker=ticker, horizon=horizon).inc()


def record_cache_hit(cache_type: str) -> None:
    """Record a cache hit."""
    cache_hits.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record a cache miss."""
    cache_misses.labels(cache_type=cache_type).inc()


def record_api_error(endpoint: str, error_type: str) -> None:
    """Record an API error."""
    api_errors.labels(endpoint=endpoint, error_type=error_type).inc()


def increment_websocket_connections() -> None:
    """Increment WebSocket connection count."""
    websocket_connections.inc()


def decrement_websocket_connections() -> None:
    """Decrement WebSocket connection count."""
    websocket_connections.dec()


def set_active_users(count: int) -> None:
    """Set the number of active users."""
    active_users.set(count)


def set_database_connections(count: int) -> None:
    """Set the number of database connections."""
    database_connections.set(count)

