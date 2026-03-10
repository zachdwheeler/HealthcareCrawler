from bs4 import BeautifulSoup
import requests
from http_client import get_with_retries


def extract_page_data(session: requests.Session, url: str):
    """
    Extract structured data from a profile page.
    
    DESIGN NOTE: Session is passed in for connection reuse + stability.
    This allows the caller to manage a single session across multiple threads,
    reducing overhead and improving resilience.
    
    Args:
        session: Shared requests.Session for connection reuse (DO NOT create new session here)
        url: Profile page URL
    
    Returns:
        Dictionary with keys: name, speciality, employer/address, type
        Type is either 'provider' (healthcare professional) or 'institution'
        Returns empty strings for any missing HTML elements (handled gracefully)
    """
    response = get_with_retries(session, url, timeout=(5, 30))
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Helper to safely extract text from elements (returns empty string if not found)
    def safe_text(element):
        return element.get_text(strip=True) if element else ""
    
    # Determine if this is a provider (zorgverlener) or institution profile
    if url.find("zorgverlener") != -1:
        # Healthcare provider profile
        data = {
            "name": safe_text(soup.find('h1', class_="mb-0 d-inline")),
            "speciality": safe_text(soup.find('p', class_="mb-0 me-4")),
            "employer": safe_text(soup.find('a', class_="address_content")),
            "type": "provider",
        }
    else:
        # Institution (healthcare facility) profile
        data = {
            "name": safe_text(soup.find('h1', class_="mb-0 d-inline")),
            "speciality": safe_text(soup.find('p', class_="mb-2")),
            "address": safe_text(soup.find('button', class_="modal-address-toggle me-lg-2 mb-3 mb-xl-0")),
            "type": "institution",
        }
    
    return data
