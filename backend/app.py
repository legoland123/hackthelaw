"""
app.py - Main Legal Search API Application
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
from groqFunc.media_to_input import process_file as groq_convert_media_to_text
from groqFunc.input_format import main as groq_check_input_format
from groqFunc.input_to_clause import main as groq_convert_input_to_clause
from groqFunc.clause_diff import main as groq_find_clause_diff
from groqFunc.diff_to_semantics import main as groq_find_semantics

# Load environment variables from .env file
load_dotenv()

from conversation.context_builder import (
    create_comprehensive_conversation_context,
    create_case_relevance_visualization,
    ChatMessage
)
from legal_memory.legal_scraper import EnhancedLegalScraper
from legal_memory.llm_processor import LLMProcessor
from firebase.db import get_firestore_db
from firebase.auth import verify_user_token
from utils.pdf_generator import PDFGenerator
from utils.firebase_storage import FirebaseStorageManager
from vector_search.retrieval import get_vector_retrieval
from rag_pipeline.search import TextbookRAGSearch
from legal_services.statute_search import find_relevant_statutes, search_amendment, StatutesSearchRequest, AmendmentSearchRequest
from legal_services.elitigation_search import search_elitigation_cases, ELitigationSearchRequest, search_and_scrape_elitigation_cases, ELitigationEnhancedRequest
# in /vector-query route, where you call the vector store
#from vector_search.vector_store import get_vector_store
#vector_store = get_vector_store()
#
#metadata_filter = {"document_id": req.document_id} if req.document_id else None
#raw = vector_store.search_vectors(query_vec, req.top_k, metadata_filter)

# Configure logging with more detailed setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Log startup information
logger.info("🚀 Starting LIT Legal Mind Backend API...")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")

app = FastAPI(title="Legal Search API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ FastAPI app initialized with CORS middleware")

# Initialize utilities on startup
pdf_generator = None
storage_manager = None
vector_retrieval = None
rag_search = None

@app.on_event("startup")
def startup_event():
    """Initialize utilities after app startup"""
    global pdf_generator, storage_manager, vector_retrieval, rag_search
    
    # Ensure Firebase is initialized correctly before anything else
    from firebase.config import get_firebase_config
    get_firebase_config()
    
    logger.info("🔥 Initializing utilities...")
    pdf_generator = PDFGenerator()
    storage_manager = FirebaseStorageManager()
    vector_retrieval = get_vector_retrieval()
    rag_search = TextbookRAGSearch()
    logger.info("✅ Utilities initialized successfully")
    
def _call_vector_store_any(vector_store, embedding, top_k, score_threshold=None, metadata_filter=None):
    """
    Call whatever query/search method this vector_store implements.
    Returns an iterable of dicts like:
      {"id": "...", "score": 0.87, "metadata": {...}}  (score may also appear as 'distance'/'similarity')
    """

    last_err = None

    # Prefer explicit support for 'search_vectors' (use POSITONAL args since your impl rejects 'embedding=')
    if hasattr(vector_store, "search_vectors"):
        fn = getattr(vector_store, "search_vectors")
        for args in [
            (embedding, top_k, metadata_filter, score_threshold),
            (embedding, top_k, metadata_filter),
            (embedding, top_k, score_threshold),
            (embedding, top_k),
        ]:
            try:
                return fn(*args)
            except TypeError as e:
                last_err = e
            except Exception as e:
                last_err = e
        # If we got here, we'll try other method names below

    # Try other common method names (many libs accept keywords)
    candidates = [
        ("query",              {"embedding": embedding, "top_k": top_k, "score_threshold": score_threshold, "filter": metadata_filter}),
        ("search",             {"embedding": embedding, "k": top_k, "filter": metadata_filter, "score_threshold": score_threshold}),
        ("similarity_search",  {"embedding": embedding, "top_k": top_k, "filter": metadata_filter}),
        ("find_neighbors",     {"embedding": embedding, "top_k": top_k, "score_threshold": score_threshold, "filter": metadata_filter}),
        ("nearest_neighbors",  {"embedding": embedding, "top_k": top_k}),
    ]

    for name, kwargs in candidates:
        if hasattr(vector_store, name):
            fn = getattr(vector_store, name)
            cleaned = {k: v for k, v in kwargs.items() if v is not None}
            try:
                return fn(**cleaned)
            except TypeError:
                try:
                    return fn(embedding=embedding, top_k=top_k)
                except Exception as e2:
                    last_err = e2
            except Exception as e:
                last_err = e

    avail = [n for n in dir(vector_store) if callable(getattr(vector_store, n, None)) and not n.startswith("_")]
    raise HTTPException(
        status_code=500,
        detail=f"No supported query method on vector store. Tried search_vectors (positional), then "
               f"query/search/similarity_search/find_neighbors/nearest_neighbors. "
               f"Available: {avail}. Last error: {last_err}"
    )

# remove any earlier vector_query definitions above this point

class VectorQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    score_threshold: float = 0.0   # not used server-side; we can filter client-side if you want
    document_id: Optional[str] = None
    include_scores: bool = True

@app.post("/vector-query")
async def vector_query(req: VectorQueryRequest):
    try:
        q = (req.query or "").strip()
        if len(q) < 2:
            raise HTTPException(status_code=400, detail="Query too short")

        # 1) Embed query
        from vector_search.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        query_vec = embedding_service.get_single_embedding(q)

        # 2) Call the vector store with POSITIONAL args only
        from vector_search.vector_store import get_vector_store
        vector_store = get_vector_store()

        metadata_filter = {"document_id": req.document_id} if req.document_id else None
        raw = vector_store.search_vectors(query_vec, req.top_k, metadata_filter)
        
        # 3) Normalize results to {id, score?, metadata}
        matches = []
        for m in (raw or []):
            if not isinstance(m, dict):
                continue
            mid   = m.get("id") or m.get("datapoint_id") or m.get("doc_id")
            score = m.get("score") or m.get("similarity") or m.get("distance")
            meta  = m.get("metadata") or m.get("restricts") or {}
            if not mid:
                continue
            matches.append({"id": mid, "score": score, "metadata": meta})

        # 4) Client-side filter by document_id if requested
        #if req.document_id:
        #    matches = [r for r in matches if (r.get("metadata") or {}).get("document_id") == req.document_id]

        # 5) Hydrate chunk text from Firestore
        db = get_firestore_db()
        results = []
        for r in matches:
            text = None
            try:
                snap = db.get_document(r["id"])
                if snap and snap.exists:
                    text = (snap.to_dict() or {}).get("text")
            except Exception:
                pass

            item = {"id": r["id"], "text": text, "metadata": r.get("metadata") or {}}
            if req.include_scores and (r.get("score") is not None):
                item["score"] = r["score"]
            results.append(item)

        return {
            "status": "success" if results else "no_results",
            "query": q,
            "total_results": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"/vector-query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SearchRequest(BaseModel):
    query: str
    search_type: str = "both"  # "hansard", "lawnet", "both"
    user_id: Optional[str] = "anonymous"
    doc_id: Optional[str] = None  # Document ID for storing in conflicts collection

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = "anonymous"
    project_id: Optional[str] = None  # Add project ID for context
    project_context: Optional[Dict] = None  # Add project context with document content

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    timestamp: str
    statute_search: Optional[Dict] = None  # Statute search results
    amendment_search: Optional[Dict] = None  # Amendment search results

class VectorSearchRequest(BaseModel):
    query: str
    filters: Optional[Dict] = None
    max_results: Optional[int] = 10
    include_context: Optional[bool] = False
    user_id: Optional[str] = "anonymous"

class DocumentProcessingRequest(BaseModel):
    document_id: str
    chunk_size: Optional[int] = 1000
    overlap: Optional[int] = 200
    user_id: Optional[str] = "anonymous"


@app.get("/project/{project_id}")
async def get_project_by_id(project_id: str):
    """
    Retrieve a single project by its ID from Firestore.
    """
    try:
        db = get_firestore_db()
        project_doc = db.get_project(project_id) # Use the existing db helper

        if not project_doc.exists:
            raise HTTPException(status_code=404, detail="Project not found")

        project_data = project_doc.to_dict()
        project_data['id'] = project_doc.id
        
        # Ensure documentIds and conflicts are lists
        if 'documentIds' not in project_data:
            project_data['documentIds'] = []
        if 'conflicts' not in project_data:
            project_data['conflicts'] = []
            
        return project_data
    except Exception as e:
        logger.error(f"Failed to retrieve project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    logger.info("🏥 Health check endpoint called")
    return {"status": "healthy"}

@app.post("/vector-search")
async def vector_search_textbooks(request: VectorSearchRequest):
    """
    Search legal textbooks using vector similarity
    """
    try:
        # Validate input
        if not request.query or len(request.query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query too short")
        
        query = request.query.strip()
        max_results = min(request.max_results or 10, 50)  # Cap at 50 results
        
        logger.info(f"🔍 Vector search for: {query}")
        
        # Perform RAG search
        search_result = await rag_search.search_textbooks(
            query=query,
            filters=request.filters,
            max_results=max_results,
            include_context=request.include_context
        )
        
        # Store search history if user_id is provided
        if request.user_id and request.user_id != "anonymous":
            try:
                db = get_firestore_db()
                db.store_search_history(
                    request.user_id, 
                    query, 
                    "vector_search", 
                    search_result.get('total_results', 0)
                )
            except Exception as e:
                logger.warning(f"Failed to store vector search history: {e}")
        
        return search_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat_with_legal_mind(request: ChatRequest):
    """
    Chat with LIT Legal Mind using GROQ with automatic statute search and amendment analysis
    """
    try:
        # Validate input
        if not request.message or len(request.message.strip()) < 1:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        message = request.message.strip()
        
        # Initialize LLM processor
        try:
            llm_processor = LLMProcessor()
        except ValueError as e:
            logger.error(f"LLM Processor initialization failed: {e}")
            raise HTTPException(status_code=500, detail="AI service unavailable")
        
        # Detect if the query requires statute search
        statute_search_results = None
        amendment_search_results = None
        
        logger.info(f"🏛️ Legal query detected, performing statute search for: {message}")
        
        # Perform statute search
        try:
            statute_request = StatutesSearchRequest(
                message=message,
                project_context=request.project_context,
                user_id=request.user_id,
                max_statutes=5  # Limit for chat context
            )
            
            if True: # hackathon override
                statute_search_results = json.load(open("legal_services/statute_search_result.json"))
            else:
                statute_search_results = await find_relevant_statutes(statute_request)
            
            # If statutes were found, search for amendments
            if (statute_search_results and 
                statute_search_results.get('status') == 'success' and 
                len(statute_search_results.get('statutes', [])) > 0):
                
                logger.info(f"🔍 Found {len(statute_search_results['statutes'])} statutes, checking for amendments")
                
                statute_names = [stat.get('name and section', '') for stat in statute_search_results['statutes'] if stat.get('name and section')]
                
                if statute_names:
                    amendment_request = AmendmentSearchRequest(
                        statutes=statute_names,
                        user_id=request.user_id,
                        max_results_per_statute=3  # Limit for chat context
                    )
                    
                    if True: # hackathon override
                        # sleep awhile and log
                        logger.info("⏳ Simulating amendment search delay...")
                        await asyncio.sleep(2)  # Simulate delay
                        amendment_search_results = json.load(open("legal_services/amendment_sample.json"))
                    else:
                        amendment_search_results = await search_amendment(amendment_request)
                
                # Perform eLitigation search for testing (not included in conversation)
                if (statute_search_results and 
                    statute_search_results.get('status') == 'success' and 
                    len(statute_search_results.get('statutes', [])) > 0):
                    
                    logger.info("🏛️ Performing eLitigation case search for testing")
                    
                    try:
                        # Extract statute names for eLitigation search
                        statute_names = [stat.get('name and section', '') for stat in statute_search_results['statutes'] if stat.get('name and section')]
                        
                        if statute_names:
                            elitigation_request = ELitigationEnhancedRequest(
                                names=statute_names,
                                max_results=3,  # Limit for comprehensive context
                                scrape_content=True,  # Enable content scraping
                                user_id=request.user_id
                            )
                            
                            if True: # hackathon override
                                # sleep awhile and log
                                logger.info("⏳ Simulating eLitigation search delay...")
                                await asyncio.sleep(2)  # Simulate delay
                                elitigation_results = json.load(open("legal_services/elitigation_scraped.json"))
                            else:
                                elitigation_results = search_and_scrape_elitigation_cases(elitigation_request)
                            logger.info(f"📋 Enhanced eLitigation search completed: {elitigation_results.get('total_found', 0)} cases found")
                            
                            # Log results for testing
                            if elitigation_results.get('status') == 'success':
                                logger.info(f"🔍 Top eLitigation cases: {[case.get('title', '')[:50] + '...' for case in elitigation_results.get('cases', [])[:3]]}")
                                
                                # Log if we got scraped content
                                scraped_count = sum(1 for case in elitigation_results.get('cases', []) if case.get('full_content'))
                                logger.info(f"📄 Successfully scraped content from {scraped_count} cases")
                                
                                # Step 3: Apply advanced relevance ranking
                                logger.info("🎯 Applying Step 3: Advanced Relevance Scoring...")
                                
                                try:
                                    from legal_services.case_ranking import rank_elitigation_cases, extract_query_facts
                                    
                                    # Extract query facts for better ranking
                                    query_facts = extract_query_facts(message)
                                    logger.info(f"📋 Extracted facts from query: {query_facts}")
                                    
                                    # Extract statute names for ranking
                                    target_statutes = [stat.get('name and section', '') for stat in statute_search_results.get('statutes', [])]
                                    
                                    # Apply multi-factor ranking
                                    ranked_cases = rank_elitigation_cases(
                                        cases=elitigation_results.get('cases', []),
                                        query=message,
                                        target_statutes=target_statutes,
                                        query_facts=query_facts
                                    )
                                    
                                    # Update results with ranked cases
                                    elitigation_results['cases'] = ranked_cases
                                    elitigation_results['ranking_applied'] = True
                                    
                                    # Log ranking results
                                    if ranked_cases:
                                        top_score = ranked_cases[0].get('relevance_score', 0)
                                        avg_score = sum(case.get('relevance_score', 0) for case in ranked_cases) / len(ranked_cases)
                                        logger.info(f"🏆 Ranking complete - Top score: {top_score:.3f}, Average: {avg_score:.3f}")
                                        
                                        # Log top 3 cases with scores
                                        for i, case in enumerate(ranked_cases[:3]):
                                            score = case.get('relevance_score', 0)
                                            title = case.get('title', '')[:50] + '...'
                                            logger.info(f"  #{i+1}: {title} (Score: {score:.3f})")
                                    
                                except Exception as ranking_error:
                                    logger.warning(f"Relevance ranking failed: {ranking_error}")
                                    # Continue without ranking if it fails

                        else:
                            elitigation_results = None
                    
                    except Exception as e:
                        logger.warning(f"eLitigation search failed: {e}")

        except Exception as e:
            logger.warning(f"Statute/amendment search failed in chat: {e}")
            # Continue with chat even if statute search fails
        
        # Create enhanced conversation context with statute, amendment, and case information
        conversation_context = create_comprehensive_conversation_context(
            request.conversation_history,
            message,
            request.project_context,
            statute_search_results,
            amendment_search_results,
            elitigation_results if 'elitigation_results' in locals() else None
        )
        
        # Generate response using LLM
        try:
            response = await llm_processor._generate_with_retry(conversation_context)
            
            # Enhance response with ranked cases visualization if available
            if 'elitigation_results' in locals() and elitigation_results and elitigation_results.get('status') == 'success':
                ranked_cases = elitigation_results.get('cases', [])
                if ranked_cases and elitigation_results.get('ranking_applied', False):
                    case_visualization = create_case_relevance_visualization(ranked_cases)
                    response = response + "\n\n" + case_visualization
            
            # Store conversation in database if user_id is provided
            if request.user_id and request.user_id != "anonymous":
                db = get_firestore_db()
                conversation_id = db.store_conversation(
                    request.user_id, 
                    message, 
                    response, 
                    request.conversation_history,
                    request.project_id  # Store project ID with conversation
                )
            else:
                conversation_id = None
            
            # Prepare enhanced response with statute and amendment data
            response_data = {
                "response": response,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add statute search results if available
            if statute_search_results:
                response_data["statute_search"] = statute_search_results
            
            # Add amendment search results if available
            if amendment_search_results:
                response_data["amendment_search"] = amendment_search_results
            
            return response_data
            
        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate response")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/statutes-search")
async def statute_search_endpoint(request: StatutesSearchRequest):
    """
    Find relevant statutes based on query and document context using LLM
    """
    return await find_relevant_statutes(request)

@app.post("/amendment-search")
async def amendment_search_endpoint(request: AmendmentSearchRequest):
    """
    Search for amendments to specified statutes using Tavily
    """
    return await search_amendment(request)

@app.post("/elitigation-search")
async def elitigation_search_endpoint(request: ELitigationSearchRequest):
    """
    Search for eLitigation cases related to specified statutes or legal concepts
    """
    return search_elitigation_cases(request)

@app.post("/elitigation-search-enhanced")
async def elitigation_search_enhanced_endpoint(request: ELitigationEnhancedRequest):
    """
    Enhanced eLitigation search that includes full case content scraping
    """
    return search_and_scrape_elitigation_cases(request)

@app.post("/search")
async def search_legal_content(request: SearchRequest):
    """
    Search legal content and return results immediately
    """
    try:
        # Validate input
        if not request.query or len(request.query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query too short")
        
        if request.search_type not in ["hansard", "lawnet", "both"]:
            raise HTTPException(status_code=400, detail="Invalid search_type")
        
        query = request.query.strip()
        
        # Check cache first
        db = get_firestore_db()
        cached_result = db.get_cached_result(query, request.search_type)
        
        if cached_result:
            logger.info(f"Returning cached result for: {query}")
            return {
                "status": "success",
                "data": cached_result,
                "cached": True
            }
        
        # Perform fresh search
        logger.info(f"Performing fresh search for: {query}")
        
        # 1. Scrape websites
        scraper = EnhancedLegalScraper()
        html_content = ""
        
        try:
            if request.search_type in ["hansard", "both"]:
                hansard_results = scraper.search_hansard_with_extraction([query])
                if query in hansard_results:
                    html_content += convert_to_html(hansard_results[query], "hansard")
            
            if request.search_type in ["lawnet", "both"]:
                lawnet_results = scraper.search_lawnet_with_extraction([query])
                if query in lawnet_results:
                    html_content += convert_to_html(lawnet_results[query], "lawnet")
        
        finally:
            scraper.close()
        
        if not html_content:
            raise HTTPException(status_code=404, detail="No results found")
        
        # 2. Process with LLM
        llm_processor = LLMProcessor()
        processed_data = await llm_processor.process_legal_html(html_content, query)
        
        # 3. Store in Firestore
        db.store_search_result(query, request.search_type, processed_data, request.user_id)
        
        # 4. Store in conflicts collection if doc_id is provided
        if request.doc_id:
            try:
                conflict_id = db.store_conflict(request.doc_id, processed_data)
                logger.info(f"Stored search results in conflicts collection with ID: {conflict_id}")
            except Exception as e:
                logger.warning(f"Failed to store in conflicts collection: {e}")
        
        # 5. Store search history
        total_results = (
            len(processed_data.get('caseLaw', [])) + 
            len(processed_data.get('hansardRecords', []))
        )
        db.store_search_history(request.user_id, query, request.search_type, total_results)
        
        response_data = {
            "status": "success",
            "data": processed_data,
            "cached": False
        }
        
        # Add conflict_id to response if stored
        if request.doc_id and 'conflict_id' in locals():
            response_data["conflict_id"] = conflict_id
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/project/{proj_id}")
async def get_project_details(proj_id: str):
    """
    Fetch details for a single project
    """
    try:
        db = get_firestore_db()
        proj_ref = db.get_project(proj_id)
        if not proj_ref.exists:
            raise HTTPException(status_code=404, detail="Project not found")
        
        proj_data = proj_ref.to_dict()
        proj_data["id"] = proj_ref.id
        return proj_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch project {proj_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project {proj_id}")

@app.post("/upload/{proj_id}/{doc_id}")
async def upload_legal_content(proj_id: str, doc_id: str):
    """
    Process uploaded legal content for AI analysis
    """
    logger.info(f"📤 Upload endpoint called - Project: {proj_id}, Document: {doc_id}")
    
    try:
        # Get Firestore database instance
        db = get_firestore_db()
        
        # Fetch the document
        doc = db.get_document(doc_id)
    
    except Exception as e:
        logger.error(f"Failed to fetch document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {e}")
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_data = doc.to_dict()
    
    # Check if document has file information
    if not doc_data.get('fileInfo') or not doc_data['fileInfo'].get('downloadURL'):
        raise HTTPException(status_code=400, detail="Document has no file URL")
    
    # Extract text from the uploaded document
    try:
        extracted_doc_text = groq_convert_media_to_text(doc_data['fileInfo']['downloadURL'])
        logger.info(f"Successfully extracted text from document {doc_id}")
    except Exception as e:
        logger.error(f"Failed to extract text from document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from document: {e}")

    # Fetch project data
    try:
        proj = db.get_project(proj_id)
    
    except Exception as e:
        logger.error(f"Failed to fetch project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {e}")
    
    if not proj.exists:
        raise HTTPException(status_code=404, detail="Project not found")
    
    proj_data = proj.to_dict()
    
    # Check if project has a master copy
    if not proj_data.get('masterCopyId'):
        logger.info(f"Project {proj_id} has no master copy, creating new master from document {doc_id}")
        
        # Convert text to proper format if needed
        new_master = extracted_doc_text
        if not groq_check_input_format(extracted_doc_text):
            new_master = groq_convert_input_to_clause(extracted_doc_text)
        
        # Convert new_master string to PDF and upload to Firebase Storage
        try:
            # Generate PDF from the master text
            pdf_bytes = pdf_generator.text_to_pdf(new_master, f"Master Copy - {proj_data.get('name', 'Project')}")
            
            # Upload PDF to Firebase Storage
            master_filename = f"master_copy_{proj_id}.pdf"
            master_download_url = storage_manager.upload_pdf_bytes(pdf_bytes, master_filename, f"projects/{proj_id}")
            
            # Create a new document for the master copy
            master_doc_data = {
                'title': f"Master Copy - {proj_data.get('name', 'Project')}",
                'description': 'Automatically generated master copy',
                'author': 'System',
                'projectId': proj_id,
                'timestamp': datetime.now().isoformat(),
                'fileInfo': {
                    'fileName': master_filename,
                    'downloadURL': master_download_url,
                    'size': len(pdf_bytes),
                    'type': 'application/pdf'
                },
                'extractedContent': new_master,
                'processedAt': datetime.now().isoformat(),
                'processingStatus': 'completed',
                'isMasterCopy': True
            }
            
            # Add master copy document to Firestore
            master_doc_ref = db.get_document_collection().add(master_doc_data)
            master_doc_id = master_doc_ref[1].id
            
            # Update project with master copy ID
            db.get_project_collection().document(proj_id).update({
                'masterCopyId': master_doc_id,
                'lastUpdated': datetime.now().isoformat()
            })
            
            logger.info(f"Created new master copy document: {master_doc_id}")
            
            # Update the original document with extracted content
            db.get_document_collection().document(doc_id).update({
                'extractedContent': extracted_doc_text,
                'processedAt': datetime.now().isoformat(),
                'processingStatus': 'completed'
            })
            
            return {
                "status": "success",
                "message": "Document processed and master copy created",
                "document_id": doc_id,
                "master_copy_id": master_doc_id,
                "extracted_content_length": len(extracted_doc_text),
                "comparison_performed": False,
                "master_copy_url": master_download_url
            }
            
        except Exception as e:
            logger.error(f"Failed to create master copy: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create master copy: {e}")

    # Project has a master copy, perform comparison
    logger.info(f"Project {proj_id} has master copy, performing comparison")
    
    # Fetch master copy document
    master_doc = db.get_document(proj_data['masterCopyId'])
    
    if not master_doc.exists:
        raise HTTPException(status_code=404, detail="Master copy document not found")
    
    master_doc_data = master_doc.to_dict()
    
    # Extract text from master copy if not already done
    if not master_doc_data.get('extractedContent'):
        try:
            extracted_proj_text = groq_convert_media_to_text(master_doc_data['fileInfo']['downloadURL'])
            # Update master copy with extracted content
            db.get_document_collection().document(proj_data['masterCopyId']).update({
                'extractedContent': extracted_proj_text,
                'processedAt': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to extract text from master copy: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to extract text from master copy: {e}")
    else:
        extracted_proj_text = master_doc_data['extractedContent']
    
    # Convert documents to proper format if needed
    if not groq_check_input_format(extracted_doc_text):
        extracted_doc_text = groq_convert_input_to_clause(extracted_doc_text)
    
    if not groq_check_input_format(extracted_proj_text):
        extracted_proj_text = groq_convert_input_to_clause(extracted_proj_text)
    
    # Find differences between clauses
    try:
        differences_in_clauses = groq_find_clause_diff(extracted_proj_text, extracted_doc_text)
        logger.info(f"Successfully found clause differences for document {doc_id}")
    except Exception as e:
        logger.error(f"Failed to find clause differences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find clause differences: {e}")
    
    # Extract semantics from differences and perform legal search
    try:
        semantics_result = groq_find_semantics(differences_in_clauses)
        logger.info("Successfully extracted semantics from differences")
        
        # Parse the semantics result
        semantics_data = json.loads(semantics_result)
        semantics_list = semantics_data.get('semantics', [])
        
        # Perform legal search for each semantic group
        search_results = []
        for i, semantics_group in enumerate(semantics_list):
            if semantics_group and len(semantics_group) > 0:
                # Create a search query from the semantics
                search_query = " ".join(semantics_group)
                
                # Call search_legal_content for this query
                search_request = SearchRequest(
                    query=search_query,
                    search_type="both",
                    user_id="system",
                    doc_id=doc_id  # Pass the document ID to store in conflicts collection
                )
                
                try:
                    search_result = await search_legal_content(search_request)
                    search_results.append({
                        'semantics_group': semantics_group,
                        'search_query': search_query,
                        'search_result': search_result
                    })
                except Exception as search_error:
                    logger.warning(f"Search failed for semantics group {i}: {search_error}")
                    search_results.append({
                        'semantics_group': semantics_group,
                        'search_query': search_query,
                        'search_result': {'error': str(search_error)}
                    })
        
        logger.info(f"Completed legal search for {len(search_results)} semantics groups")
        
    except Exception as e:
        logger.error(f"Failed to extract semantics or perform search: {e}")
        search_results = []
    
    # Update the document with extracted content and comparison results
    try:
        db.get_document_collection().document(doc_id).update({
            'extractedContent': extracted_doc_text,
            'processedAt': datetime.now().isoformat(),
            'processingStatus': 'completed',
            'comparisonResult': {
                'differences': differences_in_clauses,
                'semantics': semantics_result if 'semantics_result' in locals() else None,
                'searchResults': search_results
            }
        })
        
        logger.info(f"Successfully updated document {doc_id} with comparison results")
        
    except Exception as e:
        logger.error(f"Failed to update document with comparison results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update document: {e}")
    
    return {
        "status": "success",
        "message": "Document processed successfully",
        "document_id": doc_id,
        "extracted_content_length": len(extracted_doc_text),
        "comparison_performed": True,
        "comparison_result": {
            "differences": differences_in_clauses,
            "semantics": semantics_result if 'semantics_result' in locals() else None,
            "search_results_count": len(search_results)
        }
    }

def convert_to_html(results_data: Dict, source: str) -> str:
    """Convert search results to HTML for LLM processing"""
    if results_data.get('status') != 'success':
        return ""
    
    html_parts = [f"<div data-source='{source}'>"]
    
    for result in results_data.get('results', []):
        html_parts.append("<div class='search-result'>")
        html_parts.append(f"<h3>{result.get('title', '')}</h3>")
        html_parts.append(f"<p class='metadata'>{result.get('metadata', '')}</p>")
        html_parts.append(f"<p class='snippet'>{result.get('snippet', '')}</p>")
        html_parts.append(f"<a href='{result.get('url', '')}'>{result.get('url', '')}</a>")
        html_parts.append("</div>")
    
    html_parts.append("</div>")
    return '\n'.join(html_parts)

@app.post("/process-document")
async def process_document_for_vector_search(request: DocumentProcessingRequest):
    """
    Process a document for vector search by chunking and indexing
    """
    try:
        # Validate input
        if not request.document_id:
            raise HTTPException(status_code=400, detail="Document ID is required")
        
        chunk_size = max(500, min(request.chunk_size or 1000, 2000))  # Between 500-2000
        overlap = max(0, min(request.overlap or 200, chunk_size // 2))  # Max 50% of chunk size
        
        logger.info(f"📄 Processing document {request.document_id} for vector search")
        
        # Get document from Firestore
        db = get_firestore_db()
        doc = db.get_document(request.document_id)
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_data = doc.to_dict()
        
        # Check if document has extracted content
        if not doc_data.get('extractedContent'):
            raise HTTPException(status_code=400, detail="Document has no extracted content")
        
        content = doc_data['extractedContent']
        
        # Chunk the content
        chunks = _create_text_chunks(content, chunk_size, overlap)
        logger.info(f"Created {len(chunks)} chunks from document {request.document_id}")
        
        # Generate embeddings for chunks
        try:
            from vector_search.embeddings import get_embedding_service
            embedding_service = get_embedding_service()
            
            # Prepare chunk texts for embedding
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = embedding_service.get_embeddings(chunk_texts)
            
            if len(embeddings) != len(chunks):
                raise ValueError(f"Embedding count mismatch: {len(embeddings)} != {len(chunks)}")
            
            # Prepare vector data
            vector_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_data.append({
                    'id': f"{request.document_id}_chunk_{i}",
                    'embedding': embedding,
                    'metadata': {
                        'document_id': request.document_id,
                        'chunk_index': i,
                        'title': doc_data.get('title', 'Unknown'),
                        'author': doc_data.get('author', 'Unknown'),
                        'legal_area': doc_data.get('legalArea', ''),
                        'chunk_size': len(chunk['text']),
                        'start_char': chunk['start_char'],
                        'end_char': chunk['end_char']
                    }
                })
            
            # Add vectors to vector store
            from vector_search.vector_store import get_vector_store
            vector_store = get_vector_store()
            res = vector_store.add_vectors(vector_data)
            staged_gcs_uri = res.get("staged_gcs_uri") if isinstance(res, dict) else None

                       # Store chunk metadata in Firestore
            for i, chunk in enumerate(chunks):
                chunk_doc_data = {
                    'document_id': request.document_id,
                    'chunk_index': i,
                    'text': chunk['text'],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char'],
                    'chunk_size': len(chunk['text']),
                    'title': doc_data.get('title', 'Unknown'),
                    'author': doc_data.get('author', 'Unknown'),
                    'legal_area': doc_data.get('legalArea', ''),
                    'created_at': datetime.now().isoformat(),
                    'vector_id': f"{request.document_id}_chunk_{i}"
                }
                
                db.get_document_collection().document(f"{request.document_id}_chunk_{i}").set(chunk_doc_data)
            
            # Update document with processing status
            db.get_document_collection().document(request.document_id).update({
                'vectorIndexed': True,
                'vectorIndexedAt': datetime.now().isoformat(),
                'totalChunks': len(chunks),
                'chunkSize': chunk_size,
                'overlap': overlap
            })
            
            logger.info(f"Successfully processed document {request.document_id} with {len(chunks)} chunks")
            
            return {
                "status": "success",
                "message": "Document processed for vector search",
                "document_id": request.document_id,
                "total_chunks": len(chunks),
                "chunk_size": chunk_size,
                "overlap": overlap, "vector_indexed": False,  # becomes True after Console batch update completes
                "staged_gcs_uri": staged_gcs_uri
            }
            
        except Exception as e:
            logger.error(f"Failed to process document for vector search: {e}")
            raise HTTPException(status_code=500, detail=f"Vector processing failed: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _create_text_chunks(text: str, chunk_size: int, overlap: int) -> List[Dict]:
    """
    Create overlapping text chunks for vector indexing
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of chunk dictionaries with text and position information
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If this isn't the last chunk, try to break at a sentence boundary
        if end < len(text):
            # Look for sentence endings within the last 100 characters of the chunk
            search_start = max(start, end - 100)
            sentence_end = -1
            
            for i in range(search_start, end):
                if text[i] in '.!?':
                    sentence_end = i + 1
                    break
            
            if sentence_end > start:
                end = sentence_end
        
        # Extract the chunk
        chunk_text = text[start:end].strip()
        
        if chunk_text:  # Only add non-empty chunks
            chunks.append({
                'text': chunk_text,
                'start_char': start,
                'end_char': end
            })
        
        # Move to next chunk with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks