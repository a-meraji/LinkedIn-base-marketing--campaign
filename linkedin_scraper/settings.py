"""
Django settings for linkedin_scraper project.

This file is refactored to read all sensitive data and configurations
from the .env file for better security and manageability.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file located at the project root
load_dotenv(os.path.join(BASE_DIR, '.env'))


# ==============================================================================
# Core Django Settings
# ==============================================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'default-insecure-key-for-development')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

# SECURITY WARNING: In production, set specific domains instead of ['*']
# Example: ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'your-server-ip']
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')  # Comma-separated in .env
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'scraper',
    'messenger',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'linkedin_scraper.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'linkedin_scraper.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ==============================================================================
# Static Files Configuration (CSS, JavaScript, Images)
# ==============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Where collectstatic will collect files

# Additional locations of static files (if you have project-level static files)
STATICFILES_DIRS = [
    # BASE_DIR / 'static',  # Uncomment if you have a project-level static folder
]

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ==============================================================================
# Media Files Configuration (User Uploads - Resumes, Attachments)
# ==============================================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# Static Files Storage (Production Optimization)
# ==============================================================================
# WhiteNoise configuration for efficient static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================================
# Security Settings (Production)
# ==============================================================================
# Only enable these in production (when DEBUG=False)
if not DEBUG:
    # HTTPS/SSL
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Other security headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Proxy headers (if behind nginx/apache)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ==============================================================================
# Third-Party and Custom App Settings
# ==============================================================================
CORS_ALLOWED_ORIGINS = ["http://localhost:8080", "http://127.0.0.1:8080", "https://a-meraji.github.io"]
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# ==============================================================================
# Custom Settings for Messenger Module
# ==============================================================================
# --- FIX: Added EMAIL_USE_TLS to solve [SSL: WRONG_VERSION_NUMBER] with Gmail ---
# For Gmail on Port 587, TLS must be True and SSL must be False.
EMAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'False') == 'True'
EMAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'

MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'Mirza Agency')
INBOXINO_API_URL = 'https://back.inboxino.com/api/access-api/message/send'
EMAIL_SUBJECT_CONTENT = "Mirza AI-Automation Agency"
WHATSAPP_MESSAGE_CONTENT = "Hello, my name is Milad. I’m a software developer, and this file contains my resume. I would be glad to collaborate with your company. ✅"
RESUME_PDF_FILENAME = "resume.pdf"
EMAIL_COLUMN_NAME = "emails"
PHONE_COLUMN_NAME = "phones"
EMAIL_STATUS_COLUMN = "email_status"
WHATSAPP_STATUS_COLUMN = "whatsapp_status"

# --- Default status for messaging columns after scraping ---
PENDING_STATUS = "Pending"

# --- Rate Limiting and Sender Pool Settings ---
SENDERS_POOL_SHEET_NAME = os.getenv('SENDERS_POOL_SHEET_NAME', 'Senders Pool')
SENDERS_LOG_SHEET_NAME = os.getenv('SENDERS_LOG_SHEET_NAME', 'Senders Log')
EMAIL_DAILY_LIMIT = int(os.getenv('EMAIL_DAILY_LIMIT', 30))
WHATSAPP_DAILY_LIMIT = int(os.getenv('WHATSAPP_DAILY_LIMIT', 200))

