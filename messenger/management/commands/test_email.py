import os
from django.conf import settings
from django.core.management.base import BaseCommand
from messenger.services import send_email
from scraper.services.google_sheets_service import GoogleSheetsService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reads ALL emails from the Google Sheet and sends a separate test email to each.'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Starting Google Sheet Email Test (Loop Mode) ---")

        try:
            # Step 1: Connect to Google Sheets
            self.stdout.write("Connecting to Google Sheets...")
            google_sheet_id = os.environ["GOOGLE_SHEET_ID"]
            google_service_account_path = os.environ["GOOGLE_SERVICE_ACCOUNT_PATH"]
            
            sheets_service = GoogleSheetsService(google_service_account_path, google_sheet_id)
            worksheet = sheets_service.get_worksheet("Sheet1")
            self.stdout.write(self.style.SUCCESS("Successfully connected to Google Sheet."))

            # Step 2: Find and read ALL valid emails from the 'emails' column
            self.stdout.write("Searching for all valid emails in the sheet...")
            header_map = sheets_service.get_header_map(worksheet)
            email_column_name = settings.EMAIL_COLUMN_NAME
            email_column_index = header_map.get(email_column_name)

            if not email_column_index:
                self.stdout.write(self.style.ERROR(f"Error: Column '{email_column_name}' not found in the Google Sheet."))
                return

            all_cells_in_column = worksheet.col_values(email_column_index)
            
            # --- MODIFIED LOGIC ---
            # Flatten the list by splitting comma-separated emails from each cell
            all_individual_emails = []
            for cell_content in all_cells_in_column[1:]:  # Skip header
                if cell_content:
                    # Split by comma and strip whitespace from each potential email
                    emails_in_cell = [email.strip() for email in cell_content.split(',')]
                    all_individual_emails.extend(emails_in_cell)

            # Filter for valid, unique email addresses
            recipient_list = sorted(list(set([email for email in all_individual_emails if email and '@' in email])))
            
            if not recipient_list:
                self.stdout.write(self.style.ERROR(f"Error: No valid email addresses found in the '{email_column_name}' column."))
                return
                
            self.stdout.write(f"Found {len(recipient_list)} unique emails. Preparing to send test emails...")
            self.stdout.write(f"Recipients: {', '.join(recipient_list)}")

            # Step 3: Call the send_email function with the full list
            result = send_email(recipient_list)

            if "Failed" in result:
                self.stdout.write(self.style.ERROR(f"Email dispatch process completed with errors. Summary: {result}"))
                self.stdout.write(self.style.WARNING("Please check your .env file settings and the console logs for more details."))
            else:
                self.stdout.write(self.style.SUCCESS(f"Email sending process complete! Summary: {result}"))

        except KeyError as e:
            self.stdout.write(self.style.ERROR(f"Environment variable not set: {e}. Please check your .env file."))
        except Exception as e:
            logger.error(f"An unexpected error occurred in test_email command: {e}")
            self.stdout.write(self.style.ERROR(f"An unexpected error occurred: {e}"))

