LinkedIn Lead Generation & Outreach Automation Service
This Django-based web service provides a powerful, fully automated pipeline for scraping job listings from LinkedIn, enriching the data with company contact information, and executing an immediate outreach campaign via Email and WhatsApp.

The system is designed to be initiated via a single API call, running the entire workflow asynchronously in the background. It provides real-time task status tracking and logs all results, including messaging status, directly to a Google Sheet.

Key Features
Asynchronous & Non-Blocking: The API responds instantly with a task_id while the entire scraping and messaging process runs in the background.

Multi-Criteria Scraping: Initiates searches based on lists of job titles and countries, processing all possible combinations.

Dynamic Scraping Parameters: Control the number of results (max_results) and the proxy type (proxy_type) for each API request.

Automated Contact Enrichment: For each company found, it automatically scrapes the company website to find emails, phone numbers, and social media links.

Integrated Outreach Module:

Email: Automatically sends a templated email with a PDF attachment (e.g., a resume) to all found email addresses.

WhatsApp: Sends a templated message with the same PDF attachment to all found phone numbers via the Inboxino API.

Centralized Data Management: All scraped data and the status of each outreach attempt (email_sent, whatsapp_sent) are written to a Google Sheet in real-time.

Task Status Tracking: A dedicated API endpoint allows you to monitor the progress of a running task using its unique ID.

Resilient & Robust: Gracefully handles errors by skipping individual jobs that fail, ensuring the overall process continues.

System Architecture & Workflow
The service operates on a modular, multi-stage workflow orchestrated by the Django backend.

!

API Request: The process begins when a POST request is sent to the /scrapJobs endpoint.

Task Queuing: The Django server immediately accepts the request, creates a unique task_id, and starts a new background thread for the job. It returns the task_id to the client.

Attachment Upload: The system uploads the specified PDF resume to the messaging service (Inboxino) once per task to get a reusable attachment ID.

Main Loop (Job Combinations): The system iterates through each country and job combination provided in the request.

Module 1 (Apify - LinkedIn Scraper): For each combination, it calls the first Apify actor to scrape LinkedIn for relevant job listings based on the dynamic max_results and proxy_type.

Module 2 (Apify - Contact Scraper): For each new job found, it extracts the company's website and calls the second Apify actor to find contact details (emails, phones).

Module 3 (Messenger Service):

If emails are found, the send_email service is triggered.

If phone numbers are found, the send_whatsapp_message service is triggered.

The success or failure status of each message is recorded.

Module 4 (Google Sheets): The final, enriched data—including job details, contact info, and messaging status—is appended as a new row to the designated Google Sheet.

Completion: Once all combinations are processed, the task status is updated to "completed".

Technology Stack
Backend: Django, Django REST Framework

Web Scraping: Apify (utilizing two actors: LinkedIn Jobs Scraper & Contact Detail Scraper)

Data Storage: Google Sheets

Messaging:

Email: Django's SMTP email backend (configured for Gmail).

WhatsApp: Inboxino API

Environment Management: python-dotenv

Deployment: WSGI (e.g., Gunicorn, uWSGI for production)

Prerequisites
Python 3.8+

A virtual environment tool (venv)

An active Apify account with an API token.

A Google Cloud Platform project with the Google Sheets API enabled and a service account (credentials.json).

A Google Sheet shared with the service account's email address.

An Inboxino account with an API key.

A Gmail account with an App Password generated for sending emails.

Configuration & Setup Guide
Follow these steps carefully to set up the project.

1. Clone & Install Dependencies
Bash

# Clone the repository (if applicable)
# git clone <your-repo-url>
cd linkedin_scraper

# Create and activate a virtual environment
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

# Install required packages
pip install -r requirements.txt
2. Configure Environment Variables (.env file)
Create a file named .env in the root directory (linkedin_scraper/) and populate it with the following keys.

Ini, TOML

# Django Core Settings
DJANGO_SECRET_KEY="your-unique-and-secret-key-here"
DJANGO_DEBUG="True"

# Apify Scraper Module Settings
APIFY_API_TOKEN="your_apify_api_token"
LINKEDIN_ACTOR_ID="fetchclub/linkedin-jobs-scraper"
CONTACT_SCRAPER_ACTOR_ID="2RxbxbuelHKumjdS6"

# Google Sheets Settings
GOOGLE_SHEET_ID="your_google_sheet_id_from_url"
GOOGLE_SERVICE_ACCOUNT_PATH="credentials.json"

# Messenger Module Settings
INBOXINO_API_KEY="your_inboxino_api_key"
EMAIL_HOST_USER="your.email@gmail.com"
EMAIL_HOST_PASSWORD="your-gmail-app-password" # Important: Use an App Password, not your main password
3. Add Project Files
Place the following files in the root directory (alongside manage.py):

credentials.json: Your downloaded Google Cloud service account key.

resume.pdf: The resume or document you want to send as an attachment.

4. Set Up Google Sheet
Create a new Google Sheet.

Import the provided google_sheets_import_template.csv file to create all the necessary headers.

Click the "Share" button, and share the sheet with the client_email found in your credentials.json file, giving it Editor permissions.

5. Apply Migrations
Although this project doesn't use database models, it's good practice to apply Django's built-in migrations.

Bash

python manage.py migrate
Running the Service
To start the development server, run the following command from the root directory:

Bash

python manage.py runserver
The service will be available at http://127.0.0.1:8000/.

API Endpoints
1. Start Scraping Task
Endpoint: /scrapJobs

Method: POST

Description: Initiates the entire scraping and outreach workflow.

Request Body (JSON):
Parameter	Type	Required	Default	Description
country	string or array	Yes	N/A	A single country or a list of countries to search in.
job	string or array	Yes	N/A	A single job title or a list of job titles to search for.
max_results	integer	No	10	The maximum number of job results to scrape for each combination.
proxy_type	string	No	DATACENTER	The type of proxy to use. Recommended: RESIDENTIAL for better reliability.

Export to Sheets
Example Request:
JSON

{
    "country": ["United States", "Germany"],
    "job": ["Python Developer", "Data Scientist"],
    "max_results": 50,
    "proxy_type": "RESIDENTIAL"
}
Success Response (202 Accepted):
JSON

{
    "message": "Your request has been successfully submitted. The scraping process has started.",
    "task_id": "34ded7f5-6455-4b64-b392-5ba97410cef4"
}
2. Check Task Status
Endpoint: /scrapStatus/<task_id>

Method: GET

Description: Retrieves the current status of a background task.

URL Parameter:
Parameter	Type	Description
task_id	string	The unique ID returned from the /scrapJobs endpoint.

Export to Sheets
Example Request:
GET http://127.0.0.1:8000/scrapStatus/34ded7f5-6455-4b64-b392-5ba97410cef4

Success Response (200 OK):
JSON

{
    "status": "running",
    "progress": "Processing 3/4: 'Python Developer' in 'Germany'",
    "total_combinations": 4,
    "started_at": "2025-10-09T12:07:00.533Z",
    "finished_at": null
}# linkedInjobscrapping
# linkedInjobscrapping
