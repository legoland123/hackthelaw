"""
case_ranking.py - Advanced Legal Case Relevance Ranking System

This module implements a sophisticated multi-factor scoring model for ranking legal cases
based on statute matches, semantic similarity, court hierarchy, recency, and citation networks.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class CaseMetadata:
    """Structured case metadata for ranking"""
    title: str
    court: Optional[str]
    year: Optional[str]
    content: Optional[str]
    url: str
    snippet: str
    original_score: float = 0.0
    
    # Extracted features
    statute_references: Optional[List[str]] = field(default_factory=lambda: None)
    case_citations: Optional[List[str]] = field(default_factory=lambda: None)
    legal_concepts: Optional[List[str]] = field(default_factory=lambda: None)

@dataclass
class RankingScores:
    """Individual scoring components"""
    statute_match: float = 0.0
    keyword_similarity: float = 0.0
    court_hierarchy: float = 0.0
    recency: float = 0.0
    citation_network: float = 0.0
    final_score: float = 0.0

class LegalCaseRanker:
    """
    Advanced legal case ranking system using multi-factor scoring
    """
    
    def __init__(self):
        """Initialize the ranker with embedding model"""
        self.embedding_model = None
        self._initialize_embedding_model()
        
        # Scoring weights (tunable)
        self.weights = {
            'statute_match': 0.4,
            'keyword_similarity': 0.3,
            'court_hierarchy': 0.15,
            'recency': 0.1,
            'citation_network': 0.05
        }
        
        # Court hierarchy mapping (Singapore courts)
        self.court_hierarchy = {
            'court of appeal': 1.0,
            'high court': 0.8,
            'state courts': 0.6,
            'district court': 0.6,
            'magistrate court': 0.4,
            'family court': 0.5,
            'youth court': 0.4,
            'coroner court': 0.4,
            'tribunal': 0.3,
            'unknown': 0.2
        }
        
        # Legal concept keywords for enhanced matching
        self.legal_concepts = {
            'contract': ['contract', 'agreement', 'breach', 'consideration', 'offer', 'acceptance'],
            'tort': ['negligence', 'duty of care', 'damages', 'liability', 'tort'],
            'privacy': ['personal data', 'privacy', 'data protection', 'consent', 'disclosure'],
            'employment': ['employment', 'wrongful dismissal', 'discrimination', 'harassment'],
            'corporate': ['directors', 'shareholders', 'company', 'corporate governance'],
            'property': ['property', 'land', 'tenancy', 'lease', 'title']
        }
    
    def _initialize_embedding_model(self):
        """Initialize embedding model - simplified for now"""
        try:
            # For now, we'll use keyword-based similarity
            # In production, you could integrate with OpenAI embeddings or other services
            self.embedding_model = None
            logger.info("✅ Initialized keyword-based similarity (embedding model disabled)")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding model: {e}")
            self.embedding_model = None
    
    def rank_cases(
        self,
        cases: List[Dict],
        query: str,
        target_statutes: List[str] = None,
        query_facts: List[str] = None
    ) -> List[Dict]:
        """
        Rank cases using multi-factor scoring model
        
        Args:
            cases: List of case dictionaries
            query: Original search query
            target_statutes: List of relevant statutes to match against
            query_facts: List of factual elements from the query
            
        Returns:
            Ranked list of cases with scoring details
        """
        try:
            logger.info(f"🎯 Ranking {len(cases)} cases using multi-factor scoring")
            
            # Convert cases to structured metadata
            case_metadata = [self._extract_case_metadata(case) for case in cases]
            
            # Calculate scores for each case
            ranked_cases = []
            for i, metadata in enumerate(case_metadata):
                try:
                    scores = self._calculate_comprehensive_score(
                        metadata, query, target_statutes, query_facts
                    )
                    
                    # Add scoring information to the original case
                    enhanced_case = cases[i].copy()
                    enhanced_case.update({
                        'relevance_score': scores.final_score,
                        'scoring_breakdown': {
                            'statute_match': scores.statute_match,
                            'keyword_similarity': scores.keyword_similarity,
                            'court_hierarchy': scores.court_hierarchy,
                            'recency': scores.recency,
                            'citation_network': scores.citation_network
                        },
                        'ranking_metadata': {
                            'statute_references': metadata.statute_references or [],
                            'extracted_court': metadata.court,
                            'extracted_year': metadata.year,
                            'legal_concepts': metadata.legal_concepts or []
                        }
                    })
                    
                    ranked_cases.append(enhanced_case)
                    
                except Exception as e:
                    logger.warning(f"Failed to score case {i}: {e}")
                    # Keep original case with minimal scoring
                    enhanced_case = cases[i].copy()
                    enhanced_case['relevance_score'] = enhanced_case.get('relevance_score', 0.0)
                    ranked_cases.append(enhanced_case)
            
            # Sort by final relevance score
            ranked_cases.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
            
            logger.info(f"✅ Successfully ranked {len(ranked_cases)} cases")
            return ranked_cases
            
        except Exception as e:
            logger.error(f"Case ranking failed: {e}")
            # Return original cases if ranking fails
            return cases
    
    def _extract_case_metadata(self, case: Dict) -> CaseMetadata:
        """Extract structured metadata from case dictionary"""
        metadata = CaseMetadata(
            title=case.get('title', ''),
            court=case.get('court'),
            year=case.get('case_year'),
            content=case.get('full_content', ''),
            url=case.get('url', ''),
            snippet=case.get('snippet', ''),
            original_score=case.get('relevance_score', 0.0)
        )
        
        # Extract features
        text_content = f"{metadata.title} {metadata.content or metadata.snippet}"
        metadata.statute_references = self._extract_statute_references(text_content)
        metadata.case_citations = self._extract_case_citations(text_content)
        metadata.legal_concepts = self._extract_legal_concepts(text_content)
        
        return metadata
    
    def _calculate_comprehensive_score(
        self,
        metadata: CaseMetadata,
        query: str,
        target_statutes: List[str] = None,
        query_facts: List[str] = None
    ) -> RankingScores:
        """Calculate comprehensive relevance score using all factors"""
        
        scores = RankingScores()
        
        # 1. Statute Match Score (40% weight)
        scores.statute_match = self._calculate_statute_match_score(
            metadata, target_statutes or []
        )
        
        # 2. Keyword/Fact Similarity Score (30% weight)
        scores.keyword_similarity = self._calculate_similarity_score(
            metadata, query, query_facts or []
        )
        
        # 3. Court Hierarchy Score (15% weight)
        scores.court_hierarchy = self._calculate_court_hierarchy_score(metadata)
        
        # 4. Recency Score (10% weight)
        scores.recency = self._calculate_recency_score(metadata)
        
        # 5. Citation Network Score (5% weight)
        scores.citation_network = self._calculate_citation_network_score(metadata)
        
        # Calculate weighted final score
        scores.final_score = (
            self.weights['statute_match'] * scores.statute_match +
            self.weights['keyword_similarity'] * scores.keyword_similarity +
            self.weights['court_hierarchy'] * scores.court_hierarchy +
            self.weights['recency'] * scores.recency +
            self.weights['citation_network'] * scores.citation_network
        )
        
        return scores
    
    def _calculate_statute_match_score(
        self,
        metadata: CaseMetadata,
        target_statutes: List[str]
    ) -> float:
        """
        Calculate statute match score
        
        Exact section match = highest weight
        General statute mention = lower weight
        """
        if not target_statutes or not metadata.statute_references:
            return 0.0
        
        score = 0.0
        text_content = f"{metadata.title} {metadata.content or metadata.snippet}".lower()
        
        for target_statute in target_statutes:
            target_lower = target_statute.lower()
            
            # Check for exact section matches (e.g., "s 48O", "section 13")
            exact_match_patterns = [
                rf'\bs\s*\d+[a-z]*\s+{re.escape(target_lower)}',
                rf'section\s+\d+[a-z]*\s+{re.escape(target_lower)}',
                rf'{re.escape(target_lower)}\s+s\s*\d+[a-z]*',
                rf'{re.escape(target_lower)}\s+section\s+\d+[a-z]*'
            ]
            
            for pattern in exact_match_patterns:
                if re.search(pattern, text_content):
                    score += 1.0  # Highest score for exact section match
                    break
            else:
                # Check for general statute mention
                if target_lower in text_content:
                    score += 0.5  # Lower score for general mention
        
        # Normalize by number of target statutes
        return min(score / len(target_statutes), 1.0)
    
    def _calculate_similarity_score(
        self,
        metadata: CaseMetadata,
        query: str,
        query_facts: List[str]
    ) -> float:
        """
        Calculate keyword/fact similarity score using keyword matching
        """
        # Always use keyword matching for now
        return self._calculate_keyword_similarity_fallback(metadata, query, query_facts)
    
    def _calculate_keyword_similarity_fallback(
        self,
        metadata: CaseMetadata,
        query: str,
        query_facts: List[str]
    ) -> float:
        """Fallback keyword similarity calculation"""
        text_content = f"{metadata.title} {metadata.content or metadata.snippet}".lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # Check for query terms
        query_terms = query_lower.split()
        matching_terms = sum(1 for term in query_terms if term in text_content)
        if query_terms:
            score += (matching_terms / len(query_terms)) * 0.5
        
        # Check for factual elements
        if query_facts:
            matching_facts = sum(1 for fact in query_facts if fact.lower() in text_content)
            score += (matching_facts / len(query_facts)) * 0.5
        
        return min(score, 1.0)
    
    def _calculate_court_hierarchy_score(self, metadata: CaseMetadata) -> float:
        """
        Calculate court hierarchy score
        
        Singapore Court of Appeal (SGCA) > High Court > District Court
        """
        if not metadata.court:
            return self.court_hierarchy['unknown']
        
        court_lower = metadata.court.lower()
        
        for court_name, score in self.court_hierarchy.items():
            if court_name in court_lower:
                return score
        
        return self.court_hierarchy['unknown']
    
    def _calculate_recency_score(self, metadata: CaseMetadata) -> float:
        """
        Calculate recency score
        
        Newer cases often interpret amended statutes (important for PDPA)
        """
        if not metadata.year:
            return 0.0
        
        try:
            case_year = int(metadata.year)
            current_year = datetime.now().year
            
            # Cases from last 5 years get highest scores
            years_ago = current_year - case_year
            
            if years_ago <= 1:
                return 1.0
            elif years_ago <= 3:
                return 0.8
            elif years_ago <= 5:
                return 0.6
            elif years_ago <= 10:
                return 0.4
            else:
                return 0.2
                
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_citation_network_score(self, metadata: CaseMetadata) -> float:
        """
        Calculate citation network score
        
        Cases cited frequently in later decisions = more authoritative
        Note: This is a simplified implementation. In production, you'd want
        to maintain a citation database.
        """
        if not metadata.case_citations:
            return 0.0
        
        # Simple heuristic: more citations = more authoritative
        citation_count = len(metadata.case_citations)
        
        if citation_count >= 10:
            return 1.0
        elif citation_count >= 5:
            return 0.8
        elif citation_count >= 2:
            return 0.6
        elif citation_count >= 1:
            return 0.4
        else:
            return 0.0
    
    def _extract_statute_references(self, text: str) -> List[str]:
        """Extract statute references from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        statutes = []
        
        # Common Singapore statute patterns
        statute_patterns = [
            r'personal data protection act',
            r'companies act',
            r'partnership act',
            r'employment act',
            r'trade marks act',
            r'copyright act',
            r'criminal procedure code',
            r'penal code',
            r'evidence act'
        ]
        
        for pattern in statute_patterns:
            if re.search(pattern, text_lower):
                statutes.append(pattern.replace(r'\b', '').replace(r'\\b', '').title())
        
        return list(set(statutes))  # Remove duplicates
    
    def _extract_case_citations(self, text: str) -> List[str]:
        """Extract case citations from text"""
        if not text:
            return []
        
        # Singapore case citation patterns
        citation_patterns = [
            r'\[\d{4}\]\s+\w+\s+\d+',  # [2024] SGCA 15
            r'\[\d{4}\]\s+\d+\s+SLR\s+\d+',  # [2024] 1 SLR 123
            r'\(\d{4}\)\s+\d+\s+SLR\s+\d+'   # (2024) 1 SLR 123
        ]
        
        citations = []
        for pattern in citation_patterns:
            matches = re.findall(pattern, text)
            citations.extend(matches)
        
        return list(set(citations))  # Remove duplicates
    
    def _extract_legal_concepts(self, text: str) -> List[str]:
        """Extract legal concepts from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        concepts = []
        
        for concept_category, keywords in self.legal_concepts.items():
            for keyword in keywords:
                if keyword in text_lower:
                    concepts.append(concept_category)
                    break  # Only add category once
        
        return concepts


# Utility functions for integration with existing code

def rank_elitigation_cases(
    cases: List[Dict],
    query: str,
    target_statutes: List[str] = None,
    query_facts: List[str] = None
) -> List[Dict]:
    """
    Main function to rank eLitigation cases using the advanced scoring system
    
    Args:
        cases: List of case dictionaries from eLitigation search
        query: Original search query
        target_statutes: List of relevant statutes to match against
        query_facts: List of factual elements from the query
        
    Returns:
        Ranked list of cases with detailed scoring
    """
    ranker = LegalCaseRanker()
    return ranker.rank_cases(cases, query, target_statutes, query_facts)

def extract_query_facts(query: str) -> List[str]:
    """
    Extract factual elements from a legal query
    
    Args:
        query: Legal query string
        
    Returns:
        List of extracted factual elements
    """
    # Simple fact extraction - can be enhanced with NER
    fact_indicators = [
        'emotional distress',
        'personal data',
        'without consent',
        'advertising',
        'breach of contract',
        'negligence',
        'damages',
        'compensation'
    ]
    
    query_lower = query.lower()
    facts = [fact for fact in fact_indicators if fact in query_lower]
    
    return facts
