import trafilatura
import logging

logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.

    Some common website to crawl information from:
    MLB scores: https://www.mlb.com/scores/YYYY-MM-DD
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return ""
        
        text = trafilatura.extract(downloaded)
        if not text:
            logger.warning(f"Failed to extract text from {url}")
            return ""
        
        return text
    
    except Exception as e:
        logger.error(f"Error scraping website {url}: {e}")
        return ""

def extract_article_content(url: str, include_metadata: bool = False) -> dict:
    """
    Extract article content with optional metadata
    
    Args:
        url (str): URL to scrape
        include_metadata (bool): Whether to include metadata
        
    Returns:
        dict: Extracted content and metadata
    """
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"content": "", "error": "Failed to download"}
        
        # Extract content
        content = trafilatura.extract(downloaded)
        
        result = {"content": content or ""}
        
        if include_metadata:
            # Extract metadata
            metadata = trafilatura.extract_metadata(downloaded)
            if metadata:
                result.update({
                    "title": metadata.title,
                    "author": metadata.author,
                    "date": metadata.date,
                    "description": metadata.description,
                    "sitename": metadata.sitename,
                    "url": metadata.url
                })
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting article content from {url}: {e}")
        return {"content": "", "error": str(e)}

def scrape_multiple_urls(urls: list, max_concurrent: int = 5) -> dict:
    """
    Scrape multiple URLs with basic rate limiting
    
    Args:
        urls (list): List of URLs to scrape
        max_concurrent (int): Maximum concurrent requests
        
    Returns:
        dict: Results mapped by URL
    """
    import time
    
    results = {}
    
    for i, url in enumerate(urls):
        try:
            if i > 0 and i % max_concurrent == 0:
                # Simple rate limiting - wait between batches
                time.sleep(1)
            
            content = get_website_text_content(url)
            results[url] = {
                "content": content,
                "success": bool(content),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            results[url] = {
                "content": "",
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    return results

def clean_text_content(text: str, max_length: int = 5000) -> str:
    """
    Clean and truncate text content for processing
    
    Args:
        text (str): Raw text content
        max_length (int): Maximum length to return
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Basic cleaning
    text = text.strip()
    
    # Remove excessive whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text
