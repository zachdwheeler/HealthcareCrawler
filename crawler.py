import utils
import parse
import fetch
import storage
from pathlib import Path
import time
from http_client import make_session
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Configuration
MAX_WORKERS = 12  # Number of concurrent threads for profile fetching (tunable for performance)
BASE_DOMAIN = "https://www.zorgkaartnederland.nl"

# Target: https://www.zorgkaartnederland.nl/
INSTITUTION_PATH = Path("data/institution_data.jsonl")
PROVIDER_PATH = Path("data/provider_data.jsonl")


def _process_profile(session: requests.Session, full_url: str):
    """
    Worker function: Fetch and parse a single profile page.
    
    This runs in a thread pool worker. If any error occurs (network, HTML parsing, etc),
    we catch it and return None instead of raising. This prevents one bad page from
    crashing the entire crawl.
    
    Args:
        session: Shared requests.Session for connection reuse and stability
        full_url: Complete URL to the profile page
    
    Returns:
        Dict with profile data (including "type" key), or None if fetch/parse failed
    """
    try:
        data = parse.extract_page_data(session, full_url)
        return data
    except Exception as e:
        # Log the error but don't crash. One bad profile shouldn't stop the crawl.
        print(f"  ⚠ Failed to process {full_url}: {type(e).__name__}")
        return None


def crawl(url: str):
    """
    Main crawler function with parallel profile processing.
    
    - Creates a single session for all HTTP requests (reused across threads)
    - Finds the last page with results (sequential)
    - For each results page:
      - Fetches profile links sequentially (to respect server)
      - Spawns threads to fetch/parse profiles in parallel
      - Collects results in main thread and writes to disk (thread-safe)
    """
    
    # Clear previous data files before starting
    utils.clear_data_files(INSTITUTION_PATH, PROVIDER_PATH)
    
    # Create a shared session for all HTTP requests (created once, reused everywhere)
    session = make_session()
    
    prepped_url = f'{url}?zoekterm= &p='
    page_count = 1
    
    # Find the last page number that has results
    start = time.time()
    final_page = utils.find_last_good_page(session, prepped_url)
    end = time.time()
    print(f'Found last page: {final_page} (took {end-start:.2f}s)\n')
    
    # Iterate through all results pages (sequentially, to be respectful)
    while page_count <= final_page:
        print(f"\n=== Processing results page {page_count}/{final_page} ===")
        
        # Step 1: Fetch all profile links on this results page (SEQUENTIAL - respects server)
        page_list = fetch.fetch_results_data(session, f'{prepped_url}{page_count}')
        print(f"Found {len(page_list)} profiles on this page")
        
        # Step 2: Spawn threads to fetch and parse profile pages in parallel
        # We use ThreadPoolExecutor for I/O-bound work (network requests)
        profiles_processed = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Convert relative hrefs to full URLs and submit tasks
            futures = {}
            for href in page_list:
                full_url = f'{BASE_DOMAIN}{href}'
                future = executor.submit(_process_profile, session, full_url)
                futures[future] = full_url
            
            # Process results as they complete (not in submission order)
            # as_completed() returns futures as soon as they finish, which is more
            # responsive than waiting for all to finish - allows us to start writing
            # results sooner
            for future in as_completed(futures):
                data = future.result()
                
                if data is None:
                    # Skip failed profiles (exception was logged in _process_profile)
                    continue
                
                # IMPORTANT: File writes happen in main thread only, not in worker threads.
                # This ensures thread-safe JSONL writes without file corruption.
                if data["type"] == "provider":
                    print(f"  ✓ Provider: {data.get('name', 'Unknown')}")
                    storage.write_jsonl(PROVIDER_PATH, data)
                else:
                    print(f"  ✓ Institution: {data.get('name', 'Unknown')}")
                    storage.write_jsonl(INSTITUTION_PATH, data)
                
                profiles_processed += 1
        
        print(f"Completed page {page_count}: {profiles_processed} profiles saved")
        page_count += 1


if __name__ == "__main__":
    crawl("https://www.zorgkaartnederland.nl/")