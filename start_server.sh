#!/usr/bin/env bash

###############################################################################
# Quick Server Start Script
# For development and testing
###############################################################################

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================================"
echo "🚀 Starting LinkedIn Scraper Server"
echo "================================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if running in development or production
if [ -f ".env" ]; then
    DEBUG_VALUE=$(grep -E "^DJANGO_DEBUG=" .env | cut -d '=' -f2)
    if [ "$DEBUG_VALUE" = "False" ]; then
        echo -e "${GREEN}Running in PRODUCTION mode (DEBUG=False)${NC}"
        echo ""
        echo "Starting with Gunicorn..."
        gunicorn -c gunicorn_config.py linkedin_scraper.wsgi:application
    else
        echo -e "${GREEN}Running in DEVELOPMENT mode (DEBUG=True)${NC}"
        echo ""
        echo "Starting Django development server..."
        python manage.py runserver 0.0.0.0:8000
    fi
else
    echo -e "${YELLOW}No .env file found, using defaults${NC}"
    echo ""
    echo "Starting Django development server..."
    python manage.py runserver 0.0.0.0:8000
fi

