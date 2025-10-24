# 🚀 Production Deployment Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Setup](#environment-setup)
4. [Static Files Setup](#static-files-setup)
5. [Database Migration](#database-migration)
6. [Running with Gunicorn](#running-with-gunicorn)
7. [Nginx Configuration](#nginx-configuration)
8. [Systemd Service](#systemd-service)
9. [SSL/HTTPS Setup](#sslhttps-setup)
10. [Monitoring & Logs](#monitoring--logs)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **OS**: Linux (Ubuntu 20.04/22.04 recommended)
- **RAM**: Minimum 2GB (4GB+ recommended for large scraping operations)
- **Storage**: 10GB+ free space

### Required Services
- Web server (Nginx or Apache)
- Process supervisor (systemd or supervisor)
- SSL certificate (Let's Encrypt recommended)

---

## Pre-Deployment Checklist

### 1. **Security Check** ✅

```bash
# Generate a strong secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Update `.env.production`:
```bash
DJANGO_SECRET_KEY=your-generated-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip
```

### 2. **Install Dependencies**

```bash
# Clone/upload your project
cd /path/to/linkedin_scraper-web-update-Feature

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. **Environment Variables**

```bash
# Create production environment file
cp .env.example .env

# Edit with your production values
nano .env
```

**Important**: Never commit `.env` to git!

### 4. **File Permissions**

```bash
# Ensure proper ownership
sudo chown -R www-data:www-data /path/to/your/project

# Or if using a specific user
sudo chown -R your-user:your-user /path/to/your/project
```

---

## Environment Setup

### Create `.env` for Production

```bash
# Django Core
DJANGO_SECRET_KEY=your-production-secret-key
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,123.45.67.89

# Security
SECURE_SSL_REDIRECT=True

# (Copy all other settings from .env.example)
```

---

## Static Files Setup

### 1. **Collect Static Files**

```bash
# Activate virtual environment
source venv/bin/activate

# Collect all static files into staticfiles/
python manage.py collectstatic --noinput
```

This will:
- Gather all CSS, JS, images from apps
- Place them in `/staticfiles/` directory
- Compress and optimize with WhiteNoise

### 2. **Verify Static Files**

```bash
# Check that staticfiles directory exists
ls -la staticfiles/

# Should see:
# - admin/ (Django admin static files)
# - scraper/ (Your app's static files)
# - staticfiles.json (WhiteNoise manifest)
```

### 3. **Create Media Directory**

```bash
# Create media directory for file uploads (resumes, etc.)
mkdir -p media/resumes
chmod 755 media
```

---

## Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser (for admin access)
python manage.py createsuperuser

# Verify database
python manage.py check --deploy
```

The `check --deploy` command will show security warnings/recommendations.

---

## Running with Gunicorn

### 1. **Test Gunicorn**

```bash
# Simple test run
gunicorn linkedin_scraper.wsgi:application --bind 0.0.0.0:8000

# Test with config file
gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application
```

Visit `http://your-server-ip:8000` to verify.

### 2. **Gunicorn Configuration**

The `gunicorn_config.py` is already configured with:
- Optimal worker count (CPU cores × 2 + 1)
- 120-second timeout (for long scraping tasks)
- Auto-restart after 1000 requests
- Logging to stdout/stderr

### 3. **Environment Variables for Gunicorn**

```bash
# Optional: Override port
export PORT=8000

# Optional: Enable auto-reload (dev only)
export GUNICORN_RELOAD=True
```

---

## Nginx Configuration

### 1. **Install Nginx**

```bash
sudo apt update
sudo apt install nginx
```

### 2. **Create Nginx Site Config**

```bash
sudo nano /etc/nginx/sites-available/linkedin_scraper
```

**Paste this configuration:**

```nginx
# Upstream Gunicorn server
upstream linkedin_scraper {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    client_max_body_size 20M;  # Allow resume uploads
    
    # Logging
    access_log /var/log/nginx/linkedin_scraper_access.log;
    error_log /var/log/nginx/linkedin_scraper_error.log;
    
    # Static files (served by Nginx for performance)
    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files (user uploads)
    location /media/ {
        alias /path/to/your/project/media/;
        expires 7d;
    }
    
    # Proxy to Gunicorn
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        
        # Long timeout for scraping operations
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        proxy_pass http://linkedin_scraper;
    }
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 3. **Enable Site**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/linkedin_scraper /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Systemd Service

### 1. **Create Service File**

```bash
sudo nano /etc/systemd/system/linkedin_scraper.service
```

**Paste this:**

```ini
[Unit]
Description=LinkedIn Scraper Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/your/project
Environment="PATH=/path/to/your/project/venv/bin"
ExecStart=/path/to/your/project/venv/bin/gunicorn \
          -c /path/to/your/project/gunicorn_config.py \
          linkedin_scraper.wsgi:application

# Restart policy
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=linkedin_scraper

[Install]
WantedBy=multi-user.target
```

**Replace** `/path/to/your/project` with actual path!

### 2. **Enable and Start Service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable linkedin_scraper

# Start service
sudo systemctl start linkedin_scraper

# Check status
sudo systemctl status linkedin_scraper
```

### 3. **Manage Service**

```bash
# Start
sudo systemctl start linkedin_scraper

# Stop
sudo systemctl stop linkedin_scraper

# Restart
sudo systemctl restart linkedin_scraper

# View logs
sudo journalctl -u linkedin_scraper -f
```

---

## SSL/HTTPS Setup

### 1. **Install Certbot**

```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. **Obtain SSL Certificate**

```bash
# Automatic setup (recommended)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow prompts to:
# 1. Enter email
# 2. Agree to terms
# 3. Choose redirect HTTP to HTTPS (Yes)
```

### 3. **Auto-Renewal**

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot auto-renews via cron
# Check: /etc/cron.d/certbot
```

### 4. **Update .env**

```bash
SECURE_SSL_REDIRECT=True
```

Restart your service:
```bash
sudo systemctl restart linkedin_scraper
```

---

## Monitoring & Logs

### 1. **Application Logs**

```bash
# View Gunicorn logs
sudo journalctl -u linkedin_scraper -f

# Filter by level
sudo journalctl -u linkedin_scraper -p err -f

# View last 100 lines
sudo journalctl -u linkedin_scraper -n 100
```

### 2. **Nginx Logs**

```bash
# Access log
sudo tail -f /var/log/nginx/linkedin_scraper_access.log

# Error log
sudo tail -f /var/log/nginx/linkedin_scraper_error.log
```

### 3. **Django Logs**

Django logs to console (captured by systemd journal).

To log to file, update `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/path/to/your/project/logs/django.log',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

---

## Troubleshooting

### Issue: Static Files Not Loading

**Check:**
1. Run `python manage.py collectstatic`
2. Verify `STATIC_ROOT` path in settings
3. Check Nginx config `alias` path
4. Check file permissions: `chmod -R 755 staticfiles/`

**Test:**
```bash
# Direct file access
curl http://yourdomain.com/static/scraper/css/main.css
```

---

### Issue: 502 Bad Gateway

**Possible causes:**
1. Gunicorn not running
2. Wrong socket/port in Nginx config
3. Firewall blocking port 8000

**Debug:**
```bash
# Check if Gunicorn is running
sudo systemctl status linkedin_scraper

# Test Gunicorn directly
curl http://127.0.0.1:8000

# Check Nginx error log
sudo tail -f /var/log/nginx/linkedin_scraper_error.log
```

---

### Issue: Permission Denied

**Fix permissions:**
```bash
# For www-data user
sudo chown -R www-data:www-data /path/to/your/project

# Make directories writable
sudo chmod -R 755 /path/to/your/project
sudo chmod -R 775 /path/to/your/project/media
sudo chmod -R 775 /path/to/your/project/staticfiles
```

---

### Issue: Long-Running Tasks Timeout

Increase timeouts:

**Gunicorn** (`gunicorn_config.py`):
```python
timeout = 300  # 5 minutes
```

**Nginx** (in location block):
```nginx
proxy_read_timeout 300s;
proxy_connect_timeout 75s;
```

---

## Performance Optimization

### 1. **Database**

For production, consider PostgreSQL instead of SQLite:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'linkedin_scraper_db',
        'USER': 'db_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. **Caching** (Optional)

Add Redis for caching:

```bash
pip install django-redis
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. **Static File Compression**

WhiteNoise already compresses files. Verify:

```bash
ls staticfiles/
# Should see .gz files alongside originals
```

---

## Backup Strategy

### 1. **Database Backup**

```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup-$(date +%Y%m%d)

# PostgreSQL
pg_dump linkedin_scraper_db > backup-$(date +%Y%m%d).sql
```

### 2. **Media Files Backup**

```bash
tar -czf media-backup-$(date +%Y%m%d).tar.gz media/
```

### 3. **Automated Backups**

Create a cron job:
```bash
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup-script.sh
```

---

## Quick Reference Commands

```bash
# Collect static files
python manage.py collectstatic --noinput

# Check deployment settings
python manage.py check --deploy

# Start Gunicorn (manually)
gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application

# Service management
sudo systemctl start linkedin_scraper
sudo systemctl stop linkedin_scraper
sudo systemctl restart linkedin_scraper
sudo systemctl status linkedin_scraper

# View logs
sudo journalctl -u linkedin_scraper -f

# Nginx
sudo systemctl restart nginx
sudo nginx -t

# SSL renewal
sudo certbot renew
```

---

## Support & Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Check disk space: `df -h`
- Review error logs
- Monitor CPU/RAM usage: `htop`

**Monthly:**
- Update dependencies: `pip list --outdated`
- Review security updates
- Test backup restoration
- SSL certificate check

**As Needed:**
- Rotate logs
- Clear old data
- Update environment variables
- Deploy code updates

---

## Deployment Checklist

- [ ] SECRET_KEY is set and strong
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS is configured
- [ ] Static files collected
- [ ] Media directory created
- [ ] Database migrated
- [ ] Gunicorn running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] Firewall configured (ports 80, 443)
- [ ] Logs are accessible
- [ ] Backup strategy in place
- [ ] Service starts on boot
- [ ] .env is excluded from git

---

**Your Django application is now production-ready!** 🎉

For questions or issues, refer to the [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).

