"""
Vertex AI Text Embeddings Service with Separate Region Support
"""

import logging
import os
from typing import List, Dict
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel

logger = logging.getLogger(__name__)

class VertexEmbeddingService:
    """Handle text embeddings using Vertex AI with separate embedding region"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # Use separate region for embeddings (where models are available)
        self.embeddings_location = os.getenv('VERTEX_AI_EMBEDDINGS_LOCATION', 'us-central1')
        
        # Model versions to try (in order of preference)
        self.model_versions = [
            "text-embedding-004",           # Latest model
            "textembedding-gecko@003",      # Your original choice
            "textembedding-gecko@002",      # Fallback 1
            "textembedding-gecko@001",      # Fallback 2
            "textembedding-gecko"           # Base version
        ]
        
        # Validate required environment variables
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        self.model = None
        self.model_name = None
        
        # Try to initialize with available model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Vertex AI embeddings, honoring EMBEDDING_MODEL if set."""
        try:
            # Init Vertex AI in the embeddings region
            aiplatform.init(project=self.project_id, location=self.embeddings_location)
            logger.info(f"Initialized Vertex AI embeddings in {self.embeddings_location}")
    
            # Build candidate list: env model first (if provided), then fallbacks
            env_model = os.getenv("EMBEDDING_MODEL")
            candidates = []
            if env_model:
                candidates.append(env_model)
            # Avoid duplicates if env_model is already in the list
            for m in self.model_versions:
                if m and m not in candidates:
                    candidates.append(m)
    
            # Try each candidate
            for model_name in candidates:
                try:
                    logger.info(f"Trying to load embedding model: {model_name}")
                    model = TextEmbeddingModel.from_pretrained(model_name)
    
                    # Probe the model and record the dimension
                    probe = model.get_embeddings(["test"])
                    if not probe:
                        raise RuntimeError("No embeddings returned in probe call")
    
                    vec = probe[0].values if hasattr(probe[0], "values") else probe[0]
                    dim = len(vec)
    
                    self.model = model
                    self.model_name = model_name
                    logger.info(
                        f"Successfully initialized embedding model: {model_name} "
                        f"in {self.embeddings_location} (dim={dim})"
                    )
                    return
                except Exception as model_error:
                    logger.warning(f"Embedding model {model_name} failed: {model_error}")
                    continue
                
            raise ValueError(f"No embedding models available in region {self.embeddings_location}")
    
        except Exception as e:
            logger.error(f"Failed to initialize any embedding model: {e}")
            raise
        
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                logger.warning("Empty text list provided for embeddings")
                return []
            
            if not self.model:
                raise ValueError("No embedding model available")
            
            # Validate and clean texts
            cleaned_texts = []
            for i, text in enumerate(texts):
                if text is None:
                    logger.warning(f"None text at index {i}, using placeholder")
                    cleaned_texts.append("[Empty text]")
                elif not isinstance(text, str):
                    logger.warning(f"Non-string text at index {i}: {type(text)}, converting to string")
                    cleaned_texts.append(str(text))
                elif not text.strip():
                    logger.warning(f"Empty/whitespace text at index {i}, using placeholder")
                    cleaned_texts.append("[Empty text]")
                else:
                    # Truncate very long texts (Vertex AI has limits)
                    if len(text) > 20000:  # Conservative limit
                        logger.warning(f"Text at index {i} too long ({len(text)} chars), truncating")
                        cleaned_texts.append(text[:20000] + "...")
                    else:
                        cleaned_texts.append(text)
            
            logger.info(f"Processing {len(cleaned_texts)} texts for embeddings using model {self.model_name} in {self.embeddings_location}")
            
            # Vertex AI can handle batch requests efficiently
            try:
                embeddings = self.model.get_embeddings(cleaned_texts)
            except Exception as model_error:
                logger.error(f"Vertex AI embedding model call failed: {model_error}")
                
                # If the current model fails, try to reinitialize with a different one
                logger.warning("Attempting to reinitialize embedding model...")
                try:
                    # Remove current failed model from list and try others
                    if self.model_name in self.model_versions:
                        self.model_versions.remove(self.model_name)
                    
                    if self.model_versions:
                        self._initialize_model()
                        logger.info(f"Reinitialized with embedding model: {self.model_name}")
                        embeddings = self.model.get_embeddings(cleaned_texts)
                    else:
                        raise ValueError("No more embedding models to try")
                        
                except Exception as reinit_error:
                    logger.error(f"Embedding model reinitialization failed: {reinit_error}")
                    raise model_error  # Raise original error
            
            if not embeddings:
                raise ValueError("No embeddings returned from Vertex AI")
            
            if len(embeddings) != len(cleaned_texts):
                raise ValueError(f"Embedding count mismatch: {len(embeddings)} != {len(cleaned_texts)}")
            
            # Extract the embedding vectors
            embedding_vectors = []
            for i, embedding in enumerate(embeddings):
                try:
                    if hasattr(embedding, 'values'):
                        vector = embedding.values
                    else:
                        vector = embedding
                    
                    # Validate embedding vector
                    if not vector or not isinstance(vector, list):
                        raise ValueError(f"Invalid embedding vector at index {i}")
                    
                    if len(vector) == 0:
                        raise ValueError(f"Empty embedding vector at index {i}")
                    
                    # Validate vector values
                    for j, val in enumerate(vector):
                        if not isinstance(val, (int, float)):
                            raise ValueError(f"Invalid embedding value at index {i}, position {j}: {type(val)}")
                    
                    embedding_vectors.append(vector)
                    
                except Exception as vector_error:
                    logger.error(f"Failed to process embedding at index {i}: {vector_error}")
                    raise
            
            logger.info(f"Generated {len(embedding_vectors)} embeddings successfully with model {self.model_name}")
            
            # Log embedding dimensions for verification
            if embedding_vectors:
                logger.info(f"Embedding dimension: {len(embedding_vectors[0])}")
            
            return embedding_vectors
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            logger.exception("Detailed embedding error:")
            raise
    
    def get_single_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        try:
            if not text:
                logger.warning("Empty text provided for single embedding")
                text = "[Empty text]"
            
            embeddings = self.get_embeddings([text])
            
            if not embeddings:
                raise ValueError("No embedding returned for single text")
            
            return embeddings[0]
            
        except Exception as e:
            logger.error(f"Failed to generate single embedding: {e}")
            raise
    
    def get_query_embedding(self, query: str) -> List[float]:
        """
        Get embedding for search query
        
        Args:
            query: Search query string
            
        Returns:
            Query embedding vector
        """
        try:
            if not query or not query.strip():
                raise ValueError("Empty or invalid query provided")
            
            logger.info(f"Generating embedding for query: {query[:100]}...")
            
            return self.get_single_embedding(query.strip())
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    def validate_embedding_compatibility(self, embedding1: List[float], embedding2: List[float]) -> bool:
        """
        Validate that two embeddings are compatible (same dimensions)
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            bool: True if compatible
        """
        try:
            if not embedding1 or not embedding2:
                return False
            
            if not isinstance(embedding1, list) or not isinstance(embedding2, list):
                return False
            
            return len(embedding1) == len(embedding2)
            
        except Exception as e:
            logger.warning(f"Embedding compatibility check failed: {e}")
            return False

# Singleton instance
_embedding_service = None

def get_embedding_service():
    """Get singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = VertexEmbeddingService()
    return _embedding_service