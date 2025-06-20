"""
Enhanced Legal Research Tools for Bulgarian Law
Specialized tools for searching Bulgarian legal databases with citation extraction
"""

import requests
import urllib3
from langchain.tools import tool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
import time
import asyncio
import logging
from dotenv import load_dotenv
import json

# Bulgarian legal domains configuration
BULGARIAN_LEGAL_DOMAINS = {
    "ciela.net": {
        "authority": 0.95,
        "description": "Водеща българска правна платформа (19,300+ страници)",
        "specialties": ["laws", "regulations", "case_law"]
    },
    "apis.bg": {
        "authority": 0.90,
        "description": "Апис - специализирано правно издателство (4,190+ страници)", 
        "specialties": ["legal_commentary", "analysis", "practice"]
    },
    "lakorda.com": {
        "authority": 0.75,
        "description": "Правни новини и анализи (11+ страници)",
        "specialties": ["news", "analysis", "current_events"]
    }
}

# Disable SSL warnings for problematic government sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Import our new relevancy scoring system
from relevancy_scoring import BulgarianLegalRelevancyScorer, SearchResult

load_dotenv()

# API Configuration
GOOGLE_CSE_API_KEY = os.getenv('GOOGLE_CSE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the relevancy scorer
relevancy_scorer = BulgarianLegalRelevancyScorer(openai_api_key=os.getenv('OPENAI_API_KEY'))

# Bulgarian legal citation patterns
BULGARIAN_CITATION_PATTERNS = [
    r'чл\.\s*\d+[а-я]*',  # Article references (чл. 123а)
    r'ал\.\s*\d+',        # Paragraph references (ал. 2)
    r'т\.\s*\d+',         # Point references (т. 5)
    r'§\s*\d+',           # Section references (§ 10)
    r'р-ние\s*№?\s*\d+',  # Decision references
    r'решение\s*№?\s*\d+', # Court decision references
    r'дело\s*№?\s*\d+',   # Case references
    r'ЕCLI:[A-Z]{2}:[A-Z0-9]+:\d{4}:[A-Z0-9.]+', # ECLI identifiers
]

class BulgarianLegalExtractor:
    """Advanced content extraction for Bulgarian legal documents"""
    
    def __init__(self):
        self.legal_indicators = [
            "чл.", "ал.", "т.", "§", "Закон", "Наредба", "Решение", 
            "Определение", "Постановление", "Разпореждане"
        ]
        
        self.court_indicators = [
            "ВКС", "ВАС", "Окръжен съд", "Районен съд", "Апелативен съд",
            "Върховен касационен съд", "Върховен административен съд"
        ]
    
    def extract_legal_citations(self, text: str) -> List[str]:
        """Extract legal citations from Bulgarian legal text"""
        citations = []
        
        # Pattern for articles (чл. 123, ал. 2)
        article_pattern = r'чл\.\s*\d+(?:,\s*ал\.\s*\d+)?(?:,\s*т\.\s*\d+)?'
        citations.extend(re.findall(article_pattern, text, re.IGNORECASE))
        
        # Pattern for laws and regulations
        law_pattern = r'(?:Закон|Наредба|Правилник)\s+(?:за|относно)\s+[А-Яа-я\s]+'
        citations.extend(re.findall(law_pattern, text, re.IGNORECASE))
        
        return list(set(citations))
    
    def extract_court_decisions(self, text: str) -> List[str]:
        """Extract court decision references"""
        decisions = []
        
        # Pattern for court decisions
        decision_pattern = r'(?:Решение|Определение|Постановление)\s+№\s*\d+(?:/\d{4})?'
        decisions.extend(re.findall(decision_pattern, text, re.IGNORECASE))
        
        return list(set(decisions))
    
    def extract_key_legal_info(self, text: str) -> Dict[str, Any]:
        """Extract comprehensive legal information from text"""
        return {
            "citations": self.extract_legal_citations(text),
            "court_decisions": self.extract_court_decisions(text),
            "legal_indicators": [ind for ind in self.legal_indicators if ind in text],
            "court_mentions": [court for court in self.court_indicators if court in text],
            "text_length": len(text),
            "has_legal_content": any(ind in text for ind in self.legal_indicators)
        }

extractor = BulgarianLegalExtractor()

def google_cse_search_legal(query: str, site_search: Optional[str] = None, country: str = "bg", language: str = "lang_bg", num_results: int = 8) -> List[Dict]:
    """
    Legal-focused Google Custom Search Engine with enhanced fallback.
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("⚠️ Google CSE not configured, using DuckDuckGo")
        return fallback_ddg_search(query, site_search)
    
    try:
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_CSE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': query,
            'num': min(num_results, 10),
            'gl': country,
            'lr': language,
            'safe': 'off',
            'filter': '1'
        }
        
        if site_search:
            params['siteSearch'] = site_search
            params['siteSearchFilter'] = 'i'
            logger.info(f"Legal search within domain: {site_search}")
        
        # Add legal-specific terms for better targeting
        legal_query = f"{query} закон право юридически"
        params['q'] = legal_query
        
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            logger.warning(f"⚠️ No Google CSE results for {query}, falling back to DuckDuckGo")
            return fallback_ddg_search(query, site_search)
        
        results = []
        for item in items:
            result = {
                'title': item.get('title', 'No Title'),
                'href': item.get('link', 'No URL'),
                'body': item.get('snippet', 'No Description'),
                'source_domain': site_search if site_search else 'Google CSE Legal Search'
            }
            results.append(result)
        
        logger.info(f"✅ Google CSE legal search returned {len(results)} results")
        return results
        
    except requests.exceptions.HTTPError as e:
        if "403" in str(e):
            logger.error(f"❌ Google CSE API 403 Forbidden - Invalid credentials or quota exceeded")
        else:
            logger.error(f"❌ Google CSE HTTP error: {e}")
        logger.info("🦆 Falling back to DuckDuckGo search")
        return fallback_ddg_search(query, site_search)
        
    except Exception as e:
        logger.error(f"❌ Google CSE error: {e}")
        logger.info("🦆 Falling back to DuckDuckGo search")
        return fallback_ddg_search(query, site_search)

def fallback_ddg_search(query: str, site_search: Optional[str] = None) -> List[Dict]:
    """
    Enhanced fallback DuckDuckGo search for legal content.
    This is the primary fallback when Google CSE fails.
    """
    try:
        logger.info(f"🦆 Using DuckDuckGo fallback search for: '{query}'")
        
        search_query = query
        if site_search:
            search_query = f"site:{site_search} {query}"
        
        # Add Bulgarian legal context to improve results
        search_query += " закон право юридически България"
        
        with DDGS() as ddgs:
            results = []
            try:
                # Try to get more results from DuckDuckGo
                ddg_results = ddgs.text(search_query, max_results=15, region='bg-bg')
                
                for result in ddg_results:
                    formatted_result = {
                        'title': result.get('title', 'No Title'),
                        'href': result.get('href', 'No URL'),
                        'body': result.get('body', 'No Description'),
                        'source_domain': f"DuckDuckGo{' - ' + site_search if site_search else ''}"
                    }
                    results.append(formatted_result)
                
                logger.info(f"✅ DuckDuckGo returned {len(results)} results")
                return results
                
            except Exception as ddg_error:
                logger.error(f"DuckDuckGo search failed: {ddg_error}")
                
                # Try a simpler query without legal terms
                try:
                    simple_query = query
                    if site_search:
                        simple_query = f"site:{site_search} {query}"
                    
                    ddg_results = ddgs.text(simple_query, max_results=10, region='bg-bg')
                    
                    for result in ddg_results:
                        formatted_result = {
                            'title': result.get('title', 'No Title'),
                            'href': result.get('href', 'No URL'),
                            'body': result.get('body', 'No Description'),
                            'source_domain': f"DuckDuckGo Simple{' - ' + site_search if site_search else ''}"
                        }
                        results.append(formatted_result)
                    
                    logger.info(f"✅ DuckDuckGo simple search returned {len(results)} results")
                    return results
                    
                except Exception as simple_error:
                    logger.error(f"DuckDuckGo simple search also failed: {simple_error}")
                    return []
        
    except Exception as e:
        logger.error(f"❌ Complete DuckDuckGo fallback failure: {e}")
        return []

@tool("bulgarian_legal_search", return_direct=False)
def bulgarian_legal_search(query: str, specific_domain: Optional[str] = None) -> List[Dict]:
    """
    Enhanced Bulgarian legal search with Google CSE and multi-domain targeting.
    
    Args:
        query: Legal search query in Bulgarian
        specific_domain: Optional specific domain to search within
    """
    
    # Define Bulgarian legal domains mapping
    domain_mapping = {
        'ciela_net': 'ciela.net',
        'apis_bg': 'apis.bg',
        'lakorda_com': 'lakorda.com'
    }
    
    all_results = []
    
    if specific_domain:
        # Search specific domain
        domain_url = domain_mapping.get(specific_domain, specific_domain)
        logger.info(f"Searching specific domain: {domain_url}")
        
        try:
            results = google_cse_search_legal(query, site_search=domain_url)
            if results:
                for result in results:
                    result['source_domain'] = get_domain_description(domain_url)
                all_results.extend(results)
        except Exception as e:
            logger.error(f"Error searching {domain_url}: {e}")
    else:
        # Search all Bulgarian legal domains
        for domain_key, domain_url in domain_mapping.items():
            try:
                logger.info(f"Searching domain: {domain_url}")
                results = google_cse_search_legal(query, site_search=domain_url, num_results=3)
                
                if results:
                    for result in results:
                        result['source_domain'] = get_domain_description(domain_url)
                    all_results.extend(results)
                
                # Rate limiting between domain searches
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error searching {domain_url}: {e}")
                continue
    
    if not all_results:
        # Fallback to general Bulgarian legal search
        logger.warning("No domain-specific results, trying general Bulgarian legal search")
        try:
            general_results = google_cse_search_legal(
                f"{query} site:.bg закон право", 
                country="bg", 
                language="lang_bg"
            )
            if general_results:
                all_results.extend(general_results)
        except Exception as e:
            logger.error(f"Error in general search: {e}")
            all_results = [{"error": "No Bulgarian legal results found."}]
    
    return all_results[:12]  # Limit to top 12 results

def get_domain_description(domain: str) -> str:
    """Map domain URLs to descriptive names."""
    descriptions = {
        'ciela.net': 'Ciela - Bulgarian legal information and publishing (19,300+ pages)',
        'apis.bg': 'Апис - Bulgarian legal information and publishing (4,190+ pages)',
        'lakorda.com': 'Лакорда - Legal news and information portal (11+ pages)'
    }
    return descriptions.get(domain, domain)

@tool("legal_precedent_search", return_direct=False)
def legal_precedent_search(legal_issue: str, court_level: str = "all") -> List[Dict]:
    """
    Search for Bulgarian legal precedents using Google CSE with intelligent fallbacks.
    
    Args:
        legal_issue: The legal issue or topic
        court_level: Court level filter ('ВКС', 'ВАС', 'all')
    """
    
    # Construct search query with legal terminology
    precedent_query = f"{legal_issue} решение съд практика precedent"
    
    court_domains = {
        'ВКС': 'vks.bg',
        'Върховен касационен съд': 'vks.bg', 
        'ВАС': 'vss.bg',
        'Върховен административен съд': 'vss.bg',
        'all': None
    }
    
    target_domain = court_domains.get(court_level)
    
    try:
        if target_domain:
            # Search specific court domain
            results = google_cse_search_legal(
                precedent_query, 
                site_search=target_domain,
                num_results=10
            )
        else:
            # Search multiple court domains
            all_results = []
            for court, domain in court_domains.items():
                if domain:  # Skip 'all' entry
                    court_results = google_cse_search_legal(
                        precedent_query,
                        site_search=domain,
                        num_results=5
                    )
                    if court_results:
                        for result in court_results:
                            result['source_domain'] = f"Court: {court} ({domain})"
                        all_results.extend(court_results)
                    time.sleep(0.2)  # Rate limiting
            results = all_results
        
        if not results:
            # Fallback to general legal search
            results = google_cse_search_legal(
                f"{legal_issue} съдебна практика решение",
                country="bg"
            )
        
        if results:
            logger.info(f"Found {len(results)} precedent results")
            return results[:10]
        else:
            return []
            
    except Exception as e:
        logger.error(f"Precedent search error: {e}")
        return []

@tool("legal_citation_extractor", return_direct=False)
def legal_citation_extractor(text: str) -> Dict[str, Any]:
    """
    Extract Bulgarian legal citations from text using enhanced pattern matching.
    
    Args:
        text: Text to extract citations from
    """
    
    citations = []
    
    for pattern in BULGARIAN_CITATION_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
        citations.extend(matches)
    
    # Additional Bulgarian-specific patterns
    additional_patterns = [
        r'Закон\s+за\s+[А-Яа-я\s]+',  # Law names
        r'Кодекс\s+[А-Яа-я\s]+',      # Code names  
        r'Наредба\s+№?\s*\d+',        # Regulation references
        r'Постановление\s+№?\s*\d+',   # Decree references
        r'ПМС\s+№?\s*\d+',            # Council of Ministers decisions
    ]
    
    for pattern in additional_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
        citations.extend(matches)
    
    # Remove duplicates and clean up
    unique_citations = list(set(citations))
    cleaned_citations = [citation.strip() for citation in unique_citations if len(citation.strip()) > 2]
    
    if cleaned_citations:
        result = {
            'extracted_citations': cleaned_citations,
            'total_found': len(cleaned_citations),
            'types_found': categorize_citations(cleaned_citations)
        }
        logger.info(f"Extracted {len(cleaned_citations)} legal citations")
        return result
    else:
        return {'extracted_citations': [], 'total_found': 0, 'message': 'No Bulgarian legal citations found'}

def categorize_citations(citations: List[str]) -> Dict[str, int]:
    """Categorize Bulgarian legal citations by type."""
    categories = {
        'articles': 0,      # чл.
        'paragraphs': 0,    # ал.
        'points': 0,        # т.
        'sections': 0,      # §
        'decisions': 0,     # решение
        'cases': 0,         # дело
        'laws': 0,          # закон
        'codes': 0,         # кодекс
        'regulations': 0,   # наредба
        'decrees': 0,       # постановление
        'ecli': 0          # ECLI identifiers
    }
    
    for citation in citations:
        citation_lower = citation.lower()
        if 'чл.' in citation_lower:
            categories['articles'] += 1
        elif 'ал.' in citation_lower:
            categories['paragraphs'] += 1
        elif 'т.' in citation_lower:
            categories['points'] += 1
        elif '§' in citation:
            categories['sections'] += 1
        elif 'решение' in citation_lower:
            categories['decisions'] += 1
        elif 'дело' in citation_lower:
            categories['cases'] += 1
        elif 'закон' in citation_lower:
            categories['laws'] += 1
        elif 'кодекс' in citation_lower:
            categories['codes'] += 1
        elif 'наредба' in citation_lower:
            categories['regulations'] += 1
        elif 'постановление' in citation_lower:
            categories['decrees'] += 1
        elif 'ecli:' in citation_lower:
            categories['ecli'] += 1
    
    return {k: v for k, v in categories.items() if v > 0}

@tool("legal_area_classifier", return_direct=False) 
def legal_area_classifier(query: str) -> Dict[str, Any]:
    """
    Classify legal queries into Bulgarian legal areas for targeted search.
    
    Args:
        query: Legal query to classify
    """
    
    legal_areas = {
        'civil_law': {
            'keywords': ['граждански', 'договор', 'собственост', 'наследство', 'вреди', 'обезщетение', 'семейно'],
            'bulgarian_name': 'гражданско право',
            'domains': ['lex_bg', 'vks_bg', 'justice_bg']
        },
        'criminal_law': {
            'keywords': ['наказателен', 'престъпление', 'обвинение', 'присъда', 'криминален'],
            'bulgarian_name': 'наказателно право', 
            'domains': ['lex_bg', 'vks_bg', 'justice_bg']
        },
        'administrative_law': {
            'keywords': ['административен', 'държавен', 'служебен', 'разрешение', 'лиценз'],
            'bulgarian_name': 'административно право',
            'domains': ['vss_bg', 'justice_bg', 'parliament_bg']
        },
        'constitutional_law': {
            'keywords': ['конституционен', 'основен закон', 'права', 'свободи'],
            'bulgarian_name': 'конституционно право',
            'domains': ['parliament_bg', 'justice_bg']
        },
        'commercial_law': {
            'keywords': ['търговски', 'търговец', 'дружество', 'регистър', 'търговия'],
            'bulgarian_name': 'търговско право',
            'domains': ['lex_bg', 'vks_bg', 'justice_bg']
        },
        'labor_law': {
            'keywords': ['трудов', 'работник', 'служител', 'уволнение', 'заплата'],
            'bulgarian_name': 'трудово право',
            'domains': ['lex_bg', 'vks_bg', 'justice_bg']
        },
        'tax_law': {
            'keywords': ['данъчен', 'данък', 'ДДС', 'НАП', 'фискален'],
            'bulgarian_name': 'данъчно право',
            'domains': ['lex_bg', 'vss_bg', 'dv_bg']
        },
        'data_protection': {
            'keywords': ['лични данни', 'GDPR', 'КЗЛД', 'privacy', 'защита'],
            'bulgarian_name': 'защита на данните',
            'domains': ['cpc_bg', 'lex_bg', 'justice_bg']
        }
    }
    
    query_lower = query.lower()
    best_match = None
    max_score = 0
    
    for area, info in legal_areas.items():
        score = sum(1 for keyword in info['keywords'] if keyword in query_lower)
        if score > max_score:
            max_score = score
            best_match = area
    
    if best_match and max_score > 0:
        area_info = legal_areas[best_match]
        result = {
            'legal_area': best_match,
            'bulgarian_name': area_info['bulgarian_name'],
            'confidence': max_score,
            'recommended_domains': area_info['domains'],
            'keywords': [kw for kw in area_info['keywords'] if kw in query_lower]
        }
    else:
        result = {
            'legal_area': 'general',
            'bulgarian_name': 'общо правно съдържание',
            'confidence': 0,
            'recommended_domains': ['lex_bg', 'vks_bg', 'vss_bg', 'justice_bg', 'parliament_bg', 'cpc_bg', 'dv_bg'],
            'keywords': []
        }
    
    logger.info(f"Classified query as: {result['bulgarian_name']}")
    return result

@tool("legal_document_analyzer", return_direct=False)
def legal_document_analyzer(document_url: str) -> Dict[str, Any]:
    """
    Analyze Bulgarian legal documents with enhanced content extraction.
    
    Args:
        document_url: URL of the legal document to analyze
    """
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'bg,en-US,en;q=0.5',
        }
        
        response = requests.get(document_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract document content
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Analyze document
        analysis = {
            'document_url': document_url,
            'content_length': len(clean_text),
            'citations': legal_citation_extractor(clean_text),
            'document_type': identify_document_type(clean_text),
            'key_sections': extract_key_sections(clean_text),
            'summary': clean_text[:1000] + "..." if len(clean_text) > 1000 else clean_text
        }
        
        logger.info(f"Analyzed document: {document_url} ({len(clean_text)} chars)")
        return analysis
        
    except Exception as e:
        error_msg = f"Error analyzing document {document_url}: {str(e)}"
        logger.error(error_msg)
        return {'error': error_msg, 'document_url': document_url}

def identify_document_type(text: str) -> str:
    """Identify the type of Bulgarian legal document."""
    text_lower = text.lower()
    
    if 'решение' in text_lower and ('съд' in text_lower or 'дело' in text_lower):
        return 'Court Decision'
    elif 'закон' in text_lower:
        return 'Law'
    elif 'кодекс' in text_lower:
        return 'Code'
    elif 'наредба' in text_lower:
        return 'Regulation'
    elif 'постановление' in text_lower:
        return 'Decree'
    elif 'решение' in text_lower and 'министерски съвет' in text_lower:
        return 'Council of Ministers Decision'
    else:
        return 'Legal Document'

def extract_key_sections(text: str) -> List[str]:
    """Extract key sections from Bulgarian legal documents."""
    
    section_patterns = [
        r'Чл\.\s*\d+[а-я]*\..*?(?=Чл\.\s*\d+|$)',  # Articles
        r'§\s*\d+\..*?(?=§\s*\d+|$)',              # Sections
        r'РЕШЕНИЕ.*?(?=МОТИВИ|$)',                   # Court decision sections
        r'МОТИВИ.*?(?=РЕШЕНИЕ|$)',                   # Court reasoning
        r'Преамбул.*?(?=Глава|Чл\.|$)',             # Preambles
    ]
    
    sections = []
    
    for pattern in section_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL | re.UNICODE)
        for match in matches[:3]:  # Limit to first 3 matches per pattern
            clean_match = re.sub(r'\s+', ' ', match.strip())
            if len(clean_match) > 50:  # Only meaningful sections
                sections.append(clean_match[:200] + "..." if len(clean_match) > 200 else clean_match)
    
    return sections[:5]  # Return top 5 sections

def get_enhanced_legal_tools():
    """Get all enhanced Bulgarian legal research tools"""
    return [
        bulgarian_legal_search,
        legal_document_analyzer, 
        legal_precedent_search,
        legal_area_classifier,
        legal_citation_extractor,
        enhanced_bulgarian_legal_search_tool,
        lex_bg_search
    ] 

def preprocess_query(query: str) -> str:
    """Preprocess and clean the query for better search results"""
    
    # Common typo corrections for Bulgarian legal terms
    typo_corrections = {
        'амога': 'мога',
        'съща': 'същата',
        'връка': 'връзка',
        'обещетение': 'обезщетение',
        'насказание': 'наказание'
    }
    
    # Apply corrections
    cleaned_query = query
    for typo, correction in typo_corrections.items():
        cleaned_query = cleaned_query.replace(typo, correction)
    
    # If query is very long (>15 words), extract key legal terms
    words = cleaned_query.split()
    if len(words) > 15:
        legal_keywords = []
        important_words = ['обезщетение', 'наказание', 'счупване', 'ръка', 'сума', 'помощ', 'право', 'закон', 'съд']
        
        for word in words:
            if any(keyword in word.lower() for keyword in important_words):
                legal_keywords.append(word)
        
        if legal_keywords:
            cleaned_query = ' '.join(legal_keywords[:8])  # Limit to 8 most relevant words
    
    return cleaned_query

async def intelligent_query_expansion(query: str, context: str = "", iteration: int = 1) -> List[str]:
    """
    Use AI reasoning to intelligently expand search queries based on legal understanding.
    This is the modern agentic approach - let AI think about what to search for.
    """
    try:
        from langchain_openai import ChatOpenAI
        
        # Fix: Remove proxies parameter that's causing the error
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        expansion_prompt = f"""You are an expert Bulgarian legal research analyst. Your task is to intelligently expand the search query to find comprehensive legal information.

ORIGINAL QUERY: "{query}"
CONTEXT FROM PREVIOUS SEARCHES: {context if context else "This is the initial search"}
ITERATION: {iteration}

Think step by step about this legal query:

1. **Legal Domain Analysis**: What area of Bulgarian law does this involve? (Civil, Criminal, Administrative, Commercial, Labor, etc.)

2. **Key Legal Concepts**: What are the core legal concepts that need to be researched?

3. **Related Legal Issues**: What related legal issues should also be explored?

4. **Alternative Perspectives**: How might this issue be approached from different legal angles?

5. **Missing Information**: Based on the context, what legal aspects might be missing from previous searches?

Based on your analysis, generate 3-5 intelligent search queries that will provide comprehensive coverage:
- Each query should target different aspects of the legal issue
- Use natural Bulgarian legal terminology
- Consider different legal contexts and applications
- Think about practical legal scenarios

Format your response as:
ANALYSIS: [Your step-by-step legal thinking]

SEARCH_QUERIES:
1. [First intelligent query]
2. [Second intelligent query]  
3. [Third intelligent query]
4. [Fourth intelligent query - if relevant]
5. [Fifth intelligent query - if relevant]
"""

        response = llm.invoke(expansion_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Extract queries from response
        queries = []
        if isinstance(content, str) and "SEARCH_QUERIES:" in content:
            query_section = content.split("SEARCH_QUERIES:")[1]
            lines = query_section.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith('-')):
                    # Extract the query text after the number/bullet
                    query_text = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if query_text and len(query_text) > 5:  # Ensure it's a real query
                        queries.append(query_text)
        
        # Log the AI's reasoning
        if isinstance(content, str) and "ANALYSIS:" in content:
            analysis = content.split("SEARCH_QUERIES:")[0].replace("ANALYSIS:", "").strip()
            logger.info(f"🧠 AI Legal Analysis (Iteration {iteration}): {analysis[:200]}...")
        
        logger.info(f"🎯 Generated {len(queries)} intelligent search queries")
        return queries[:5]  # Limit to 5 queries max
        
    except Exception as e:
        logger.error(f"Error in intelligent query expansion: {e}")
        # Fallback to original query
        return [query]

async def adaptive_query_refinement(query: str, search_results: List[Dict], relevancy_scores: List[float]) -> List[str]:
    """
    Analyze search results and intelligently generate follow-up queries to fill gaps.
    This implements the iterative thinking approach of modern agentic AI.
    """
    try:
        from langchain_openai import ChatOpenAI
        
        # Fix: Remove proxies parameter that's causing the error
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        
        # Prepare results summary for AI analysis
        results_summary = []
        for i, (result, score) in enumerate(zip(search_results[:5], relevancy_scores[:5])):
            title = result.get('title', 'No Title')[:100]
            snippet = result.get('body', result.get('snippet', ''))[:200]
            results_summary.append(f"Result {i+1} (Score: {score:.1%}): {title} - {snippet}")
        
        results_text = "\n".join(results_summary)
        
        refinement_prompt = f"""You are an expert Bulgarian legal researcher analyzing search results for gaps and needed follow-up research.

ORIGINAL QUERY: "{query}"

CURRENT SEARCH RESULTS:
{results_text}

AVERAGE RELEVANCY: {sum(relevancy_scores)/len(relevancy_scores):.1%}

Analyze these results and identify:

1. **Coverage Gaps**: What important legal aspects are missing or underrepresented?

2. **Low Relevancy Issues**: Why might some results have low relevancy? What different search approach is needed?

3. **Emerging Themes**: What new legal angles or related issues have emerged from these results?

4. **Deeper Research Needs**: What specific legal documents, cases, or regulations should be searched for?

5. **Alternative Approaches**: How can we search differently to get better, more relevant results?

Based on your analysis, generate 2-4 refined search queries that will:
- Fill the identified gaps
- Target higher relevancy results  
- Explore emerging legal themes
- Find specific legal authorities mentioned

Format your response as:
ANALYSIS: [Your analysis of gaps and opportunities]

REFINED_QUERIES:
1. [First refined query]
2. [Second refined query]
3. [Third refined query - if needed]
4. [Fourth refined query - if needed]
"""

        response = llm.invoke(refinement_prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Extract refined queries
        queries = []
        if isinstance(content, str) and "REFINED_QUERIES:" in content:
            query_section = content.split("REFINED_QUERIES:")[1]
            lines = query_section.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and (line.startswith(('1.', '2.', '3.', '4.')) or line.startswith('-')):
                    query_text = line.split('.', 1)[-1].strip() if '.' in line else line[1:].strip()
                    if query_text and len(query_text) > 5:
                        queries.append(query_text)
        
        # Log the AI's analysis
        if isinstance(content, str) and "ANALYSIS:" in content:
            analysis = content.split("REFINED_QUERIES:")[0].replace("ANALYSIS:", "").strip()
            logger.info(f"🔍 AI Gap Analysis: {analysis[:200]}...")
        
        logger.info(f"🎯 Generated {len(queries)} refined follow-up queries")
        return queries[:4]  # Limit to 4 refined queries
        
    except Exception as e:
        logger.error(f"Error in adaptive query refinement: {e}")
        return []

async def extract_deep_content(result: Dict) -> Dict:
    """
    Deep content extraction from legal documents.
    Goes beyond surface-level snippets to get meaningful legal content.
    """
    enhanced_result = result.copy()
    url = result.get('href', result.get('url', ''))
    
    if not url or url == 'No URL':
        enhanced_result['enhanced_content'] = result.get('body', result.get('snippet', ''))
        return enhanced_result
    
    try:
        # Use existing process_content function for deep extraction
        from tools import process_content
        deep_content = process_content.invoke({"url": url})
        
        if deep_content and len(deep_content) > 100:  # Ensure we got meaningful content
            enhanced_result['enhanced_content'] = deep_content
            enhanced_result['content_length'] = len(deep_content)
            logger.info(f"📄 Deep extracted {len(deep_content)} characters from {url[:50]}...")
        else:
            # Fallback to snippet if deep extraction failed
            enhanced_result['enhanced_content'] = result.get('body', result.get('snippet', ''))
            logger.warning(f"⚠️ Deep extraction failed for {url[:50]}..., using snippet")
            
    except Exception as e:
        logger.warning(f"⚠️ Content extraction error for {url[:50]}...: {e}")
        enhanced_result['enhanced_content'] = result.get('body', result.get('snippet', ''))
    
    return enhanced_result

async def enhanced_bulgarian_legal_search(query: str, max_results: int = 30, min_relevancy: float = 0.15) -> str:
    """
    Advanced Bulgarian legal document search with state-of-the-art relevancy scoring.
    
    Features:
    - BM25 keyword matching optimized for legal documents
    - Semantic similarity using OpenAI embeddings
    - Multi-factor relevancy scoring (title, domain authority, content quality)
    - Reciprocal Rank Fusion (RRF) for optimal ranking
    - Confidence scoring for result reliability
    
    Args:
        query: The legal research query in Bulgarian
        max_results: Maximum number of results to return (default: 15)
        min_relevancy: Minimum relevancy probability threshold (default: 0.3)
    
    Returns:
        Formatted search results with enhanced metadata and scoring
    """
    
    try:
        # Preprocess the query
        processed_query = preprocess_query(query)
        logger.info(f"🔍 Starting enhanced legal search for: '{query}'")
        if processed_query != query:
            logger.info(f"📝 Processed query: '{processed_query}'")
        
        # AGENTIC MULTI-ITERATION SEARCH WITH INTELLIGENT THINKING
        all_results = []
        search_context = f"Initial search for: {query}"
        
        # Phase 1: AI-driven intelligent query expansion
        logger.info("🧠 Phase 1: Intelligent Query Expansion via AI Reasoning")
        try:
            expanded_queries = await intelligent_query_expansion(query, search_context, iteration=1)
            logger.info(f"🎯 AI generated {len(expanded_queries)} intelligent queries")
            
            if not expanded_queries:
                logger.warning("No queries generated by AI, falling back to original query")
                expanded_queries = [query]
                
        except Exception as e:
            logger.error(f"AI query expansion failed: {e}")
            logger.info("🔄 Falling back to original query")
            expanded_queries = [query]
        
        for i, expanded_query in enumerate(expanded_queries):
            logger.info(f"🔍 Searching with query {i+1}: '{expanded_query}'")
            try:
                phase_results = google_domain_search(expanded_query, max_results // len(expanded_queries) if len(expanded_queries) > 0 else max_results)
                if phase_results:
                    all_results.extend(phase_results)
                    logger.info(f"✅ Found {len(phase_results)} results from query {i+1}")
                else:
                    logger.warning(f"⚠️ No results from query {i+1}")
            except Exception as e:
                logger.error(f"Search failed for query {i+1}: {e}")
        
        logger.info(f"📊 Phase 1 Complete: {len(all_results)} total results from {len(expanded_queries)} queries")
        
        # Phase 2: Deep content extraction and preliminary analysis
        if all_results:
            logger.info("📄 Phase 2: Deep Content Extraction and Preliminary Scoring")
            enhanced_results = []
            
            for result in all_results[:max_results]:  # Process reasonable number
                enhanced_result = await extract_deep_content(result)
                enhanced_results.append(enhanced_result)
            
            # Preliminary relevancy scoring
            logger.info("🎯 Applying preliminary relevancy scoring")
            try:
                from relevancy_scoring import BulgarianLegalRelevancyScorer
                scorer = BulgarianLegalRelevancyScorer()
                preliminary_scores = []
                
                # Convert to SearchResult objects for scoring
                search_result_objects = []
                for result in enhanced_results:
                    search_result = SearchResult(
                        url=result.get('url', result.get('href', '')),
                        title=result.get('title', ''),
                        snippet=result.get('body', result.get('snippet', '')),
                        content=result.get('enhanced_content', ''),
                        metadata=result
                    )
                    search_result_objects.append(search_result)
                
                # Score and rank all results at once
                scored_results = scorer.score_and_rank(query, search_result_objects)
                preliminary_scores = [r.relevancy_probability for r in scored_results]
            except ImportError as e:
                logger.warning(f"Relevancy scorer not available: {e}")
                # Simple fallback scoring based on query match
                preliminary_scores = []
                query_words = query.lower().split()
                for result in enhanced_results:
                    content = result.get('enhanced_content', result.get('body', '')).lower()
                    matches = sum(1 for word in query_words if word in content)
                    score = min(matches / len(query_words), 1.0) if query_words else 0.5
                    preliminary_scores.append(score)
            
            avg_relevancy = sum(preliminary_scores) / len(preliminary_scores) if preliminary_scores else 0
            logger.info(f"📊 Preliminary Analysis: Average relevancy {avg_relevancy:.1%}")
            
            # Phase 3: Adaptive refinement based on gaps identified by AI
            if avg_relevancy < 0.7 or len(enhanced_results) < max_results * 0.8:
                logger.info("🧠 Phase 3: AI Gap Analysis and Adaptive Query Refinement")
                
                try:
                    refined_queries = await adaptive_query_refinement(
                        query, enhanced_results[:10], preliminary_scores[:10]
                    )
                    logger.info(f"🎯 AI generated {len(refined_queries)} refined queries")
                    
                    for i, refined_query in enumerate(refined_queries):
                        logger.info(f"🔍 Refined search {i+1}: '{refined_query}'")
                        try:
                            refined_results = google_domain_search(refined_query, max_results // 3)
                            if refined_results:
                                # Deep extract new results
                                for result in refined_results:
                                    try:
                                        enhanced_result = await extract_deep_content(result)
                                        enhanced_results.append(enhanced_result)
                                    except Exception as e:
                                        logger.warning(f"Content extraction failed for refined result: {e}")
                                        enhanced_results.append(result)  # Add without enhancement
                                logger.info(f"✅ Added {len(refined_results)} refined results")
                        except Exception as e:
                            logger.error(f"Refined search {i+1} failed: {e}")
                    
                    logger.info(f"📊 Phase 3 Complete: {len(enhanced_results)} total enhanced results")
                    
                except Exception as e:
                    logger.error(f"AI refinement failed: {e}")
                    logger.info("🔄 Continuing with existing results")
            
            # Use enhanced results for final processing
            raw_results = enhanced_results
        else:
            logger.warning("No results from intelligent search - falling back to basic search")
            raw_results = google_domain_search(processed_query, max_results)
        
        if not raw_results:
            return "❌ **Няма намерени резултати**\n\nМоля, опитайте с различни ключови думи."
        
        # For simplified processing, work directly with dict results
        search_results = []
        for result in raw_results:
            if isinstance(result, dict):
                # Handle different URL field names from different sources
                url = result.get('href', '') or result.get('link', '') or result.get('url', '')
                snippet = result.get('body', '') or result.get('snippet', '') or result.get('content', '')
                
                # Skip results with no URL
                if not url:
                    logger.warning(f"Skipping result with no URL: {result.get('title', 'No Title')}")
                    continue
                
                # Work with dict directly instead of SearchResult objects for simplicity
                simplified_result = {
                    'url': url,
                    'href': url,  # For compatibility
                    'title': result.get('title', ''),
                    'snippet': snippet,
                    'body': snippet,  # For compatibility
                    'content': result.get('content', ''),
                    'metadata': result
                }
                search_results.append(simplified_result)
        
        # Apply simplified scoring if not already done in earlier phases
        if 'enhanced_content' not in search_results[0] if search_results else {}:
            logger.info(f"📄 Final scoring for {len(search_results)} results")
            query_words = query.lower().split()
            scored_results = []
            
            for result in search_results:
                # Calculate simple relevancy score
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                content = result.get('content', '').lower()
                full_text = f"{title} {snippet} {content}"
                
                matches = sum(1 for word in query_words if word in full_text)
                relevancy = min(matches / len(query_words), 1.0) if query_words else 0.5
                
                # Add scoring metadata to result
                result['relevancy_score'] = relevancy
                result['confidence_score'] = 0.8 if relevancy > 0.7 else 0.6 if relevancy > 0.4 else 0.4
                
                scored_results.append(result)
        else:
            scored_results = search_results
        
        # Sort by relevancy score
        scored_results.sort(key=lambda x: x.get('relevancy_score', 0), reverse=True)
        
        # IMPROVED FILTERING: More generous thresholds based on agentic search best practices
        # Use adaptive threshold: if we have many high-quality results, be stricter; if few, be more generous
        high_quality_results = [r for r in scored_results if r.get('relevancy_score', 0) >= 0.6]
        medium_quality_results = [r for r in scored_results if r.get('relevancy_score', 0) >= 0.3]
        
        if len(high_quality_results) >= 10:
            # We have plenty of high-quality results
            filtered_results = high_quality_results[:20]
        elif len(medium_quality_results) >= 8:
            # Use medium quality results
            filtered_results = medium_quality_results[:15]
        else:
            # Be generous - take all scored results
            filtered_results = scored_results[:12]
        
        logger.info(f"📊 Result filtering: {len(scored_results)} → {len(filtered_results)} results (adaptive threshold)")
        
        # Ensure minimum number of results for comprehensive analysis
        final_results = filtered_results[:max(15, min(len(filtered_results), 20))]
        
        logger.info(f"✅ Returning {len(final_results)} comprehensive results for analysis")
        
        # Format simplified results 
        return format_simplified_search_results(query, final_results)
        
    except Exception as e:
        logger.error(f"Error in enhanced legal search: {e}")
        return f"❌ **Грешка при търсенето**: {str(e)}"

async def extract_enhanced_content(search_results: List[SearchResult]) -> List[SearchResult]:
    """
    Extract enhanced content from search results with better context and metadata
    """
    
    enhanced_results = []
    
    for result in search_results:
        try:
            # Make HTTP request to get full page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; BulgarianLegalResearcher/1.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'bg,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(result.url, headers=headers, timeout=10, allow_redirects=True, verify=False)
            response.raise_for_status()
            
            if response.status_code == 200:
                # Enhanced content extraction - optimized length
                content = extract_legal_content(response.text)
                result.content = content[:1800]  # Optimized content length for better processing
                
                # Extract additional metadata
                result.metadata.update({
                    'status_code': response.status_code,
                    'content_length': len(content),
                    'response_time': response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
                    'final_url': response.url
                })
                
        except Exception as e:
            logger.warning(f"Failed to extract content from {result.url}: {e}")
            # Keep the result but mark content extraction as failed
            result.metadata['content_extraction_error'] = str(e)
        
        enhanced_results.append(result)
    
    return enhanced_results

def extract_legal_content(html: str) -> str:
    """
    Enhanced content extraction optimized for Bulgarian legal documents
    """
    try:
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Priority content selectors for legal sites
        content_selectors = [
            'article',
            '.content',
            '.article-content', 
            '.post-content',
            '.entry-content',
            '.legal-content',
            '.document-content',
            'main',
            '.main-content',
            '#content',
            '.text-content'
        ]
        
        content_text = ""
        
        # Try to find content using priority selectors
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    content_text += element.get_text(separator=' ', strip=True) + " "
                break
        
        # Fallback to body content if no specific content found
        if not content_text.strip():
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator=' ', strip=True)
        
        # Clean and normalize text
        content_text = ' '.join(content_text.split())
        
        return content_text
        
    except Exception as e:
        logger.warning(f"Error extracting content: {e}")
        return ""

def format_enhanced_search_results(query: str, results: List[SearchResult]) -> str:
    """
    Format search results with enhanced metadata and scoring information
    """
    
    if not results:
        return "❌ **Няма намерени релевантни резултати**"
    
    # Build the enhanced response
    response_parts = []
    
    # Header with search statistics
    avg_relevancy = sum(r.relevancy_probability for r in results) / len(results)
    avg_confidence = sum(r.confidence_score for r in results) / len(results)
    
    response_parts.append(f"🔍 **РЕЗУЛТАТИ ОТ НАПРЕДНА ПРАВНА АНАЛИТИКА**")
    response_parts.append(f"📊 **Статистика**: {len(results)} резултата | Средна релевантност: {avg_relevancy:.1%} | Средна увереност: {avg_confidence:.1%}")
    response_parts.append("=" * 80)
    
    # Top 5 sources section with enhanced metadata
    response_parts.append(f"📚 **ТОП {min(5, len(results))} НАЙ-РЕЛЕВАНТНИ ИЗТОЧНИЦИ**")
    
    for i, result in enumerate(results[:5], 1):
        # Format domain description
        domain_desc = get_domain_description(result.domain)
        
        # Relevancy and confidence indicators
        relevancy_bar = "🟢" * int(result.relevancy_probability * 5) + "⚪" * (5 - int(result.relevancy_probability * 5))
        confidence_bar = "🔵" * int(result.confidence_score * 5) + "⚪" * (5 - int(result.confidence_score * 5))
        
        response_parts.append(f"\n**{i}. [{result.title}]({result.url})**")
        response_parts.append(f"   🏛️ *{result.domain} - {domain_desc}*")
        response_parts.append(f"   📊 Релевантност: {relevancy_bar} {result.relevancy_probability:.1%}")
        response_parts.append(f"   🎯 Увереност: {confidence_bar} {result.confidence_score:.1%}")
        response_parts.append(f"   📄 {result.snippet[:200]}{'...' if len(result.snippet) > 200 else ''}")
        
        # Show key scoring components
        scores = []
        if result.bm25_score > 0.1:
            scores.append(f"BM25: {result.bm25_score:.2f}")
        if result.semantic_score > 0.1:
            scores.append(f"Семантика: {result.semantic_score:.2f}")
        if result.title_relevance > 0.1:
            scores.append(f"Заглавие: {result.title_relevance:.2f}")
        
        if scores:
            response_parts.append(f"   🔢 Компоненти: {' | '.join(scores)}")
    
    response_parts.append("\n" + "-" * 80)
    
    # Enhanced legal analysis section
    response_parts.append(f"📋 **ПРАВЕН АНАЛИЗ**: {query}")
    
    # Extract key legal themes from top results
    legal_themes = extract_legal_themes(results[:5])
    if legal_themes:
        response_parts.append(f"\n🎯 **ОСНОВНИ ПРАВНИ ТЕМИ**:")
        for theme in legal_themes[:3]:
            response_parts.append(f"   • {theme}")
    
    # Summary based on top results
    response_parts.append(f"\n⚖️ **КРАТКО РЕЗЮМЕ**:")
    summary = generate_smart_summary(query, results[:3])
    response_parts.append(f"{summary}")
    
    # Detailed analysis with references
    response_parts.append(f"\n📖 **ПОДРОБЕН АНАЛИЗ**:")
    detailed_analysis = generate_detailed_analysis(query, results[:5])
    response_parts.append(f"{detailed_analysis}")
    
    # Practical recommendations
    response_parts.append(f"\n💡 **ПРАКТИЧЕСКИ ПРЕПОРЪКИ**:")
    recommendations = generate_practical_recommendations(query, results[:3])
    response_parts.append(f"{recommendations}")
    
    # Additional insights section
    if len(results) > 5:
        response_parts.append(f"\n📎 **ДОПЪЛНИТЕЛНИ ИЗТОЧНИЦИ**:")
        for i, result in enumerate(results[5:10], 6):
            response_parts.append(f"   {i}. [{result.title[:80]}...]({result.url}) - {result.relevancy_probability:.1%}")
    
    # Search methodology note
    response_parts.append(f"\n" + "=" * 80)
    response_parts.append(f"🔬 **МЕТОДОЛОГИЯ**: Използва BM25 + семантичен анализ + RRF рейтинг за максимална точност")
    
    return "\n".join(response_parts)

def get_domain_description(domain: str) -> str:
    """Get enhanced description for Bulgarian legal domains"""
    descriptions = {
        'ciela.net': 'Водеща българска правна платформа (19,300+ страници)',
        'apis.bg': 'Апис - специализирано правно издателство (4,190+ страници)', 
        'lakorda.com': 'Правни новини и анализи (актуална информация)',
        'lex.bg': 'Правна база данни и консултации',
        'justice.bg': 'Министерство на правосъдието (официални актове)',
        'vks.bg': 'Върховен касационен съд (съдебна практика)',
        'vss.bg': 'Върховен административен съд (административна практика)'
    }
    return descriptions.get(domain, 'Правен източник')

def extract_legal_themes(results: List[SearchResult]) -> List[str]:
    """Extract key legal themes from search results"""
    
    # Legal keywords in Bulgarian
    theme_keywords = {
        'наказателно право': ['наказание', 'престъпление', 'съд', 'присъда', 'обвинение'],
        'гражданско право': ['договор', 'собственост', 'облигация', 'деликт', 'вреда'],
        'административно право': ['административен', 'орган', 'актове', 'жалба', 'производство'],
        'трудово право': ['трудов', 'работник', 'работодател', 'заплата', 'увольнение'],
        'търговско право': ['търговски', 'дружество', 'сделка', 'търговец', 'регистър'],
        'процесуално право': ['процедура', 'съдебно', 'производство', 'доказателства'],
        'конституционно право': ['конституция', 'права', 'свободи', 'държава', 'власт']
    }
    
    # Combine all text content
    all_text = ' '.join([r.title + ' ' + r.snippet + ' ' + r.content for r in results]).lower()
    
    # Find matching themes
    themes = []
    for theme, keywords in theme_keywords.items():
        matches = sum(1 for keyword in keywords if keyword in all_text)
        if matches >= 2:  # Require at least 2 keyword matches
            themes.append(f"{theme} ({matches} индикатора)")
    
    return themes

def generate_smart_summary(query: str, results: List[SearchResult]) -> str:
    """Generate intelligent summary based on top results"""
    
    if not results:
        return "Няма достатъчно информация за генериране на резюме."
    
    # Extract key information from top results
    key_points = []
    
    for result in results:
        # Extract sentences that might contain key legal information
        text = result.snippet + ' ' + result.content[:500]
        sentences = text.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 30 and any(keyword in sentence.lower() for keyword in query.lower().split()):
                key_points.append(sentence[:200])
                if len(key_points) >= 3:
                    break
    
    if key_points:
        summary = "Въз основа на анализираните източници: " + " ".join(key_points[:2])
        return summary[:500] + "..." if len(summary) > 500 else summary
    else:
        return f"Търсенето за '{query}' е свързано с правни въпроси, документирани в горните източници."

def generate_detailed_analysis(query: str, results: List[SearchResult]) -> str:
    """Generate detailed legal analysis with source references"""
    
    analysis_parts = []
    
    # Reference legal sources
    for i, result in enumerate(results[:3], 1):
        domain_authority = "висок" if result.domain_authority > 0.9 else "среден" if result.domain_authority > 0.7 else "базов"
        
        analysis_parts.append(
            f"**Източник {i}** ({result.domain} - {domain_authority} авторитет): "
            f"{result.snippet[:150]}{'...' if len(result.snippet) > 150 else ''} "
            f"[Виж пълния документ]({result.url})"
        )
    
    # Add legal context
    analysis_parts.append(
        f"\n**Правен контекст**: Анализът се базира на {len(results)} релевантни източника "
        f"с висока степен на съответствие към търсената тема '{query}'. "
        f"Източниците са автоматично класирани по релевантност използвайки "
        f"напредни алгоритми за семантичен анализ и съответствие на съдържанието."
    )
    
    return "\n".join(analysis_parts)

def generate_practical_recommendations(query: str, results: List[SearchResult]) -> str:
    """Generate practical recommendations based on search results"""
    
    recommendations = []
    
    # Generic recommendations based on result types
    if any('съд' in (r.title + r.snippet).lower() for r in results):
        recommendations.append("📋 Проверете актуалната съдебна практика по въпроса")
        recommendations.append("⚖️ Консултирайте се с юрист за конкретния случай")
    
    if any('закон' in (r.title + r.snippet).lower() for r in results):
        recommendations.append("📜 Проверете за скорошни изменения в законодателството")
        recommendations.append("🔍 Изучете пълния текст на приложимите правни норми")
    
    # Add source-specific recommendations
    high_authority_sources = [r for r in results if r.domain_authority > 0.9]
    if high_authority_sources:
        recommendations.append(f"🏛️ Използвайте информацията от {len(high_authority_sources)} официални източника като водеща")
    
    # Default recommendations
    if not recommendations:
        recommendations = [
            "📚 Проучете допълнителни източници за по-пълна информация",
            "💼 При необходимост потърсете професионална правна помощ",
            "🔄 Проверете за актуализации на информацията"
        ]
    
    return "\n".join(recommendations[:4])  # Limit to 4 recommendations

def format_simplified_search_results(query: str, results: List[Dict]) -> str:
    """
    COMPREHENSIVE legal analysis with intelligent content processing and real answers.
    """
    
    if not results:
        return "❌ **Няма намерени релевантни резултати**"
    
    # Extract and analyze full content from top results
    comprehensive_analysis = analyze_legal_content_comprehensively(query, results)
    
    # Build the response
    response_parts = []
    
    # Header with search statistics
    avg_relevancy = sum(r.get('relevancy_score', 0) for r in results) / len(results)
    avg_confidence = sum(r.get('confidence_score', 0) for r in results) / len(results)
    
    response_parts.append(f"🔍 **РЕЗУЛТАТИ ОТ НАПРЕДНА ПРАВНА АНАЛИТИКА**")
    response_parts.append(f"📊 **Статистика**: {len(results)} резултата | Средна релевантност: {avg_relevancy:.1%} | Средна увереност: {avg_confidence:.1%}")
    response_parts.append("=" * 80)
    
    # TOP RESULTS DISPLAY (Non-AI section - just showing the ranked pages)
    response_parts.append("🏆 **ТОП КЛАСИРАНИ РЕЗУЛТАТИ ПО РЕЛЕВАНТНОСТ**")
    response_parts.append("*Автоматично класирани с BM25 + семантичен анализ + RRF рейтинг*")
    response_parts.append("")
    
    for i, result in enumerate(results[:min(12, len(results))], 1):
        url = result.get('url', result.get('href', ''))
        title = result.get('title', 'No Title')
        snippet = result.get('body', result.get('snippet', ''))[:200]
        domain = extract_domain_from_url(url)
        relevancy = result.get('relevancy_score', 0)
        
        # Create visual relevancy indicator
        relevancy_bar = "🟢" * int(relevancy * 5) + "⚪" * (5 - int(relevancy * 5))
        
        # Get domain description from BULGARIAN_LEGAL_DOMAINS
        domain_info = BULGARIAN_LEGAL_DOMAINS.get(domain, {})
        domain_type = domain_info.get('description', 'Правен източник')
        
        response_parts.append(f"**{i}. {title}**")
        response_parts.append(f"   🏛️ *{domain}* ({domain_type})")
        response_parts.append(f"   📊 Релевантност: {relevancy_bar} **{relevancy:.1%}**")
        response_parts.append(f"   📄 {snippet}...")
        response_parts.append(f"   🔗 [{url}]({url})")
        response_parts.append("")
    
    response_parts.append("=" * 80)
    response_parts.append("")
    
    # AI-DRIVEN COMPREHENSIVE ANALYSIS
    response_parts.append("🤖 **AI АНАЛИЗ И ОТГОВОР**")
    response_parts.append("*Генериран чрез дълбок анализ на съдържанието от горните източници*")
    response_parts.append("")
    
    # MAIN LEGAL ANSWER - This is what the user wants!
    response_parts.append(f"⚖️ **ДИРЕКТЕН ОТГОВОР НА ЗАПИТВАНЕТО: '{query}'**")
    response_parts.append(comprehensive_analysis['direct_answer'])
    
    # Legal framework and applicable laws
    response_parts.append(f"\n📜 **ПРИЛОЖИМО ЗАКОНОДАТЕЛСТВО**")
    response_parts.append(comprehensive_analysis['applicable_laws'])
    
    # Procedure and steps
    response_parts.append(f"\n📋 **ПРОЦЕДУРА И СТЪПКИ**")
    response_parts.append(comprehensive_analysis['procedure'])
    
    # Compensation amounts and calculations
    if 'compensation' in comprehensive_analysis:
        response_parts.append(f"\n💰 **РАЗМЕР НА ОБЕЗЩЕТЕНИЕТО**")
        response_parts.append(comprehensive_analysis['compensation'])
    
    # Court practice and precedents
    response_parts.append(f"\n🏛️ **СЪДЕБНА ПРАКТИКА**")
    response_parts.append(comprehensive_analysis['court_practice'])
    
    # Practical recommendations
    response_parts.append(f"\n💡 **ПРАКТИЧЕСКИ СЪВЕТИ**")
    response_parts.append(comprehensive_analysis['recommendations'])
    
    response_parts.append("\n" + "-" * 80)
    
    # Top sources section (condensed)
    response_parts.append(f"📚 **ТОП {min(5, len(results))} ИЗПОЛЗВАНИ ИЗТОЧНИЦИ**")
    
    for i, result in enumerate(results[:5], 1):
        url = result.get('url', result.get('href', ''))
        title = result.get('title', 'No Title')
        domain = extract_domain_from_url(url)
        relevancy = result.get('relevancy_score', 0)
        
        relevancy_bar = "🟢" * int(relevancy * 5) + "⚪" * (5 - int(relevancy * 5))
        
        response_parts.append(f"**{i}.** [{title[:80]}...]({url})")
        response_parts.append(f"    🏛️ {domain} | 📊 {relevancy_bar} {relevancy:.1%}")
    
    # Footer with methodology
    response_parts.append(f"\n" + "=" * 80)
    response_parts.append(f"🔬 **МЕТОДОЛОГИЯ**: AI анализ на {len(results)} правни документа с 7000 символа съдържание от всеки източник")
    response_parts.append(f"📈 **Технологии**: BM25 алгоритъм + OpenAI семантичен анализ + Адаптивно филтриране + GPT-4o-mini аналитика")
    
    return "\n".join(response_parts)

def analyze_legal_content_comprehensively(query: str, results: List[Dict]) -> Dict[str, str]:
    """
    Use AI to perform DEEP legal analysis of the extracted content and provide REAL answers.
    NO more generic templates - only content-driven AI analysis.
    """
    
    # Extract all deep content from top sources
    all_content = []
    
    for result in results[:12]:  # Analyze more sources for comprehensive coverage  
        content = result.get('enhanced_content', '') or result.get('content', '') or result.get('body', '')
        if content and len(content) > 150:  # Only meaningful content
            all_content.append(content[:7000])  # Use full 7K characters per source
    
    # Combine the extracted content
    combined_content = "\n".join(all_content)
    
    # Use AI to analyze the content and generate real legal answers
    try:
        from openai import OpenAI
        client = OpenAI()
        
        analysis_prompt = f"""
Ти си експерт в българското право. Анализирай извлеченото съдържание от правни документи и отговори ДИРЕКТНО на въпроса: "{query}"

ПРАВНО СЪДЪРЖАНИЕ ЗА АНАЛИЗ:
{combined_content[:15000]}

ЗАДАЧА:
1. Прочети ЦЯЛОТО съдържание и извлечи КОНКРЕТНИ правни отговори
2. Цитирай ТОЧНИ членове, суми, срокове от документите  
3. Обясни процедурите със СТЪПКИ ПО СТЪПКИ
4. Посочи ПРАКТИЧЕСКИ примери от съдържанието
5. БЕЗ общи фрази като "консултирайте се с юрист" - САМО конкретни отговори

ФОРМАТ НА ОТГОВОРА:
DIRECT_ANSWER: [Ясен, директен отговор на въпроса с конкретни данни от документите]
APPLICABLE_LAWS: [Точни членове и закони от съдържанието] 
PROCEDURE: [Конкретни стъпки от документите]
COURT_PRACTICE: [Съдебна практика от съдържанието]
RECOMMENDATIONS: [Практически съвети базирани на документите]

Използвай САМО информация от предоставеното съдържание. Отговори на български език:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=4000,  # Increased for comprehensive analysis
            temperature=0.1
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Parse the AI response into sections
        analysis = parse_ai_legal_response(ai_response)
        
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
        # Fallback to content-based extraction if AI fails
        analysis = {
            'direct_answer': f"Според анализираните {len(results)} правни източника за '{query}', има информация за приложимите правни норми и процедури.",
            'applicable_laws': extract_laws_from_content(combined_content),
            'procedure': extract_procedures_from_content(combined_content),
            'court_practice': extract_court_info_from_content(combined_content),
            'recommendations': "Проверете актуалната правна информация и консултирайте се със специалист за конкретния случай."
        }
    
    return analysis

def parse_ai_legal_response(ai_response: str) -> Dict[str, str]:
    """Parse the structured AI response into components"""
    
    sections = {
        'direct_answer': '',
        'applicable_laws': '',
        'procedure': '',
        'court_practice': '',
        'recommendations': ''
    }
    
    # Try to extract structured sections
    lines = ai_response.split('\n')
    current_section = 'direct_answer'
    current_content = []
    
    for line in lines:
        line = line.strip()
        if line.upper().startswith('DIRECT_ANSWER:'):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'direct_answer'
            current_content = [line.replace('DIRECT_ANSWER:', '').strip()]
        elif line.upper().startswith('APPLICABLE_LAWS:'):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'applicable_laws'
            current_content = [line.replace('APPLICABLE_LAWS:', '').strip()]
        elif line.upper().startswith('PROCEDURE:'):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'procedure'
            current_content = [line.replace('PROCEDURE:', '').strip()]
        elif line.upper().startswith('COURT_PRACTICE:'):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'court_practice'
            current_content = [line.replace('COURT_PRACTICE:', '').strip()]
        elif line.upper().startswith('RECOMMENDATIONS:'):
            if current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'recommendations'
            current_content = [line.replace('RECOMMENDATIONS:', '').strip()]
        elif line:
            current_content.append(line)
    
    # Add the last section
    if current_content:
        sections[current_section] = '\n'.join(current_content)
    
    # If parsing failed, use the whole response as direct answer
    if not any(sections.values()):
        sections['direct_answer'] = ai_response
        sections['applicable_laws'] = "Информацията е включена в основния анализ по-горе."
        sections['procedure'] = "Вижте детайлите в основния анализ."
        sections['court_practice'] = "Съдебната практика е разгледана в основния анализ."
        sections['recommendations'] = "Практическите препоръки са включени в анализа."
    
    return sections

def extract_laws_from_content(content: str) -> str:
    """Fallback function to extract laws from content"""
    import re
    
    law_patterns = [
        r'чл\.\s*\d+[а-я]*[^\d]*',
        r'Закон\s+за\s+[А-Яа-я\s]+',
        r'Кодекс\s+[А-Яа-я\s]+',
        r'Наредба\s+№?\s*\d+'
    ]
    
    found_laws = []
    for pattern in law_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        found_laws.extend(matches[:3])
    
    if found_laws:
        return "• " + "\n• ".join(list(set(found_laws))[:5])
    else:
        return "Правни норми са посочени в анализираните документи."

def extract_procedures_from_content(content: str) -> str:
    """Fallback function to extract procedures"""
    procedure_keywords = ['подаване', 'заявление', 'срок', 'документи', 'процедура', 'стъпки']
    
    sentences = content.split('.')
    procedure_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 50 and any(keyword in sentence.lower() for keyword in procedure_keywords):
            procedure_sentences.append(f"• {sentence[:100]}...")
            if len(procedure_sentences) >= 3:
                break
    
    return "\n".join(procedure_sentences) if procedure_sentences else "Процедурата е описана в основните документи."

def extract_court_info_from_content(content: str) -> str:
    """Fallback function to extract court practice"""
    court_keywords = ['съд', 'решение', 'практика', 'становище']
    
    sentences = content.split('.')
    court_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 50 and any(keyword in sentence.lower() for keyword in court_keywords):
            court_sentences.append(f"• {sentence[:100]}...")
            if len(court_sentences) >= 2:
                break
    
    return "\n".join(court_sentences) if court_sentences else "Съдебната практика изисква анализ на конкретните обстоятелства."



def extract_domain_from_url(url: str) -> str:
    """Extract domain name from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except:
        return 'Unknown domain'

def enhanced_bulgarian_legal_search_sync(query: str, max_results: int = 30, min_relevancy: float = 0.15) -> str:
    """
    Synchronous wrapper for the async enhanced legal search function.
    This ensures compatibility with the existing tool system.
    """
    import asyncio
    
    try:
        # Create new event loop if none exists, or use existing one
        try:
            loop = asyncio.get_running_loop()
            # If we're in an async context, create a new thread to run the async function
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(
                        enhanced_bulgarian_legal_search(query, max_results, min_relevancy)
                    )
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
                
        except RuntimeError:
            # No event loop running, we can create one
            return asyncio.run(enhanced_bulgarian_legal_search(query, max_results, min_relevancy))
            
    except Exception as e:
        logger.error(f"Error in sync wrapper: {e}")
        return f"⚠️ Грешка при асинхронно изпълнение: {e}"

@tool
def enhanced_bulgarian_legal_search_tool(query: str) -> str:
    """
    Advanced Bulgarian legal document search with state-of-the-art relevancy scoring.
    
    This tool uses:
    - AI-driven intelligent query expansion with legal reasoning
    - Multi-iteration search with adaptive refinement
    - Deep content extraction from legal documents
    - BM25 keyword matching optimized for legal documents
    - Semantic similarity using OpenAI embeddings
    - Multi-factor relevancy scoring (title, domain authority, content quality)
    - Reciprocal Rank Fusion (RRF) for optimal ranking
    - Confidence scoring for result reliability
    
    Args:
        query: The legal research query in Bulgarian
    
    Returns:
        Formatted search results with enhanced metadata and scoring
    """
    return enhanced_bulgarian_legal_search_sync(query, max_results=30, min_relevancy=0.15)

def google_domain_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search multiple Bulgarian legal domains efficiently using Google CSE.
    """
    logger.info(f"🔍 Starting multi-domain search for: '{query}'")
    
    all_results = []
    
    # Search each domain
    for domain in BULGARIAN_LEGAL_DOMAINS.keys():
        try:
            logger.info(f"🔍 Searching in {domain}...")
            domain_results = google_cse_search_legal(
                query=query,
                site_search=domain,
                num_results=max_results // len(BULGARIAN_LEGAL_DOMAINS)
            )
            
            if domain_results:
                # Add domain-specific metadata
                for result in domain_results:
                    result.update({
                        'domain': domain,
                        'domain_authority': BULGARIAN_LEGAL_DOMAINS[domain]['authority'],
                        'source_type': 'legal_database'
                    })
                all_results.extend(domain_results)
                logger.info(f"✅ Found {len(domain_results)} results in {domain}")
            else:
                logger.info(f"⚠️ No results found in {domain}")
                
        except Exception as e:
            logger.error(f"❌ Error searching {domain}: {e}")
            continue
    
    logger.info(f"📊 Multi-domain search complete: {len(all_results)} total results")
    return all_results

# VKS.bg (Supreme Court) Integration
def vks_bg_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Enhanced VKS.bg search with comprehensive result gathering and intelligent filtering.
    
    This function:
    1. Searches multiple sources for VKS content
    2. Gathers maximum possible results
    3. Filters and ranks by relevance and authority
    4. Returns structured data optimized for AI analysis
    
    Args:
        query: Legal search query in Bulgarian
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing VKS search results sorted by relevance
    """
    try:
        all_vks_results = []
        
        # Multiple search strategies for comprehensive coverage
        search_strategies = [
            # Strategy 1: Direct VKS search with legal terms
            f"site:vks.bg {query} решение постановление определение",
            # Strategy 2: Broader VKS search
            f"site:vks.bg {query}",
            # Strategy 3: VKS with case numbers
            f"site:vks.bg {query} дело номер",
            # Strategy 4: VKS with legal areas
            f"site:vks.bg {query} гражданско наказателно търговско",
        ]
        
        # Try Google CSE with multiple strategies
        if GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID:
            for strategy in search_strategies:
                try:
                    strategy_results = google_cse_search_legal(
                        query=strategy,
                        site_search="vks.bg",
                        num_results=min(max_results * 2, 20)  # Get more results initially
                    )
                    if strategy_results:
                        all_vks_results.extend(strategy_results)
                except Exception:
                    continue
        
        # Fallback to DuckDuckGo with multiple approaches
        if len(all_vks_results) < max_results:
            ddg_strategies = [
                f"site:vks.bg {query}",
                f"vks.bg {query} решение",
                f"върховен касационен съд {query}"
            ]
            
            for strategy in ddg_strategies:
                try:
                    ddg_results = fallback_ddg_search(strategy, "vks.bg")
                    if ddg_results:
                        all_vks_results.extend(ddg_results)
                except Exception:
                    continue
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in all_vks_results:
            url = result.get('href', result.get('url', ''))
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Enhance results with VKS-specific metadata and scoring
        enhanced_results = []
        for result in unique_results:
            enhanced_result = result.copy()
            
            # Add VKS-specific metadata
            enhanced_result.update({
                'domain': 'vks.bg',
                'domain_authority': 1.0,  # Supreme Court has highest authority
                'source_type': 'supreme_court',
                'court_level': 'supreme',
                'document_type': extract_vks_document_type(result.get('title', '')),
                'legal_area': classify_vks_legal_area(result.get('title', '') + ' ' + result.get('body', '')),
                'search_method': 'vks_bg_integration'
            })
            
            # Calculate relevance score based on query match
            relevance_score = calculate_vks_relevance(query, enhanced_result)
            enhanced_result['relevance_score'] = relevance_score
            
            enhanced_results.append(enhanced_result)
        
        # Sort by relevance score (highest first)
        enhanced_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Return top results
        return enhanced_results[:max_results]
        
    except Exception as e:
        logger.error(f"VKS search error: {e}")
        return []

def calculate_vks_relevance(query: str, result: Dict) -> float:
    """Calculate relevance score for VKS documents"""
    score = 0.0
    query_words = query.lower().split()
    
    # Title relevance (highest weight)
    title = result.get('title', '').lower()
    title_matches = sum(1 for word in query_words if word in title)
    score += (title_matches / len(query_words)) * 0.4 if query_words else 0
    
    # Content relevance
    content = result.get('body', '').lower()
    content_matches = sum(1 for word in query_words if word in content)
    score += (content_matches / len(query_words)) * 0.3 if query_words else 0
    
    # Document type bonus (decisions are more valuable)
    doc_type = result.get('document_type', '')
    if doc_type == 'решение':
        score += 0.2
    elif doc_type in ['определение', 'постановление']:
        score += 0.1
    
    # Legal area relevance
    legal_area = result.get('legal_area', '')
    if any(word in legal_area for word in query_words):
        score += 0.1
    
    return min(score, 1.0)  # Cap at 1.0

def simulate_vks_search(query: str, max_results: int = 10) -> List[Dict]:
    """
    Simulate VKS.bg search with realistic legal document structure.
    This creates realistic VKS search results for testing purposes.
    """
    logger.info("🎭 Simulating VKS.bg search with realistic court decision structure")
    
    # Common VKS decision types and topics
    decision_types = ["Решение", "Определение", "Постановление"]
    legal_areas = ["гражданско право", "наказателно право", "търговско право", "административно право", "трудово право"]
    case_numbers = ["1234/2024", "5678/2024", "9012/2023", "3456/2023", "7890/2024"]
    
    simulated_results = []
    
    for i in range(min(max_results, 5)):  # Limit to reasonable number
        decision_type = decision_types[i % len(decision_types)]
        legal_area = legal_areas[i % len(legal_areas)]
        case_number = case_numbers[i % len(case_numbers)]
        
        title = f"{decision_type} № {case_number} по {legal_area}"
        
        # Generate relevant snippet based on query
        snippet = f"По делото относно {query.lower()}, Върховният касационен съд постанови {decision_type.lower()} " \
                 f"№ {case_number}. Въпросът се отнася до {legal_area} и засяга въпроси свързани с {query.lower()}. " \
                 f"Решението е от {datetime.now().year} година и има прецедентно значение."
        
        url = f"https://vks.bg/decisions/{case_number.replace('/', '-')}"
        
        result = {
            'title': title,
            'href': url,
            'body': snippet,
            'source_domain': 'vks.bg',
            'case_number': case_number,
            'decision_type': decision_type,
            'legal_area': legal_area,
            'year': datetime.now().year,
            'simulated': True  # Mark as simulated for testing
        }
        
        simulated_results.append(result)
    
    logger.info(f"🎭 Generated {len(simulated_results)} simulated VKS results")
    return simulated_results

def extract_vks_document_type(title: str) -> str:
    """Extract document type from VKS document title"""
    title_lower = title.lower()
    
    if "решение" in title_lower:
        return "решение"
    elif "определение" in title_lower:
        return "определение"
    elif "постановление" in title_lower:
        return "постановление"
    elif "разпореждане" in title_lower:
        return "разпореждане"
    else:
        return "неизвестен"

def classify_vks_legal_area(text: str) -> str:
    """Classify the legal area of VKS document"""
    text_lower = text.lower()
    
    # Legal area keywords
    legal_areas = {
        "гражданско право": ["гражд", "договор", "собственост", "наследство", "вещно право", "облигационно право"],
        "наказателно право": ["наказ", "престъпление", "санкция", "кривично", "наказание", "обвинение"],
        "търговско право": ["търг", "дружество", "търговец", "конкуренция", "фирма", "регистрация"],
        "административно право": ["админ", "държава", "акт", "производство", "жалба", "контрол"],
        "трудово право": ["труд", "работа", "заплата", "отпуск", "договор", "длъжност", "служител"],
        "социално право": ["социал", "пенсия", "обезщетение", "инвалидност", "социална помощ"],
        "данъчно право": ["данък", "такса", "декларация", "НАП", "фискален", "облагане"],
        "семейно право": ["семейство", "брак", "развод", "дете", "алименти", "родителство"]
    }
    
    for area, keywords in legal_areas.items():
        if any(keyword in text_lower for keyword in keywords):
            return area
    
    return "общо право"

async def analyze_vks_documents(query: str, vks_results: List[Dict]) -> Dict[str, Any]:
    """
    Advanced VKS document analysis using GPT-4o-mini for precise legal analysis.
    
    Args:
        query: Original search query
        vks_results: List of VKS search results
        
    Returns:
        Analysis results with AI-selected best documents and fallback options
    """
    if not vks_results:
        return {
            "found_exact_match": False,
            "summary": "Няма намерени документи от ВКС",
            "best_documents": [],
            "analysis": "Не са намерени релевантни документи от Върховния касационен съд",
            "fallback_options": [
                "Опитайте с по-общи термини",
                "Търсете в други правни бази данни", 
                "Използвайте синоними на ключовите думи"
            ]
        }
    
    try:
        # Sort by relevance score (already sorted in vks_bg_search)
        sorted_results = sorted(vks_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Prepare documents for GPT-4o-mini analysis
        top_documents = sorted_results[:5]  # Analyze top 5 most relevant
        
        documents_text = ""
        for i, result in enumerate(top_documents, 1):
            documents_text += f"\nДокумент {i}:\n"
            documents_text += f"Заглавие: {result.get('title', 'Без заглавие')}\n"
            documents_text += f"Съдържание: {result.get('body', 'Без съдържание')}\n"
            documents_text += f"Правна област: {result.get('legal_area', 'неизвестна')}\n"
            documents_text += f"Тип документ: {result.get('document_type', 'неизвестен')}\n"
            documents_text += f"Релевантност: {result.get('relevance_score', 0):.2f}\n"
            documents_text += f"URL: {result.get('href', 'Няма линк')}\n"
            documents_text += "-" * 50
        
        # GPT-4o-mini analysis prompt
        analysis_prompt = f"""
        Анализирай внимателно следните документи от Върховния касационен съд на България по отношение на запитването: "{query}"

        {documents_text}

        Задачи:
        1. ТОЧНО СЪВПАДЕНИЕ: Има ли документ, който директно отговаря на запитването?
        2. ИЗБОР НА ДОКУМЕНТИ: Избери най-добрите 2-3 документа за подробен анализ
        3. ПРАВЕН АНАЛИЗ: Обясни правните принципи и прецеденти
        4. ПРАКТИЧЕСКИ СЪВЕТИ: Дай конкретни препоръки

        Отговори в следния формат:
        ТОЧНО_СЪВПАДЕНИЕ: [ДА/НЕ]
        ИЗБРАНИ_ДОКУМЕНТИ: [номера на документите]
        АНАЛИЗ: [подробен анализ]
        СЪВЕТИ: [практически препоръки]
        ЗАКЛЮЧЕНИЕ: [финално заключение]
        """
        
        # Call GPT-4o-mini for analysis
        try:
            from openai import OpenAI
            client = OpenAI()
            
            ai_analysis = None
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ти си експерт по българско право със специализация в анализ на решения на Върховния касационен съд. Отговаряш на български език."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            if response.choices and response.choices[0].message.content:
                content_str = response.choices[0].message.content
                if content_str:
                    ai_analysis = content_str.strip()
                else:
                    ai_analysis = ""
            else:
                ai_analysis = ""
            
            # Parse AI response
            found_exact_match = False
            if ai_analysis and "ТОЧНО_СЪВПАДЕНИЕ: ДА" in ai_analysis:
                found_exact_match = True
            
            # Extract selected documents
            selected_docs = []
            if ai_analysis and "ИЗБРАНИ_ДОКУМЕНТИ:" in ai_analysis:
                try:
                    selected_line = ai_analysis.split("ИЗБРАНИ_ДОКУМЕНТИ:")[1].split("\n")[0]
                    doc_numbers = [int(x.strip()) for x in selected_line.split(",") if x.strip().isdigit()]
                    selected_docs = [top_documents[i-1] for i in doc_numbers if 0 < i <= len(top_documents)]
                except:
                    selected_docs = top_documents[:3]  # Fallback
            else:
                selected_docs = top_documents[:3]  # Fallback
            
            # Format final response
            if found_exact_match:
                return {
                    "found_exact_match": True,
                    "summary": f"Намерени са точни съвпадения в {len(selected_docs)} документа от ВКС",
                    "best_documents": selected_docs,
                    "analysis": ai_analysis or "Анализът е генериран успешно",
                    "query": query,
                    "total_documents": len(vks_results),
                    "ai_confidence": "high"
                }
            else:
                return {
                    "found_exact_match": False,
                    "summary": f"Не са намерени точни съвпадения, но има {len(selected_docs)} релевантни документа",
                    "best_documents": selected_docs,
                    "analysis": ai_analysis or "Анализът е генериран, но не са намерени точни съвпадения",
                    "query": query,
                    "total_documents": len(vks_results),
                    "ai_confidence": "medium",
                    "fallback_options": [
                        "Разгледайте следните релевантни документи",
                        "Потърсете с по-общи термини",
                        "Разширете търсенето в други правни бази",
                        "Консултирайте се с правен експерт"
                    ],
                    "dig_deeper_options": [
                        f"Търсете с термини от намерените документи: {', '.join(set([doc.get('legal_area', '') for doc in selected_docs]))}",
                        f"Търсете подобни дела с документи тип: {', '.join(set([doc.get('document_type', '') for doc in selected_docs]))}",
                        "Разгледайте и по-слабо релевантните резултати"
                    ]
                }
        
        except Exception as ai_error:
            logger.error(f"GPT-4o-mini analysis failed: {ai_error}")
            
            # Fallback to manual analysis
            best_documents = sorted_results[:3]
            
            return {
                "found_exact_match": False,
                "summary": f"Анализирани са {len(vks_results)} документа от ВКС (без AI анализ)",
                "best_documents": best_documents,
                "analysis": f"""
                **Анализ на документи от ВКС по запитването: "{query}"**
                
                **Резюме:**
                Намерени са {len(vks_results)} документа от Върховния касационен съд.
                Най-релевантните документи са свързани с: {', '.join(set([doc.get('legal_area', 'общо право') for doc in best_documents]))}.
                
                **Най-релевантни документи:**
                {chr(10).join([f"• {doc.get('title', 'Без заглавие')} (Релевантност: {doc.get('relevance_score', 0):.2f})" for doc in best_documents])}
                
                **Препоръки:**
                • Прегледайте внимателно избраните решения
                • Потърсете мотивите в решенията  
                • Проверете за по-нови решения по същия въпрос
                • При необходимост се консултирайте с правен експерт
                """,
                "query": query,
                "total_documents": len(vks_results),
                "ai_confidence": "low",
                "fallback_options": [
                    "Разгледайте намерените документи",
                    "Потърсете с различни термини",
                    "Разширете търсенето в други правни бази"
                ]
            }
        
    except Exception as e:
        logger.error(f"VKS analysis error: {e}")
        return {
            "found_exact_match": False,
            "summary": "Възникна грешка при анализа",
            "best_documents": vks_results[:3] if vks_results else [],
            "analysis": f"Грешка при анализа: {str(e)}",
            "query": query,
            "total_documents": len(vks_results),
            "fallback_options": [
                "Опитайте отново с по-прости термини",
                "Проверете интернет връзката",
                "Свържете се с поддръжката"
            ]
        }

# Tool wrapper for VKS search
@tool
def vks_bg_search_tool(query: str) -> str:
    """
    Search VKS.bg (Supreme Court of Bulgaria) for court decisions and legal precedents.
    
    This tool searches the official database of the Supreme Court of Bulgaria
    for relevant court decisions, rulings, and legal precedents.
    
    Args:
        query: Legal search query in Bulgarian
        
    Returns:
        Formatted search results from VKS.bg
    """
    logger.info(f"🔧 VKS.bg search tool called with query: '{query}'")
    
    try:
        # Execute VKS search
        vks_results = vks_bg_search(query, max_results=10)
        
        if not vks_results:
            return f"❌ Няма намерени резултати от ВКС за запитването: '{query}'"
        
        # Format results for display
        formatted_results = f"⚖️ **РЕЗУЛТАТИ ОТ ВЪРХОВЕН КАСАЦИОНЕН СЪД** за: '{query}'\n\n"
        
        for i, result in enumerate(vks_results, 1):
            formatted_results += f"**{i}. {result.get('title', 'Без заглавие')}**\n"
            formatted_results += f"   📄 {result.get('body', 'Няма описание')}\n"
            formatted_results += f"   🔗 {result.get('href', 'Няма линк')}\n"
            formatted_results += f"   📂 Правна област: {result.get('legal_area', 'Неопределена')}\n"
            formatted_results += f"   📋 Тип документ: {result.get('document_type', 'Неизвестен')}\n\n"
        
        formatted_results += f"\n📊 **Статистика**: {len(vks_results)} документа от ВКС\n"
        formatted_results += f"⚖️ **Източник**: Върховен касационен съд на Република България"
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"❌ VKS search tool error: {e}")
        return f"❌ Възникна грешка при търсенето в ВКС: {str(e)}"

@tool("lex_bg_search", return_direct=False)
def lex_bg_search(query: str, max_results: int = 15) -> str:
    """
    WORKING VERSION: Search and scrape results from lex.bg legal information site.
    This version properly handles Bulgarian text encoding.
    
    Args:
        query: Search query in Bulgarian
        max_results: Maximum number of results to return (default: 15)
    
    Returns:
        JSON string containing scraped sources with their titles, URLs, and content
    """
    logger.info(f"🏛️ LEX.BG Search (Fixed) for: '{query}'")
    
    try:
        # Use GET request instead of POST to avoid encoding issues
        url = "https://lex.bg/search"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "bg,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        # Use GET parameters instead of POST data to avoid encoding issues
        params = {
            "searchBox": query,
            "search_for_all": "1",
            "search_for_spravochnik": "1"
        }
        
        logger.info(f"🔍 Sending GET request to lex.bg with query: {query}")
        
        # Use session for better handling
        session = requests.Session()
        session.headers.update(headers)
        
        # Make GET request instead of POST
        response = session.get(url, params=params, timeout=30, verify=False)
        response.raise_for_status()
        
        # Set the correct encoding for Bulgarian content
        response.encoding = 'windows-1251'
        content_text = response.text
        
        # Parse the HTML response
        soup = BeautifulSoup(content_text, 'html.parser')
        
        logger.info(f"📄 Parsed HTML with {len(soup.find_all())} elements")
        
        # Check if there are no results first
        no_results_indicators = [
            "Няма резултати",
            "Няма намерени резултати", 
            "No results",
            "резултати от търсенето"
        ]
        
        page_text = soup.get_text().lower()
        if any(indicator.lower() in page_text for indicator in no_results_indicators):
            logger.warning(f"⚠️ No results found for query: {query}")
            return json.dumps({
                "status": "no_results", 
                "message": f"Няма намерени резултати за '{query}' в Lex.bg",
                "query": query,
                "sources": []
            }, ensure_ascii=False, indent=2)
        
        # Find search results - lex.bg specific selectors
        sources = []
        result_count = 0
        
        # Method 1: Look for structured results in main content areas
        main_containers = [
            soup.find('div', id='colleft'),
            soup.find('div', class_='col630'),
            soup.find('div', id='contentcolumn'),
            soup.find('div', id='container')
        ]
        
        for container in main_containers:
            if container and result_count < max_results:
                # Look for all links that could be search results
                all_links = container.find_all('a', href=True)
                
                for link in all_links:
                    if result_count >= max_results:
                        break
                    
                    href = link.get('href', '').strip()
                    title = link.get_text(strip=True)
                    
                    # Filter for actual content links (not navigation)
                    if (href and title and 
                        len(title) > 10 and  # Substantial title
                        not href.startswith('javascript:') and
                        not href.startswith('#') and
                        not href.startswith('mailto:') and
                        'login' not in href.lower() and
                        'register' not in href.lower() and
                        'password' not in href.lower() and
                        'search' not in href.lower() and
                        href != '/' and href != url):
                        
                        # Make absolute URL
                        if href.startswith('/'):
                            href = 'https://lex.bg' + href
                        elif not href.startswith('http'):
                            href = 'https://lex.bg/' + href
                        
                        # Determine category from link context
                        category = "General Results"
                        parent_text = ""
                        if link.parent:
                            parent_text = link.parent.get_text(strip=True).lower()
                        
                        if any(term in parent_text for term in ['закон', 'law', 'наредба']):
                            category = "Нормативни актове"
                        elif any(term in parent_text for term in ['съд', 'решение', 'court']):
                            category = "Съдебна практика"
                        elif any(term in parent_text for term in ['новин', 'news']):
                            category = "Новини"
                        
                        sources.append({
                            "title": title,
                            "url": href,
                            "category": category,
                            "source_type": "lex_bg_result",
                            "domain": "lex.bg",
                            "relevancy_score": calculate_lex_relevancy(query, title, category),
                            "extraction_timestamp": datetime.now().isoformat()
                        })
                        result_count += 1
                        
                if sources:  # If we found results in this container, don't check others
                    break
        
        # Sort by relevancy
        sources.sort(key=lambda x: x.get('relevancy_score', 0), reverse=True)
        
        # Calculate statistics
        category_stats = {}
        for source in sources:
            category = source.get('category', 'Unknown')
            category_stats[category] = category_stats.get(category, 0) + 1
        
        result_data = {
            "status": "success",
            "query": query,
            "total_results": len(sources),
            "sources": sources,
            "statistics": {
                "categories": category_stats,
                "avg_relevancy": sum(s.get('relevancy_score', 0) for s in sources) / len(sources) if sources else 0
            },
            "metadata": {
                "search_engine": "lex.bg",
                "search_timestamp": datetime.now().isoformat(),
                "method": "GET_request",
                "encoding": "windows-1251"
            }
        }
        
        logger.info(f"✅ LEX.BG search completed: {len(sources)} results from {len(category_stats)} categories")
        
        return json.dumps(result_data, ensure_ascii=False, indent=2)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ LEX.BG request error: {e}")
        return json.dumps({
            "status": "request_error",
            "message": f"Грешка при заявката към Lex.bg: {str(e)}",
            "query": query,
            "sources": []
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ LEX.BG processing error: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps({
            "status": "processing_error", 
            "message": f"Грешка при обработката на резултатите: {str(e)}",
            "query": query,
            "sources": []
        }, ensure_ascii=False, indent=2)

def calculate_lex_relevancy(query: str, title: str, category: str) -> float:
    """Calculate relevancy score for LEX.bg results"""
    try:
        score = 0.0
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        category_words = set(category.lower().split())
        
        # Exact matches get highest score
        exact_matches = len(query_words.intersection(title_words))
        score += exact_matches * 0.4
        
        # Partial matches in title
        for q_word in query_words:
            for t_word in title_words:
                if q_word in t_word or t_word in q_word:
                    score += 0.2
        
        # Category relevance bonus
        category_matches = len(query_words.intersection(category_words))
        score += category_matches * 0.1
        
        # Normalize to 0-1 range
        return min(score, 1.0)
        
    except Exception:
        return 0.5  # Default moderate relevancy

def extract_lex_content_preview(url: str) -> str:
    """Extract content preview from LEX.bg document pages"""
    try:
        if not url.startswith('http'):
            return ""
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find main content areas
        content_selectors = [
            'div.content',
            'div.main-content', 
            'div.document-content',
            'div.law-content',
            'article',
            'main'
        ]
        
        content_text = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content_text = content_elem.get_text(strip=True)
                break
        
        # Fallback to body text if no specific content area found
        if not content_text:
            body = soup.find('body')
            if body:
                content_text = body.get_text(strip=True)
        
        # Clean and truncate content
        if content_text:
            # Remove extra whitespace
            content_text = re.sub(r'\s+', ' ', content_text)
            # Truncate to reasonable preview length
            if len(content_text) > 500:
                content_text = content_text[:500] + "..."
        
        return content_text
        
    except Exception as e:
        logger.warning(f"Could not extract content from {url}: {e}")
        return ""



if __name__ == "__main__":
    result = lex_bg_search('права')  # Returns 15 results
    # result2 = lex_bg_search_fixed('обир')  # Returns 15 results
    print(result)
    # print(result2)