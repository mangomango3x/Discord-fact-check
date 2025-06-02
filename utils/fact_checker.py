import asyncio
import aiohttp
import logging
from urllib.parse import quote
import json

from utils.web_scraper import get_website_text_content
from config import FACT_CHECK_SOURCES

logger = logging.getLogger(__name__)

class FactChecker:
    """Class for checking facts against reliable sources"""
    
    def __init__(self):
        self.sources = FACT_CHECK_SOURCES
        self.session = None
    
    async def check_statement(self, statement):
        """
        Check a statement against multiple reliable fact-checking sources
        
        Args:
            statement (str): The statement to fact-check
            
        Returns:
            dict: Results from various fact-checking sources
        """
        try:
            async with aiohttp.ClientSession() as session:
                self.session = session
                
                # Create tasks for checking each source
                tasks = []
                for source_name, base_url in self.sources.items():
                    task = self.check_source(source_name, base_url, statement)
                    tasks.append(task)
                
                # Wait for all checks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                fact_check_results = {}
                for i, result in enumerate(results):
                    source_name = list(self.sources.keys())[i]
                    if isinstance(result, Exception):
                        logger.error(f"Error checking {source_name}: {result}")
                        fact_check_results[source_name] = {
                            "error": str(result),
                            "relevant": False
                        }
                    else:
                        fact_check_results[source_name] = result
                
                return fact_check_results
                
        except Exception as e:
            logger.error(f"Error in fact checking: {e}")
            return {}
    
    async def check_source(self, source_name, base_url, statement):
        """
        Check a statement against a specific source
        
        Args:
            source_name (str): Name of the source
            base_url (str): Base URL of the source
            statement (str): Statement to check
            
        Returns:
            dict: Results from the source
        """
        try:
            # Create search URL based on source
            search_url = self.create_search_url(source_name, base_url, statement)
            
            if not search_url:
                return {"relevant": False, "reason": "Search not supported for this source"}
            
            # Get search results
            search_results = await self.search_source(search_url)
            
            if not search_results:
                return {"relevant": False, "reason": "No search results found"}
            
            # Analyze relevance and extract information
            analysis = await self.analyze_search_results(statement, search_results, source_name)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error checking source {source_name}: {e}")
            return {"error": str(e), "relevant": False}
    
    def create_search_url(self, source_name, base_url, statement):
        """Create search URL for the given source"""
        # Extract key terms from statement for search
        search_terms = self.extract_search_terms(statement)
        
        if source_name == "snopes":
            return f"https://www.snopes.com/?s={quote(search_terms)}"
        elif source_name == "factcheck":
            return f"https://www.factcheck.org/?s={quote(search_terms)}"
        elif source_name == "politifact":
            return f"https://www.politifact.com/search/?q={quote(search_terms)}"
        elif source_name == "reuters_fact_check":
            return f"https://www.reuters.com/site-search/?query={quote(search_terms)}"
        elif source_name == "ap_fact_check":
            return f"https://apnews.com/hub/ap-fact-check"
        
        return None
    
    def extract_search_terms(self, statement):
        """Extract key search terms from a statement"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        words = statement.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return ' '.join(keywords[:5])  # Limit to first 5 keywords
    
    async def search_source(self, url):
        """
        Search a fact-checking source
        
        Args:
            url (str): Search URL
            
        Returns:
            str: Search results content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    # Use web scraper to extract clean text
                    content = get_website_text_content(url)
                    return content
                else:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.warning(f"Timeout accessing URL: {url}")
            return None
        except Exception as e:
            logger.error(f"Error searching source: {e}")
            return None
    
    async def analyze_search_results(self, statement, search_results, source_name):
        """
        Analyze search results for relevance to the statement
        
        Args:
            statement (str): Original statement
            search_results (str): Search results content
            source_name (str): Name of the source
            
        Returns:
            dict: Analysis results
        """
        try:
            # Simple relevance check - look for key terms
            statement_lower = statement.lower()
            results_lower = search_results.lower() if search_results else ""
            
            # Extract key terms from statement
            key_terms = self.extract_search_terms(statement)
            term_list = key_terms.split()
            
            # Check how many terms appear in results
            matches = sum(1 for term in term_list if term in results_lower)
            relevance_score = matches / len(term_list) if term_list else 0
            
            if relevance_score < 0.3:  # Less than 30% of terms found
                return {
                    "relevant": False,
                    "reason": "Low relevance to search terms",
                    "relevance_score": relevance_score
                }
            
            # Extract summary from results
            summary = self.extract_summary(search_results, statement)
            
            # Determine if it supports or contradicts the statement
            supports_truth = self.analyze_support(statement, search_results)
            
            return {
                "relevant": True,
                "summary": summary,
                "supports_truth": supports_truth,
                "relevance_score": relevance_score,
                "source": source_name
            }
            
        except Exception as e:
            logger.error(f"Error analyzing search results: {e}")
            return {"relevant": False, "error": str(e)}
    
    def extract_summary(self, content, statement, max_length=300):
        """Extract a relevant summary from content"""
        if not content:
            return "No content available"
        
        # Find sentences that contain key terms from the statement
        sentences = content.split('.')
        key_terms = self.extract_search_terms(statement).split()
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(term in sentence_lower for term in key_terms):
                relevant_sentences.append(sentence.strip())
                if len(' '.join(relevant_sentences)) > max_length:
                    break
        
        if relevant_sentences:
            summary = '. '.join(relevant_sentences)
            return summary[:max_length] + "..." if len(summary) > max_length else summary
        else:
            # Fallback to first part of content
            return content[:max_length] + "..." if len(content) > max_length else content
    
    def analyze_support(self, statement, content):
        """
        Analyze whether the content supports or contradicts the statement
        
        Args:
            statement (str): Original statement
            content (str): Content to analyze
            
        Returns:
            bool: True if content supports the statement, False if it contradicts
        """
        if not content:
            return None
        
        # Simple keyword-based analysis
        positive_indicators = ['true', 'correct', 'accurate', 'confirmed', 'verified', 'supported by evidence']
        negative_indicators = ['false', 'incorrect', 'inaccurate', 'debunked', 'myth', 'misinformation', 'conspiracy']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for indicator in positive_indicators if indicator in content_lower)
        negative_count = sum(1 for indicator in negative_indicators if indicator in content_lower)
        
        if negative_count > positive_count:
            return False
        elif positive_count > negative_count:
            return True
        else:
            return None  # Neutral or unclear
