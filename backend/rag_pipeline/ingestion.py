"""
RAG Ingestion Pipeline for Legal Textbooks
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List
from firebase_admin import storage, firestore
from document_processing.pdf_extractor import get_pdf_extractor
from document_processing.chunker import get_text_chunker
from vector_search.embeddings import get_embedding_service
from vector_search.vector_store import get_vector_store
from firebase.db import get_firestore_db

logger = logging.getLogger(__name__)

class TextbookIngestionPipeline:
    """Handle end-to-end ingestion of legal textbooks"""
    
    def __init__(self):
        self.pdf_extractor = get_pdf_extractor()
        self.text_chunker = get_text_chunker()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()
        self.db = get_firestore_db()
        
        # Firebase Storage
        self.storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
        if self.storage_bucket:
            self.bucket = storage.bucket(self.storage_bucket)
        else:
            logger.warning("Firebase Storage bucket not configured")
            self.bucket = None
    
    async def process_uploaded_textbook(self, file_data: bytes, filename: str, 
                                      metadata: Dict = None) -> Dict:
        """
        Complete pipeline to process an uploaded textbook
        
        Args:
            file_data: PDF file as bytes
            filename: Original filename
            metadata: Additional metadata (title, author, etc.)
            
        Returns:
            Processing result with document ID and status
        """
        document_id = None
        doc_ref = None
        
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            logger.info(f"Starting ingestion for {filename} (ID: {document_id})")
            
            # Validate input
            if not file_data or len(file_data) == 0:
                raise ValueError("Empty file data provided")
            
            if not filename:
                raise ValueError("No filename provided")
            
            # 1. Store original file in Firebase Storage
            storage_path = None
            if self.bucket:
                try:
                    storage_path = await self._store_in_firebase_storage(
                        file_data, filename, document_id
                    )
                    logger.info(f"File stored in Firebase Storage: {storage_path}")
                except Exception as storage_error:
                    logger.warning(f"Firebase Storage failed: {storage_error}")
                    # Continue processing even if storage fails
            
            # 2. Extract text from PDF
            logger.info(f"Extracting text from {filename}")
            try:
                extraction_result = self.pdf_extractor.extract_text_from_bytes(
                    file_data, filename
                )
                logger.info(f"Text extraction successful: {len(extraction_result['text'])} characters")
            except Exception as extraction_error:
                logger.error(f"PDF text extraction failed: {extraction_error}")
                raise ValueError(f"Failed to extract text from PDF: {extraction_error}")
            
            # 3. Create document record in Firestore
            document_metadata = self._prepare_document_metadata(
                filename, extraction_result['metadata'], metadata, storage_path
            )
            
            # Store in referenceMaterials subcollection
            doc_ref = self.db.db.collection('referenceMaterials').document(document_id)
            doc_ref.set({
                **document_metadata,
                'processingStatus': 'processing',
                'uploadedAt': firestore.SERVER_TIMESTAMP,
                'processingStartedAt': firestore.SERVER_TIMESTAMP
            })
            logger.info(f"Document record created in Firestore: {document_id}")
            
            # 4. Chunk the text
            logger.info(f"Chunking text for {filename}")
            try:
                chunks = self.text_chunker.chunk_document(
                    extraction_result['text'],
                    document_id,
                    extraction_result['page_contents']
                )
                logger.info(f"Chunking successful: {len(chunks)} chunks created")
                
                if not chunks:
                    raise ValueError("No chunks were created from the document")
                
            except Exception as chunking_error:
                logger.error(f"Text chunking failed: {chunking_error}")
                raise ValueError(f"Failed to chunk document: {chunking_error}")
            
            # 5. Generate embeddings and store vectors
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            try:
                await self._process_chunks(chunks, document_metadata)
                logger.info("Embeddings and vector storage successful")
            except Exception as embedding_error:
                logger.error(f"Embedding/vector storage failed: {embedding_error}")
                raise ValueError(f"Failed to process embeddings: {embedding_error}")
            
            # 6. Update document status
            try:
                doc_ref.update({
                    'processingStatus': 'completed',
                    'processedAt': firestore.SERVER_TIMESTAMP,
                    'totalChunks': len(chunks)
                })
                logger.info(f"Document status updated to completed")
            except Exception as update_error:
                logger.error(f"Failed to update document status: {update_error}")
                # Don't raise - processing was successful even if status update failed
            
            logger.info(f"Successfully processed {filename} with {len(chunks)} chunks")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'total_chunks': len(chunks),
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}")
            logger.exception("Detailed error information:")
            
            # Update status to failed if document was created
            try:
                if doc_ref:
                    doc_ref.update({
                        'processingStatus': 'failed',
                        'errorMessage': str(e),
                        'processedAt': firestore.SERVER_TIMESTAMP
                    })
                    logger.info("Updated document status to failed")
            except Exception as status_error:
                logger.error(f"Failed to update error status: {status_error}")
            
            return {
                'status': 'error',
                'error': str(e),
                'filename': filename,
                'document_id': document_id
            }
    
    async def _store_in_firebase_storage(self, file_data: bytes, filename: str, 
                                       document_id: str) -> str:
        """Store file in Firebase Storage"""
        try:
            if not self.bucket:
                raise ValueError("Firebase Storage not configured")
            
            # Create storage path
            storage_path = f"textbooks/{document_id}/{filename}"
            
            # Upload file
            blob = self.bucket.blob(storage_path)
            blob.upload_from_string(file_data, content_type='application/pdf')
            
            logger.info(f"Stored file at {storage_path}")
            return storage_path
            
        except Exception as e:
            logger.error(f"Failed to store file in Firebase Storage: {e}")
            raise
    
    def _prepare_document_metadata(self, filename: str, pdf_metadata: Dict, 
                                 user_metadata: Dict, storage_path: str) -> Dict:
        """Prepare document metadata for Firestore"""
        try:
            metadata = {
                'fileName': filename,
                'title': (user_metadata or {}).get('title') or pdf_metadata.get('title', filename),
                'author': (user_metadata or {}).get('author') or pdf_metadata.get('author', ''),
                'edition': (user_metadata or {}).get('edition', ''),
                'publicationYear': (user_metadata or {}).get('publicationYear'),
                'legalArea': (user_metadata or {}).get('legalArea', ''),
                'publisher': (user_metadata or {}).get('publisher') or pdf_metadata.get('producer', ''),
                'isbn': (user_metadata or {}).get('isbn', ''),
                'fileSize': len(pdf_metadata.get('filename', '')),
                'mimeType': 'application/pdf',
                'totalPages': pdf_metadata.get('total_pages', 0),
                'pagesWithText': pdf_metadata.get('pages_with_text', 0)
            }
            
            if storage_path:
                metadata['storagePath'] = storage_path
            
            # Add existing storage URL if provided
            if user_metadata and user_metadata.get('existingStorageUrl'):
                metadata['existingStorageUrl'] = user_metadata['existingStorageUrl']
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to prepare document metadata: {e}")
            raise
    
    async def _process_chunks(self, chunks: List, document_metadata: Dict):
        """Process chunks: generate embeddings and store in vector database"""
        try:
            logger.info(f"Processing {len(chunks)} chunks for embeddings")
            
            # Check if we have any chunks
            if not chunks:
                raise ValueError("No chunks to process")
            
            # Prepare texts for embedding
            chunk_texts = []
            for i, chunk in enumerate(chunks):
                if not chunk.text or not chunk.text.strip():
                    logger.warning(f"Empty chunk text at index {i}, using placeholder")
                    chunk_texts.append(f"[Empty chunk {i}]")
                else:
                    chunk_texts.append(chunk.text)
            
            logger.info(f"Prepared {len(chunk_texts)} texts for embedding")
            
            # Generate embeddings in batches
            batch_size = 50  # Vertex AI can handle larger batches
            embeddings = []
            
            try:
                for i in range(0, len(chunk_texts), batch_size):
                    batch_texts = chunk_texts[i:i + batch_size]
                    logger.info(f"Generating embeddings for batch {i//batch_size + 1} ({len(batch_texts)} texts)")
                    
                    batch_embeddings = self.embedding_service.get_embeddings(batch_texts)
                    
                    if not batch_embeddings:
                        raise ValueError(f"No embeddings returned for batch {i//batch_size + 1}")
                    
                    if len(batch_embeddings) != len(batch_texts):
                        raise ValueError(f"Embedding count mismatch: {len(batch_embeddings)} != {len(batch_texts)}")
                    
                    embeddings.extend(batch_embeddings)
                    logger.info(f"Batch {i//batch_size + 1} completed, total embeddings: {len(embeddings)}")
                
            except Exception as embedding_error:
                logger.error(f"Embedding generation failed: {embedding_error}")
                raise
            
            # Validate embeddings
            if len(embeddings) != len(chunks):
                raise ValueError(f"Embedding count mismatch: {len(embeddings)} embeddings for {len(chunks)} chunks")
            
            # Prepare vector data for storage
            vector_data = []
            chunk_metadata_batch = []
            
            for chunk, embedding in zip(chunks, embeddings):
                # Validate embedding
                if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                    raise ValueError(f"Invalid embedding for chunk {chunk.chunk_id}")
                
                # Vector data for Vertex AI
                vector_data.append({
                    'id': chunk.chunk_id,
                    'embedding': embedding,
                    'metadata': {
                        'legal_area': document_metadata.get('legalArea', ''),
                        'author': document_metadata.get('author', ''),
                        'title': document_metadata.get('title', '')
                    }
                })
                
                # Chunk metadata for Firestore
                chunk_metadata_batch.append({
                    'chunk_id': chunk.chunk_id,
                    'text': chunk.text,
                    'document_id': chunk.document_id,
                    'page_number': chunk.page_number,
                    'chunk_index': chunk.chunk_index,
                    'section_title': chunk.section_title,
                    'document_metadata': document_metadata,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"Prepared {len(vector_data)} vectors and {len(chunk_metadata_batch)} metadata records")
            
            # Store vectors in Vertex AI
            logger.info("Storing vectors in Vertex AI")
            try:
                success = self.vector_store.add_vectors(vector_data)
                if not success:
                    raise Exception("Vector store returned False")
                logger.info("Vector storage successful")
            except Exception as vector_error:
                logger.error(f"Vector storage failed: {vector_error}")
                raise
            
            # Store chunk metadata in Firestore in batches
            logger.info(f"Storing {len(chunk_metadata_batch)} chunk metadata records in Firestore")
            try:
                # Firestore batch limit is 500 operations
                batch_size = 450  # Leave some margin
                
                for i in range(0, len(chunk_metadata_batch), batch_size):
                    batch = self.db.db.batch()
                    batch_chunk_meta = chunk_metadata_batch[i:i + batch_size]
                    
                    for chunk_meta in batch_chunk_meta:
                        doc_ref = self.db.db.collection('textbook_chunks').document(chunk_meta['chunk_id'])
                        batch.set(doc_ref, chunk_meta)
                    
                    batch.commit()
                    logger.info(f"Committed Firestore batch {i//batch_size + 1} ({len(batch_chunk_meta)} records)")
                
                logger.info("All chunk metadata stored successfully")
                
            except Exception as firestore_error:
                logger.error(f"Firestore metadata storage failed: {firestore_error}")
                raise
            
            logger.info(f"Successfully processed {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Failed to process chunks: {e}")
            logger.exception("Detailed chunk processing error:")
            raise
    
    async def delete_textbook(self, document_id: str) -> bool:
        """
        Delete a textbook and all its associated data
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Starting deletion of textbook {document_id}")
            
            # Get document metadata
            doc_ref = self.db.db.collection('referenceMaterials').document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Document {document_id} not found")
                return False
            
            doc_data = doc.to_dict()
            
            # Delete from Firebase Storage
            if self.bucket and doc_data.get('storagePath'):
                try:
                    blob = self.bucket.blob(doc_data['storagePath'])
                    blob.delete()
                    logger.info(f"Deleted file from storage: {doc_data['storagePath']}")
                except Exception as e:
                    logger.warning(f"Failed to delete from storage: {e}")
            
            # Get all chunk IDs for this document
            chunks_query = (self.db.db.collection('textbook_chunks')
                          .where('document_id', '==', document_id))
            chunks = chunks_query.get()
            
            chunk_ids = [chunk.id for chunk in chunks]
            logger.info(f"Found {len(chunk_ids)} chunks to delete")
            
            # Delete vectors from Vertex AI
            if chunk_ids:
                try:
                    self.vector_store.delete_vectors(chunk_ids)
                    logger.info(f"Deleted {len(chunk_ids)} vectors from Vertex AI")
                except Exception as e:
                    logger.error(f"Failed to delete vectors: {e}")
                    # Continue with other deletions
            
            # Delete chunks from Firestore in batches
            if chunks:
                batch_size = 450
                for i in range(0, len(chunks), batch_size):
                    batch = self.db.db.batch()
                    batch_chunks = chunks[i:i + batch_size]
                    
                    for chunk in batch_chunks:
                        batch.delete(chunk.reference)
                    
                    batch.commit()
                    logger.info(f"Deleted Firestore batch {i//batch_size + 1}")
            
            # Delete document record
            doc_ref.delete()
            logger.info(f"Deleted document record {document_id}")
            
            logger.info(f"Successfully deleted textbook {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete textbook {document_id}: {e}")
            logger.exception("Detailed deletion error:")
            return False

# Singleton instance
_ingestion_pipeline = None

def get_ingestion_pipeline():
    """Get singleton ingestion pipeline instance"""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = TextbookIngestionPipeline()
    return _ingestion_pipeline