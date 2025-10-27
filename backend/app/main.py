"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import get_settings
from app.core.db import engine
from app.core.logging import logger
from app.core.scheduler import start_scheduler, stop_scheduler
from app.models import Base
from app.api import articles, sources, settings, websocket

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting news-tunneler backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down news-tunneler backend...")
    stop_scheduler()


app = FastAPI(
    title="News Tunneler",
    description="Real-time news scoring and alerting system",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(articles.router)
app.include_router(sources.router)
app.include_router(settings.router)
app.include_router(websocket.router)


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
        port=settings.port,
        reload=settings.debug,
    )

