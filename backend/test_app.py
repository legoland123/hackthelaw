#!/usr/bin/env python3
"""
Test script for the Legal Memory Tool Flask API
"""

import requests
import json
import sys
from pathlib import Path

# API base URL
API_BASE = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API. Make sure it's running on localhost:5000")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_get_endpoint(fileID):
    """Test the GET /get/<fileID> endpoint"""
    print(f"📄 Testing GET /get/{fileID}...")
    try:
        response = requests.get(f"{API_BASE}/get/{fileID}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Job data retrieved successfully:")
            print(f"   Status: {data.get('status')}")
            print(f"   FileID: {data.get('fileID')}")
            print(f"   Has JSON data: {'json_data' in data}")
            print(f"   Has file address: {'file_address' in data}")
            print(f"   Has download URL: {'download_url' in data}")
            return True
        elif response.status_code == 404:
            data = response.json()
            print(f"⚠️ Job not found: {data.get('error')}")
            return True  # This is expected for non-existent fileIDs
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ GET endpoint error: {e}")
        return False

def test_jobs_endpoint(fileID):
    """Test the GET /jobs/<fileID> endpoint"""
    print(f"📊 Testing GET /jobs/{fileID}...")
    try:
        response = requests.get(f"{API_BASE}/jobs/{fileID}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Job status retrieved successfully:")
            print(f"   Status: {data.get('status')}")
            print(f"   Job Status: {data.get('job_status')}")
            print(f"   Has JSON data: {data.get('has_json_data')}")
            print(f"   Has file address: {data.get('has_file_address')}")
            print(f"   Has download URL: {data.get('has_download_url')}")
            return True
        elif response.status_code == 404:
            data = response.json()
            print(f"⚠️ Job not found: {data.get('message')}")
            return True  # This is expected for non-existent fileIDs
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Jobs endpoint error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Legal Memory Tool API Test Suite")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health_endpoint():
        print("\n❌ Health check failed. API may not be running.")
        print("💡 Start the API with: python run_api.py")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Test with sample fileIDs
    test_fileIDs = [
        "sample_file_123",
        "test_document_456",
        "nonexistent_file_999"
    ]
    
    for fileID in test_fileIDs:
        print(f"\n🔍 Testing with fileID: {fileID}")
        print("-" * 30)
        
        # Test both endpoints
        get_success = test_get_endpoint(fileID)
        jobs_success = test_jobs_endpoint(fileID)
        
        if get_success and jobs_success:
            print(f"✅ All tests passed for fileID: {fileID}")
        else:
            print(f"❌ Some tests failed for fileID: {fileID}")
    
    print("\n" + "=" * 50)
    print("🎉 API test suite completed!")
    print("\n💡 To test with real fileIDs, modify the test_fileIDs list in this script.")

if __name__ == "__main__":
    main() 