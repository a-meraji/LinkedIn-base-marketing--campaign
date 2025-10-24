import logging
import threading
import os
import uuid
import time
from datetime import datetime

from dotenv import load_dotenv
from django.conf import settings
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.apify_service import ApifyService
from .services.google_sheets_service import GoogleSheetsService
from .services.processing_service import build_linkedin_url, process_contact_data
from messenger.services import send_email, send_whatsapp_message, upload_file_to_inboxino
from messenger.rate_limiter_service import RateLimiterService

load_dotenv()
logger = logging.getLogger(__name__)

tasks_status = {}
tasks_lock = threading.Lock()

EXPECTED_HEADERS = [
    'employmentType', 'companyName', 'companyCountry', 'companyWebsite', 'postedAt', 'phones', 'emails',
    'title', 'linkedin', 'link', 'fullCompanyAddress', 'twitter', 'instagram', 'facebook', 'youtube',
    'tiktok', 'pinterest', 'discord', settings.EMAIL_STATUS_COLUMN, settings.WHATSAPP_STATUS_COLUMN
]

# ==============================================================================
# MODULE 1: DATA SCRAPING LOGIC (Unaltered)
# ==============================================================================
def run_scraping_logic(task_id: str, job_combinations: list, max_results: int, proxy_type: str):
    """
    Initiates the data scraping process. This logic is unchanged and works as intended.
    It scrapes data and sets the status columns to "Pending".
    """
    total_combinations = len(job_combinations)
    logger.info(f"Task [{task_id}]: Starting scraping for {total_combinations} combinations.")

    try:
        sheets_service = GoogleSheetsService(os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"], os.environ["GOOGLE_SHEET_ID"])
        worksheet = sheets_service.get_worksheet("Sheet1")
        header_map = sheets_service.get_header_map(worksheet)
        link_col_index = header_map.get('link')
        if not link_col_index: raise Exception("Column 'link' not found in the Google Sheet.")
        existing_links = sheets_service.get_column_values(worksheet, link_col_index)
        apify_service = ApifyService(os.environ["APIFY_API_TOKEN"])
    except Exception as e:
        error_message = f"Initialization failed: {e}"
        with tasks_lock:
            tasks_status[task_id].update({'status': 'failed', 'error': error_message, 'finished_at': datetime.utcnow()})
        return

    for i, combo in enumerate(job_combinations):
        with tasks_lock:
            tasks_status[task_id]['progress'] = f"Processing combination {i+1}/{total_combinations}: '{combo['job']}' in '{combo['country']}'"

        search_url = build_linkedin_url(keyword=combo['job'], location_name=combo['country'])
        
        # ============================================================================
        # MEMORY-OPTIMIZED STREAMING APPROACH
        # ============================================================================
        # Instead of loading all jobs into memory, we process them one-by-one
        # as they're fetched from Apify. This prevents RAM exhaustion on large datasets.
        # ============================================================================
        logger.info(f"Task [{task_id}]: Starting STREAMING scrape for '{combo['job']}' in '{combo['country']}'")
        logger.info(f"Task [{task_id}]: Jobs will be processed incrementally as they're found")
        
        jobs_processed = 0
        
        # Stream jobs one at a time from LinkedIn scraper
        for job in apify_service.run_linkedin_job_scraper_streaming(
            search_url=search_url,
            max_results=max_results,
            proxy_group=proxy_type,
            memory_mbytes=512,
            max_concurrency=1  # Keep concurrency at 1 to avoid rate limiting
        ):
            try:
                job_link = job.get('job_url')
                if not job_link or job_link in existing_links:
                    continue

                contact_info = {}
                company_website = job.get('company_website')
                if company_website:
                    logger.info(f"Task [{task_id}]: Scraping contact details for {job.get('company_name', 'Unknown')} - {company_website}")
                    
                    # Call contact scraper with optimized settings
                    contact_results = apify_service.run_contact_detail_scraper(
                        website_url=company_website,
                        memory_mbytes=512,
                        max_concurrency=1,
                        max_depth=2,
                        max_requests=5
                    )
                    
                    if contact_results:
                        contact_info = process_contact_data(contact_results, job)
                        logger.info(f"Task [{task_id}]: Found {len(contact_info.get('emails', '').split(','))} email(s) and {len(contact_info.get('phones', '').split(','))} phone(s)")
                    else:
                        logger.warning(f"Task [{task_id}]: No contact details found for {company_website}")
                    
                    # Small delay between contact scrapes to avoid rate limiting
                    time.sleep(2)

                row_data = {
                    'employmentType': job.get('employment_type', ''), 'companyName': job.get('company_name', ''),
                    'companyCountry': combo['country'],
                    'postedAt': job.get('posted_datetime', ''), 'phones': contact_info.get('phones', ''),
                    'emails': contact_info.get('emails', ''), 'title': job.get('title', ''),
                    'linkedin': contact_info.get('linkedin', ''), 'link': job.get('job_url', ''),
                    'fullCompanyAddress': f"{job.get('company_street', '')}, {job.get('company_locality', '')}",
                    'twitter': contact_info.get('twitter', ''), 'instagram': contact_info.get('instagram', ''),
                    'facebook': contact_info.get('facebook', ''), 'youtube': contact_info.get('youtube', ''),
                    'tiktok': contact_info.get('tiktok', ''), 'pinterest': contact_info.get('pinterest', ''),
                    'discord': contact_info.get('discord', ''),
                    settings.EMAIL_STATUS_COLUMN: settings.PENDING_STATUS,
                    settings.WHATSAPP_STATUS_COLUMN: settings.PENDING_STATUS,
                }
                new_row = [row_data.get(header, '') for header in EXPECTED_HEADERS]
                sheets_service.append_row(worksheet, new_row)
                existing_links.add(job_link)
                jobs_processed += 1
                
                logger.info(f"Task [{task_id}]: ✅ Job #{jobs_processed} saved: {job.get('title', 'Unknown')} at {job.get('company_name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Task [{task_id}]: Error processing job '{job.get('title')}': {e}. Continuing.")
                continue
        
        # Summary for this combination
        logger.info("")
        logger.info(f"Task [{task_id}]: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info(f"Task [{task_id}]: ✅ Combination {i+1}/{total_combinations} COMPLETED")
        logger.info(f"Task [{task_id}]:    Search: '{combo['job']}' in '{combo['country']}'")
        logger.info(f"Task [{task_id}]:    Jobs processed: {jobs_processed}")
        logger.info(f"Task [{task_id}]: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("")
        
        # Add a small delay between job combinations to avoid rate limiting
        if i < total_combinations - 1:  # Don't delay after the last combination
            delay_seconds = 5
            logger.info(f"Task [{task_id}]: ⏸️  Waiting {delay_seconds} seconds before next search combination...")
            time.sleep(delay_seconds)

    with tasks_lock:
        tasks_status[task_id].update({'status': 'completed', 'progress': f"Completed all {total_combinations} combinations.", 'finished_at': datetime.utcnow()})
    logger.info(f"Task [{task_id}]: Scraping finished.")

# ==============================================================================
# MODULE 2: SEQUENTIAL EMAIL CAMPAIGN LOGIC (Rewritten)
# ==============================================================================
def run_email_campaign_logic(task_id: str):
    """
    Executes a sequential email campaign. For each target, it iterates through a
    pre-defined sequence of senders (with unique resumes/subjects) from the Senders Pool.
    """
    logger.info("=" * 100)
    logger.info(f"📧 EMAIL CAMPAIGN STARTED - Task ID: {task_id}")
    logger.info("=" * 100)
    
    try:
        logger.info("🔧 Initializing Email Campaign Services...")
        sheets_service = GoogleSheetsService(os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"], os.environ["GOOGLE_SHEET_ID"])
        rate_limiter = RateLimiterService(sheets_service)

        logger.info("📋 Loading target recipients from Google Sheets...")
        worksheet = sheets_service.get_worksheet("Sheet1")
        all_data = sheets_service.get_all_values(worksheet)
        header_map = {header.strip(): i for i, header in enumerate(all_data[0])}

        email_col = header_map.get(settings.EMAIL_COLUMN_NAME)
        status_col = header_map.get(settings.EMAIL_STATUS_COLUMN)
        if email_col is None or status_col is None:
            raise Exception("Email or email_status columns not found in the sheet.")

        # Get the sequence of senders from the Senders Pool
        email_sequence = rate_limiter.get_senders_by_type('email')
        if not email_sequence:
            raise Exception("No active email senders found in the 'Senders Pool' sheet.")

    except Exception as e:
        error_message = f"Initialization failed: {e}"
        logger.error(f"❌ Campaign initialization failed: {e}")
        with tasks_lock:
            tasks_status[task_id].update({'status': 'failed', 'error': error_message, 'finished_at': datetime.utcnow()})
        return

    # Find all targets (rows) that are pending
    targets_to_process = [(i, row) for i, row in enumerate(all_data) if i > 0 and row[status_col] == settings.PENDING_STATUS]
    total_targets = len(targets_to_process)
    
    logger.info("=" * 100)
    logger.info(f"📊 CAMPAIGN OVERVIEW")
    logger.info(f"   Total pending targets: {total_targets}")
    logger.info(f"   Available senders: {len(email_sequence)}")
    logger.info(f"   Sends per target: {len(email_sequence)} (sequential)")
    logger.info(f"   Maximum total sends: {total_targets * len(email_sequence)}")
    logger.info("=" * 100)

    # --- Main loop iterates over TARGETS ---
    for target_count, (row_index, target_row) in enumerate(targets_to_process, 1):
        logger.info("")
        logger.info("━" * 100)
        logger.info(f"🎯 TARGET {target_count}/{total_targets}")
        logger.info("━" * 100)
        
        with tasks_lock:
            tasks_status[task_id]['progress'] = f"Processing Target {target_count}/{total_targets}"

        target_emails_str = target_row[email_col]
        if not target_emails_str:
            logger.warning(f"⚠️  No email found for target {target_count}")
            sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, "No Email Found")
            continue

        valid_emails = [e.strip() for e in target_emails_str.split(',') if e.strip() and '@' in e]
        if not valid_emails:
            logger.warning(f"⚠️  No valid email found for target {target_count}")
            sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, "No Valid Email")
            continue

        recipient = valid_emails[0]
        logger.info(f"📬 Recipient: {recipient}")
        logger.info(f"📋 Will attempt sequential sends using {len(email_sequence)} sender(s)")
        
        sent_count_for_target = 0
        final_status_messages = []

        # --- Inner loop iterates over the SENDER SEQUENCE for EACH target ---
        for sender_index, sender_config in enumerate(email_sequence, 1):
            sender_id = sender_config.get('id')
            if not sender_id:
                logger.warning("⚠️  Skipping a sender in sequence due to missing ID.")
                continue

            logger.info("")
            logger.info(f"   → Sender #{sender_index}: {sender_id}")
            
            # Check if this specific sender is available (has not hit its daily limit)
            is_available = rate_limiter.is_sender_available('email', sender_id)

            if is_available:
                resume = sender_config.get('resume_filename', 'N/A')
                subject = sender_config.get('email_subject', 'N/A')
                
                logger.info(f"      📧 Preparing email...")
                logger.info(f"         From: {sender_id}")
                logger.info(f"         To: {recipient}")
                logger.info(f"         Resume: {resume}")
                logger.info(f"         Subject: {subject}")
                logger.info(f"      🚀 Sending email...")

                # Send email with the specific resume and subject for this sender
                status_msg = send_email(
                    recipient_email=recipient,
                    sender_config=sender_config,
                    resume_filename=sender_config.get('resume_filename'),
                    subject=sender_config.get('email_subject')
                )

                final_status_messages.append(status_msg)

                if "Sent via" in status_msg:
                    logger.info(f"      ✅ SUCCESS - Email sent from {sender_id} to {recipient}")
                    rate_limiter.log_send(sender_id, recipient, 'email')
                    sent_count_for_target += 1
                else:
                    logger.error(f"      ❌ FAILED - {status_msg}")
            else:
                status_msg = f"Skipped: {sender_id} rate-limited"
                logger.warning(f"      ⏸️  SKIPPED - Sender rate-limited")
                final_status_messages.append(status_msg)

        # After iterating through all senders for this target, update the master status in the sheet
        logger.info("")
        logger.info(f"📊 SUMMARY for {recipient}:")
        logger.info(f"   Successful sends: {sent_count_for_target}/{len(email_sequence)}")
        logger.info(f"   Status messages: {final_status_messages}")
        
        final_status = f"Completed: Sent {sent_count_for_target}/{len(email_sequence)}. Details: [{', '.join(final_status_messages)}]"
        sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, final_status)
        logger.info(f"   💾 Status updated in Google Sheets")
        logger.info("━" * 100)

    logger.info("")
    logger.info("=" * 100)
    logger.info("🎉 EMAIL CAMPAIGN COMPLETED")
    logger.info(f"   Task ID: {task_id}")
    logger.info(f"   Total targets processed: {total_targets}")
    logger.info("=" * 100)
    
    with tasks_lock:
        tasks_status[task_id].update({'status': 'completed', 'progress': 'Email campaign finished.', 'finished_at': datetime.utcnow()})

# ==============================================================================
# MODULE 3: SEQUENTIAL WHATSAPP CAMPAIGN LOGIC (COMPLETELY NEW)
# ==============================================================================
def run_whatsapp_campaign_logic(task_id: str):
    """
    Executes a sequential WhatsApp campaign, similar to the email campaign.
    For each target, it iterates through the WhatsApp sender sequence.
    """
    logger.info("=" * 100)
    logger.info(f"💬 WHATSAPP CAMPAIGN STARTED - Task ID: {task_id}")
    logger.info("=" * 100)
    
    try:
        logger.info("🔧 Initializing WhatsApp Campaign Services...")
        sheets_service = GoogleSheetsService(os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"], os.environ["GOOGLE_SHEET_ID"])
        rate_limiter = RateLimiterService(sheets_service)

        logger.info("📋 Loading target recipients from Google Sheets...")
        worksheet = sheets_service.get_worksheet("Sheet1")
        all_data = sheets_service.get_all_values(worksheet)
        header_map = {header.strip(): i for i, header in enumerate(all_data[0])}

        phone_col = header_map.get(settings.PHONE_COLUMN_NAME)
        status_col = header_map.get(settings.WHATSAPP_STATUS_COLUMN)

        if phone_col is None or status_col is None:
            raise Exception("Phone or whatsapp_status columns not found in the sheet.")

        whatsapp_sequence = rate_limiter.get_senders_by_type('whatsapp')
        if not whatsapp_sequence:
            raise Exception("No active WhatsApp senders found in 'Senders Pool'.")

    except Exception as e:
        error_message = f"Initialization failed: {e}"
        logger.error(f"❌ Campaign initialization failed: {e}")
        with tasks_lock:
            tasks_status[task_id].update({'status': 'failed', 'error': error_message, 'finished_at': datetime.utcnow()})
        return

    targets_to_process = [(i, row) for i, row in enumerate(all_data) if i > 0 and row[status_col] == settings.PENDING_STATUS]
    total_targets = len(targets_to_process)
    
    logger.info("=" * 100)
    logger.info(f"📊 CAMPAIGN OVERVIEW")
    logger.info(f"   Total pending targets: {total_targets}")
    logger.info(f"   Available senders: {len(whatsapp_sequence)}")
    logger.info(f"   Sends per target: {len(whatsapp_sequence)} (sequential)")
    logger.info(f"   Maximum total sends: {total_targets * len(whatsapp_sequence)}")
    logger.info("=" * 100)

    for target_count, (row_index, target_row) in enumerate(targets_to_process, 1):
        logger.info("")
        logger.info("━" * 100)
        logger.info(f"🎯 TARGET {target_count}/{total_targets}")
        logger.info("━" * 100)
        
        with tasks_lock:
            tasks_status[task_id]['progress'] = f"Processing WhatsApp Target {target_count}/{total_targets}"

        phones_str = target_row[phone_col]
        if not phones_str:
            logger.warning(f"⚠️  No phone found for target {target_count}")
            sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, "No Phone Found")
            continue

        phone_numbers = list(set(f"+{p.strip()}" for p in phones_str.split(',') if p.strip().isdigit()))
        if not phone_numbers:
            logger.warning(f"⚠️  No valid phone found for target {target_count}")
            sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, "No Valid Phone")
            continue
        
        logger.info(f"📱 Recipient(s): {', '.join(phone_numbers)}")
        logger.info(f"📋 Will attempt sequential sends using {len(whatsapp_sequence)} sender(s)")
        
        sent_count_for_target = 0
        final_status_messages = []

        for sender_index, sender_config in enumerate(whatsapp_sequence, 1):
            sender_id = sender_config.get('id')
            api_key = sender_config.get('api_key')
            resume_file = sender_config.get('resume_filename')

            if not all([sender_id, api_key, resume_file]):
                logger.warning(f"⚠️  Skipping WhatsApp sender '{sender_id}' due to missing config")
                continue

            logger.info("")
            logger.info(f"   → Sender #{sender_index}: {sender_id}")
            
            is_available = rate_limiter.is_sender_available('whatsapp', sender_id)

            if is_available:
                logger.info(f"      💬 Preparing WhatsApp message...")
                logger.info(f"         From Account: {sender_id}")
                logger.info(f"         To: {', '.join(phone_numbers)}")
                logger.info(f"         Resume File: {resume_file}")
                logger.info(f"      📤 Uploading resume to Inboxino...")
                
                # For WhatsApp, the attachment must be uploaded for each send to get a temporary ID
                attachment_id = upload_file_to_inboxino(api_key, resume_file)
                
                if attachment_id:
                    logger.info(f"      ✅ Resume uploaded successfully")
                    logger.info(f"      🚀 Sending WhatsApp message...")
                    
                    status_msg = send_whatsapp_message(
                        phone_numbers_to_send=phone_numbers,
                        attachment_file_id=attachment_id,
                        sender_config=sender_config,
                        resume_filename=resume_file
                    )
                    
                    if "Sent via" in status_msg:
                        logger.info(f"      ✅ SUCCESS - WhatsApp sent from {sender_id} to {', '.join(phone_numbers)}")
                        rate_limiter.log_send(sender_id, ','.join(phone_numbers), 'whatsapp')
                        sent_count_for_target += 1
                    else:
                        logger.error(f"      ❌ FAILED - {status_msg}")
                else:
                    status_msg = f"Failed: Upload error for {resume_file}"
                    logger.error(f"      ❌ FAILED - Could not upload resume to Inboxino")
                
                final_status_messages.append(status_msg)
            else:
                status_msg = f"Skipped: {sender_id} rate-limited"
                logger.warning(f"      ⏸️  SKIPPED - Sender rate-limited")
                final_status_messages.append(status_msg)

        logger.info("")
        logger.info(f"📊 SUMMARY for {', '.join(phone_numbers)}:")
        logger.info(f"   Successful sends: {sent_count_for_target}/{len(whatsapp_sequence)}")
        logger.info(f"   Status messages: {final_status_messages}")
        
        final_status = f"Completed: Sent {sent_count_for_target}/{len(whatsapp_sequence)}. Details: [{', '.join(final_status_messages)}]"
        sheets_service.update_cell(worksheet, row_index + 1, status_col + 1, final_status)
        logger.info(f"   💾 Status updated in Google Sheets")
        logger.info("━" * 100)

    logger.info("")
    logger.info("=" * 100)
    logger.info("🎉 WHATSAPP CAMPAIGN COMPLETED")
    logger.info(f"   Task ID: {task_id}")
    logger.info(f"   Total targets processed: {total_targets}")
    logger.info("=" * 100)
    
    with tasks_lock:
        tasks_status[task_id].update({'status': 'completed', 'progress': 'WhatsApp campaign finished.', 'finished_at': datetime.utcnow()})

# ==============================================================================
# FRONTEND VIEW CLASSES
# ==============================================================================
class DashboardView(View):
    """Render the dashboard page."""
    def get(self, request):
        return render(request, 'scraper/dashboard.html')

class ScrapingPageView(View):
    """Render the scraping page."""
    def get(self, request):
        return render(request, 'scraper/scraping.html')

class EmailCampaignPageView(View):
    """Render the email campaign page."""
    def get(self, request):
        return render(request, 'scraper/email_campaign.html')

class WhatsAppCampaignPageView(View):
    """Render the WhatsApp campaign page."""
    def get(self, request):
        return render(request, 'scraper/whatsapp_campaign.html')

class TaskTrackerPageView(View):
    """Render the task tracker page."""
    def get(self, request):
        return render(request, 'scraper/task_tracker.html')

# ==============================================================================
# API VIEW CLASSES
# ==============================================================================
class StartScrapingView(APIView):
    """API endpoint to start the data scraping process."""
    def post(self, request):
        countries = request.data.get('country')
        jobs = request.data.get('job')
        max_results = request.data.get('max_results', 30)  # Reduced from 3 to 30 as reasonable default
        proxy_type = request.data.get('proxy_type', 'RESIDENTIAL')  # Changed to RESIDENTIAL for better LinkedIn scraping

        if not countries or not jobs:
            return Response({"error": "'country' and 'job' fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        job_combinations = [{'country': c, 'job': j} for c in (countries if isinstance(countries, list) else [countries]) for j in (jobs if isinstance(jobs, list) else [jobs]) if c and j]
        if not job_combinations:
            return Response({"error": "No valid country/job combinations provided."}, status=status.HTTP_400_BAD_REQUEST)

        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks_status[task_id] = {'type': 'Scraping', 'status': 'queued', 'progress': 'Waiting to start...', 'started_at': datetime.utcnow()}

        thread = threading.Thread(target=run_scraping_logic, args=(task_id, job_combinations, max_results, proxy_type))
        thread.start()

        return Response({"message": "Scraping task has been successfully started.", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)

class StartEmailCampaignView(APIView):
    """API endpoint to start the email sending campaign."""
    def post(self, request):
        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks_status[task_id] = {'type': 'Email Campaign', 'status': 'queued', 'progress': 'Waiting to start...', 'started_at': datetime.utcnow()}

        thread = threading.Thread(target=run_email_campaign_logic, args=(task_id,))
        thread.start()

        return Response({"message": "Email campaign has been successfully started.", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)

class StartWhatsappCampaignView(APIView):
    """API endpoint to start the WhatsApp sending campaign."""
    def post(self, request):
        task_id = str(uuid.uuid4())
        with tasks_lock:
            tasks_status[task_id] = {'type': 'WhatsApp Campaign', 'status': 'queued', 'progress': 'Waiting to start...'}

        thread = threading.Thread(target=run_whatsapp_campaign_logic, args=(task_id,))
        thread.start()

        return Response({"message": "WhatsApp campaign has been successfully started.", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)

class TaskStatusView(APIView):
    """API endpoint to check the status of a running task."""
    def get(self, request, task_id):
        with tasks_lock:
            task_info = tasks_status.get(task_id)
        if not task_info:
            return Response({"error": "Task ID not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(task_info.copy(), status=status.HTTP_200_OK)