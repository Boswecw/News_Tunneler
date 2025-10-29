-- Initialize PostgreSQL database for News Tunneler
-- This script runs automatically when the container is first created

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For GIN indexes on multiple columns

-- Create database (already created by POSTGRES_DB env var, but included for reference)
-- CREATE DATABASE news_tunneler;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE news_tunneler TO news_tunneler;

-- Set default search path
ALTER DATABASE news_tunneler SET search_path TO public;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'News Tunneler database initialized successfully';
END $$;

