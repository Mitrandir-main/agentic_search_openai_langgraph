"""
Enhanced Legal Research Tools for Bulgarian Law
Specialized tools for searching Bulgarian legal databases with citation extraction
"""

import requests
from langchain.tools import tool
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
import time
import logging
from dotenv import load_dotenv
from bulgarian_legal_domains import BULGARIAN_LEGAL_DOMAINS

load_dotenv()

# API Configuration
GOOGLE_CSE_API_KEY = os.getenv('GOOGLE_CSE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def google_cse_search_legal(query: str, site_search: str = None, country: str = "bg", language: str = "lang_bg", num_results: int = 8) -> List[Dict]:
    """
    Legal-focused Google Custom Search Engine with domain targeting.
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("Google CSE not configured, falling back to DuckDuckGo")
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
            logger.warning(f"No Google CSE results for {query}")
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
        
        logger.info(f"Google CSE legal search returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Google CSE legal search error: {e}")
        return fallback_ddg_search(query, site_search)

def fallback_ddg_search(query: str, site_search: str = None) -> List[Dict]:
    """
    Fallback DuckDuckGo search for legal content.
    """
    try:
        search_query = query
        if site_search:
            search_query = f"site:{site_search} {query}"
        
        search_query += " закон право юридически"
        
        with DDGS() as ddgs:
            results = []
            ddg_results = ddgs.text(search_query, max_results=8, region='bg-bg')
            
            for result in ddg_results:
                formatted_result = {
                    'title': result.get('title', 'No Title'),
                    'href': result.get('href', 'No URL'),
                    'body': result.get('body', 'No Description'),
                    'source_domain': site_search if site_search else 'DuckDuckGo Legal Search'
                }
                results.append(formatted_result)
            
            logger.info(f"DuckDuckGo fallback returned {len(results)} results")
            return results
            
    except Exception as e:
        logger.error(f"DuckDuckGo fallback error: {e}")
        return []

@tool("bulgarian_legal_search", return_direct=False)
def bulgarian_legal_search(query: str, specific_domain: str = None) -> str:
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
def legal_precedent_search(legal_issue: str, court_level: str = "all") -> str:
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
            return f"Грешка при търсене на precedents: No results found"
            
    except Exception as e:
        logger.error(f"Precedent search error: {e}")
        return f"Грешка при търсене на precedents: {str(e)}"

@tool("legal_citation_extractor", return_direct=False)
def legal_citation_extractor(text: str) -> str:
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
def legal_area_classifier(query: str) -> str:
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
def legal_document_analyzer(document_url: str) -> str:
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
        legal_citation_extractor
    ] 