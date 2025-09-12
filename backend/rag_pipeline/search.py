"""
RAG Search Service for Legal Textbooks
"""

import logging
from typing import List, Dict, Optional
from vector_search.retrieval import get_vector_retrieval

logger = logging.getLogger(__name__)

class TextbookRAGSearch:
    """Handle RAG search operations for legal textbooks"""
    
    def __init__(self):
        self.vector_retrieval = get_vector_retrieval()
    
    async def search_textbooks(self, query: str, filters: Optional[Dict] = None,
                             max_results: int = 5, include_context: bool = False) -> Dict:
        """
        Search legal textbooks using RAG
        
        Args:
            query: Search query (e.g., "termination rights", "breach remedies")
            filters: Optional filters (legal_area, author, title)
            max_results: Maximum number of chunks to return
            include_context: Whether to include surrounding context
            
        Returns:
            Search results with relevant textbook excerpts
        """
        try:
            logger.info(f"Searching textbooks for: {query}")
            
            # Perform vector search
            search_results = self.vector_retrieval.search_textbooks(
                query=query,
                filters=filters,
                max_results=max_results
            )
            
            if not search_results:
                return {
                    'status': 'no_results',
                    'query': query,
                    'results': [],
                    'total_results': 0
                }
            
            # Group results by document for better presentation
            grouped_results = self._group_by_document(search_results)
            
            # Add context if requested
            if include_context:
                grouped_results = await self._add_context(grouped_results)
            
            # Format for response
            formatted_results = self._format_search_results(grouped_results)
            
            logger.info(f"Found {len(search_results)} relevant chunks from {len(grouped_results)} documents")
            
            return {
                'status': 'success',
                'query': query,
                'results': formatted_results,
                'total_results': len(search_results),
                'documents_found': len(grouped_results)
            }
            
        except Exception as e:
            logger.error(f"Textbook search failed for query '{query}': {e}")
            return {
                'status': 'error',
                'query': query,
                'error': str(e),
                'results': []
            }
    
    def _group_by_document(self, search_results: List[Dict]) -> Dict[str, List[Dict]]:
        """Group search results by document"""
        grouped = {}
        
        for result in search_results:
            doc_id = result['document_id']
            if doc_id not in grouped:
                grouped[doc_id] = []
            grouped[doc_id].append(result)
        
        # Sort chunks within each document by chunk_index
        for doc_id in grouped:
            grouped[doc_id].sort(key=lambda x: x.get('chunk_index', 0))
        
        return grouped
    
    async def _add_context(self, grouped_results: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Add surrounding context to search results"""
        try:
            # Get chunk IDs that need context
            all_chunk_ids = []
            for doc_chunks in grouped_results.values():
                for chunk in doc_chunks:
                    all_chunk_ids.append(chunk['chunk_id'])
            
            # Get context chunks
            context_chunks = self.vector_retrieval.get_textbook_context(
                chunk_ids=all_chunk_ids,
                context_window=1  # 1 chunk before and after
            )
            
            # Organize context by document and chunk
            context_by_doc = {}
            for chunk in context_chunks:
                doc_id = chunk['document_id']
                if doc_id not in context_by_doc:
                    context_by_doc[doc_id] = {}
                context_by_doc[doc_id][chunk['chunk_id']] = chunk
            
            # Add context to grouped results
            for doc_id, doc_chunks in grouped_results.items():
                if doc_id in context_by_doc:
                    for chunk in doc_chunks:
                        chunk_id = chunk['chunk_id']
                        # Add surrounding chunks
                        chunk['context_chunks'] = []
                        for context_chunk_id, context_chunk in context_by_doc[doc_id].items():
                            if context_chunk_id != chunk_id:  # Don't include the original chunk
                                chunk['context_chunks'].append(context_chunk)
            
            return grouped_results
            
        except Exception as e:
            logger.error(f"Failed to add context: {e}")
            return grouped_results
    
    def _format_search_results(self, grouped_results: Dict[str, List[Dict]]) -> List[Dict]:
        """Format grouped results for API response"""
        formatted_results = []
        
        for doc_id, chunks in grouped_results.items():
            if not chunks:
                continue
            
            # Get document metadata from first chunk
            first_chunk = chunks[0]
            doc_metadata = first_chunk.get('document_metadata', {})
            
            # Format chunks
            formatted_chunks = []
            for chunk in chunks:
                formatted_chunk = {
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'page_number': chunk['page_number'],
                    'section_title': chunk.get('section_title', ''),
                    'similarity_score': round(chunk['similarity_score'], 3),
                    'chunk_index': chunk.get('chunk_index', 0)
                }
                
                # Add context if available
                if 'context_chunks' in chunk:
                    formatted_chunk['context_chunks'] = [
                        {
                            'text': ctx['text'],
                            'page_number': ctx['page_number'],
                            'chunk_index': ctx.get('chunk_index', 0)
                        }
                        for ctx in chunk['context_chunks']
                    ]
                
                formatted_chunks.append(formatted_chunk)
            
            # Create document result
            document_result = {
                'document_id': doc_id,
                'title': doc_metadata.get('title', 'Unknown Title'),
                'author': doc_metadata.get('author', 'Unknown Author'),
                'legal_area': doc_metadata.get('legalArea', ''),
                'edition': doc_metadata.get('edition', ''),
                'publication_year': doc_metadata.get('publicationYear'),
                'relevant_chunks': formatted_chunks,
                'max_similarity_score': max(chunk['similarity_score'] for chunk in chunks),
                'total_chunks_found': len(chunks)
            }
            
            formatted_results.append(document_result)
        
        # Sort by highest similarity score
        formatted_results.sort(
            key=lambda x: x['max_similarity_score'], 
            reverse=True
        )
        
        return formatted_results
    
    async def get_textbook_summary(self, document_id: str) -> Dict:
        """
        Get a summary of a specific textbook
        
        Args:
            document_id: Document ID
            
        Returns:
            Textbook summary with metadata and structure
        """
        try:
            # Get document metadata
            doc_ref = self.vector_retrieval.db.db.collection('referenceMaterials').document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return {
                    'status': 'not_found',
                    'document_id': document_id
                }
            
            doc_data = doc.to_dict()
            
            # Get chunk structure
            chunks_query = (self.vector_retrieval.db.db.collection('textbook_chunks')
                          .where('document_id', '==', document_id)
                          .order_by('chunk_index'))
            chunks = chunks_query.get()
            
            # Extract section structure
            sections = []
            current_section = None
            
            for chunk in chunks:
                chunk_data = chunk.to_dict()
                section_title = chunk_data.get('section_title', '')
                
                if section_title and section_title != current_section:
                    current_section = section_title
                    sections.append({
                        'title': section_title,
                        'start_page': chunk_data.get('page_number', 1),
                        'chunk_count': 1
                    })
                elif sections:
                    sections[-1]['chunk_count'] += 1
            
            return {
                'status': 'success',
                'document_id': document_id,
                'metadata': doc_data,
                'total_chunks': len(chunks),
                'sections': sections,
                'processing_status': doc_data.get('processingStatus', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Failed to get textbook summary for {document_id}: {e}")
            return {
                'status': 'error',
                'document_id': document_id,
                'error': str(e)
            }

# Singleton instance
_rag_search = None

def get_rag_search():
    """Get singleton RAG search instance"""
    global _rag_search
    if _rag_search is None:
        _rag_search = TextbookRAGSearch()
    return _rag_search