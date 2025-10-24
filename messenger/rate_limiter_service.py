# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta
import pandas as pd
from django.conf import settings
from scraper.services.google_sheets_service import GoogleSheetsService

logger = logging.getLogger(__name__)

class RateLimiterService:
    """
    Manages sender accounts and controls daily sending limits for each.
    This version is optimized for sequential campaigns.
    """
    def __init__(self, sheets_service: GoogleSheetsService):
        """Initializes the service and fetches usage logs once to cache them."""
        logger.info("=" * 80)
        logger.info("RATE LIMITER SERVICE - Initializing...")
        logger.info("=" * 80)
        
        self.sheets_service = sheets_service
        self.senders_pool_sheet_name = settings.SENDERS_POOL_SHEET_NAME
        self.senders_log_sheet_name = settings.SENDERS_LOG_SHEET_NAME
        
        logger.info(f"📋 Senders Pool Sheet: '{self.senders_pool_sheet_name}'")
        logger.info(f"📋 Senders Log Sheet: '{self.senders_log_sheet_name}'")
        
        self._load_limits()
        # Cache logs to avoid reading from Google Sheets repeatedly during a campaign
        self.usage_df = self._get_usage_logs()
        
        logger.info("✅ Rate Limiter Service initialized successfully")
        logger.info("=" * 80)

    def _load_limits(self):
        """Loads sending limits from Django settings."""
        logger.info("⚙️  Loading daily sending limits from settings...")
        
        self.limits = {
            'email': settings.EMAIL_DAILY_LIMIT,
            'whatsapp': settings.WHATSAPP_DAILY_LIMIT,
        }
        
        logger.info(f"   📧 Email daily limit: {self.limits['email']} messages per sender")
        logger.info(f"   💬 WhatsApp daily limit: {self.limits['whatsapp']} messages per sender")

    def get_senders_by_type(self, service_type: str) -> list:
        """
        [NEW] Retrieves the FULL list of active sender configurations for a given service type.
        This is used to get the entire sequence for a campaign.
        """
        logger.info("-" * 80)
        logger.info(f"🔍 Fetching active senders for type: '{service_type}'")
        
        try:
            worksheet = self.sheets_service.get_worksheet(self.senders_pool_sheet_name)
            records = worksheet.get_all_records()
            
            # Filter for active senders of this type
            active_senders = [record for record in records if record.get('type') == service_type and record.get('is_active')]
            
            logger.info(f"✅ Found {len(active_senders)} active {service_type} sender(s)")
            
            if active_senders:
                logger.info(f"📋 Sender sequence for {service_type}:")
                for idx, sender in enumerate(active_senders, 1):
                    sender_id = sender.get('id', 'Unknown')
                    logger.info(f"   {idx}. Account: {sender_id}")
            else:
                logger.warning(f"⚠️  No active senders found for type '{service_type}'")
            
            logger.info("-" * 80)
            return active_senders
            
        except Exception as e:
            logger.error(f"❌ Could not read the '{self.senders_pool_sheet_name}' sheet: {e}")
            logger.info("-" * 80)
            return []

    def _get_usage_logs(self) -> pd.DataFrame:
        """Retrieves all sending logs from the 'Senders Log' sheet and returns a pandas DataFrame."""
        logger.info("📊 Loading sending history from 'Senders Log' sheet...")
        
        try:
            worksheet = self.sheets_service.get_worksheet(self.senders_log_sheet_name)
            logs = worksheet.get_all_records()
            
            if not logs:
                logger.info("   ℹ️  No previous sending history found (clean slate)")
                return pd.DataFrame(columns=['sender_id', 'timestamp'])
            
            df = pd.DataFrame(logs)
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df_clean = df.dropna(subset=['timestamp'])
            
            # Calculate stats for last 24 hours
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_logs = df_clean[df_clean['timestamp'] >= twenty_four_hours_ago]
            
            logger.info(f"   📈 Total sending records: {len(df_clean)}")
            logger.info(f"   🕐 Messages sent in last 24h: {len(recent_logs)}")
            
            if len(recent_logs) > 0:
                # Show breakdown by service type
                by_type = recent_logs.groupby('service_type').size()
                for service_type, count in by_type.items():
                    logger.info(f"      • {service_type}: {count} messages")
            
            return df_clean
            
        except Exception as e:
            logger.error(f"❌ Could not read the '{self.senders_log_sheet_name}' sheet: {e}")
            return pd.DataFrame(columns=['sender_id', 'timestamp'])

    def is_sender_available(self, service_type: str, sender_id: str) -> bool:
        """
        [NEW & CRITICAL] Checks if a SPECIFIC sender has reached its daily sending limit.
        Uses the cached usage logs for efficiency.
        """
        if not sender_id:
            logger.warning("⚠️  No sender_id provided for availability check")
            return False

        logger.info(f"🔎 Checking availability for sender: {sender_id}")
        
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        # Filter the cached DataFrame
        sender_usage = self.usage_df[
            (self.usage_df['sender_id'] == sender_id) &
            (self.usage_df['timestamp'] >= twenty_four_hours_ago)
        ]
        
        usage_count = len(sender_usage)
        limit = self.limits.get(service_type, 0)
        remaining = limit - usage_count

        if usage_count < limit:
            logger.info(f"   ✅ AVAILABLE - Account: {sender_id}")
            logger.info(f"      📊 Usage: {usage_count}/{limit} ({remaining} remaining)")
            logger.info(f"      ⏰ Window: Last 24 hours")
            return True
        else:
            logger.warning(f"   ❌ RATE LIMITED - Account: {sender_id}")
            logger.warning(f"      📊 Usage: {usage_count}/{limit} (limit reached)")
            logger.warning(f"      ⏸️  This sender needs to wait before sending more messages")
            return False

    def log_send(self, sender_id: str, recipient: str, service_type: str):
        """
        Logs a successful send operation to the 'Senders Log' sheet and updates the in-memory cache.
        """
        logger.info("=" * 80)
        logger.info("📝 LOGGING SUCCESSFUL SEND")
        logger.info(f"   📤 From Account: {sender_id}")
        logger.info(f"   📬 To: {recipient}")
        logger.info(f"   📋 Service: {service_type}")
        
        try:
            worksheet = self.sheets_service.get_worksheet(self.senders_log_sheet_name)
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            new_log = [sender_id, service_type, recipient, timestamp]
            
            logger.info(f"   🕐 Timestamp: {timestamp}")
            logger.info("   💾 Saving to Google Sheets...")
            
            worksheet.append_row(new_log)
            
            # Also update the in-memory dataframe to avoid re-reading the sheet during the same campaign
            new_log_df = pd.DataFrame([new_log], columns=['sender_id', 'service_type', 'recipient', 'timestamp'])
            new_log_df['timestamp'] = pd.to_datetime(new_log_df['timestamp'])
            self.usage_df = pd.concat([self.usage_df, new_log_df], ignore_index=True)
            
            # Calculate updated usage
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            sender_usage = self.usage_df[
                (self.usage_df['sender_id'] == sender_id) &
                (self.usage_df['timestamp'] >= twenty_four_hours_ago)
            ]
            usage_count = len(sender_usage)
            limit = self.limits.get(service_type, 0)
            remaining = limit - usage_count
            
            logger.info(f"   ✅ Successfully logged to 'Senders Log' sheet")
            logger.info(f"   📊 Updated usage for {sender_id}: {usage_count}/{limit} ({remaining} remaining)")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ FAILED to log send for sender '{sender_id}'")
            logger.error(f"   Error: {e}")
            logger.error("=" * 80)