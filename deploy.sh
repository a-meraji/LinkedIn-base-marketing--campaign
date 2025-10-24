#!/usr/bin/env bash

###############################################################################
# Production Deployment Script for LinkedIn Scraper
###############################################################################

set -e  # Exit on error

echo "=================================="
echo "🚀 Production Deployment Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warn "Virtual environment not activated!"
    print_info "Activating venv..."
    source venv/bin/activate
fi

# Step 1: Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
print_info "Python version: $PYTHON_VERSION"

# Step 2: Install/Update dependencies
print_info "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 3: Check for .env file
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Creating .env from .env.example..."
    cp .env.example .env
    print_warn "Please edit .env with your production values!"
    exit 1
fi

# Step 4: Run Django checks
print_info "Running Django system checks..."
python manage.py check

# Step 5: Run deployment checks
print_info "Running deployment security checks..."
python manage.py check --deploy || print_warn "Some security warnings found (see above)"

# Step 6: Collect static files
print_info "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Step 7: Run migrations
print_info "Running database migrations..."
python manage.py migrate --noinput

# Step 8: Create necessary directories
print_info "Creating necessary directories..."
mkdir -p media/resumes
mkdir -p logs
chmod -R 755 media
chmod -R 755 staticfiles

# Step 9: Check credentials.json
if [ ! -f "credentials.json" ]; then
    print_warn "credentials.json not found! Make sure to add Google Service Account credentials."
fi

# Step 10: Test Gunicorn
print_info "Testing Gunicorn configuration..."
gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application --check-config

echo ""
echo "=================================="
print_info "✅ Deployment preparation complete!"
echo "=================================="
echo ""

print_info "Next steps:"
echo "  1. Update .env with production values"
echo "  2. Create superuser: python manage.py createsuperuser"
echo "  3. Test server: gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application"
echo "  4. Set up systemd service (see PRODUCTION_DEPLOYMENT_GUIDE.md)"
echo "  5. Configure Nginx (see PRODUCTION_DEPLOYMENT_GUIDE.md)"
echo ""
print_info "For detailed instructions, see: PRODUCTION_DEPLOYMENT_GUIDE.md"

