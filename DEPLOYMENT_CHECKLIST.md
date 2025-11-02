# 🚀 News Tunneler Deployment Checklist

Quick reference for deploying News Tunneler to production.

## 📋 Pre-Deployment

### 1. Choose Deployment Platform

- [ ] **Render** (Recommended) - One-click deploy, managed services
- [ ] **Docker** - Self-hosted with full control
- [ ] **Other Cloud** - Railway, Fly.io, Heroku, etc.

### 2. Gather API Keys (Optional but Recommended)

- [ ] OpenAI API key → [platform.openai.com](https://platform.openai.com)
- [ ] NewsAPI key → [newsapi.org](https://newsapi.org)
- [ ] Alpha Vantage key → [alphavantage.co](https://www.alphavantage.co)
- [ ] Polygon.io key → [polygon.io](https://polygon.io)

### 3. Setup Email Notifications (Optional)

- [ ] SMTP server details (Gmail, SendGrid, etc.)
- [ ] Generate app password (if using Gmail)
- [ ] Test email credentials

### 4. Setup Slack Notifications (Optional)

- [ ] Create Slack incoming webhook
- [ ] Test webhook URL

---

## 🎯 Render Deployment (Recommended)

### Quick Deploy

- [ ] Click **Deploy to Render** button in README
- [ ] Connect GitHub account
- [ ] Review services (Backend, Frontend, PostgreSQL, Redis)
- [ ] Click **Apply**
- [ ] Wait 10-15 minutes for deployment

### Manual Configuration

#### PostgreSQL Database
- [ ] Create PostgreSQL database
- [ ] Name: `news-tunneler-db`
- [ ] Plan: Starter ($7/month) or Free
- [ ] Save connection details

#### Redis Cache
- [ ] Create Redis instance
- [ ] Name: `news-tunneler-redis`
- [ ] Plan: Starter ($10/month)
- [ ] Save connection details

#### Backend Service
- [ ] Create Web Service
- [ ] Name: `news-tunneler-backend`
- [ ] Root Directory: `backend`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `./start.sh`
- [ ] Add environment variables (see below)
- [ ] Health Check Path: `/health`

#### Frontend Service
- [ ] Create Static Site
- [ ] Name: `news-tunneler-frontend`
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm install && npm run build`
- [ ] Publish Directory: `dist`
- [ ] Add environment variables (see below)

### Environment Variables

#### Backend (Required)
- [ ] `PYTHON_VERSION=3.12.0`
- [ ] `ENV=production`
- [ ] `USE_POSTGRESQL=true`
- [ ] `POSTGRES_HOST=<from-database>`
- [ ] `POSTGRES_PORT=5432`
- [ ] `POSTGRES_DB=news_tunneler`
- [ ] `POSTGRES_USER=<from-database>`
- [ ] `POSTGRES_PASSWORD=<from-database>`
- [ ] `REDIS_HOST=<from-redis>`
- [ ] `REDIS_PORT=6379`
- [ ] `JWT_SECRET_KEY=<generate-64-chars>`

#### Backend (Optional)
- [ ] `OPENAI_API_KEY=sk-...`
- [ ] `NEWSAPI_KEY=...`
- [ ] `ALPHAVANTAGE_KEY=...`
- [ ] `SMTP_HOST=smtp.gmail.com`
- [ ] `SMTP_PORT=587`
- [ ] `SMTP_USER=your-email@gmail.com`
- [ ] `SMTP_PASSWORD=your-app-password`
- [ ] `ALERT_EMAIL_TO=recipient@example.com`
- [ ] `SLACK_WEBHOOK_URL=https://hooks.slack.com/...`

#### Frontend
- [ ] `NODE_VERSION=20.11.0`
- [ ] `VITE_API_URL=<backend-url>`
- [ ] `VITE_WS_URL=<backend-url-with-wss>`

### Post-Deployment
- [ ] Wait for all services to deploy
- [ ] Check backend health: `https://your-backend.onrender.com/health`
- [ ] Check frontend: `https://your-frontend.onrender.com`
- [ ] Create admin user (see below)

---

## 🐳 Docker Deployment

### Prerequisites
- [ ] Docker & Docker Compose installed
- [ ] 4GB RAM, 2 CPU cores minimum
- [ ] 20GB disk space

### Steps

1. **Generate Secrets**
   ```bash
   cd backend
   python -m app.cli.generate_secrets
   ```
   - [ ] Review generated `.env` file
   - [ ] Update API keys
   - [ ] Update SMTP settings

2. **Start Services**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```
   - [ ] PostgreSQL started
   - [ ] Redis started
   - [ ] Backend started
   - [ ] Frontend started

3. **Verify Services**
   - [ ] Backend: http://localhost:8000/health
   - [ ] Frontend: http://localhost:3000
   - [ ] PostgreSQL: `docker exec -it news-tunneler-postgres pg_isready`
   - [ ] Redis: `docker exec -it news-tunneler-redis redis-cli ping`

4. **Optional: Start Monitoring**
   ```bash
   docker-compose -f docker-compose.prod.yml --profile monitoring up -d
   ```
   - [ ] Prometheus: http://localhost:9090
   - [ ] Grafana: http://localhost:3001

---

## 👤 Create Admin User

### Render
```bash
# In backend service shell
python -m app.cli.create_admin
```

### Docker
```bash
docker exec -it news-tunneler-backend python -m app.cli.create_admin
```

### Local
```bash
cd backend
source venv/bin/activate
python -m app.cli.create_admin
```

**Admin User Details:**
- [ ] Email: _______________
- [ ] Username: _______________
- [ ] Password: _______________ (save securely!)

---

## 🔒 Security Checklist

### Secrets
- [ ] JWT secret is 64+ characters
- [ ] PostgreSQL password is 16+ characters
- [ ] No default/weak passwords used
- [ ] `.env` file is not in version control

### Authentication
- [ ] `REQUIRE_AUTH=true` (for production)
- [ ] `ALLOW_REGISTRATION=false` (or implement approval)
- [ ] Admin user created with strong password

### Network
- [ ] HTTPS/SSL enabled
- [ ] CORS configured for your domain only
- [ ] Firewall rules configured (if self-hosted)

### Monitoring
- [ ] Prometheus metrics enabled
- [ ] Sentry error tracking configured (optional)
- [ ] Log aggregation setup (optional)

---

## ✅ Post-Deployment Verification

### Functionality
- [ ] Can access frontend
- [ ] Can access backend API docs
- [ ] Can login with admin user
- [ ] Articles are being fetched
- [ ] Signals are being generated
- [ ] Live charts are working
- [ ] Email notifications working (if configured)
- [ ] Slack notifications working (if configured)

### Performance
- [ ] Backend responds in < 500ms
- [ ] Frontend loads in < 3s
- [ ] Database queries are fast
- [ ] Redis cache is working

### Monitoring
- [ ] Logs are being generated
- [ ] Metrics are being collected
- [ ] Health checks are passing
- [ ] No errors in logs

---

## 🔄 Maintenance

### Daily
- [ ] Check error logs
- [ ] Monitor resource usage
- [ ] Verify data is being collected

### Weekly
- [ ] Review performance metrics
- [ ] Check for security updates
- [ ] Verify backups (if configured)

### Monthly
- [ ] Update dependencies
- [ ] Review and rotate secrets
- [ ] Optimize database (vacuum, analyze)
- [ ] Review and archive old data

---

## 📚 Documentation Links

- [Render Deployment Guide](docs/RENDER_DEPLOYMENT.md)
- [Docker Deployment Guide](docs/DEPLOYMENT.md)
- [Environment Variables Reference](docs/ENVIRONMENT_VARIABLES.md)
- [Technical Due Diligence](docs/TECHNICAL_DUE_DILIGENCE.md)
- [Main README](README.md)

---

## 🆘 Troubleshooting

### Backend won't start
1. Check logs for errors
2. Verify database connection
3. Verify Redis connection
4. Check environment variables
5. Run migrations: `alembic upgrade head`

### Frontend shows API errors
1. Verify `VITE_API_URL` is correct
2. Check backend is running
3. Verify CORS settings
4. Check browser console for errors

### Database connection errors
1. Verify PostgreSQL is running
2. Check connection string
3. Verify credentials
4. Check firewall rules

### No data appearing
1. Check RSS feeds are configured
2. Verify scheduler is running
3. Check logs for fetch errors
4. Manually trigger fetch (admin panel)

---

## 📞 Support

- **GitHub Issues**: [github.com/Boswecw/News_Tunneler/issues](https://github.com/Boswecw/News_Tunneler/issues)
- **Documentation**: [github.com/Boswecw/News_Tunneler/tree/master/docs](https://github.com/Boswecw/News_Tunneler/tree/master/docs)
- **Render Support**: [render.com/docs](https://render.com/docs)

---

**Last Updated**: 2025-11-02

