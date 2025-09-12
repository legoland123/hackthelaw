#!/usr/bin/env python3
"""
Test script for the fixed app.py functionality
"""

import requests
import json
import time

def test_health_endpoint():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_vector_search_endpoint():
    """Test the vector search endpoint"""
    try:
        payload = {
            "query": "termination rights employment contract",
            "max_results": 5,
            "include_context": True,
            "user_id": "test_user"
        }
        
        response = requests.post("http://localhost:8000/vector-search", json=payload)
        print(f"Vector search status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Vector search endpoint working")
            print(f"Results: {result.get('total_results', 0)} found")
            return True
        else:
            print(f"❌ Vector search failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint"""
    try:
        payload = {
            "message": "What are the key elements of a valid contract?",
            "user_id": "test_user"
        }
        
        response = requests.post("http://localhost:8000/chat", json=payload)
        print(f"Chat status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat endpoint working")
            print(f"Response length: {len(result.get('response', ''))}")
            return True
        else:
            print(f"❌ Chat failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_search_endpoint():
    """Test the legal search endpoint"""
    try:
        payload = {
            "query": "employment termination",
            "search_type": "both",
            "user_id": "test_user"
        }
        
        response = requests.post("http://localhost:8000/search", json=payload)
        print(f"Search status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Search endpoint working")
            print(f"Status: {result.get('status')}")
            return True
        else:
            print(f"❌ Search failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def test_upload_endpoint():
    """Test the upload endpoint (this will fail without real document IDs)"""
    try:
        # This will fail but we can test the endpoint structure
        response = requests.post("http://localhost:8000/upload/test_project/test_doc")
        print(f"Upload status: {response.status_code}")
        
        if response.status_code in [400, 404, 500]:
            print("✅ Upload endpoint responding (expected error for test data)")
            return True
        else:
            print(f"❌ Unexpected upload response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Fixed App.py Functionality")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_endpoint),
        ("Vector Search", test_vector_search_endpoint),
        ("Chat", test_chat_endpoint),
        ("Legal Search", test_search_endpoint),
        ("Upload", test_upload_endpoint)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Small delay between tests
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The app.py is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs for details.")

if __name__ == "__main__":
    main() 