# ⚡ Production Quick Start

## TL;DR - Get to Production FAST

### 1. Prepare Environment (5 minutes)

```bash
# Upload project to server
cd /path/to/linkedin_scraper-web-update-Feature

# Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables (2 minutes)

```bash
# Create .env file
cp .env.example .env

# Edit with your values
nano .env

# MUST SET:
# - DJANGO_SECRET_KEY (generate new one!)
# - DJANGO_DEBUG=False
# - ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
# - All API keys and credentials
```

### 3. Run Deployment Script (2 minutes)

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

This script will:
- ✅ Check Python version
- ✅ Install dependencies
- ✅ Verify .env exists
- ✅ Run Django checks
- ✅ Collect static files
- ✅ Run database migrations
- ✅ Create necessary directories
- ✅ Test Gunicorn configuration

### 4. Start with Gunicorn (1 minute)

```bash
# Test run
gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application

# Visit: http://your-server-ip:8000
```

---

## 🚀 Full Production Setup

For full production with Nginx, SSL, and systemd service:

👉 **See [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)**

---

## 📋 Pre-Flight Checklist

Before running `./deploy.sh`:

- [ ] `.env` file created and configured
- [ ] `credentials.json` uploaded (Google Service Account)
- [ ] Resume PDF files placed in project root
- [ ] Database backed up (if migrating)
- [ ] DNS pointed to server (for SSL setup)
- [ ] Firewall allows ports 80, 443, 8000

---

## 🔧 Common Issues & Quick Fixes

### Issue: "Permission Denied" on deploy.sh

```bash
chmod +x deploy.sh
```

### Issue: WhiteNoise not installed

```bash
pip install whitenoise
```

### Issue: Static files not loading

```bash
python manage.py collectstatic --noinput
sudo chmod -R 755 staticfiles/
```

### Issue: Gunicorn workers timeout

Edit `gunicorn_config.py`:
```python
timeout = 300  # Increase from 120 to 300
```

---

## 🎯 Testing Checklist

After deployment, test:

- [ ] Homepage loads: `http://your-ip:8000`
- [ ] Static files load (CSS, JS)
- [ ] API endpoints work: `POST /startScraping`
- [ ] Admin panel accessible: `/admin/`
- [ ] Logs are being written
- [ ] No errors in `sudo journalctl -u linkedin_scraper -f`

---

## 📊 Monitoring Commands

```bash
# View application logs
sudo journalctl -u linkedin_scraper -f

# Check service status
sudo systemctl status linkedin_scraper

# Monitor system resources
htop

# Check disk space
df -h

# View Nginx logs
sudo tail -f /var/log/nginx/linkedin_scraper_error.log
```

---

## 🔄 Update Deployment

When you push new code:

```bash
# Pull latest code
git pull origin main

# Activate venv
source venv/bin/activate

# Run deployment script
./deploy.sh

# Restart service
sudo systemctl restart linkedin_scraper
```

---

## 🆘 Emergency Rollback

If something breaks:

```bash
# Stop service
sudo systemctl stop linkedin_scraper

# Restore database backup
cp db.sqlite3.backup db.sqlite3

# Checkout previous commit
git checkout HEAD~1

# Redeploy
./deploy.sh

# Restart
sudo systemctl start linkedin_scraper
```

---

## 📞 Need Help?

1. Check logs: `sudo journalctl -u linkedin_scraper -f`
2. Review: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)
3. Check: [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md)

---

**Time to Production: ~10 minutes** ⚡

