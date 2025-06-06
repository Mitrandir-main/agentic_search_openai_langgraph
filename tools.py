import requests
from langchain.tools import tool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
import time
import logging

load_dotenv()

# API Configuration
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
GOOGLE_CSE_API_KEY = os.getenv('GOOGLE_CSE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool("google_cse_search", return_direct=False)
def google_cse_search(query: str, site_search: str = None, country: str = "bg", language: str = "lang_bg", num_results: int = 8) -> str:
    """
    Optimized Google Custom Search Engine with Bulgarian legal focus.
    Uses performance optimizations from Google CSE best practices.
    
    Args:
        query: Search query
        country: Country code for geolocation (default: 'bg' for Bulgaria)
        language: Language restriction (default: 'lang_bg' for Bulgarian)
        num_results: Number of results to return (1-10)
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("Google CSE API key or Search Engine ID not configured")
        return internet_search_DDGO(query)
    
    try:
        # Build the API URL
        base_url = "https://www.googleapis.com/customsearch/v1"
        
        # Enhanced query for Bulgarian legal content
        enhanced_query = query
        if any(keyword in query.lower() for keyword in ['закон', 'право', 'обезщетение', 'наказание', 'съд']):
            enhanced_query = f"{query} български"  # Add Bulgarian context for legal terms
        
        params = {
            'key': GOOGLE_CSE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': enhanced_query,
            'num': min(num_results, 10),  # Max 10 results per request
            'gl': country,  # Country targeting
            'lr': language,  # Language restriction
            'safe': 'off',  # Disable SafeSearch for legal content
            'filter': '1',   # Enable duplicate content filtering
            # Performance optimization: only request fields we need
            'fields': 'items(title,link,snippet),searchInformation(totalResults)'
        }
        
        # Add site-specific search if specified
        if site_search:
            # Try both siteSearch parameter and site: operator in query
            params['siteSearch'] = site_search
            params['siteSearchFilter'] = 'i'  # Include results from this site
            # Also add site: operator to the query for better coverage
            enhanced_query = f"site:{site_search} {enhanced_query}"
            params['q'] = enhanced_query
            logger.info(f"Searching within domain: {site_search} with enhanced query: {enhanced_query}")
        
        logger.info(f"Google CSE search: {enhanced_query} (country: {country}, lang: {language})")
        
        # Performance optimization: enable gzip compression
        headers = {
            'Accept-Encoding': 'gzip',
            'User-Agent': 'Bulgarian Legal Research System (gzip)',
            'Accept': 'application/json'
        }
        
        # Make the API request with optimizations
        response = requests.get(base_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # Check for API errors
        if 'error' in data:
            error_msg = data['error'].get('message', 'Unknown API error')
            logger.error(f"Google CSE API error: {error_msg}")
            return internet_search_DDGO(query)
        
        # Process search results
        results = []
        items = data.get('items', [])
        total_results = data.get('searchInformation', {}).get('totalResults', 0)
        
        if not items:
            logger.warning(f"No results from Google CSE (total available: {total_results})")
            return []  # Return empty list instead of falling back to DuckDuckGo
        
        for item in items:
            result = {
                'title': item.get('title', 'No Title'),
                'href': item.get('link', 'No URL'),
                'body': item.get('snippet', 'No Description'),
                'source_domain': f"Google CSE - {site_search if site_search else 'Web Search'}"
            }
            results.append(result)
        
        logger.info(f"Google CSE returned {len(results)} results (total available: {total_results})")
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Google CSE API request error: {e}")
        return []  # Return empty list instead of falling back
    except Exception as e:
        logger.error(f"Google CSE processing error: {e}")
        return []  # Return empty list instead of falling back

@tool("google_domain_search", return_direct=False)
def google_domain_search(query: str, domains: list = None) -> str:
    """
    Intelligent multi-domain search for Bulgarian legal content with optimization.
    
    Args:
        query: Search query
        domains: List of domains to search (default: Bulgarian legal domains)
    """
    if not domains:
        # Bulgarian legal domains with verified Google CSE indexing
        domains = [
            'ciela.net',    # Bulgarian legal information (19,300+ pages)
            'apis.bg',      # Bulgarian legal information (4,190+ pages)
            'lakorda.com'   # Legal news portal (11+ pages)
        ]
    
    all_results = []
    successful_searches = 0
    
    for i, domain in enumerate(domains):
        try:
            logger.info(f"Searching domain {i+1}/{len(domains)}: {domain}")
            
            # Adjust results per domain based on domain priority
            results_per_domain = 5 if i < 3 else 3  # More results from top domains
            
            domain_results = google_cse_search.invoke({
                "query": query,
                "site_search": domain,
                "country": "bg",
                "language": "lang_bg",
                "num_results": results_per_domain
            })
            
            if isinstance(domain_results, list) and domain_results:
                # Add domain identifier and priority to results
                for result in domain_results:
                    result['source_domain'] = f"Domain: {domain} (Priority: {i+1})"
                    result['domain_priority'] = i + 1
                all_results.extend(domain_results)
                successful_searches += 1
                
                logger.info(f"Found {len(domain_results)} results from {domain}")
            
            # Intelligent rate limiting - faster for high-priority domains
            if i < 3:  # Top priority domains
                time.sleep(0.3)
            else:
                time.sleep(0.5)
            
            # Early termination if we have enough results from top domains
            if successful_searches >= 3 and len(all_results) >= 15:
                logger.info(f"Early termination: {len(all_results)} results from {successful_searches} domains")
                break
                
        except Exception as e:
            logger.error(f"Error searching domain {domain}: {e}")
            continue
    
    if not all_results:
        logger.warning("No results from domain search, trying without site restriction")
        # Try a general search with domain terms included in query
        domain_terms = " OR ".join([f"site:{domain}" for domain in domains[:3]])  # Top 3 domains
        general_query = f"{query} ({domain_terms})"
        
        general_results = google_cse_search.invoke({
            "query": general_query,
            "country": "bg", 
            "language": "lang_bg",
            "num_results": 10
        })
        
        if isinstance(general_results, list) and general_results:
            for result in general_results:
                result['source_domain'] = "Google CSE - Multi-domain search"
                result['domain_priority'] = 999
            return general_results
        
        # If still no results, return empty list instead of falling back
        logger.error("No results found even with general domain search")
        return []
    
    # Sort results by domain priority and limit total results
    all_results.sort(key=lambda x: x.get('domain_priority', 999))
    
    logger.info(f"Domain search completed: {len(all_results)} total results from {successful_searches} domains")
    return all_results[:20]  # Return top 20 results across all domains

@tool("internet_search_DDGO", return_direct=False)
def internet_search_DDGO(query: str) -> str:
    """Enhanced DuckDuckGo search with better error handling and Bulgarian language targeting."""
    
    # Check if query is about Bulgaria or should prioritize Bulgarian sources
    bulgarian_keywords = ["bulgaria", "bulgarian", "българия", "български", "sofia", "софия", "закон", "право"]
    is_bulgarian_related = any(keyword.lower() in query.lower() for keyword in bulgarian_keywords)
    
    enhanced_query = query
    if is_bulgarian_related:
        enhanced_query += " site:.bg OR language:bg"
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(
                    enhanced_query, 
                    max_results=8, 
                    region='bg-bg' if is_bulgarian_related else None,
                    timelimit='m'  # Recent results
                )]
                
                if results:
                    logger.info(f"DuckDuckGo returned {len(results)} results")
                    return results
                
        except Exception as e:
            logger.warning(f"DuckDuckGo attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
            continue
    
    # Final fallback with basic query
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
            if results:
                return results
    except Exception as e:
        logger.error(f"DuckDuckGo final fallback failed: {e}")
    
    return "No results found from DuckDuckGo search."

@tool("bulgarian_search", return_direct=False)
def bulgarian_search(query: str) -> str:
    """Specialized search for Bulgarian websites and Bulgarian language content using Google CSE."""
    
    logger.info(f"Bulgarian search for: {query}")
    
    # Try Google CSE first for Bulgarian content
    try:
        google_results = google_cse_search(
            query=query,
            country="bg",
            language="lang_bg",
            num_results=8
        )
        
        if isinstance(google_results, list) and google_results:
            logger.info(f"Bulgarian search via Google CSE: {len(google_results)} results")
            return google_results
            
    except Exception as e:
        logger.error(f"Google CSE Bulgarian search failed: {e}")
    
    # Fallback to DuckDuckGo with Bulgarian targeting
    bulgarian_query = f"{query} site:.bg OR (Bulgarian OR България OR български)"
    
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(bulgarian_query, max_results=10, region='bg-bg')]
            
            if results:
                logger.info(f"Bulgarian search via DuckDuckGo: {len(results)} results")
                return results
            
    except Exception as e:
        logger.error(f"DuckDuckGo Bulgarian search failed: {e}")
    
    return "No Bulgarian results found."

@tool("current_events_search", return_direct=False)  
def current_events_search(query: str) -> str:
    """Search for current events and recent news using Google CSE and DuckDuckGo."""
    
    current_year = datetime.now().year
    
    # Try Google CSE first with temporal keywords
    try:
        temporal_query = f"{query} новини актуално {current_year}"
        google_results = google_cse_search(
            query=temporal_query,
            country="bg",
            num_results=8
        )
        
        if isinstance(google_results, list) and google_results:
            # Filter results for current content
            current_results = []
            for result in google_results:
                content = str(result)
                if str(current_year) in content or "2025" in content or "актуално" in content:
                    current_results.append(result)
            
            if current_results:
                logger.info(f"Current events via Google CSE: {len(current_results)} results")
                return current_results
                
    except Exception as e:
        logger.error(f"Google CSE current events search failed: {e}")
    
    # Fallback to DuckDuckGo
    temporal_query = f"{query} {current_year} OR recent OR latest OR актуално OR новини"
    
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(temporal_query, max_results=8, timelimit='d')]
            
            if results:
                # Filter out old results
                current_results = []
                for result in results:
                    if str(current_year) in str(result) or "2025" in str(result):
                        current_results.append(result)
                        
                logger.info(f"Current events via DuckDuckGo: {len(current_results)} results")
                return current_results if current_results else results
                
    except Exception as e:
        logger.error(f"DuckDuckGo current events search failed: {e}")
    
    return []

@tool("process_content", return_direct=False)
def process_content(url: str) -> str:
    """Processes content from a webpage with improved error handling and content extraction."""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'bg,en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length
        result = text[:4000] + "..." if len(text) > 4000 else text
        logger.info(f"Processed content from {url}: {len(result)} characters")
        return result
        
    except Exception as e:
        error_msg = f"Error processing URL {url}: {str(e)}"
        logger.error(error_msg)
        return error_msg

@tool("internet_search", return_direct=False)
def internet_search(query: str) -> str:
    """Primary search function that tries Google CSE first, then falls back to other providers."""
    
    logger.info(f"Primary search for: {query}")
    
    # Try Google CSE first
    try:
        google_results = google_cse_search(query)
        if isinstance(google_results, list) and google_results:
            return google_results
    except Exception as e:
        logger.warning(f"Google CSE primary search failed: {e}")
    
    # Fallback to Tavily if available
    if TAVILY_API_KEY:
        try:
            search_tool = TavilySearchResults(api_key=TAVILY_API_KEY, max_results=5)
            results = search_tool.invoke(query)

            if isinstance(results, list) and all(isinstance(result, dict) for result in results):
                formatted_results = ""
                references = []
                for i, result in enumerate(results):
                    title = result.get('title', 'No Title')
                    url = result.get('url', 'No URL')
                    snippet = result.get('snippet', 'No Snippet')
                    formatted_results += f"{i+1}. {title}\n{snippet} [^{i+1}]\n\n"
                    references.append(f"[^{i+1}]: [{title}]({url})")

                references_section = "\n**References:**\n" + "\n".join(references)
                return formatted_results + references_section
                
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
    
    # Final fallback to DuckDuckGo
    return internet_search_DDGO(query)

def get_tools():
    """Return the list of available search tools with Google CSE as primary."""
    return [
        google_cse_search,
        google_domain_search, 
        internet_search,
        internet_search_DDGO,
        bulgarian_search,
        current_events_search,
        process_content
    ]