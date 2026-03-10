from bs4 import BeautifulSoup
import json
import requests
from pathlib import Path
from http_client import get_with_retries


def page_has_results(session: requests.Session, url: str) -> bool:
    """
    Check if a page has results by looking for the filter-result div.
    Uses the provided session and automatic retries.
    """
    response = get_with_retries(session, url, timeout=(5, 30))
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("div", class_="filter-result") is not None

def find_last_good_page(session: requests.Session, base_url: str) -> int:
    """
    Find the last page number with results using binary search.
    
    Args:
        session: requests.Session to use for HTTP requests
        base_url: Base URL with pagination parameter (e.g., 'url?p=')
    
    Returns:
        The highest page number that has results
    
    Strategy:
      1) Exponential search: double page number until we hit a page with no results
      2) Binary search: narrow down the exact boundary
    """
    # Step 1: Exponential search to find a failing upper bound
    low = 0
    high = 1
    while page_has_results(session, base_url + str(high)):
        low = high
        high *= 2

    # Step 2: Binary search between low (good) and high (bad)
    while low + 1 < high:
        mid = (low + high) // 2
        if page_has_results(session, base_url + str(mid)):
            low = mid
        else:
            high = mid

    return low

def detect_type(url):
    if "zorgverlener" in url:
        return "provider"
    else:
        return "institution"


def clear_data_files(*file_paths):
    """
    Clear (delete) data files before starting a fresh crawl.
    
    Args:
        *file_paths: Variable number of Path objects to clear
    
    This ensures you start with empty files for each test run.
    """
    for file_path in file_paths:
        if file_path.exists():
            file_path.unlink()
            print(f"Cleared {file_path}")
        else:
            print(f"ℹ{file_path} doesn't exist yet (will be created)")
    