import logging
import os
import time
from apify_client import ApifyClient

logger = logging.getLogger(__name__)

class ApifyService:
    """
    This class is responsible for all interactions with the Apify API.
    """

    def __init__(self, api_token: str):
        logger.info("=" * 80)
        logger.info("🔧 APIFY SERVICE - Initializing...")
        logger.info("=" * 80)
        
        if not api_token:
            logger.error("❌ Apify API token is missing!")
            raise ValueError("Apify API token is required.")
        
        logger.info("🔐 API token provided (length: {})".format(len(api_token)))
        logger.info("🌐 Creating Apify client...")
        self.client = ApifyClient(api_token)
        logger.info("✅ Apify client created successfully")

        # Actor IDs are read from environment variables for flexibility
        logger.info("📋 Loading Actor IDs from environment...")
        self.LINKEDIN_ACTOR_ID = os.environ.get("LINKEDIN_ACTOR_ID")
        self.CONTACT_SCRAPER_ACTOR_ID = os.environ.get("CONTACT_SCRAPER_ACTOR_ID")

        if not self.LINKEDIN_ACTOR_ID or not self.CONTACT_SCRAPER_ACTOR_ID:
            logger.error("❌ Actor IDs not found in environment variables!")
            raise ValueError("Actor IDs (LINKEDIN_ACTOR_ID, CONTACT_SCRAPER_ACTOR_ID) must be set in the .env file.")
        
        logger.info(f"   📌 LinkedIn Actor: {self.LINKEDIN_ACTOR_ID}")
        logger.info(f"   📌 Contact Scraper Actor: {self.CONTACT_SCRAPER_ACTOR_ID}")
        logger.info("✅ Apify Service initialized successfully")
        logger.info("=" * 80)


    def _run_actor(self, actor_id: str, run_input: dict, memory_mbytes: int | None = None, timeout_secs: int | None = None, max_retries: int = 3) -> list:
        """
        A generic method to run any actor and retrieve its results from the dataset.
        Includes retry logic with exponential backoff for transient errors.
        """
        logger.info("-" * 80)
        logger.info(f"🎬 EXECUTING APIFY ACTOR")
        logger.info(f"   Actor ID: {actor_id}")
        logger.info(f"   Input Parameters: {run_input}")
        logger.info(f"   Memory (MB): {memory_mbytes}")
        logger.info(f"   Timeout (s) : {timeout_secs}")
        logger.info(f"   Max Retries: {max_retries}")
        logger.info("-" * 80)
        
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    # Exponential backoff: 5s, 10s, 20s
                    wait_time = 5 * (2 ** (attempt - 2))
                    logger.info(f"⏰ Retry attempt {attempt}/{max_retries} - Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                logger.info(f"⏳ Starting actor execution (attempt {attempt}/{max_retries})...")
                actor_run = self.client.actor(actor_id).call(
                    run_input=run_input,
                    memory_mbytes=memory_mbytes,
                    timeout_secs=timeout_secs,
                )
                
                run_id = actor_run.get('id', 'unknown')
                dataset_id = actor_run.get('defaultDatasetId', 'unknown')
                run_status = actor_run.get('status', 'unknown')
                
                logger.info(f"✅ Actor execution completed")
                logger.info(f"   Run ID: {run_id}")
                logger.info(f"   Status: {run_status}")
                logger.info(f"   Dataset ID: {dataset_id}")
                
                logger.info(f"📥 Fetching results from dataset...")
                items = list(self.client.dataset(dataset_id).iterate_items())
                
                logger.info(f"✅ Successfully retrieved {len(items)} item(s)")
                logger.info("-" * 80)
                return items
                
            except Exception as e:
                error_msg = str(e)
                logger.error("-" * 80)
                logger.error(f"❌ ACTOR EXECUTION FAILED (Attempt {attempt}/{max_retries})")
                logger.error(f"   Actor ID: {actor_id}")
                logger.error(f"   Error: {error_msg}")
                
                # Check if it's a transient error that we should retry
                is_retryable = any(keyword in error_msg.lower() for keyword in [
                    'timeout', 'connection', 'network', 'temporary', 'rate limit', '429', '503', '502'
                ])
                
                if attempt < max_retries and is_retryable:
                    logger.warning(f"⚠️  Transient error detected. Will retry...")
                    logger.error("-" * 80)
                    continue
                else:
                    if attempt >= max_retries:
                        logger.error(f"❌ Maximum retries ({max_retries}) reached. Giving up.")
                    else:
                        logger.error(f"❌ Non-retryable error. Not attempting retry.")
                    logger.error("-" * 80)
                    return []
        
        # If we get here, all retries failed
        return []

    def _run_actor_streaming(self, actor_id: str, run_input: dict, memory_mbytes: int | None = None, timeout_secs: int | None = None, max_retries: int = 3):
        """
        Runs an actor and yields results incrementally instead of loading all into memory.
        This is a generator that yields items one by one as they're fetched from the dataset.
        
        This is the MEMORY-OPTIMIZED version for large datasets.
        """
        logger.info("-" * 80)
        logger.info(f"🎬 EXECUTING APIFY ACTOR (STREAMING MODE)")
        logger.info(f"   Actor ID: {actor_id}")
        logger.info(f"   Input Parameters: {run_input}")
        logger.info(f"   Memory (MB): {memory_mbytes}")
        logger.info(f"   Timeout (s) : {timeout_secs}")
        logger.info(f"   Max Retries: {max_retries}")
        logger.info(f"   🔄 Mode: Incremental/Streaming (Memory Optimized)")
        logger.info("-" * 80)
        
        for attempt in range(1, max_retries + 1):
            try:
                if attempt > 1:
                    wait_time = 5 * (2 ** (attempt - 2))
                    logger.info(f"⏰ Retry attempt {attempt}/{max_retries} - Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                logger.info(f"⏳ Starting actor execution (attempt {attempt}/{max_retries})...")
                actor_run = self.client.actor(actor_id).call(
                    run_input=run_input,
                    memory_mbytes=memory_mbytes,
                    timeout_secs=timeout_secs,
                )
                
                run_id = actor_run.get('id', 'unknown')
                dataset_id = actor_run.get('defaultDatasetId', 'unknown')
                run_status = actor_run.get('status', 'unknown')
                
                logger.info(f"✅ Actor execution completed")
                logger.info(f"   Run ID: {run_id}")
                logger.info(f"   Status: {run_status}")
                logger.info(f"   Dataset ID: {dataset_id}")
                
                logger.info(f"📥 Streaming results from dataset (processing incrementally)...")
                
                # Yield items one by one instead of loading all into memory
                item_count = 0
                for item in self.client.dataset(dataset_id).iterate_items():
                    item_count += 1
                    if item_count % 10 == 0:
                        logger.info(f"   📊 Processed {item_count} items so far...")
                    yield item
                
                logger.info(f"✅ Successfully streamed {item_count} item(s)")
                logger.info("-" * 80)
                return  # Generator finished successfully
                
            except Exception as e:
                error_msg = str(e)
                logger.error("-" * 80)
                logger.error(f"❌ ACTOR EXECUTION FAILED (Attempt {attempt}/{max_retries})")
                logger.error(f"   Actor ID: {actor_id}")
                logger.error(f"   Error: {error_msg}")
                
                is_retryable = any(keyword in error_msg.lower() for keyword in [
                    'timeout', 'connection', 'network', 'temporary', 'rate limit', '429', '503', '502'
                ])
                
                if attempt < max_retries and is_retryable:
                    logger.warning(f"⚠️  Transient error detected. Will retry...")
                    logger.error("-" * 80)
                    continue
                else:
                    if attempt >= max_retries:
                        logger.error(f"❌ Maximum retries ({max_retries}) reached. Giving up.")
                    else:
                        logger.error(f"❌ Non-retryable error. Not attempting retry.")
                    logger.error("-" * 80)
                    return  # Exit generator
        
        # If we get here, all retries failed
        return

    def run_linkedin_job_scraper(self, search_url: str, max_results: int = 30, proxy_group: str = "RESIDENTIAL", memory_mbytes: int = 512, max_concurrency: int = 1) -> list:
        """
        Runs the LinkedIn job scraping actor.
        The 'proxy_group' parameter was added for consistency.
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("🔍 LINKEDIN JOB SCRAPER")
        logger.info("=" * 80)
        logger.info(f"🔗 Search URL: {search_url}")
        logger.info(f"📊 Max Results: {max_results}")
        logger.info(f"🌐 Proxy Type: {proxy_group.upper()}")
        logger.info(f"🏢 Include Company Details: Yes")
        logger.info(f"⚙️  Max Concurrency: {max_concurrency}")
        logger.info(f"💾 Memory Allocated: {memory_mbytes} MB")
        logger.info("=" * 80)
        
        run_input = {
            "search_url": search_url,
            "include_company_details": True,
            "max_results": max_results,
            "proxy_group": proxy_group.upper(),
            # actor-specific concurrency setting (if supported)
            "maxConcurrency": max_concurrency,
            # optional flags many store actors accept to reduce overhead:
            "headless": True,
            "debugMode": False,
            "saveScreenshots": False,
            "saveHtml": False,
            # Additional settings for stability
            "useChrome": False,  # Use Firefox instead (sometimes more stable)
            "useApifyProxy": True,  # Ensure proxy usage
        }
        
        logger.info("🚀 Initiating LinkedIn job scraping...")
        results = self._run_actor(
            self.LINKEDIN_ACTOR_ID,
            run_input,
            memory_mbytes=memory_mbytes,
            timeout_secs=600,   # tune as needed
        )
        
        if results:
            logger.info("=" * 80)
            logger.info(f"✅ LINKEDIN SCRAPING COMPLETED")
            logger.info(f"   Jobs found: {len(results)}")
            logger.info("=" * 80)
        else:
            logger.warning("=" * 80)
            logger.warning("⚠️  NO JOBS FOUND OR SCRAPING FAILED")
            logger.warning("   This could be due to:")
            logger.warning("   - LinkedIn rate limiting (429 errors)")
            logger.warning("   - No matching jobs for this search")
            logger.warning("   - LinkedIn blocking the scraper")
            logger.warning("   - Network/proxy issues")
            logger.warning("")
            logger.warning("   💡 SUGGESTIONS:")
            logger.warning("   1. Reduce max_results (try 20-50 instead of 100)")
            logger.warning("   2. Wait 5-10 minutes before trying again")
            logger.warning("   3. Check if your Apify proxy credits are active")
            logger.warning("   4. Try different proxy_group (GOOGLE_SERP, SHADER)")
            logger.warning("=" * 80)
        
        return results

    def run_linkedin_job_scraper_streaming(self, search_url: str, max_results: int = 30, proxy_group: str = "RESIDENTIAL", memory_mbytes: int = 512, max_concurrency: int = 1):
        """
        MEMORY-OPTIMIZED VERSION: Streams LinkedIn job results incrementally.
        
        This generator yields jobs one by one as they're fetched from Apify,
        allowing immediate processing (contact scraping) without loading all jobs into memory.
        
        Perfect for large datasets (many countries/job titles) to avoid RAM exhaustion.
        
        Usage:
            for job in apify_service.run_linkedin_job_scraper_streaming(...):
                # Process this job immediately
                # Scrape contacts, save to sheet, etc.
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("🔍 LINKEDIN JOB SCRAPER (STREAMING MODE)")
        logger.info("=" * 80)
        logger.info(f"🔗 Search URL: {search_url}")
        logger.info(f"📊 Max Results: {max_results}")
        logger.info(f"🌐 Proxy Type: {proxy_group.upper()}")
        logger.info(f"🏢 Include Company Details: Yes")
        logger.info(f"⚙️  Max Concurrency: {max_concurrency}")
        logger.info(f"💾 Memory Allocated: {memory_mbytes} MB")
        logger.info(f"🔄 Processing Mode: INCREMENTAL (Memory Optimized)")
        logger.info("=" * 80)
        
        run_input = {
            "search_url": search_url,
            "include_company_details": True,
            "max_results": max_results,
            "proxy_group": proxy_group.upper(),
            "maxConcurrency": max_concurrency,
            "headless": True,
            "debugMode": False,
            "saveScreenshots": False,
            "saveHtml": False,
            "useChrome": False,
            "useApifyProxy": True,
        }
        
        logger.info("🚀 Initiating LinkedIn job scraping (streaming mode)...")
        
        jobs_yielded = 0
        for job in self._run_actor_streaming(
            self.LINKEDIN_ACTOR_ID,
            run_input,
            memory_mbytes=memory_mbytes,
            timeout_secs=600,
        ):
            jobs_yielded += 1
            yield job
        
        if jobs_yielded > 0:
            logger.info("=" * 80)
            logger.info(f"✅ LINKEDIN SCRAPING COMPLETED (STREAMING)")
            logger.info(f"   Jobs yielded: {jobs_yielded}")
            logger.info(f"   Memory Usage: Optimized (incremental processing)")
            logger.info("=" * 80)
        else:
            logger.warning("=" * 80)
            logger.warning("⚠️  NO JOBS FOUND OR SCRAPING FAILED")
            logger.warning("   This could be due to:")
            logger.warning("   - LinkedIn rate limiting (429 errors)")
            logger.warning("   - No matching jobs for this search")
            logger.warning("   - LinkedIn blocking the scraper")
            logger.warning("   - Network/proxy issues")
            logger.warning("")
            logger.warning("   💡 SUGGESTIONS:")
            logger.warning("   1. Reduce max_results (try 20-50 instead of 100)")
            logger.warning("   2. Wait 5-10 minutes before trying again")
            logger.warning("   3. Check if your Apify proxy credits are active")
            logger.warning("   4. Try different proxy_group (GOOGLE_SERP, SHADER)")
            logger.warning("=" * 80)

    def run_contact_detail_scraper(self, website_url: str,
                                   memory_mbytes: int = 512,
                                   max_concurrency: int = 1,
                                   max_depth: int = 2,
                                   max_requests: int = 5) -> list:
        """
        Runs the actor to scrape contact details from a website (Module 2).
        """
        logger.info("")
        logger.info("=" * 80)
        logger.info("📧 CONTACT DETAIL SCRAPER")
        logger.info("=" * 80)
        logger.info(f"🌐 Target Website: {website_url}")
        logger.info(f"🔍 Max Depth: {max_depth} levels")
        logger.info(f"📄 Max Requests: {max_requests} pages")
        logger.info(f"🔒 Same Domain Only: Yes")
        logger.info(f"🖼️  Include Frames: Yes")
        logger.info(f"⚙️  Max Concurrency: {max_concurrency}")
        logger.info(f"💾 Memory Allocated: {memory_mbytes} MB")
        logger.info("=" * 80)
        
        run_input = {
            "startUrls": [{"url": website_url, "method": "GET"}],
            "maxDepth": max_depth,
            "maxRequests": max_requests,
            "sameDomain": True,
            "considerChildFrames": True,
            # concurrency to reduce RAM (if actor supports it)
            "maxConcurrency": max_concurrency,
            # reduce extras
            "saveScreenshots": False,
            "debugMode": False,
            # Additional stability settings
            "ignoreSslErrors": True,  # Handle SSL certificate issues
            "maxRequestRetries": 3,  # Retry failed requests within the actor
        }
        
        logger.info("🚀 Initiating contact detail scraping...")
        results = self._run_actor(
            self.CONTACT_SCRAPER_ACTOR_ID,
            run_input,
            memory_mbytes=memory_mbytes,
            timeout_secs=600,
        )
        
        if results:
            logger.info("=" * 80)
            logger.info(f"✅ CONTACT SCRAPING COMPLETED")
            logger.info(f"   Data records found: {len(results)}")
            
            # Show summary of what was found
            if len(results) > 0:
                first_result = results[0]
                emails = first_result.get('emails', [])
                phones = first_result.get('phones', [])
                socials = []
                for key in ['linkedIns', 'twitters', 'facebooks', 'instagrams']:
                    if first_result.get(key):
                        socials.append(key)
                
                logger.info(f"   📧 Emails found: {len(emails)}")
                logger.info(f"   📱 Phones found: {len(phones)}")
                logger.info(f"   🔗 Social media: {len(socials)} types")
            logger.info("=" * 80)
        else:
            logger.warning("=" * 80)
            logger.warning("⚠️  NO CONTACT DETAILS FOUND")
            logger.warning(f"   Website: {website_url}")
            logger.warning("   Possible reasons:")
            logger.warning("   - Website doesn't have contact information")
            logger.warning("   - Contact info is behind forms/login")
            logger.warning("   - Website is blocking scrapers")
            logger.warning("=" * 80)
        
        return results
