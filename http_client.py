import requests
import random
import time


def make_session() -> requests.Session:
    """
    Create and return a new requests.Session with a proper User-Agent header.
    This ensures the server recognizes us as a real browser, not a bot.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session


def get_with_retries(session: requests.Session, url: str, *, 
                     timeout=(5, 30), retries=4) -> requests.Response:
    """
    Fetch a URL using the provided session with automatic retries on failure.
    
    Args:
        session: requests.Session object to use for the request
        url: URL to fetch
        timeout: tuple of (connect_timeout, read_timeout) in seconds
        retries: number of retry attempts before giving up
    
    Returns:
        requests.Response object
    
    Raises:
        requests.exceptions.RequestException: if all retries fail
    
    The function retries on:
      - Timeout errors
      - Connection errors
      - ChunkedEncodingError (mid-response connection loss)
    
    It uses exponential backoff with random jitter to avoid hammering the server:
      wait_time = (2 ^ attempt) + random_value
    """
    attempt = 0
    
    while attempt < retries:
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
            
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ChunkedEncodingError) as e:
            attempt += 1
            
            if attempt >= retries:
                # Out of retries, re-raise the exception
                raise
            
            # Calculate exponential backoff with jitter
            wait_time = (2 ** attempt) + random.random()
            print(f"⚠ Request failed (attempt {attempt}/{retries}): {type(e).__name__}")
            print(f"  Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
