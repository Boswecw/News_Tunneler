"""CLI tool to migrate data from SQLite to PostgreSQL."""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.models.base import Base
from app.models import (
    Source, Article, Score, Setting, Webhook, PriceCache,
    Signal, ModelRun, ResearchFeatures, ResearchLabels,
    OpportunityCache, PredictionBounds
)

settings = get_settings()


def migrate_table(source_session, target_session, model_class, batch_size=1000):
    """
    Migrate a single table from source to target database.
    
    Args:
        source_session: Source database session
        target_session: Target database session
        model_class: SQLAlchemy model class
        batch_size: Number of records to process at once
    """
    table_name = model_class.__tablename__
    print(f"Migrating {table_name}...", end=" ", flush=True)
    
    try:
        # Count total records
        total = source_session.query(model_class).count()
        if total == 0:
            print("✓ (0 records)")
            return
        
        # Migrate in batches
        migrated = 0
        offset = 0
        
        while offset < total:
            # Fetch batch from source
            records = source_session.query(model_class).offset(offset).limit(batch_size).all()
            
            if not records:
                break
            
            # Convert to dicts and create new instances
            for record in records:
                # Get all columns
                record_dict = {
                    column.name: getattr(record, column.name)
                    for column in model_class.__table__.columns
                }
                
                # Create new instance
                new_record = model_class(**record_dict)
                target_session.add(new_record)
            
            # Commit batch
            target_session.commit()
            migrated += len(records)
            offset += batch_size
            
            # Progress indicator
            print(f"\rMigrating {table_name}... {migrated}/{total}", end="", flush=True)
        
        print(f"\r✓ Migrated {table_name}: {migrated} records")
        
    except Exception as e:
        print(f"\r❌ Error migrating {table_name}: {e}")
        target_session.rollback()
        raise


def main():
    """Main migration function."""
    print("=" * 70)
    print("News Tunneler - SQLite to PostgreSQL Migration")
    print("=" * 70)
    print()
    
    # Check if PostgreSQL is configured
    if not settings.use_postgresql:
        print("❌ Error: PostgreSQL is not enabled in settings")
        print("   Set USE_POSTGRESQL=true in your .env file")
        return
    
    # Confirm migration
    print("⚠️  WARNING: This will migrate all data from SQLite to PostgreSQL")
    print()
    print(f"Source (SQLite): {settings.database_url}")
    print(f"Target (PostgreSQL): {settings.postgres_url}")
    print()
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted. No changes made.")
        return
    
    print()
    print("Starting migration...")
    print()
    
    # Create engines
    sqlite_engine = create_engine(settings.database_url)
    postgres_engine = create_engine(settings.postgres_url)
    
    # Create sessions
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        # Create all tables in PostgreSQL
        print("Creating PostgreSQL tables...")
        Base.metadata.create_all(bind=postgres_engine)
        print("✓ Tables created")
        print()
        
        # Migrate tables in order (respecting foreign keys)
        tables_to_migrate = [
            Source,
            Article,
            Score,
            Setting,
            Webhook,
            PriceCache,
            Signal,
            ModelRun,
            ResearchFeatures,
            ResearchLabels,
            OpportunityCache,
            PredictionBounds,
        ]
        
        start_time = datetime.now()
        
        for model_class in tables_to_migrate:
            migrate_table(sqlite_session, postgres_session, model_class)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 70)
        print(f"✅ Migration completed successfully in {duration:.2f} seconds!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Verify data in PostgreSQL")
        print("  2. Update your .env file to use PostgreSQL")
        print("  3. Restart the application")
        print("  4. Backup and archive the SQLite database")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Migration failed: {e}")
        print("=" * 70)
        print()
        print("The PostgreSQL database may be in an inconsistent state.")
        print("You may need to drop and recreate the database before retrying.")
        
    finally:
        sqlite_session.close()
        postgres_session.close()


if __name__ == "__main__":
    main()

