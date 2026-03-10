from bs4 import BeautifulSoup
import time
import requests
from http_client import get_with_retries


def fetch_results_data(session: requests.Session, url: str):
    """
    Fetch search results from a URL and extract profile links.
    
    DESIGN NOTE: Session is passed in for connection reuse + stability.
    This allows the full crawl to use a single session across sequential
    results-page fetches, reducing overhead and improving resilience.
    
    Args:
        session: Shared requests.Session for connection reuse (DO NOT create new session here)
        url: Search results page URL
    
    Returns:
        List of href links to individual profiles (e.g., '/professional/123')
        Filters out None hrefs automatically
    """
    start = time.time()
    response = get_with_retries(session, url, timeout=(5, 30))
    end = time.time()
    print(f'It took {end-start} seconds to fetch the page')
    
    soup = BeautifulSoup(response.text, 'html.parser')
    start = time.time()
    print(f'It took {start-end} seconds to parse HTML')
    
    # page_links: search results pointing to different institutions or providers
    page_list = []
    page_links = soup.find_all('a', class_="filter-result__name")
    for link in page_links:
        href = link.get("href")
        if href:  # Only add non-None hrefs
            page_list.append(href)
    
    end = time.time()
    print(f'Link extraction took {end-start} seconds')
    return page_list