"""
elitigation_search.py - eLitigation case search service
"""

import json
import logging
import os
from datetime import datetime
from pydoc import cli
from typing import List, Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from tavily import TavilyClient
import asyncio

logger = logging.getLogger(__name__)

class ELitigationSearchRequest(BaseModel):
    names: List[str]  # List of names to search for (e.g., ["Companies Act", "Partnership Act"])
    max_results: Optional[int] = 5  # Maximum number of cases to return
    user_id: Optional[str] = "anonymous"

class ELitigationCaseResult(BaseModel):
    title: str
    url: str
    snippet: str
    relevance_score: float
    case_year: Optional[str] = None
    court: Optional[str] = None
    full_content: Optional[str] = None  # Add field for scraped content

class ELitigationEnhancedRequest(BaseModel):
    names: List[str]  # List of names to search for
    max_results: Optional[int] = 5  # Maximum number of cases to return
    scrape_content: Optional[bool] = True  # Whether to scrape full case content
    user_id: Optional[str] = "anonymous"

def search_elitigation_cases(request: ELitigationSearchRequest) -> Dict:
    """
    Search for cases on eLitigation using a list of names
    
    Args:
        request: Search request containing list of names to search for
        
    Returns:
        JSON response with list of relevant cases
    """
    try:
        # Validate input
        if not request.names or len(request.names) == 0:
            raise HTTPException(status_code=400, detail="Names list cannot be empty")
        
        # Filter out empty/short names
        valid_names = [name.strip() for name in request.names if name and len(name.strip()) >= 3]
        if not valid_names:
            raise HTTPException(status_code=400, detail="No valid names provided (minimum 3 characters each)")
        
        max_results = min(request.max_results or 5, 10)  # Cap at 10 results
        
        logger.info(f"🏛️ Searching eLitigation for cases related to: {', '.join(valid_names)}")
        
        # Initialize Tavily client
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            client = TavilyClient(tavily_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            raise HTTPException(status_code=500, detail="Search service unavailable")
        
        # Search for each name and collect all results
        all_cases = []
        search_queries = []
        
        for name in valid_names:
            # Build search query for this name
            search_query = _build_elitigation_search_query(name)
            search_queries.append(search_query)
            
            # Search using Tavily with focus on eLitigation and Singapore court websites
            try:
                response = client.search(
                    query=search_query,
                    search_depth="advanced",
                    max_results=max_results,  
                    include_domains=["elitigation.sg"]
                )
                
                # Process and rank results for this name
                cases = _process_elitigation_results(response.get('results', []), name)
                all_cases.extend(cases)
                
            except Exception as e:
                logger.warning(f"Tavily search failed for '{name}': {e}")
                continue
        
        # Remove duplicates based on URL and sort by relevance
        unique_cases = {}
        for case in all_cases:
            if case.url not in unique_cases or case.relevance_score > unique_cases[case.url].relevance_score:
                unique_cases[case.url] = case
        
        final_cases = list(unique_cases.values())
        final_cases.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Return top results
        top_cases = final_cases[:max_results]
        
        return {
            "status": "success",
            "search_names": valid_names,
            "search_queries": search_queries,
            "total_found": len(final_cases),
            "total_returned": len(top_cases),
            "cases": [case.dict() for case in top_cases],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"eLitigation search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def scrape_case_content(url: str, client: TavilyClient) -> Optional[str]:
    """
    Scrape full content from an eLitigation case URL using Tavily
    
    Args:
        url: Case URL to scrape
        client: Tavily client instance
        
    Returns:
        Scraped content or None if failed
    """
    try:
        logger.info(f"📄 Scraping case content from: {url}")
        
        # remove pdf / from url or ends with /pdf
        if '/pdf/' in url or url.endswith('.pdf') or url.endswith('/pdf'):
            # remove the pdf part
            url = url.split('/pdf')[0]
            url = url.rstrip('/')

        # Use Tavily to extract content from the specific URL, only for that page
        response = client.crawl(url=url, max_breadth=1)['results']
        
        
        if response and len(response) > 0:
            content = response[0].get('raw_content', '')
            if content:
                # Clean and truncate content (limit to ~5000 chars for LLM context)
                cleaned_content = _clean_case_content(content)
                return cleaned_content[:5000] + "..." if len(cleaned_content) > 5000 else cleaned_content
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to scrape content from {url}: {e}")
        return None

def _clean_case_content(content: str) -> str:
    """
    Clean scraped case content for better LLM processing
    
    Args:
        content: Raw scraped content
        
    Returns:
        Cleaned content
    """
    import re
    
    # Remove excessive whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Remove common navigation/UI elements
    content = re.sub(r'(Skip to main content|Navigation|Menu|Footer|Copyright)', '', content, flags=re.IGNORECASE)
    
    # Focus on judgment content - look for common legal document patterns
    patterns_to_keep = [
        r'JUDGMENT.*?(?=JUDGMENT|$)',
        r'GROUNDS OF DECISION.*?(?=GROUNDS OF DECISION|$)',
        r'COURT OF APPEAL.*?(?=COURT OF APPEAL|$)',
        r'HIGH COURT.*?(?=HIGH COURT|$)',
    ]
    
    # Try to extract main judgment content
    for pattern in patterns_to_keep:
        match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
        if match and len(match.group()) > 500:  # Only use if substantial content
            content = match.group()
            break
    
    return content.strip()

def search_and_scrape_elitigation_cases(request: ELitigationEnhancedRequest) -> Dict:
    """
    Enhanced eLitigation search that includes full case content scraping
    
    Args:
        request: Enhanced search request with scraping option
        
    Returns:
        JSON response with cases including full content if requested
    """
    try:
        # Validate input
        if not request.names or len(request.names) == 0:
            raise HTTPException(status_code=400, detail="Names list cannot be empty")
        
        # Filter out empty/short names
        valid_names = [name.strip() for name in request.names if name and len(name.strip()) >= 3]
        if not valid_names:
            raise HTTPException(status_code=400, detail="No valid names provided (minimum 3 characters each)")
        
        logger.info(f"🏛️ Enhanced eLitigation search for: {', '.join(valid_names)} (scrape_content: {request.scrape_content})")
        
        # Initialize Tavily client
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            client = TavilyClient(tavily_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            raise HTTPException(status_code=500, detail="Search service unavailable")
        
        # First, get the basic search results
        basic_request = ELitigationSearchRequest(
            names=request.names,
            max_results=request.max_results,
            user_id=request.user_id
        )
        
        # Use the existing search function to get initial results
        if True: # hackathon override
            # sleep awhile and log
            logger.info("⏳ Simulating initial search delay...")
            asyncio.sleep(1)  # Simulate delay
            initial_results = json.load(open("legal_services/elitigation_initial_results.json"))
        else:
            initial_results = search_elitigation_cases(basic_request)

        if initial_results.get('status') != 'success' or not initial_results.get('cases'):
            return initial_results
        
        # If scraping is requested, enhance with full content
        enhanced_cases = []
        if request.scrape_content:
            logger.info(f"📄 Scraping content for {len(initial_results['cases'])} cases")
            
            # Scrape content for each case synchronously
            for case_data in initial_results['cases']:
                case = ELitigationCaseResult(**case_data)
                full_content = scrape_case_content(case.url, client)
                case.full_content = full_content
                enhanced_cases.append(case)
            
        else:
            # Convert to enhanced format without scraping
            enhanced_cases = [ELitigationCaseResult(**case) for case in initial_results['cases']]
        
        return {
            "status": "success",
            "search_names": valid_names,
            "total_found": len(enhanced_cases),
            "total_returned": len(enhanced_cases),
            "content_scraped": request.scrape_content,
            "cases": [case.dict() for case in enhanced_cases],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced eLitigation search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _build_elitigation_search_query(name: str) -> str:
    """
    Build search query for eLitigation case search
    
    Args:
        name: Name to search for (statute, act, regulation, etc.)
        
    Returns:
        Formatted search query string
    """
    # Base query with the name
    query_parts = [f'"{name}"']
    
    # Add Singapore legal context
    query_parts.extend([
        "Singapore",
        "case law",
        "judgment",
        "court decision"
    ])
    
    return " ".join(query_parts)

def _process_elitigation_results(results: List[Dict], search_name: str) -> List[ELitigationCaseResult]:
    """
    Process and rank eLitigation search results
    
    Args:
        results: Raw search results from Tavily
        search_name: Original search name for relevance scoring
        
    Returns:
        List of processed and ranked case results
    """
    processed_cases = []
    
    for result in results:
        try:
            # Extract basic information
            title = result.get('title', '').strip()
            url = result.get('url', '').strip()
            content = result.get('content', '').strip()
            score = result.get('score', 0.0)
            
            # Skip if missing essential information
            if not title or not url or not content:
                continue
            
            # Create snippet (first 200 characters of content)
            snippet = _create_snippet(content, search_name)
            
            # Calculate relevance score
            relevance_score = _calculate_relevance_score(title, content, search_name, score)
            
            # Extract additional case information
            case_year = _extract_case_year(title, content)
            court = _extract_court_info(title, content, url)
            
            # Create case result
            case = ELitigationCaseResult(
                title=title,
                url=url,
                snippet=snippet,
                relevance_score=relevance_score,
                case_year=case_year,
                court=court
            )
            
            processed_cases.append(case)
            
        except Exception as e:
            logger.warning(f"Failed to process result: {e}")
            continue
    
    # Sort by relevance score (highest first)
    processed_cases.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return processed_cases

def _create_snippet(content: str, search_name: str) -> str:
    """
    Create a relevant snippet from the content
    
    Args:
        content: Full content text
        search_name: Search name to highlight context around
        
    Returns:
        Relevant snippet (max 200 characters)
    """
    content_lower = content.lower()
    search_name_lower = search_name.lower()
    
    # Try to find context around the search name
    name_pos = content_lower.find(search_name_lower)
    
    if name_pos != -1:
        # Extract context around the found position
        start = max(0, name_pos - 50)
        end = min(len(content), name_pos + 150)
        snippet = content[start:end].strip()
        
        # Clean up snippet
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
    else:
        # No specific match found, use beginning of content
        snippet = content[:200].strip()
        if len(content) > 200:
            snippet += "..."
    
    return snippet

def _calculate_relevance_score(title: str, content: str, search_name: str, base_score: float) -> float:
    """
    Calculate relevance score for a case result
    
    Args:
        title: Case title
        content: Case content
        search_name: Target search name
        base_score: Base score from search engine
        
    Returns:
        Calculated relevance score (0.0 to 1.0)
    """
    score = base_score
    
    title_lower = title.lower()
    content_lower = content.lower()
    search_name_lower = search_name.lower()
    
    # Boost for search name in title
    if search_name_lower in title_lower:
        score += 0.3
    
    # Boost for search name in content
    name_count = content_lower.count(search_name_lower)
    score += min(name_count * 0.1, 0.2)
    
    # Boost for legal keywords
    legal_keywords = ['judgment', 'court', 'decision', 'ruling', 'appeal', 'high court', 'supreme court']
    for keyword in legal_keywords:
        if keyword in title_lower or keyword in content_lower:
            score += 0.05
    
    # Boost for eLitigation domain
    if 'elitigation.sg' in title_lower or 'elitigation.sg' in content_lower:
        score += 0.2
    
    # Normalize score to 0.0-1.0 range
    return min(score, 1.0)

def _extract_case_year(title: str, content: str) -> Optional[str]:
    """
    Extract case year from title or content
    
    Args:
        title: Case title
        content: Case content
        
    Returns:
        Extracted year string or None
    """
    import re
    
    # Look for year patterns in title first
    year_pattern = r'\b(19|20)\d{2}\b'
    
    # Check title
    title_match = re.search(year_pattern, title)
    if title_match:
        return title_match.group()
    
    # Check content (first occurrence)
    content_match = re.search(year_pattern, content)
    if content_match:
        return content_match.group()
    
    return None

def _extract_court_info(title: str, content: str, url: str) -> Optional[str]:
    """
    Extract court information from title, content, or URL
    
    Args:
        title: Case title
        content: Case content
        url: Case URL
        
    Returns:
        Extracted court name or None
    """
    import re
    
    text_to_search = f"{title} {content} {url}".lower()
    
    # Define court patterns
    court_patterns = [
        r'high court',
        r'supreme court',
        r'court of appeal',
        r'district court',
        r'magistrate[\'s]? court',
        r'family court',
        r'state court',
        r'tribunal'
    ]
    
    for pattern in court_patterns:
        match = re.search(pattern, text_to_search)
        if match:
            return match.group().title()
    
    return None
