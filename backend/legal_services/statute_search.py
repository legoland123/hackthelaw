"""
statute_search.py - Legal statute search and amendment services
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import HTTPException
from pydantic import BaseModel
from tavily import TavilyClient


from legal_memory.llm_processor import LLMProcessor
from firebase.db import get_firestore_db

logger = logging.getLogger(__name__)

class StatutesSearchRequest(BaseModel):
    message: str  # The query/question about statutes
    project_context: Optional[Dict] = None  # Project context with document content (textbooks)
    user_id: Optional[str] = "anonymous"
    max_statutes: Optional[int] = 10  # Maximum number of statutes to return

class AmendmentSearchRequest(BaseModel):
    statutes: List[str]  # List of statute names to check for amendments
    user_id: Optional[str] = "anonymous"
    max_results_per_statute: Optional[int] = 5  # Maximum search results per statute

async def find_relevant_statutes(request: StatutesSearchRequest):
    """
    Find relevant statutes based on query and document context using LLM
    """
    try:
        # Validate input
        if not request.message or len(request.message.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query too short")
        
        query = request.message.strip()
        max_statutes = min(request.max_statutes or 10, 20)  # Cap at 20 statutes
        
        logger.info(f"🏛️ Searching for relevant statutes for query: {query}")
        
        # Initialize LLM processor
        try:
            llm_processor = LLMProcessor()
        except ValueError as e:
            logger.error(f"LLM Processor initialization failed: {e}")
            raise HTTPException(status_code=500, detail="AI service unavailable")
        
        # Create context for statute search
        statute_context = _create_statutes_search_context(query, request.project_context, max_statutes)
        
        # Generate response using LLM
        try:
            response = await llm_processor._generate_with_retry(statute_context)
            
            # Parse the JSON response
            try:
                statutes_data = json.loads(response)
                
                # Validate the response structure
                if not isinstance(statutes_data, dict) or 'statutes' not in statutes_data:
                    raise ValueError("Invalid response structure")
                
                # Ensure statutes is a list
                if not isinstance(statutes_data['statutes'], list):
                    statutes_data['statutes'] = []
                
                # Store search history if user_id is provided
                if request.user_id and request.user_id != "anonymous":
                    try:
                        db = get_firestore_db()
                        db.store_search_history(
                            request.user_id, 
                            query, 
                            "statutes_search", 
                            len(statutes_data.get('statutes', []))
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store statute search history: {e}")
                
                return {
                    "status": "success",
                    "query": query,
                    "total_statutes": len(statutes_data.get('statutes', [])),
                    "statutes": statutes_data.get('statutes', []),
                    "reasoning": statutes_data.get('reasoning', ''),
                    "timestamp": datetime.now().isoformat()
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response}")
                raise HTTPException(status_code=500, detail="Failed to parse statute search results")
            except ValueError as e:
                logger.error(f"Invalid response structure: {e}")
                raise HTTPException(status_code=500, detail="Invalid statute search response format")
            
        except Exception as e:
            logger.error(f"Statute search generation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate statute search results")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Statute search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def search_amendment(request: AmendmentSearchRequest):
    """
    Search for amendments to specified statutes using Tavily
    """
    try:
        # Validate input
        if not request.statutes or len(request.statutes) == 0:
            raise HTTPException(status_code=400, detail="At least one statute must be provided")
        
        max_results_per_statute = min(request.max_results_per_statute or 5, 10)  # Cap at 10 results per statute
        
        logger.info(f"🔍 Searching for amendments to {len(request.statutes)} statutes")
        
        # Initialize Tavily client
        try:
            # Get Tavily API key from environment
            import os
            tavily_api_key = os.getenv("TAVILY_API_KEY", "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")
            client = TavilyClient(tavily_api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            raise HTTPException(status_code=500, detail="Search service unavailable")
        
        amendment_results = []
        
        for statute in request.statutes:
            try:
                # Create search query for amendments
                search_query = f"Singapore {statute} amendment changed updated recent"
                
                logger.info(f"Searching for amendments to: {statute}")
                
                # Search using Tavily
                response = client.search(
                    query=search_query,
                    search_depth="advanced",
                    max_results=max_results_per_statute,
                    include_domains=["mlaw.gov.sg", "sso.agc.gov.sg", "parliament.gov.sg", "lawnet.sg"],
                    exclude_domains=["wikipedia.org", "reddit.com"]
                )
                
                # Process and structure the results
                search_results = []
                for result in response.get('results', []):
                    search_results.append({
                        'title': result.get('title', ''),
                        'url': result.get('url', ''),
                        'content': result.get('content', ''),
                        'score': result.get('score', 0.0),
                        'published_date': result.get('published_date', '')
                    })
                
                # Analyze results using LLM to determine if amendments were found
                amendment_analysis = await _analyze_amendment_results(statute, search_results)
                
                amendment_results.append({
                    'statute': statute,
                    'search_query': search_query,
                    'total_results': len(search_results),
                    'search_results': search_results,
                    'amendment_analysis': amendment_analysis,
                    'search_timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.warning(f"Amendment search failed for statute '{statute}': {e}")
                amendment_results.append({
                    'statute': statute,
                    'search_query': f"Singapore {statute} amendment",
                    'total_results': 0,
                    'search_results': [],
                    'amendment_analysis': {
                        'has_amendments': False,
                        'confidence': 0.0,
                        'summary': f"Search failed: {str(e)}",
                        'key_changes': []
                    },
                    'error': str(e),
                    'search_timestamp': datetime.now().isoformat()
                })
        
        # Store search history if user_id is provided
        if request.user_id and request.user_id != "anonymous":
            try:
                db = get_firestore_db()
                db.store_search_history(
                    request.user_id, 
                    f"Amendment search for {len(request.statutes)} statutes", 
                    "amendment_search", 
                    sum(len(r.get('search_results', [])) for r in amendment_results)
                )
            except Exception as e:
                logger.warning(f"Failed to store amendment search history: {e}")
        
        return {
            "status": "success",
            "total_statutes_searched": len(request.statutes),
            "statutes_with_amendments": len([r for r in amendment_results if r.get('amendment_analysis', {}).get('has_amendments', False)]),
            "results": amendment_results,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Amendment search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _analyze_amendment_results(statute: str, search_results: List[Dict]) -> Dict:
    """
    Analyze search results to determine if the statute has been amended
    """
    try:
        if not search_results:
            return {
                "has_amendments": False,
                "confidence": 0.0,
                "summary": "No search results found",
                "key_changes": []
            }
        
        # Initialize LLM processor
        llm_processor = LLMProcessor()
        
        # Create analysis context
        analysis_context = f"""You are a legal expert analyzing search results to determine if the statute "{statute}" has been recently amended.

Instructions:
1. Analyze the provided search results
2. Determine if there is evidence of recent amendments to this statute
3. Identify key changes if amendments are found
4. Provide a confidence score (0.0 to 1.0) based on the evidence quality
5. Return your analysis in the following JSON format:

{{
    "has_amendments": true/false,
    "confidence": 0.0-1.0,
    "summary": "Brief summary of findings",
    "key_changes": ["Change 1", "Change 2", ...],
    "amendment_dates": ["Date 1", "Date 2", ...],
    "sources": ["Source 1", "Source 2", ...]
}}

Search Results for "{statute}":
"""
        
        for i, result in enumerate(search_results[:5], 1):  # Limit to top 5 results for analysis
            analysis_context += f"""
Result {i}:
Title: {result.get('title', 'No title')}
URL: {result.get('url', 'No URL')}
Content: {result.get('content', 'No content')[:1000]}...
Published Date: {result.get('published_date', 'Unknown')}
Score: {result.get('score', 0.0)}
---
"""
        
        analysis_context += """

Focus on:
- Official government sources (mlaw.gov.sg, sso.agc.gov.sg, parliament.gov.sg)
- Recent amendment dates and effective dates
- Specific changes to sections or provisions
- Bill numbers and parliamentary readings

Return only valid JSON."""
        
        # Generate analysis
        response = await llm_processor._generate_with_retry(analysis_context)
        
        try:
            analysis_data = json.loads(response)
            return analysis_data
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse amendment analysis for {statute}")
            return {
                "has_amendments": False,
                "confidence": 0.0,
                "summary": "Analysis parsing failed",
                "key_changes": []
            }
            
    except Exception as e:
        logger.error(f"Amendment analysis failed for {statute}: {e}")
        return {
            "has_amendments": False,
            "confidence": 0.0,
            "summary": f"Analysis error: {str(e)}",
            "key_changes": []
        }

def _create_statutes_search_context(query: str, project_context: Optional[Dict] = None, max_statutes: int = 10) -> str:
    """Create context for statutes search using LLM"""
    
    # System prompt for statute search
    system_prompt = """You are a legal expert specializing in Singapore law. Your task is to identify the most relevant statutes for the given query base on the document context.

Instructions:
1. Analyze the query and any provided document context (textbooks, legal documents)
2. Identify only relevant statutes that are most applicable
4. Return your response in the following JSON format:

schema = {
    "status": str,
    "query": str,
    "total_statutes": int,
    "statutes": [
        {
            "name and section": str,
            "description": str,
            "source": str
        }
    ]
}


Query to analyze:"""

    # Build context
    context_text = system_prompt + f"\n\n**QUERY:** {query}\n\n"
    
    # Add project context if available
    if project_context:
        if project_context.get('project_name'):
            context_text += f"**PROJECT CONTEXT:**\nProject: {project_context['project_name']}\n"
        if project_context.get('project_description'):
            context_text += f"Description: {project_context['project_description']}\n"
        
        if project_context.get('documents') and len(project_context['documents']) > 0:
            context_text += f"\n**RELEVANT DOCUMENTS ({len(project_context['documents'])} documents):**\n"
            for i, doc in enumerate(project_context['documents'], 1):
                context_text += f"\nDocument {i}:\n"
                if doc.get('title'):
                    context_text += f"Title: {doc['title']}\n"
                if doc.get('author'):
                    context_text += f"Author: {doc.get('author', 'Unknown')}\n"
                if doc.get('content'):
                    # Extract relevant legal concepts from content
                    content = doc['content'][:3000] + "..." if len(doc['content']) > 3000 else doc['content']
                    context_text += f"Content: {content}\n"
                context_text += "-" * 40 + "\n"
        
        context_text += "\n"
    
    context_text += """
**INSTRUCTIONS:**
Based on the query and document context above, identify the most relevant Singapore statutes. Focus on statutes that directly address the legal issues, concepts, or scenarios mentioned. Return only valid JSON in the specified format."""
    
    return context_text
