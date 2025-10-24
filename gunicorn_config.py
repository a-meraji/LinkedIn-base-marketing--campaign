"""
Gunicorn configuration file for production deployment.
Usage: gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application
"""

import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = 'sync'  # 'gevent' or 'eventlet' for async
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests (prevents memory leaks)
max_requests_jitter = 50
timeout = 120  # Worker timeout (seconds) - increase for long-running scraping tasks
keepalive = 5

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process Naming
proc_name = 'linkedin_scraper'

# Server Mechanics
daemon = False  # Don't daemonize (let supervisor/systemd handle this)
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Reload
reload = os.getenv('GUNICORN_RELOAD', 'False') == 'True'  # Auto-reload on code changes (dev only)
reload_engine = 'auto'
reload_extra_files = []

# Worker Lifecycle Hooks (optional, for custom behavior)
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload."""
    server.log.info("Reloading Gunicorn server...")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Gunicorn server ready. Listening on: {bind}")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    server.log.info(f"Worker exited (pid: {worker.pid})")

