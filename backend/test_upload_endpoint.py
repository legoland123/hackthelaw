#!/usr/bin/env python3
"""
Test script for the upload endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys
from datetime import datetime
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# The GOOGLE_CLOUD_PROJECT environment variable should be loaded from your .env file
# for the embedding service to initialize correctly.

# We are not mocking the embedding service to test its initialization.
patch('backend.legal_memory.llm_processor.LLMProcessor', MagicMock()).start()

# Patch all external dependencies before importing the app
mock_app_sentinel = MagicMock()
with patch('firebase_admin.credentials.Certificate'), \
     patch('firebase_admin.initialize_app'), \
     patch('firebase_admin.get_app', return_value=mock_app_sentinel), \
     patch('firebase_admin._apps', {'[DEFAULT]': mock_app_sentinel}), \
     patch('firebase_admin.storage.bucket'), \
     patch('firebase_admin.firestore.client'), \
     patch('os.path.exists', return_value=True), \
     patch('backend.legal_memory.llm_processor.LLMProcessor'):
    from backend.app import app, SearchRequest

client = TestClient(app)

@patch('backend.app.get_firestore_db')
@patch('backend.app.groq_convert_media_to_text')
@patch('backend.app.groq_check_input_format')
@patch('backend.app.groq_convert_input_to_clause')
@patch('backend.app.pdf_generator')
@patch('backend.app.storage_manager')
@pytest.mark.asyncio
async def test_upload_new_master_copy(
    mock_storage_manager,
    mock_pdf_generator,
    mock_groq_input_to_clause,
    mock_groq_check_format,
    mock_groq_media_to_text,
    mock_get_db
):
    # --- Mocks for Firestore ---
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock document snapshot
    mock_doc_snapshot = MagicMock()
    mock_doc_snapshot.exists = True
    mock_doc_snapshot.to_dict.return_value = {
        'fileInfo': {'downloadURL': 'https://firebasestorage.googleapis.com/v0/b/hackthelaw-smulit-4fec4.firebasestorage.app/o/documents%2FAe2AYnRUbJiNfFiedczo%2F1750504650491_Service_Agreement_Sample.pdf?alt=media&token=60fdb8cd-3d81-435c-80e5-28515af96a8e'},
        'title': 'Test Document'
    }

    # Mock project snapshot (no master copy)
    mock_proj_snapshot = MagicMock()
    mock_proj_snapshot.exists = True
    mock_proj_snapshot.to_dict.return_value = {
        'name': 'Test Project',
        'masterCopyId': None
    }

    # Correctly mock the chained calls for db.collection(...).document(...).get()
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc_snapshot
    mock_proj_ref = MagicMock()
    mock_proj_ref.get.return_value = mock_proj_snapshot

    def document_side_effect(doc_id):
        if doc_id == 'test_doc':
            return mock_doc_ref
        if doc_id == 'test_proj':
            return mock_proj_ref
        return MagicMock() # Default mock for other calls

    mock_collection_ref = MagicMock()
    mock_collection_ref.document.side_effect = document_side_effect
    mock_db.collection.return_value = mock_collection_ref

    # Mock the 'add' call for creating the master document
    mock_master_doc_ref = MagicMock()
    mock_master_doc_ref.id = 'new_master_id'
    mock_collection_ref.add.return_value = (datetime.now(), mock_master_doc_ref)

    # --- Mocks for Groq, PDF, and Storage ---
    mock_groq_media_to_text.return_value = "raw text from document"
    mock_groq_check_format.return_value = False
    mock_groq_input_to_clause.return_value = "clause 1: converted text"
    mock_pdf_generator.text_to_pdf.return_value = b"pdf_bytes"
    mock_storage_manager.upload_pdf_bytes.return_value = "https://firebasestorage.googleapis.com/v0/b/hackthelaw-smulit-4fec4.firebasestorage.app/o/documents%2FAe2AYnRUbJiNfFiedczo%2F1750506429720_Service_Agreement_Follow_Up.pdf?alt=media&token=dacaffab-fc42-4fbe-9b5e-1c3707c2dbdb"

    # --- Call the endpoint ---
    response = client.post("/upload/test_proj/test_doc")

    # --- Assertions ---
    assert response.status_code == 200
    json_response = response.json()
    assert json_response['status'] == 'success'
    assert json_response['master_copy_id'] == 'new_master_id'

    # Verify calls
    mock_get_db.assert_called_once()
    mock_groq_media_to_text.assert_called_once_with('https://firebasestorage.googleapis.com/v0/b/hackthelaw-smulit-4fec4.firebasestorage.app/o/documents%2FAe2AYnRUbJiNfFiedczo%2F1750504650491_Service_Agreement_Sample.pdf?alt=media&token=60fdb8cd-3d81-435c-80e5-28515af96a8e')
    mock_groq_check_format.assert_called_once_with("raw text from document")
    mock_groq_input_to_clause.assert_called_once_with("raw text from document")
    mock_pdf_generator.text_to_pdf.assert_called_once_with("clause 1: converted text", "Master Copy - Test Project")
    mock_storage_manager.upload_pdf_bytes.assert_called_once_with(b"pdf_bytes", "master_copy_test_proj.pdf", "projects/test_proj")
    
    # Check that project was updated with the new master ID
    mock_proj_ref.update.assert_called_once()
    update_args = mock_proj_ref.update.call_args[0][0]
    assert update_args['masterCopyId'] == 'new_master_id'

    # Check that the original document was updated
    mock_doc_ref.update.assert_called_once()
    update_args = mock_doc_ref.update.call_args[0][0]
    assert update_args['extractedContent'] == "raw text from document"
    assert 'processedAt' in update_args
    assert update_args['processingStatus'] == 'completed'


@patch('backend.app.search_legal_content', new_callable=AsyncMock)
@patch('backend.app.get_firestore_db')
@patch('backend.app.groq_convert_media_to_text')
@patch('backend.app.groq_check_input_format')
@patch('backend.app.groq_convert_input_to_clause')
@patch('backend.app.groq_find_clause_diff')
@patch('backend.app.groq_find_semantics')
@pytest.mark.asyncio
async def test_upload_with_comparison(
    mock_groq_find_semantics,
    mock_groq_find_clause_diff,
    mock_groq_input_to_clause,
    mock_groq_check_format,
    mock_groq_media_to_text,
    mock_get_db,
    mock_search_legal_content
):
    # --- Mocks for Firestore ---
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock document snapshots
    mock_uploaded_doc_snap = MagicMock()
    mock_uploaded_doc_snap.exists = True
    mock_uploaded_doc_snap.to_dict.return_value = {'fileInfo': {'downloadURL': 'https://firebasestorage.googleapis.com/v0/b/hackthelaw-smulit-4fec4.firebasestorage.app/o/documents%2FAe2AYnRUbJiNfFiedczo%2F1750504650491_Service_Agreement_Sample.pdf?alt=media&token=60fdb8cd-3d81-435c-80e5-28515af96a8e'}}

    mock_master_doc_snap = MagicMock()
    mock_master_doc_snap.exists = True
    mock_master_doc_snap.to_dict.return_value = {
        'fileInfo': {'downloadURL': 'http://example.com/master.pdf'},
        'extractedContent': 'clause 1: master content'
    }

    # Mock project snapshot
    mock_proj_snapshot = MagicMock()
    mock_proj_snapshot.exists = True
    mock_proj_snapshot.to_dict.return_value = {
        'name': 'Test Project',
        'masterCopyId': 'existing_master_id'
    }

    # Correctly mock the chained calls for db.collection(...).document(...).get()
    mock_uploaded_doc_ref = MagicMock()
    mock_uploaded_doc_ref.get.return_value = mock_uploaded_doc_snap
    mock_master_doc_ref = MagicMock()
    mock_master_doc_ref.get.return_value = mock_master_doc_snap
    mock_proj_ref = MagicMock()
    mock_proj_ref.get.return_value = mock_proj_snapshot

    def document_side_effect(doc_id):
        if doc_id == 'test_doc':
            return mock_uploaded_doc_ref
        if doc_id == 'test_proj':
            return mock_proj_ref
        if doc_id == 'existing_master_id':
            return mock_master_doc_ref
        return MagicMock()

    mock_collection_ref = MagicMock()
    mock_collection_ref.document.side_effect = document_side_effect
    mock_db.collection.return_value = mock_collection_ref

    # --- Mocks for Groq functions ---
    mock_groq_media_to_text.return_value = "raw text from uploaded doc"
    mock_groq_check_format.side_effect = [False, True]  # uploaded doc, master doc
    mock_groq_input_to_clause.return_value = "clause 1: uploaded content"
    mock_groq_find_clause_diff.return_value = "differences"
    mock_groq_find_semantics.return_value = '{"semantics": [["semantic1", "semantic2"]]}'