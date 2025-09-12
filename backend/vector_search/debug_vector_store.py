#!/usr/bin/env python3
"""
Debug script to test vector store operations separately
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add your project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_embeddings_and_vector_store():
    """Test embeddings and vector store separately"""
    
    try:
        # Test 1: Check environment variables
        logger.info("=== Environment Variables ===")
        env_vars = [
            'GOOGLE_CLOUD_PROJECT',
            'VERTEX_AI_EMBEDDINGS_LOCATION',
            'VERTEX_AI_VECTOR_SEARCH_LOCATION',
            'VECTOR_SEARCH_INDEX_ID',
            'VECTOR_SEARCH_ENDPOINT_ID',
            'VECTOR_SEARCH_DEPLOYED_INDEX_ID'
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"✓ {var}: {value}")
            else:
                logger.error(f"✗ {var}: NOT SET")
        
        # Test 2: Test embeddings in US Central
        logger.info("\n=== Testing Embeddings (US Central) ===")
        from vector_search.embeddings import get_embedding_service
        
        embedding_service = get_embedding_service()
        logger.info(f"Embedding service initialized with model: {embedding_service.model_name}")
        logger.info(f"Embeddings location: {embedding_service.embeddings_location}")
        
        # Test single embedding
        test_text = "This is a test document for legal research."
        embedding = embedding_service.get_single_embedding(test_text)
        logger.info(f"✓ Single embedding successful: {len(embedding)} dimensions")
        logger.info(f"First 5 values: {embedding[:5]}")
        
        # Test 3: Test vector store initialization (Singapore)
        logger.info("\n=== Testing Vector Store Initialization (Singapore) ===")
        from vector_search.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        logger.info(f"Vector store initialized in: {vector_store.vector_search_location}")
        logger.info(f"Index ID: {vector_store.index_id}")
        logger.info(f"Endpoint ID: {vector_store.endpoint_id}")
        logger.info(f"Deployed Index ID: {vector_store.deployed_index_id}")
        
        # Test 4: Test adding a single vector
        logger.info("\n=== Testing Vector Addition ===")
        test_vector_data = [{
            'id': 'debug_test_vector_001',
            'embedding': embedding,
            'metadata': {
                'title': 'Debug Test Document',
                'legal_area': 'Test',
                'author': 'Debug'
            }
        }]
        
        logger.info(f"Attempting to add test vector with ID: {test_vector_data[0]['id']}")
        logger.info(f"Embedding dimension: {len(test_vector_data[0]['embedding'])}")
        logger.info(f"Metadata: {test_vector_data[0]['metadata']}")
        
        success = vector_store.add_vectors(test_vector_data)
        
        if success:
            logger.info("✓ Vector addition successful!")
        else:
            logger.error("✗ Vector addition failed - returned False")
            return
        
        # Test 5: Test vector search
        logger.info("\n=== Testing Vector Search ===")
        search_results = vector_store.search_vectors(
            query_vector=embedding,
            num_neighbors=3
        )
        
        if search_results:
            logger.info(f"✓ Vector search successful: {len(search_results)} results")
            for i, result in enumerate(search_results):
                logger.info(f"  Result {i}: ID={result['id']}, similarity={result['similarity_score']:.3f}")
        else:
            logger.warning("Vector search returned no results")
        
        # Test 6: Clean up test vector
        logger.info("\n=== Cleaning Up Test Vector ===")
        cleanup_success = vector_store.delete_vectors(['debug_test_vector_001'])
        if cleanup_success:
            logger.info("✓ Test vector cleanup successful")
        else:
            logger.warning("Test vector cleanup failed")
        
        logger.info("\n=== All Tests Completed ===")
        
    except Exception as e:
        logger.error(f"Debug test failed: {e}")
        logger.exception("Error details:")

def check_vertex_ai_apis():
    """Check if required Vertex AI APIs are enabled"""
    try:
        logger.info("\n=== Checking Vertex AI API Access ===")
        
        # Test embedding model access
        logger.info("Testing embedding model access...")
        from google.cloud import aiplatform
        from vertexai.language_models import TextEmbeddingModel
        
        # Initialize for embeddings
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        embeddings_location = os.getenv('VERTEX_AI_EMBEDDINGS_LOCATION', 'us-central1')
        
        aiplatform.init(project=project_id, location=embeddings_location)
        
        # Try to load model
        model = TextEmbeddingModel.from_pretrained("text-embedding-004")
        test_embedding = model.get_embeddings(["test"])
        logger.info("✓ Embedding model access successful")
        
        # Test vector search access
        logger.info("Testing vector search access...")
        vector_location = os.getenv('VERTEX_AI_VECTOR_SEARCH_LOCATION', 'asia-southeast1')
        index_id = os.getenv('VECTOR_SEARCH_INDEX_ID')
        
        aiplatform.init(project=project_id, location=vector_location)
        
        from google.cloud.aiplatform import MatchingEngineIndex
        index = MatchingEngineIndex(
            index_name=f"projects/{project_id}/locations/{vector_location}/indexes/{index_id}"
        )
        logger.info("✓ Vector search index access successful")
        
    except Exception as e:
        logger.error(f"API access check failed: {e}")
        logger.exception("API access error details:")

if __name__ == "__main__":
    print("Vector Store Debug Script")
    print("========================")
    
    # Check API access first
    check_vertex_ai_apis()
    
    # Then run detailed tests
    test_embeddings_and_vector_store()