import re
from typing import List, Dict, Any, Set
from urllib.parse import urlencode

#=====================================================#
#  LinkedIn URL Builder
#=====================================================#

def build_linkedin_url(keyword: str, location_name: str) -> str:
    """
    Constructs a valid LinkedIn job search URL with the primary parameters.
    This function is simplified to be compatible with the new actor that accepts a full URL.
    """
    base_url = "https://www.linkedin.com/jobs/search/"
    params = {
        "keywords": keyword,
        "location": location_name,
    }
    # Other filters like post date or job type should be applied by the user
    # in the frontend or directly in the URL, as per the new actor's documentation.
    query_string = urlencode(params)
    return f"{base_url}?{query_string}&f_WT=2&f_TPR=r86400"


#=====================================================#
#   Data Processing and Cleaning
#=====================================================#

def _clean_and_get_unique_items(items: List[str]) -> List[str]:
    """Filters a list of strings and returns only the unique, non-empty items."""
    if not items:
        return []
    return list(set(filter(None, items)))

def _clean_phones(phones: List[str]) -> List[str]:
    """Takes a list of phone numbers, removes non-numeric characters, and deduplicates them."""
    if not phones:
        return []
    
    phone_set: Set[str] = set()
    for phone in phones:
        if phone and isinstance(phone, str):
            # Remove any character that is not a digit
            cleaned_phone = re.sub(r'\D', '', phone)
            if cleaned_phone:
                phone_set.add(cleaned_phone)
    return list(phone_set)

def _clean_emails(emails: List[str]) -> List[str]:
    """Takes a list of emails, trims whitespace, converts to lowercase, and deduplicates them."""
    if not emails:
        return []
        
    email_set: Set[str] = set()
    for email in emails:
        if email and isinstance(email, str):
            email_set.add(email.strip().lower())
    return list(email_set)


def process_contact_data(scraped_items: List[Dict[str, Any]], original_job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes and aggregates the raw data scraped from the contact info scraper.
    """
    if not scraped_items:
        return {}

    # Initialize lists to aggregate all data
    all_emails: List[str] = []
    all_phones: List[str] = []
    all_linkedins: List[str] = []
    all_twitters: List[str] = []
    all_instagrams: List[str] = []
    all_facebooks: List[str] = []
    all_youtubes: List[str] = []
    all_tiktoks: List[str] = []
    all_pinterests: List[str] = []
    all_discords: List[str] = []
    
    # Iterate through all scraped items and collect the data
    for item in scraped_items:
        all_emails.extend(item.get('emails', []))
        all_phones.extend(item.get('phones', []))
        all_phones.extend(item.get('phonesUncertain', []))
        all_linkedins.extend(item.get('linkedIns', []))
        all_twitters.extend(item.get('twitters', []))
        all_instagrams.extend(item.get('instagrams', []))
        all_facebooks.extend(item.get('facebooks', []))
        all_youtubes.extend(item.get('youtubes', []))
        all_tiktoks.extend(item.get('tiktoks', []))
        all_pinterests.extend(item.get('pinterests', []))
        all_discords.extend(item.get('discords', []))
        
    # Clean and deduplicate the collected data
    unique_phones = _clean_phones(all_phones)
    unique_emails = _clean_emails(all_emails)
    
    def get_first_unique_link(links: list) -> str:
        """Helper function to get the first valid link from a list."""
        unique_links = _clean_and_get_unique_items(links)
        return unique_links[0] if unique_links else ''

    # Compile the final, clean dictionary
    clean_data = {
        "domain": scraped_items[0].get('domain', ''),
        "phones": ', '.join(unique_phones),
        "emails": ', '.join(unique_emails),
        "linkedin": get_first_unique_link(all_linkedins),
        "twitter": get_first_unique_link(all_twitters),
        "instagram": get_first_unique_link(all_instagrams),
        "facebook": get_first_unique_link(all_facebooks),
        "youtube": get_first_unique_link(all_youtubes),
        "tiktok": get_first_unique_link(all_tiktoks),
        "pinterest": get_first_unique_link(all_pinterests),
        "discord": get_first_unique_link(all_discords),
    }
    return clean_data
