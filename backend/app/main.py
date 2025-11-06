"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.db import engine
from app.core.logging import logger
from app.core.scheduler import start_scheduler, stop_scheduler
from app.core.structured_logging import setup_structured_logging, get_logger
from app.core.memory_cache import cache_cleanup_task
from app.core.secrets import validate_secrets_on_startup
from app.core.monitoring import setup_monitoring
from app.core.sentry import setup_sentry
from app.models import Base
from app.api import articles, sources, websocket, analysis, backtest, stream, signals, admin, ml, research, training, predict_bounds, auth
from app.api import settings as settings_router
from app.middleware.rate_limit import limiter, custom_rate_limit_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.request_size import RequestSizeLimitMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import asyncio

config = get_settings()

# Setup structured logging
setup_structured_logging(
    log_level="DEBUG" if config.debug else "INFO",
    log_file="logs/app.log"
)
structured_logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    structured_logger.info("Starting news-tunneler backend...", extra={'version': '1.0.0'})

    # Setup Sentry error tracking (before other initialization)
    setup_sentry()

    # Validate secrets
    validate_secrets_on_startup(config.env)

    Base.metadata.create_all(bind=engine)
    structured_logger.info("Database tables created/verified")
    start_scheduler()
    structured_logger.info("Scheduler started")

    # Start cache cleanup task
    asyncio.create_task(cache_cleanup_task())
    structured_logger.info("Cache cleanup task started")

    yield

    # Shutdown
    structured_logger.info("Shutting down news-tunneler backend...")
    stop_scheduler()
    structured_logger.info("Shutdown complete")


app = FastAPI(
    title="News Tunneler",
    description="Real-time news scoring and alerting system",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup Prometheus monitoring
setup_monitoring(app)

# Request ID middleware (must be first for proper logging)
app.add_middleware(RequestIDMiddleware)

# Request size limiting (10MB max, prevents DoS attacks)
app.add_middleware(RequestSizeLimitMiddleware, max_size=10_000_000)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router)
app.include_router(sources.router)
app.include_router(settings_router.router)
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(analysis.router)
app.include_router(backtest.router)
app.include_router(stream.router)
app.include_router(signals.router)
app.include_router(admin.router)
app.include_router(ml.router)
app.include_router(research.router)
app.include_router(training.router)
app.include_router(predict_bounds.router)


@app.get("/health")
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
def root() -> dict:
    """Root endpoint."""
    return {
        "name": "News Tunneler",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.debug,
    )

