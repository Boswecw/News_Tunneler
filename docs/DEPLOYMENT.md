# News Tunneler - Production Deployment Guide

This guide covers deploying News Tunneler to production with PostgreSQL, Redis, and monitoring.

## Prerequisites

- Docker & Docker Compose installed
- Minimum 4GB RAM, 2 CPU cores
- 20GB disk space

## Quick Start

### 1. Generate Secure Secrets

```bash
cd backend
python -m app.cli.generate_secrets
```

### 2. Create Admin User

```bash
cd backend
python -m app.cli.create_admin
```

### 3. Deploy with Docker

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# With monitoring (Prometheus + Grafana)
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

## Services

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Database Migration

Migrate from SQLite to PostgreSQL:

```bash
docker-compose -f docker-compose.prod.yml up -d postgres
cd backend
python -m app.cli.migrate_to_postgres
```

## Security Checklist

- [ ] All secrets are strong and unique
- [ ] `REQUIRE_AUTH=true` is set
- [ ] `ALLOW_REGISTRATION=false` in production
- [ ] PostgreSQL password is 16+ characters
- [ ] Admin user created with strong password

## Monitoring

Access Grafana at http://localhost:3001 with credentials from `.env`.

Key metrics at http://localhost:8000/metrics:
- HTTP requests and latency
- Articles processed
- Trading signals generated
- ML predictions made
- Cache performance

## Maintenance

### Backups

```bash
docker exec news-tunneler-postgres pg_dump -U news_tunneler news_tunneler > backup.sql
```

### Updates

```bash
git pull origin master
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
docker exec news-tunneler-backend alembic upgrade head
```

For detailed documentation, see the full deployment guide in the repository.
