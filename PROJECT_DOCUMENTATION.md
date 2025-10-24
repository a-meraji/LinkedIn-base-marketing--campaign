# LinkedIn Lead Generation & Outreach Automation - Project Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [API Endpoints](#api-endpoints)
6. [Core Modules & Services](#core-modules--services)
7. [Data Flow](#data-flow)
8. [Getting Started](#getting-started)
9. [Configuration](#configuration)

---

## Project Overview

This is a **Django-based web service** that provides a fully automated pipeline for:
1. **Scraping job listings** from LinkedIn
2. **Enriching data** with company contact information (emails, phones, social media)
3. **Executing automated outreach campaigns** via Email and WhatsApp
4. **Tracking and logging** all activities to Google Sheets

### Key Capabilities
- ✅ Asynchronous background processing (non-blocking API responses)
- ✅ Multi-criteria job search (combinations of job titles and countries)
- ✅ **Memory-optimized streaming architecture** (processes jobs incrementally)
- ✅ Automated contact enrichment from company websites
- ✅ Sequential multi-sender outreach campaigns
- ✅ Rate limiting and sender pool management
- ✅ Real-time task status tracking
- ✅ Centralized data management via Google Sheets
- ✅ **Retry logic with exponential backoff** for transient errors

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENT (API Request)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO REST API                            │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │ Scraping     │ Email        │ WhatsApp     │ Task Status  │ │
│  │ Endpoint     │ Campaign     │ Campaign     │ Endpoint     │ │
│  └──────┬───────┴──────┬───────┴──────┬───────┴──────┬───────┘ │
│         │              │              │              │          │
│         ▼              ▼              ▼              ▼          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │       Background Thread Pool (Async Processing)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────┬───────────────┬───────────────┬────────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   APIFY      │  │  MESSENGER   │  │ GOOGLE       │
│   SERVICE    │  │  SERVICE     │  │ SHEETS       │
│              │  │              │  │ SERVICE      │
│ • LinkedIn   │  │ • Email      │  │              │
│   Job        │  │   (SMTP)     │  │ • Data       │
│   Scraper    │  │ • WhatsApp   │  │   Storage    │
│ • Contact    │  │   (Inboxino) │  │ • Status     │
│   Scraper    │  │              │  │   Logging    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | Django + Django REST Framework |
| **Web Scraping** | Apify API (2 actors: LinkedIn Jobs & Contact Scraper) |
| **Data Storage** | Google Sheets API |
| **Email** | Django SMTP (Gmail) |
| **WhatsApp** | Inboxino API |
| **Environment Management** | python-dotenv |
| **Data Processing** | pandas |
| **HTTP Requests** | requests |
| **CORS** | django-cors-headers |

---

## Project Structure

```
linkedin_scraper-web-update-Feature/
│
├── manage.py                          # Django management script
├── requirements.txt                   # Python dependencies
├── .env                              # Environment variables (not in repo)
├── credentials.json                  # Google Service Account key (not in repo)
├── resume.pdf                        # Default resume attachment
│
├── linkedin_scraper/                 # Main Django project
│   ├── settings.py                   # Project settings (reads from .env)
│   ├── urls.py                       # Root URL configuration
│   └── wsgi.py                       # WSGI application
│
├── scraper/                          # Scraping & Data Collection App
│   ├── views.py                      # API views (endpoints)
│   ├── urls.py                       # App URL routing
│   └── services/
│       ├── apify_service.py          # Apify API interactions
│       ├── google_sheets_service.py  # Google Sheets operations
│       └── processing_service.py     # Data cleaning & processing
│
└── messenger/                        # Outreach Campaign App
    ├── services.py                   # Email & WhatsApp sending logic
    ├── rate_limiter_service.py       # Sender pool & rate limiting
    └── management/
        └── commands/
            └── test_email.py         # Django command to test email
```

---

## API Endpoints

### Where to Start: Main Entry Points

All endpoints are defined in: **`scraper/urls.py`** and routed through **`linkedin_scraper/urls.py`**

Base URL: `http://127.0.0.1:8000/` (development)

### 1. **Start Scraping** 🔍
**Endpoint:** `POST /startScraping`  
**File:** `scraper/views.py` → `StartScrapingView`

**Purpose:** Initiates the LinkedIn job scraping and contact enrichment process.

**Request Body:**
```json
{
    "country": ["United States", "Germany"],
    "job": ["Python Developer", "Data Scientist"],
    "max_results": 50,
    "proxy_type": "RESIDENTIAL"
}
```

**Parameters:**
- `country` (string or array, required): Target countries
- `job` (string or array, required): Job titles to search
- `max_results` (integer, optional, default=3): Jobs per search combination
- `proxy_type` (string, optional, default="DATACENTER"): Proxy type for Apify

**Response:**
```json
{
    "message": "Scraping task has been successfully started.",
    "task_id": "34ded7f5-6455-4b64-b392-5ba97410cef4"
}
```

**What it does:**
1. Creates all combinations of countries × jobs
2. Starts background thread
3. Returns immediately with task_id
4. Background process (**memory-optimized streaming**):
   - Scrapes LinkedIn jobs via Apify (one-by-one, not all at once)
   - For each job immediately:
     * Scrapes contact info from company website
     * Writes data to Google Sheet with "Pending" status
   - Repeats until all jobs are processed
   - **Memory usage**: Constant (O(1)), not dependent on dataset size

---

### 2. **Start Email Campaign** 📧
**Endpoint:** `POST /startEmailCampaign`  
**File:** `scraper/views.py` → `StartEmailCampaignView`

**Purpose:** Executes sequential email outreach to all pending targets.

**Request:** No body required (reads from Google Sheet)

**Response:**
```json
{
    "message": "Email campaign has been successfully started.",
    "task_id": "a4f5d6e7-1234-5678-90ab-cdef12345678"
}
```

**What it does:**
1. Reads all rows with `email_status = "Pending"` from Google Sheet
2. For each target:
   - Iterates through sender sequence from "Senders Pool" sheet
   - Sends email using first available sender (checks rate limits)
   - Logs activity to "Senders Log" sheet
   - Updates status in main sheet
3. Uses dynamic resume files and subjects per sender

---

### 3. **Start WhatsApp Campaign** 💬
**Endpoint:** `POST /startWhatsappCampaign`  
**File:** `scraper/views.py` → `StartWhatsappCampaignView`

**Purpose:** Executes sequential WhatsApp outreach to all pending targets.

**Request:** No body required

**Response:**
```json
{
    "message": "WhatsApp campaign has been successfully started.",
    "task_id": "b5c6d7e8-2345-6789-01bc-def123456789"
}
```

**What it does:**
1. Reads all rows with `whatsapp_status = "Pending"`
2. For each target:
   - Iterates through WhatsApp sender sequence
   - Uploads resume to Inboxino (gets attachment ID)
   - Sends WhatsApp message via Inboxino API
   - Logs and updates status
3. Rate limiting applied per sender

---

### 4. **Task Status** 📊
**Endpoint:** `GET /taskStatus/<task_id>`  
**File:** `scraper/views.py` → `TaskStatusView`

**Purpose:** Check the status of any running background task.

**Example:** `GET /taskStatus/34ded7f5-6455-4b64-b392-5ba97410cef4`

**Response:**
```json
{
    "type": "Scraping",
    "status": "running",
    "progress": "Processing combination 2/4: 'Python Developer' in 'Germany'",
    "started_at": "2025-10-19T12:07:00.533Z",
    "finished_at": null
}
```

**Status values:**
- `queued`: Task is waiting to start
- `running`: Task is in progress
- `completed`: Task finished successfully
- `failed`: Task encountered an error

---

## Core Modules & Services

### 1. Apify Service (`scraper/services/apify_service.py`)

**Class:** `ApifyService`

**Purpose:** Handles all interactions with Apify actors.

**Key Methods:**
- `run_linkedin_job_scraper(search_url, max_results, proxy_group)`: Scrapes LinkedIn jobs (returns list)
- `run_linkedin_job_scraper_streaming(...)`: **Memory-optimized version** (returns generator, processes incrementally)
- `run_contact_detail_scraper(website_url)`: Extracts contact info from websites
- `_run_actor(actor_id, run_input)`: Generic actor execution method (loads all results)
- `_run_actor_streaming(actor_id, run_input)`: **Streaming version** (yields results one-by-one)

**Memory Optimization:**
The streaming methods prevent RAM exhaustion on large datasets by processing jobs incrementally instead of loading everything into memory. See `MEMORY_OPTIMIZATION_GUIDE.md` for details.

**Configuration (from .env):**
- `APIFY_API_TOKEN`: Your Apify API key
- `LINKEDIN_ACTOR_ID`: LinkedIn job scraper actor
- `CONTACT_SCRAPER_ACTOR_ID`: Contact detail scraper actor

---

### 2. Google Sheets Service (`scraper/services/google_sheets_service.py`)

**Class:** `GoogleSheetsService`

**Purpose:** Wrapper for Google Sheets API operations.

**Key Methods:**
- `get_worksheet(sheet_name)`: Get a specific worksheet
- `get_all_values(worksheet)`: Fetch all data
- `get_header_map(worksheet)`: Map headers to column indices
- `append_row(worksheet, row_data)`: Add new row
- `update_cell(worksheet, row, col, value)`: Update specific cell

**Configuration (from .env):**
- `GOOGLE_SHEET_ID`: Your Google Sheet ID
- `GOOGLE_SERVICE_ACCOUNT_PATH`: Path to credentials.json

**Important Sheets:**
- `Sheet1`: Main data storage (jobs, contacts, statuses)
- `Senders Pool`: Configuration for email/WhatsApp senders
- `Senders Log`: Activity log for rate limiting

---

### 3. Processing Service (`scraper/services/processing_service.py`)

**Purpose:** Data cleaning, validation, and URL building.

**Key Functions:**
- `build_linkedin_url(keyword, location_name)`: Constructs LinkedIn search URLs
- `process_contact_data(scraped_items, original_job_data)`: Cleans and deduplicates contact info
- `_clean_phones(phones)`: Removes non-numeric characters
- `_clean_emails(emails)`: Normalizes email addresses

---

### 4. Messenger Service (`messenger/services.py`)

**Functions:**

**a) `send_email(recipient_email, sender_config, resume_filename, subject)`**
- Sends HTML email with PDF attachment
- Uses dynamic sender configuration
- Supports TLS (port 587) and SSL
- Returns status message

**b) `send_whatsapp_message(phone_numbers_to_send, attachment_file_id, sender_config, resume_filename)`**
- Sends WhatsApp message via Inboxino API
- Supports multiple recipients
- Includes file attachment
- Returns status message

**c) `upload_file_to_inboxino(api_key, resume_filename)`**
- Uploads PDF to Inboxino
- Returns attachment ID for messaging
- Called before each WhatsApp send

**Configuration (from .env):**
- `INBOXINO_API_KEY`: Inboxino API key
- `EMAIL_HOST_USER`: Gmail address
- `EMAIL_HOST_PASSWORD`: Gmail app password
- `MAIL_FROM_NAME`: Sender name in emails

---

### 5. Rate Limiter Service (`messenger/rate_limiter_service.py`)

**Class:** `RateLimiterService`

**Purpose:** Manages sender pool and enforces daily sending limits.

**Key Methods:**
- `get_senders_by_type(service_type)`: Returns all active senders for email/whatsapp
- `is_sender_available(service_type, sender_id)`: Checks if sender can send (rate limit check)
- `log_send(sender_id, recipient, service_type)`: Records successful send

**Configuration (from .env):**
- `EMAIL_DAILY_LIMIT`: Max emails per sender per 24 hours (default: 30)
- `WHATSAPP_DAILY_LIMIT`: Max WhatsApp messages per sender per 24 hours (default: 200)
- `SENDERS_POOL_SHEET_NAME`: Name of sender configuration sheet
- `SENDERS_LOG_SHEET_NAME`: Name of activity log sheet

---

## Data Flow

### Flow 1: Scraping Process (Memory-Optimized Streaming)

```
1. Client → POST /startScraping
   ↓
2. Create task_id, return immediately
   ↓
3. Background Thread Starts:
   ↓
4. Build LinkedIn URLs (processing_service)
   ↓
5. Start LinkedIn Scraping (STREAMING MODE):
   ↓
6. FOR EACH job AS IT'S FOUND (one-by-one):
   ├─ Yield job from Apify dataset
   ├─ Extract company website
   ├─ Apify: Scrape contact details
   ├─ Clean & process data (processing_service)
   ├─ Append to Google Sheet (status: Pending)
   ├─ Log progress
   └─ Free memory, get next job
   ↓
7. Update task status → "completed"

Note: Jobs are processed incrementally, not loaded all at once.
This prevents memory exhaustion on large datasets.
```

### Flow 2: Email Campaign

```
1. Client → POST /startEmailCampaign
   ↓
2. Create task_id, return immediately
   ↓
3. Background Thread:
   ↓
4. Read Google Sheet (all Pending rows)
   ↓
5. Load Sender Sequence (from Senders Pool)
   ↓
6. For each Target:
   ├─ For each Sender in sequence:
   │   ├─ Check rate limit (RateLimiterService)
   │   ├─ If available:
   │   │   ├─ Send email (with sender's resume & subject)
   │   │   ├─ Log to Senders Log
   │   │   └─ Count successful send
   │   └─ If rate-limited: Skip to next sender
   └─ Update status in Sheet
   ↓
7. Task status → "completed"
```

### Flow 3: WhatsApp Campaign

```
1. Client → POST /startWhatsappCampaign
   ↓
2. Create task_id, return immediately
   ↓
3. Background Thread:
   ↓
4. Read Google Sheet (all Pending rows)
   ↓
5. Load WhatsApp Sender Sequence
   ↓
6. For each Target:
   ├─ For each Sender:
   │   ├─ Check rate limit
   │   ├─ If available:
   │   │   ├─ Upload resume to Inboxino
   │   │   ├─ Get attachment_id
   │   │   ├─ Send WhatsApp message
   │   │   └─ Log activity
   │   └─ If rate-limited: Skip
   └─ Update status
   ↓
7. Task status → "completed"
```

---

## Getting Started

### Prerequisites
1. Python 3.8+
2. Apify account with API token
3. Google Cloud project with Sheets API enabled
4. Google service account JSON file
5. Inboxino account (for WhatsApp)
6. Gmail account with app password (for email)

### Installation

```bash
# 1. Navigate to project directory
cd /home/amin/Documents/projects/jobScrappinglinkedIn/linkedin_scraper-web-update-Feature

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up .env file (see Configuration section)

# 5. Place credentials.json in project root

# 6. Place resume PDF files in project root

# 7. Run migrations
python manage.py migrate

# 8. Start server
python manage.py runserver
```

Server will be available at: `http://127.0.0.1:8000/`

---

## Configuration

### Environment Variables (.env file)

Create a `.env` file in the project root:

```ini
# Django Core
DJANGO_SECRET_KEY="your-secret-key-here"
DJANGO_DEBUG="True"

# Apify
APIFY_API_TOKEN="your_apify_token"
LINKEDIN_ACTOR_ID="fetchclub/linkedin-jobs-scraper"
CONTACT_SCRAPER_ACTOR_ID="2RxbxbuelHKumjdS6"

# Google Sheets
GOOGLE_SHEET_ID="your_google_sheet_id"
GOOGLE_SERVICE_ACCOUNT_PATH="credentials.json"

# Messenger
INBOXINO_API_KEY="your_inboxino_key"
EMAIL_HOST_USER="your.email@gmail.com"
EMAIL_HOST_PASSWORD="your-gmail-app-password"
MAIL_FROM_NAME="Mirza Agency"
MAIL_USE_TLS="True"
MAIL_USE_SSL="False"

# Rate Limiting
EMAIL_DAILY_LIMIT="30"
WHATSAPP_DAILY_LIMIT="200"
SENDERS_POOL_SHEET_NAME="Senders Pool"
SENDERS_LOG_SHEET_NAME="Senders Log"
```

### Google Sheet Setup

**Sheet1 (Main Data):**
Headers: `employmentType`, `companyName`, `companyCountry`, `companyWebsite`, `postedAt`, `phones`, `emails`, `title`, `linkedin`, `link`, `fullCompanyAddress`, `twitter`, `instagram`, `facebook`, `youtube`, `tiktok`, `pinterest`, `discord`, `email_status`, `whatsapp_status`

**Senders Pool:**
Headers: `id`, `type`, `is_active`, `password`, `host`, `port`, `resume_filename`, `email_subject`, `api_key`

**Senders Log:**
Headers: `sender_id`, `service_type`, `recipient`, `timestamp`

---

## Key Files to Examine

| Purpose | File Location |
|---------|--------------|
| **API Endpoints** | `scraper/urls.py` |
| **View Logic** | `scraper/views.py` |
| **Main Settings** | `linkedin_scraper/settings.py` |
| **Scraping Logic** | `scraper/services/apify_service.py` |
| **Messaging Logic** | `messenger/services.py` |
| **Rate Limiting** | `messenger/rate_limiter_service.py` |
| **Data Processing** | `scraper/services/processing_service.py` |
| **Memory Optimization** | `MEMORY_OPTIMIZATION_GUIDE.md` |
| **Rate Limiting Issues** | `RATE_LIMITING_ISSUE.md` |

---

## Summary

This project is a **complete lead generation and outreach automation system** that:
1. **Scrapes** LinkedIn job postings based on customizable search criteria
2. **Enriches** data by extracting contact information from company websites
3. **Automates** email and WhatsApp outreach campaigns with intelligent sender rotation
4. **Manages** rate limits to prevent spam and account restrictions
5. **Tracks** all activities in Google Sheets for transparency and reporting

**Start here:**
- Review `scraper/urls.py` to see all endpoints
- Read `scraper/views.py` to understand the workflow logic
- Check `messenger/services.py` to see how messages are sent
- Examine `linkedin_scraper/settings.py` for configuration options

The system is designed to be **asynchronous**, **scalable**, and **production-ready** with proper error handling and logging throughout.

