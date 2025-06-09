#!/usr/bin/env python3
"""
Advanced Relevancy Scoring and Ranking System for Bulgarian Legal Research
Implements state-of-the-art relevancy scoring algorithms inspired by modern agentic search systems
"""

import os
import re
import math
import logging
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with comprehensive scoring"""
    url: str
    title: str
    snippet: str
    content: str = ""
    domain: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Scoring components
    bm25_score: float = 0.0
    semantic_score: float = 0.0
    title_relevance: float = 0.0
    domain_authority: float = 0.0
    content_quality: float = 0.0
    freshness_score: float = 0.0
    
    # Final scores
    hybrid_score: float = 0.0
    relevancy_probability: float = 0.0
    confidence_score: float = 0.0
    
    # New: Legal context relevance
    legal_context_score: float = 0.0
    combined_score: float = 0.0
    
    # Legal classification
    legal_domain: str = "unknown"
    legal_relevance: float = 0.0
    
    def __post_init__(self):
        """Extract domain from URL"""
        if not self.domain and self.url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                self.domain = parsed.netloc.lower()
            except:
                self.domain = "unknown"

class BulgarianLegalRelevancyScorer:
    """
    Enhanced relevancy scorer specifically designed for Bulgarian legal content
    with context-aware scoring and domain understanding.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_client = None
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized for semantic scoring")
            except Exception as e:
                logger.warning(f"OpenAI client initialization failed: {e}")
        
        # Bulgarian legal domain definitions
        self.legal_domains = {
            'гражданско_право': {
                'keywords': ['обезщетение', 'договор', 'собственост', 'наследство', 'семейство', 'развод', 'алименти', 'данъци'],
                'weight': 1.0,
                'description': 'Civil Law'
            },
            'наказателно_право': {
                'keywords': ['престъпление', 'наказание', 'затвор', 'глоба', 'убийство', 'кража', 'измама', 'дрога'],
                'weight': 1.0,
                'description': 'Criminal Law'
            },
            'административно_право': {
                'keywords': ['административен', 'лиценз', 'разрешение', 'наредба', 'постановление', 'министерство', 'регулация'],
                'weight': 0.6,  # Lower weight as often less relevant to personal legal issues
                'description': 'Administrative Law'
            },
            'трудово_право': {
                'keywords': ['работа', 'трудов', 'заплата', 'отпуска', 'уволнение', 'договор', 'осигуровка', 'пенсия'],
                'weight': 1.0,
                'description': 'Labor Law'
            },
            'процесуално_право': {
                'keywords': ['съд', 'дело', 'процес', 'съдебен', 'апелация', 'касация', 'решение', 'призовка'],
                'weight': 0.9,
                'description': 'Procedural Law'
            },
            'медицинско_право': {
                'keywords': ['медицински', 'лечение', 'болница', 'лекар', 'здравеопазване', 'увреждане', 'инвалидност'],
                'weight': 1.0,
                'description': 'Medical Law'
            }
        }
        
        # Domain authority scores for Bulgarian legal sites
        self.domain_authority = {
            'ciela.net': 0.95,
            'apis.bg': 0.90,
            'lakorda.com': 0.75,
            'justice.government.bg': 0.85,
            'vks.bg': 0.80,
            'vss.bg': 0.80
        }
        
        # Enhanced BM25 parameters optimized for legal content
        self.bm25_k1 = 1.8  # Slightly higher term frequency saturation for legal documents
        self.bm25_b = 0.7   # Document length normalization
        
        # Weights for final scoring
        self.scoring_weights = {
            'bm25': 0.30,           # Lexical matching
            'semantic': 0.25,       # Semantic similarity
            'legal_context': 0.25,  # Legal domain relevance
            'domain_authority': 0.10, # Source credibility
            'title_boost': 0.10     # Title relevance boost
        }
        
        # Initialize TF-IDF vectorizer for legal content - FIXED FOR SMALL DOCUMENT COLLECTIONS
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words=None,  # Keep legal stop words for Bulgarian
            ngram_range=(1, 2),
            min_df=1,  # Allow terms that appear in just 1 document (fixes small collection issues)
            max_df=0.95  # Be more generous with common terms
        )
        
        logger.info("Bulgarian Legal Relevancy Scorer initialized")

    def identify_legal_domain(self, text: str) -> Tuple[str, float]:
        """
        Identify the most relevant legal domain for the given text.
        Returns domain name and confidence score.
        """
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, config in self.legal_domains.items():
            score = 0.0
            keyword_matches = 0
            
            for keyword in config['keywords']:
                if keyword in text_lower:
                    # Count occurrences with diminishing returns
                    occurrences = text_lower.count(keyword)
                    score += math.log(1 + occurrences) * config['weight']
                    keyword_matches += 1
            
            # Bonus for multiple keyword matches in same domain
            if keyword_matches > 1:
                score *= (1 + 0.1 * keyword_matches)
            
            domain_scores[domain] = score
        
        if not domain_scores or max(domain_scores.values()) == 0:
            return 'unknown', 0.0
        
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = min(domain_scores[best_domain] / 10.0, 1.0)  # Normalize to 0-1
        
        return best_domain, confidence

    def preprocess_query(self, query: str) -> str:
        """
        Enhanced query preprocessing for Bulgarian legal queries.
        """
        # Common typo corrections for Bulgarian legal terms
        corrections = {
            'обещетение': 'обезщетение',
            'насказание': 'наказание',
            'същта': 'същата',
            'връка': 'връзка',
            'амога': 'мога',
            'намам': 'нямам'
        }
        
        processed = query.lower()
        for typo, correction in corrections.items():
            processed = processed.replace(typo, correction)
        
        # Expand common legal abbreviations
        expansions = {
            'гк': 'граждански кодекс',
            'нк': 'наказателен кодекс',
            'апк': 'административнопроцесуален кодекс',
            'тк': 'трудов кодекс'
        }
        
        for abbrev, expansion in expansions.items():
            processed = re.sub(r'\b' + abbrev + r'\b', expansion, processed)
        
        return processed

    def calculate_bm25_score(self, query_terms: List[str], document_text: str, 
                           avg_doc_length: float = 1000) -> float:
        """
        Calculate BM25 score with legal content optimization.
        """
        doc_terms = document_text.lower().split()
        doc_length = len(doc_terms)
        term_freq = Counter(doc_terms)
        
        score = 0.0
        for term in query_terms:
            tf = term_freq.get(term.lower(), 0)
            if tf > 0:
                # BM25 formula
                idf = math.log((1 + avg_doc_length) / (1 + tf))
                numerator = tf * (self.bm25_k1 + 1)
                denominator = tf + self.bm25_k1 * (1 - self.bm25_b + self.bm25_b * (doc_length / avg_doc_length))
                score += idf * (numerator / denominator)
        
        return score

    def calculate_semantic_similarity(self, query: str, document_text: str) -> float:
        """
        Calculate semantic similarity using OpenAI embeddings if available,
        otherwise fall back to TF-IDF cosine similarity.
        """
        if self.openai_client:
            try:
                # Get embeddings for query and document
                query_embedding = self._get_embedding(query)
                doc_embedding = self._get_embedding(document_text[:1500])  # Limit doc length
                
                if query_embedding and doc_embedding:
                    # Calculate cosine similarity
                    query_array = np.array(query_embedding)
                    doc_array = np.array(doc_embedding)
                    
                    dot_product = np.dot(query_array, doc_array)
                    norm_product = np.linalg.norm(query_array) * np.linalg.norm(doc_array)
                    
                    if norm_product > 0:
                        return dot_product / norm_product
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}")
        
        # Fallback to TF-IDF similarity - IMPROVED ERROR HANDLING
        try:
            # Create a fresh vectorizer for this pair to avoid collection size issues
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,  # Must work with just 2 documents
                max_df=1.0,  # Allow all terms in small collections
                lowercase=True
            )
            tfidf_matrix = vectorizer.fit_transform([query, document_text])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return similarity
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            # Simple word overlap fallback
            query_words = set(query.lower().split())
            doc_words = set(document_text.lower().split())
            if query_words and doc_words:
                overlap = len(query_words.intersection(doc_words))
                return min(overlap / len(query_words), 1.0)
            return 0.0

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get OpenAI embedding for text."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
            return None

    def calculate_domain_authority(self, url: str) -> float:
        """Calculate domain authority score based on URL."""
        for domain, score in self.domain_authority.items():
            if domain in url:
                return score
        return 0.5  # Default score for unknown domains

    def calculate_legal_context_score(self, query: str, document_text: str) -> float:
        """
        Calculate how well the document matches the legal context of the query.
        """
        query_domain, query_confidence = self.identify_legal_domain(query)
        doc_domain, doc_confidence = self.identify_legal_domain(document_text)
        
        # If both are in the same legal domain, high score
        if query_domain == doc_domain and query_domain != 'unknown':
            return min(query_confidence * doc_confidence * 2, 1.0)
        
        # If query is about personal legal issues but doc is administrative law
        personal_legal_domains = ['гражданско_право', 'наказателно_право', 'трудово_право', 'медицинско_право']
        
        if (query_domain in personal_legal_domains and 
            doc_domain == 'административно_право'):
            return 0.2  # Very low relevance
        
        # If one is unknown but the other is legal content
        if query_domain == 'unknown' and doc_domain != 'unknown':
            return doc_confidence * 0.6
        
        if query_domain != 'unknown' and doc_domain == 'unknown':
            return query_confidence * 0.4
        
        # Both unknown
        return 0.3

    def score_and_rank(self, query: str, search_results: List[SearchResult]) -> List[SearchResult]:
        """
        Score and rank search results using the enhanced Bulgarian legal scoring system.
        """
        if not search_results:
            return []
        
        # Preprocess query
        processed_query = self.preprocess_query(query)
        query_terms = processed_query.split()
        
        # Calculate average document length for BM25
        total_length = sum(len((result.content or result.snippet).split()) for result in search_results)
        avg_doc_length = total_length / len(search_results) if search_results else 1000
        
        scored_results = []
        
        for result in search_results:
            # Combine content for analysis
            full_text = f"{result.title} {result.snippet} {result.content}"
            
            # Calculate individual scores
            bm25_score = self.calculate_bm25_score(query_terms, full_text, avg_doc_length)
            semantic_score = self.calculate_semantic_similarity(processed_query, full_text)
            legal_context_score = self.calculate_legal_context_score(processed_query, full_text)
            domain_authority_score = self.calculate_domain_authority(result.url)
            
            # Title boost - higher weight if query terms appear in title
            title_boost = 0.0
            title_lower = result.title.lower()
            for term in query_terms:
                if term in title_lower:
                    title_boost += 0.1
            title_boost = min(title_boost, 0.5)
            
            # Normalize scores to 0-1 range
            bm25_normalized = min(bm25_score / 10.0, 1.0)  # Adjust divisor based on your data
            semantic_normalized = semantic_score
            legal_context_normalized = legal_context_score
            domain_authority_normalized = domain_authority_score
            title_boost_normalized = title_boost
            
            # Calculate combined score
            combined_score = (
                self.scoring_weights['bm25'] * bm25_normalized +
                self.scoring_weights['semantic'] * semantic_normalized +
                self.scoring_weights['legal_context'] * legal_context_normalized +
                self.scoring_weights['domain_authority'] * domain_authority_normalized +
                self.scoring_weights['title_boost'] * title_boost_normalized
            )
            
            # Identify legal domain
            legal_domain, legal_relevance = self.identify_legal_domain(full_text)
            
            # Update result with scores
            result.bm25_score = bm25_score
            result.semantic_score = semantic_score
            result.legal_context_score = legal_context_score
            result.domain_authority_score = domain_authority_score
            result.combined_score = combined_score
            result.relevancy_probability = combined_score
            result.legal_domain = legal_domain
            result.legal_relevance = legal_relevance
            
            # Calculate confidence based on score distribution
            result.confidence_score = min(combined_score * 1.2, 1.0)
            
            scored_results.append(result)
        
        # Sort by combined score (highest first)
        scored_results.sort(key=lambda x: x.combined_score, reverse=True)
        
        logger.info(f"Scored {len(scored_results)} results. Top score: {scored_results[0].combined_score:.3f}")
        
        return scored_results

    def explain_scoring(self, result: SearchResult, query: str) -> str:
        """
        Provide human-readable explanation of the scoring.
        """
        explanation = f"""
Scoring Breakdown for: {result.title[:50]}...

BM25 Score: {result.bm25_score:.3f} (Lexical matching)
Semantic Score: {result.semantic_score:.3f} (Semantic similarity)
Legal Context Score: {result.legal_context_score:.3f} (Legal domain relevance)
Domain Authority: {result.domain_authority_score:.3f} (Source credibility)
Legal Domain: {result.legal_domain} (Confidence: {result.legal_relevance:.2f})

Combined Score: {result.combined_score:.3f}
Overall Confidence: {result.confidence_score:.3f}
        """
        return explanation.strip()

# For backward compatibility
class AdvancedRelevancyScorer(BulgarianLegalRelevancyScorer):
    """Backward compatibility class"""
    pass 