# -*- coding: utf-8 -*-
import os
import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
import logging

logger = logging.getLogger(__name__)

# ==============================================================================
# WhatsApp Service (Updated for dynamic resumes)
# ==============================================================================
def upload_file_to_inboxino(api_key: str, resume_filename: str):
    """
    Handles uploading a specific resume file to the Inboxino server.
    """
    if not api_key:
        logger.error("Inboxino API Key is required for file upload.")
        return None
    if not resume_filename:
        logger.error("A resume filename is required for upload.")
        return None

    logger.info(f"Attempting to upload '{resume_filename}' to Inboxino...")
    file_path = os.path.join(settings.BASE_DIR, resume_filename)
    
    if not os.path.exists(file_path):
        logger.error(f"Inboxino Upload Error: The resume file '{file_path}' was not found.")
        return None

    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    upload_url = 'https://dl2.inboxino.com/api/upload/file'

    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(upload_url, headers=headers, files=files, timeout=45)
            response.raise_for_status()
            
            response_json = response.json()
            attachment_id = response_json.get('data', {}).get('path')

            if not attachment_id:
                logger.error("Inboxino upload successful, but could not find 'path' key in the API response.")
                return None
            
            logger.info(f"File '{resume_filename}' uploaded successfully. Attachment Path: {attachment_id}")
            return attachment_id

    except requests.exceptions.HTTPError as e:
        logger.error(f"Inboxino Upload API Error ({e.response.status_code}): {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Inboxino Upload Error: A network error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during file upload to Inboxino: {e}")
        return None

def send_whatsapp_message(phone_numbers_to_send: list, attachment_file_id: str, sender_config: dict, resume_filename: str):
    """
    Sends a WhatsApp message using a specific sender configuration and resume filename.
    """
    if not phone_numbers_to_send: return "No Valid Phone Found"
    if not attachment_file_id: return "Failed: Missing Attachment ID"
    if not sender_config or not sender_config.get('api_key'): return "Failed: Invalid Sender Config"

    api_key = sender_config['api_key']
    sender_id = sender_config['id']
    logger.info(f"Sending WhatsApp message via sender '{sender_id}' to: {', '.join(phone_numbers_to_send)}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "messages": [{
            "message_type": "file",
            "attachment_file": attachment_file_id,
            "origin_file_name": resume_filename, # Use the dynamic filename
            "message": settings.WHATSAPP_MESSAGE_CONTENT
        }],
        "type": "notification",
        "recipients": phone_numbers_to_send,
        "platforms": ["whatsapp"],
        "with_country_code": "0"
    }

    try:
        response = requests.post(settings.INBOXINO_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        return f"Sent via {sender_id}"
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send WhatsApp message via {sender_id}: {e}")
        return f"Failed: Sending Error ({sender_id})"

# ==============================================================================
# Email Service (UPDATED FOR TLS CONNECTION)
# ==============================================================================
def send_email(recipient_email: str, sender_config: dict, resume_filename: str, subject: str):
    """
    Sends a single email with a dynamic resume and subject, based on the sender configuration.
    """
    if not recipient_email:
        return "No Valid Email Found"
    if not all(k in sender_config for k in ['id', 'password', 'host', 'port']):
        return "Failed: Invalid Sender Config"
    if not resume_filename or not subject:
        return "Failed: Missing resume filename or subject from Senders Pool"

    sender_id = sender_config['id']
    logger.info(f"Preparing to send email from '{sender_id}' to '{recipient_email}' with resume '{resume_filename}' and subject '{subject}'")
    
    resume_path = os.path.join(settings.BASE_DIR, resume_filename)
    if not os.path.exists(resume_path):
        logger.error(f"Email Error: Attachment file not found at '{resume_path}'. Make sure '{resume_filename}' is in the project root.")
        return f"Failed: Attachment '{resume_filename}' not found"

    html_content = """
    <div style="font-family: 'Segoe UI', Arial, sans-serif; color: #333;">
      <p>Dear Hiring Manager,</p>
      <p>I am writing to express my interest in a software development role at your company. My experience in Python, Django, and automation aligns with the kind of innovative work you are doing.</p>
      <p>Please find my resume attached for your consideration. I am confident that my skills would be a valuable asset to your team.</p>
      <p>Thank you for your time.</p>
      <p>Sincerely,</p>
      <p>A Professional Developer</p>
    </div>
    """
    
    try:
        # --- CRITICAL FIX: Added use_tls from settings ---
        connection = get_connection(
            host=sender_config['host'],
            port=sender_config['port'],
            username=sender_id,
            password=sender_config['password'],
            use_tls=settings.EMAIL_USE_TLS, # This enables STARTTLS for Port 587
            use_ssl=settings.EMAIL_USE_SSL
        )
        email = EmailMultiAlternatives(
            subject=subject,
            body="Please find my resume attached.",
            from_email=f"{settings.MAIL_FROM_NAME} <{sender_id}>",
            to=[recipient_email],
            connection=connection
        )
        email.attach_alternative(html_content, "text/html")
        email.attach_file(resume_path)
        
        email.send(fail_silently=False)
        logger.info(f"Successfully sent email from '{sender_id}' to '{recipient_email}'")
        return f"Sent via {sender_id}"

    except Exception as e:
        logger.error(f"Failed to send email from {sender_id} to {recipient_email}: {e}")
        return f"Failed: Sending Error ({sender_id})"

