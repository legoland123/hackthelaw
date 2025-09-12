"""
Vector Search and Retrieval Service
"""

import logging
import os
from typing import List, Dict, Optional
from .embeddings import get_embedding_service
from .vector_store import get_vector_store
from firebase.db import get_firestore_db

logger = logging.getLogger(__name__)

class VectorRetrieval:
    """Handle vector search and retrieval operations"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.db = get_firestore_db()
        
        self.max_results = int(os.getenv('MAX_RETRIEVAL_RESULTS', 10))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
    
    def search_textbooks(self, query: str, filters: Optional[Dict] = None, 
                        max_results: Optional[int] = None) -> List[Dict]:
        """
        Search textbooks using semantic similarity
        
        Args:
            query: Search query
            filters: Optional metadata filters (e.g., legal_area, author)
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant textbook chunks with metadata
        """
        try:
            # Get query embedding
            query_embedding = self.embedding_service.get_query_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Search vectors
            max_results = max_results or self.max_results
            vector_results = self.vector_store.search_vectors(
                query_vector=query_embedding,
                num_neighbors=max_results,
                metadata_filters=filters
            )
            
            if not vector_results:
                logger.info(f"No vector results found for query: {query}")
                return []
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in vector_results 
                if result['similarity_score'] >= self.similarity_threshold
            ]
            
            if not filtered_results:
                logger.info(f"No results above similarity threshold {self.similarity_threshold}")
                return []
            
            # Enrich with chunk metadata from Firestore
            enriched_results = self._enrich_with_metadata(filtered_results)
            
            # Sort by similarity score
            enriched_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            logger.info(f"Retrieved {len(enriched_results)} relevant chunks for query: {query}")
            return enriched_results
            
        except Exception as e:
            logger.error(f"Textbook search failed: {e}")
            return []
    
    def _enrich_with_metadata(self, vector_results: List[Dict]) -> List[Dict]:
        """
        Enrich vector search results with chunk metadata from Firestore
        
        Args:
            vector_results: Results from vector search
            
        Returns:
            Enriched results with full metadata
        """
        enriched_results = []
        
        for result in vector_results:
            chunk_id = result['id']
            
            try:
                # Get chunk metadata from Firestore
                chunk_doc = self.db.db.collection('textbook_chunks').document(chunk_id).get()
                
                if chunk_doc.exists:
                    chunk_data = chunk_doc.to_dict()
                    
                    # Combine vector result with chunk metadata
                    enriched_result = {
                        'chunk_id': chunk_id,
                        'similarity_score': result['similarity_score'],
                        'distance': result['distance'],
                        'text': chunk_data.get('text', ''),
                        'document_id': chunk_data.get('document_id', ''),
                        'page_number': chunk_data.get('page_number', 1),
                        'chunk_index': chunk_data.get('chunk_index', 0),
                        'section_title': chunk_data.get('section_title', ''),
                        'document_metadata': chunk_data.get('document_metadata', {}),
                        'created_at': chunk_data.get('created_at')
                    }
                    
                    enriched_results.append(enriched_result)
                else:
                    logger.warning(f"Chunk metadata not found for ID: {chunk_id}")
                    
            except Exception as e:
                logger.error(f"Failed to enrich chunk {chunk_id}: {e}")
                continue
        
        return enriched_results
    
    def get_textbook_context(self, chunk_ids: List[str], context_window: int = 2) -> List[Dict]:
        """
        Get additional context around selected chunks
        
        Args:
            chunk_ids: List of chunk IDs to get context for
            context_window: Number of chunks before/after to include
            
        Returns:
            List of chunks with additional context
        """
        try:
            context_chunks = []
            
            for chunk_id in chunk_ids:
                # Parse chunk index from ID
                parts = chunk_id.split('_chunk_')
                if len(parts) != 2:
                    continue
                
                document_id = parts[0]
                try:
                    chunk_index = int(parts[1])
                except ValueError:
                    continue
                
                # Get surrounding chunks
                for i in range(max(0, chunk_index - context_window), 
                              chunk_index + context_window + 1):
                    context_chunk_id = f"{document_id}_chunk_{i:04d}"
                    
                    try:
                        chunk_doc = self.db.db.collection('textbook_chunks').document(context_chunk_id).get()
                        if chunk_doc.exists:
                            chunk_data = chunk_doc.to_dict()
                            chunk_data['chunk_id'] = context_chunk_id
                            chunk_data['is_original'] = (context_chunk_id == chunk_id)
                            context_chunks.append(chunk_data)
                    except Exception as e:
                        logger.warning(f"Failed to get context chunk {context_chunk_id}: {e}")
                        continue
            
            # Remove duplicates and sort by document and chunk index
            unique_chunks = {chunk['chunk_id']: chunk for chunk in context_chunks}
            sorted_chunks = sorted(
                unique_chunks.values(),
                key=lambda x: (x.get('document_id', ''), x.get('chunk_index', 0))
            )
            
            return sorted_chunks
            
        except Exception as e:
            logger.error(f"Failed to get textbook context: {e}")
            return []

# Singleton instance
_vector_retrieval = None

def get_vector_retrieval():
    """Get singleton vector retrieval instance"""
    global _vector_retrieval
    if _vector_retrieval is None:
        _vector_retrieval = VectorRetrieval()
    return _vector_retrieval