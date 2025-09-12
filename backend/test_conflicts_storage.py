"""
Test script for conflicts storage functionality
"""

import asyncio
import json
from app import SearchRequest, search_legal_content
from firebase.db import get_firestore_db

async def test_conflicts_storage():
    """Test storing search results in conflicts collection"""
    
    print("🧪 Testing conflicts storage functionality...")
    
    # Test data
    test_doc_id = "test_document_123"
    test_query = "contract law"
    
    # Create search request with doc_id
    search_request = SearchRequest(
        query=test_query,
        search_type="both",
        user_id="test_user",
        doc_id=test_doc_id
    )
    
    try:
        # Call the search endpoint
        print(f"🔍 Performing search for: {test_query}")
        result = await search_legal_content(search_request)
        
        print("✅ Search completed successfully")
        print(f"📊 Search result status: {result.get('status')}")
        print(f"🆔 Conflict ID: {result.get('conflict_id', 'Not stored')}")
        
        # Verify the conflict was stored in the database
        if result.get('conflict_id'):
            db = get_firestore_db()
            
            # Get the conflict document
            conflict_doc = db.db.collection('conflicts').document(result['conflict_id']).get()
            
            if conflict_doc.exists:
                conflict_data = conflict_doc.to_dict()
                print("✅ Conflict document found in database")
                print(f"📄 Document ID: {conflict_data.get('doc_id')}")
                print(f"⏰ Timestamp: {conflict_data.get('timestamp')}")
                print(f"📊 Search results keys: {list(conflict_data.get('search_results', {}).keys())}")
            else:
                print("❌ Conflict document not found in database")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

async def test_search_without_doc_id():
    """Test search without doc_id (should not store in conflicts)"""
    
    print("\n🧪 Testing search without doc_id...")
    
    # Create search request without doc_id
    search_request = SearchRequest(
        query="legal research",
        search_type="both",
        user_id="test_user"
        # No doc_id provided
    )
    
    try:
        result = await search_legal_content(search_request)
        
        print("✅ Search completed successfully")
        print(f"📊 Search result status: {result.get('status')}")
        print(f"🆔 Conflict ID: {result.get('conflict_id', 'Not stored')}")
        
        if 'conflict_id' not in result:
            print("✅ Correctly did not store in conflicts collection")
        else:
            print("❌ Unexpectedly stored in conflicts collection")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Starting conflicts storage tests...")
    
    # Run tests
    asyncio.run(test_conflicts_storage())
    asyncio.run(test_search_without_doc_id())
    
    print("\n✨ Tests completed!") 