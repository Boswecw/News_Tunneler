# Environment Variables Reference

Complete reference for all News Tunneler environment variables.

## 🔐 Required Variables (Production)

These **must** be set for production deployment:

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT tokens (64+ chars) | `<generate-with-secrets-tool>` |
| `POSTGRES_PASSWORD` | PostgreSQL database password (16+ chars) | `<generate-with-secrets-tool>` |
| `USE_POSTGRESQL` | Enable PostgreSQL (set to `true` in production) | `true` |
| `POSTGRES_HOST` | PostgreSQL host | `postgres` or `dpg-xxx.render.com` |
| `POSTGRES_DB` | PostgreSQL database name | `news_tunneler` |
| `POSTGRES_USER` | PostgreSQL username | `news_tunneler` |

## 🔑 API Keys (Optional but Recommended)

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `OPENAI_API_KEY` | OpenAI API key for LLM analysis | [platform.openai.com](https://platform.openai.com) |
| `NEWSAPI_KEY` | NewsAPI key for news sources | [newsapi.org](https://newsapi.org) |
| `ALPHAVANTAGE_KEY` | Alpha Vantage key for stock data | [alphavantage.co](https://www.alphavantage.co) |
| `POLYGON_API_KEY` | Polygon.io key for market data | [polygon.io](https://polygon.io) |

## 📧 Email Notifications (Optional)

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` (TLS) or `465` (SSL) |
| `SMTP_USER` | SMTP username/email | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP password/app password | `your-app-password` |
| `ALERT_EMAIL_TO` | Recipient email(s) (comma-separated) | `user@example.com,admin@example.com` |

### Gmail Setup

1. Enable 2-factor authentication
2. Generate app password: [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Use app password for `SMTP_PASSWORD`

## 💬 Slack Notifications (Optional)

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | [api.slack.com/messaging/webhooks](https://api.slack.com/messaging/webhooks) |

## 🗄️ Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_POSTGRESQL` | `false` | Use PostgreSQL instead of SQLite |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `news_tunneler` | Database name |
| `POSTGRES_USER` | `news_tunneler` | Database user |
| `POSTGRES_PASSWORD` | - | Database password (required) |
| `POSTGRES_POOL_SIZE` | `10` | Connection pool size |
| `POSTGRES_MAX_OVERFLOW` | `20` | Max overflow connections |

## 🔴 Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | - | Redis password (optional) |

## 🔒 Authentication & Security

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | - | JWT signing key (required, 32+ chars) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token expiry (minutes) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiry (days) |
| `REQUIRE_AUTH` | `false` | Require authentication for all endpoints |
| `ALLOW_REGISTRATION` | `true` | Allow new user registration |

## 📊 Monitoring & Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_ENABLED` | `true` | Enable Prometheus metrics |
| `PROMETHEUS_PORT` | `9090` | Prometheus port |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `SENTRY_DSN` | - | Sentry error tracking DSN |

## 🎯 Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `development` | Environment (development, production) |
| `DEBUG` | `false` | Enable debug mode |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |

## 🌐 Frontend Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.yourdomain.com` |
| `VITE_WS_URL` | Backend WebSocket URL | `wss://api.yourdomain.com` |

## 📝 Example .env File

### Development (SQLite)

```bash
# Application
ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database (SQLite - default)
USE_POSTGRESQL=false

# Authentication (weak keys OK for dev)
JWT_SECRET_KEY=dev-secret-key-change-in-production
REQUIRE_AUTH=false
ALLOW_REGISTRATION=true

# API Keys (optional)
OPENAI_API_KEY=sk-...
NEWSAPI_KEY=...
```

### Production (PostgreSQL + Redis)

```bash
# Application
ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database
USE_POSTGRESQL=true
POSTGRES_HOST=dpg-xxx.render.com
POSTGRES_PORT=5432
POSTGRES_DB=news_tunneler
POSTGRES_USER=news_tunneler
POSTGRES_PASSWORD=<strong-password-32-chars>

# Redis
REDIS_HOST=red-xxx.render.com
REDIS_PORT=6379

# Authentication
JWT_SECRET_KEY=<generate-64-char-random-string>
JWT_ALGORITHM=HS256
REQUIRE_AUTH=true
ALLOW_REGISTRATION=false

# API Keys
OPENAI_API_KEY=sk-...
NEWSAPI_KEY=...
ALPHAVANTAGE_KEY=...

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=recipient@example.com

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=https://...@sentry.io/...
```

## 🛠️ Generating Secure Secrets

### Using Python

```bash
# Generate JWT secret (64 characters)
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate database password (32 characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Using News Tunneler CLI

```bash
cd backend
python -m app.cli.generate_secrets
```

This generates a complete `.env` file with secure random secrets.

## ✅ Validation

News Tunneler automatically validates secrets on startup:

- **Errors**: Critical issues that prevent startup in production
- **Warnings**: Issues that should be fixed but don't prevent startup
- **Recommendations**: Optional improvements

Check logs on startup for validation results.

## 🔗 Related Documentation

- [Render Deployment Guide](RENDER_DEPLOYMENT.md)
- [Docker Deployment Guide](DEPLOYMENT.md)
- [Technical Due Diligence](TECHNICAL_DUE_DILIGENCE.md)

