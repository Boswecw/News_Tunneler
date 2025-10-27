# Deployment Guide

## Local Development

### Quick Start

```bash
# Clone and setup
cd news-tunneler
cp .env.example .env

# Install dependencies
make install

# Start development servers
make dev
```

Access:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Build and Run

```bash
# Build images
make docker-build

# Start containers
make docker-up

# View logs
make docker-logs

# Stop containers
make docker-down
```

Access: http://localhost:5173

### Environment Setup

Create `.env` file:

```env
# Backend
DATABASE_URL=sqlite:///./app.db
ENVIRONMENT=production
LOG_LEVEL=info
POLL_INTERVAL_SEC=900

# Optional: Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: Email
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Optional: NewsAPI
NEWSAPI_KEY=your-newsapi-key

# Frontend
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/alerts
```

## Production Deployment

### Server Requirements
- Ubuntu 20.04+ or similar
- 2GB RAM minimum
- 10GB disk space
- Python 3.12+
- Node.js 18+

### Manual Deployment

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/news-tunneler.git
cd news-tunneler
```

#### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Seed initial data (optional)
python -c "from app.seeds.seed import seed_sources, seed_articles, seed_settings; seed_sources(); seed_articles(); seed_settings()"
```

#### 3. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Build for production
npm run build
```

#### 4. Configure Systemd Services

Create `/etc/systemd/system/news-tunneler-backend.service`:

```ini
[Unit]
Description=News Tunneler Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/opt/news-tunneler/backend
Environment="PATH=/opt/news-tunneler/backend/venv/bin"
ExecStart=/opt/news-tunneler/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/news-tunneler-frontend.service`:

```ini
[Unit]
Description=News Tunneler Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/news-tunneler/frontend
ExecStart=/usr/bin/npm run preview
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable news-tunneler-backend
sudo systemctl enable news-tunneler-frontend
sudo systemctl start news-tunneler-backend
sudo systemctl start news-tunneler-frontend
```

#### 5. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/news-tunneler`:

```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 80;
    server_name news-tunneler.example.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://backend;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/news-tunneler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d news-tunneler.example.com
```

### Cloud Deployment

#### AWS EC2

1. Launch Ubuntu 20.04 instance
2. Install Docker and Docker Compose
3. Clone repository
4. Create `.env` file
5. Run `docker-compose up -d`
6. Configure security groups (ports 80, 443)
7. Setup Route53 DNS
8. Configure CloudFront CDN (optional)

#### Heroku

```bash
# Create app
heroku create news-tunneler

# Set environment variables
heroku config:set DATABASE_URL=postgresql://...
heroku config:set SLACK_WEBHOOK_URL=...

# Deploy
git push heroku main
```

#### DigitalOcean App Platform

1. Connect GitHub repository
2. Create app from `docker-compose.yml`
3. Set environment variables
4. Deploy

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:5173
```

### Logs

```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# System logs
journalctl -u news-tunneler-backend -f
```

### Metrics

Monitor:
- CPU usage
- Memory usage
- Disk space
- Database size
- API response times
- WebSocket connections

## Backup & Recovery

### Database Backup

```bash
# Backup SQLite database
cp backend/app.db backend/app.db.backup

# Or with timestamp
cp backend/app.db backend/app.db.$(date +%Y%m%d_%H%M%S).backup
```

### Restore

```bash
cp backend/app.db.backup backend/app.db
```

## Scaling

### Horizontal Scaling

For multiple instances:

1. Use PostgreSQL instead of SQLite
2. Deploy backend to multiple servers
3. Use load balancer (Nginx, HAProxy)
4. Use Redis for caching
5. Use message queue (RabbitMQ, Celery)

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database queries
- Enable caching
- Use CDN for frontend

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose logs backend

# Check port availability
lsof -i :8000

# Check database
sqlite3 backend/app.db ".tables"
```

### Frontend won't connect

```bash
# Check API endpoint
curl http://localhost:8000/health

# Check WebSocket
wscat -c ws://localhost:8000/ws/alerts
```

### High memory usage

- Check for memory leaks
- Limit article retention
- Optimize queries
- Increase server resources

### Slow performance

- Check database indexes
- Monitor API response times
- Check network latency
- Optimize frontend bundle size

## Security Checklist

- [ ] Use HTTPS/SSL
- [ ] Set strong admin token
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable firewall
- [ ] Regular backups
- [ ] Monitor logs for errors
- [ ] Keep dependencies updated
- [ ] Use strong database passwords
- [ ] Restrict API access if needed

## Maintenance

### Regular Tasks

- Monitor disk space
- Check logs for errors
- Update dependencies
- Backup database
- Review performance metrics

### Updates

```bash
# Backend
pip install --upgrade -r requirements.txt

# Frontend
npm update

# Docker images
docker-compose pull
docker-compose up -d
```

## Support

For issues:
1. Check logs
2. Review documentation
3. Check GitHub issues
4. Open new issue with details

