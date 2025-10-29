"""Database connection and session management."""
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from .config import get_settings

settings = get_settings()

# Determine database URL
database_url = settings.effective_database_url

# Configure engine based on database type
if settings.use_postgresql:
    # PostgreSQL with connection pooling
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=settings.postgres_pool_size,
        max_overflow=settings.postgres_max_overflow,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        echo=settings.debug,
    )
else:
    # SQLite without connection pooling
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # Disable pooling for SQLite
        echo=settings.debug,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Dependency for FastAPI to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for DB session outside of FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

