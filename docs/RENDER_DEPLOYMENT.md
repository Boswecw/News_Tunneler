# News Tunneler - Render Deployment Guide

This guide covers deploying News Tunneler to Render.com with PostgreSQL and Redis.

## 🚀 Quick Deploy

### Option 1: One-Click Deploy (Recommended)

Click the button below to deploy News Tunneler to Render:

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Boswecw/News_Tunneler)

This will automatically:
- Create PostgreSQL database
- Create Redis instance
- Deploy backend API
- Deploy frontend static site
- Set up environment variables
- Run database migrations

### Option 2: Manual Deployment

Follow the steps below for manual deployment with more control.

---

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Fork or connect your News Tunneler repo
3. **API Keys** (optional but recommended):
   - OpenAI API key (for LLM analysis)
   - NewsAPI key (for news sources)
   - Alpha Vantage key (for stock data)

---

## 🗄️ Step 1: Create PostgreSQL Database

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **PostgreSQL**
3. Configure:
   - **Name**: `news-tunneler-db`
   - **Database**: `news_tunneler`
   - **User**: `news_tunneler`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Starter ($7/month) or Free
4. Click **Create Database**
5. **Save the connection details** (you'll need them later)

---

## 🔴 Step 2: Create Redis Instance

1. Click **New** → **Redis**
2. Configure:
   - **Name**: `news-tunneler-redis`
   - **Region**: Oregon (same as database)
   - **Plan**: Starter ($10/month) or Free
   - **Maxmemory Policy**: `allkeys-lru`
3. Click **Create Redis**
4. **Save the connection details**

---

## 🖥️ Step 3: Deploy Backend API

1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `news-tunneler-backend`
   - **Region**: Oregon
   - **Branch**: `master`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `./start.sh`
   - **Plan**: Starter ($7/month) or Free

4. **Add Environment Variables**:

   Click **Advanced** → **Add Environment Variable** and add:

   ```bash
   # Python
   PYTHON_VERSION=3.12.0
   
   # Application
   ENV=production
   DEBUG=false
   LOG_LEVEL=INFO
   
   # Database (from Step 1)
   USE_POSTGRESQL=true
   POSTGRES_HOST=<your-postgres-host>
   POSTGRES_PORT=5432
   POSTGRES_DB=news_tunneler
   POSTGRES_USER=news_tunneler
   POSTGRES_PASSWORD=<your-postgres-password>
   
   # Redis (from Step 2)
   REDIS_HOST=<your-redis-host>
   REDIS_PORT=6379
   
   # Authentication (generate secure values)
   JWT_SECRET_KEY=<generate-64-char-random-string>
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
   REQUIRE_AUTH=false
   ALLOW_REGISTRATION=true
   
   # API Keys (optional)
   OPENAI_API_KEY=sk-...
   NEWSAPI_KEY=...
   ALPHAVANTAGE_KEY=...
   POLYGON_API_KEY=...
   
   # Notifications (optional)
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ALERT_EMAIL_TO=recipient@example.com
   
   # Monitoring
   PROMETHEUS_ENABLED=true
   SENTRY_DSN=https://...@sentry.io/...
   ```

5. **Health Check Path**: `/health`

6. Click **Create Web Service**

7. Wait for deployment to complete (5-10 minutes)

8. **Note the backend URL**: `https://news-tunneler-backend.onrender.com`

---

## 🌐 Step 4: Deploy Frontend

1. Click **New** → **Static Site**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `news-tunneler-frontend`
   - **Region**: Oregon
   - **Branch**: `master`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. **Add Environment Variables**:

   ```bash
   NODE_VERSION=20.11.0
   VITE_API_URL=https://news-tunneler-backend.onrender.com
   VITE_WS_URL=wss://news-tunneler-backend.onrender.com
   ```

5. **Headers** (optional, for security):
   - Add in **Settings** → **Headers**:
   ```
   /*
     X-Frame-Options: DENY
     X-Content-Type-Options: nosniff
     Referrer-Policy: strict-origin-when-cross-origin
   
   /assets/*
     Cache-Control: public, max-age=31536000, immutable
   ```

6. **Redirects/Rewrites** (for SPA routing):
   - Add in **Settings** → **Redirects/Rewrites**:
   ```
   /*  /index.html  200
   ```

7. Click **Create Static Site**

8. Wait for deployment (3-5 minutes)

9. **Your app is live!** 🎉
   - Frontend: `https://news-tunneler-frontend.onrender.com`
   - Backend: `https://news-tunneler-backend.onrender.com`
   - API Docs: `https://news-tunneler-backend.onrender.com/docs`

---

## 🔐 Step 5: Create Admin User

After backend deployment completes:

1. Go to backend service → **Shell**
2. Run:
   ```bash
   python -m app.cli.create_admin
   ```
3. Follow prompts to create admin account

---

## 🔧 Configuration Tips

### Generate Secure JWT Secret

```bash
# On your local machine
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the output and use it for `JWT_SECRET_KEY`.

### Update CORS Settings

If your frontend is on a custom domain, update backend CORS:

1. Go to backend service → **Environment**
2. Add:
   ```bash
   CORS_ORIGINS=https://your-custom-domain.com,https://news-tunneler-frontend.onrender.com
   ```

### Enable Authentication

For production, enable authentication:

1. Set `REQUIRE_AUTH=true`
2. Set `ALLOW_REGISTRATION=false` (or keep true if you want public signups)
3. Redeploy backend

---

## 📊 Monitoring

### View Logs

1. Go to service → **Logs**
2. Real-time logs appear here
3. Filter by severity (INFO, WARNING, ERROR)

### Metrics

1. Go to service → **Metrics**
2. View:
   - CPU usage
   - Memory usage
   - Request count
   - Response time

### Prometheus Metrics

Access at: `https://news-tunneler-backend.onrender.com/metrics`

---

## 🔄 Updates & Maintenance

### Auto-Deploy

Render automatically deploys when you push to `master` branch.

### Manual Deploy

1. Go to service → **Manual Deploy**
2. Click **Deploy latest commit**

### Database Backups

Render automatically backs up PostgreSQL databases daily (on paid plans).

Manual backup:
1. Go to database → **Backups**
2. Click **Create Backup**

### Rollback

1. Go to service → **Events**
2. Find previous successful deploy
3. Click **Rollback to this version**

---

## 💰 Pricing

### Free Tier
- **Backend**: Free (spins down after 15 min inactivity)
- **Frontend**: Free
- **PostgreSQL**: Free (90 days, then $7/month)
- **Redis**: Not available on free tier

**Total Free**: $0/month (first 90 days)

### Starter Tier (Recommended)
- **Backend**: $7/month (always on)
- **Frontend**: Free
- **PostgreSQL**: $7/month
- **Redis**: $10/month

**Total**: $24/month

### Professional Tier
- **Backend**: $25/month (more resources)
- **Frontend**: Free
- **PostgreSQL**: $20/month (more storage)
- **Redis**: $25/month (more memory)

**Total**: $70/month

---

## 🐛 Troubleshooting

### Backend Won't Start

**Check logs for:**
- Database connection errors → Verify `POSTGRES_*` env vars
- Missing dependencies → Check `requirements.txt`
- Port binding errors → Render uses `$PORT` env var

**Solution:**
```bash
# In start.sh, use:
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

### Frontend Shows API Errors

**Check:**
- `VITE_API_URL` points to correct backend URL
- Backend is running and healthy
- CORS is configured correctly

**Solution:**
1. Update `VITE_API_URL` in frontend env vars
2. Redeploy frontend

### Database Migration Fails

**Check:**
- PostgreSQL is running
- Connection string is correct
- Alembic is installed

**Solution:**
```bash
# In backend shell
alembic upgrade head
```

### Redis Connection Errors

**Check:**
- Redis instance is running
- `REDIS_HOST` and `REDIS_PORT` are correct
- No password required (Render Redis doesn't use passwords by default)

---

## 🔗 Custom Domain

### Add Custom Domain to Frontend

1. Go to frontend service → **Settings** → **Custom Domains**
2. Click **Add Custom Domain**
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Add DNS records as shown:
   ```
   Type: CNAME
   Name: app
   Value: news-tunneler-frontend.onrender.com
   ```
5. Wait for DNS propagation (5-60 minutes)
6. Render automatically provisions SSL certificate

### Add Custom Domain to Backend

1. Go to backend service → **Settings** → **Custom Domains**
2. Add `api.yourdomain.com`
3. Update frontend `VITE_API_URL` to `https://api.yourdomain.com`
4. Redeploy frontend

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [News Tunneler GitHub](https://github.com/Boswecw/News_Tunneler)
- [News Tunneler Issues](https://github.com/Boswecw/News_Tunneler/issues)

---

## ✅ Post-Deployment Checklist

- [ ] Backend is deployed and healthy
- [ ] Frontend is deployed and accessible
- [ ] PostgreSQL database is created
- [ ] Redis instance is created
- [ ] Database migrations ran successfully
- [ ] Admin user created
- [ ] API keys configured (OpenAI, NewsAPI, etc.)
- [ ] Email notifications configured (optional)
- [ ] Slack notifications configured (optional)
- [ ] Custom domain configured (optional)
- [ ] SSL certificate active
- [ ] Monitoring enabled
- [ ] Backups configured

**Congratulations! Your News Tunneler is live on Render! 🎉**

