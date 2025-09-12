# Fixed App.py - Legal Search API Documentation

## Overview

The `app.py` file has been completely fixed and enhanced to provide a comprehensive legal search and document processing API. The application now includes:

- **Document Processing**: PDF extraction, text processing, and vector indexing
- **Vector Search**: Semantic search using embeddings and vector similarity
- **Legal Research**: Integration with Hansard and LawNet
- **AI Chat**: Conversational AI for legal assistance
- **Document Comparison**: Automated clause comparison and conflict detection

## New Features Added

### 1. Document Processing & PDF Generation
- **PDF Generation**: Convert text content to properly formatted PDF documents
- **Firebase Storage Integration**: Upload generated PDFs to Firebase Storage
- **Text Extraction**: Extract text from various document formats (PDF, DOCX, images)
- **Format Conversion**: Convert informal text to proper legal clause format

### 2. Vector Search System
- **Semantic Search**: Search legal textbooks using vector similarity
- **Document Chunking**: Intelligent text chunking with overlap
- **Vector Indexing**: Add documents to vector search index
- **RAG Pipeline**: Retrieval-Augmented Generation for legal research

### 3. Enhanced Upload Processing
- **Master Copy Creation**: Automatically create master copies for new projects
- **Clause Comparison**: Compare documents and identify differences
- **Semantic Analysis**: Extract semantic meaning from differences
- **Legal Research Integration**: Automatically search for relevant legal precedents

## API Endpoints

### Health Check
```http
GET /health
```
Returns the health status of the API.

### Vector Search
```http
POST /vector-search
```
Search legal textbooks using semantic similarity.

**Request Body:**
```json
{
  "query": "termination rights employment contract",
  "filters": {
    "legal_area": "employment",
    "author": "John Doe"
  },
  "max_results": 10,
  "include_context": true,
  "user_id": "user123"
}
```

**Response:**
```json
{
  "status": "success",
  "query": "termination rights employment contract",
  "results": [...],
  "total_results": 5,
  "documents_found": 3
}
```

### Document Processing
```http
POST /process-document
```
Process a document for vector search by chunking and indexing.

**Request Body:**
```json
{
  "document_id": "doc123",
  "chunk_size": 1000,
  "overlap": 200,
  "user_id": "user123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Document processed for vector search",
  "document_id": "doc123",
  "total_chunks": 15,
  "chunk_size": 1000,
  "overlap": 200,
  "vector_indexed": true
}
```

### Upload Processing
```http
POST /upload/{proj_id}/{doc_id}
```
Process uploaded legal content for AI analysis.

**Response:**
```json
{
  "status": "success",
  "message": "Document processed successfully",
  "document_id": "doc123",
  "extracted_content_length": 2500,
  "comparison_performed": true,
  "comparison_result": {
    "differences": "...",
    "semantics": "...",
    "search_results_count": 3
  }
}
```

### Chat
```http
POST /chat
```
Chat with LIT Legal Mind AI assistant.

**Request Body:**
```json
{
  "message": "What are the key elements of a valid contract?",
  "conversation_history": [...],
  "user_id": "user123",
  "project_id": "proj123",
  "project_context": {...}
}
```

### Legal Search
```http
POST /search
```
Search legal content from Hansard and LawNet.

**Request Body:**
```json
{
  "query": "employment termination",
  "search_type": "both",
  "user_id": "user123"
}
```

## Key Improvements Made

### 1. Fixed Upload Endpoint Logic
- **Corrected variable references**: Fixed `doc.exists` vs `proj.exists` confusion
- **Proper error handling**: Added comprehensive error handling and logging
- **Master copy creation**: Implemented automatic master copy generation
- **Document comparison**: Added proper clause comparison functionality

### 2. PDF Generation & Storage
- **PDF Generator**: Created utility for converting text to PDF
- **Firebase Storage**: Added utility for uploading files to Firebase Storage
- **Format handling**: Proper handling of different document formats

### 3. Vector Search Integration
- **RAG Pipeline**: Integrated with existing vector search system
- **Document chunking**: Intelligent text chunking with sentence boundary detection
- **Vector indexing**: Add documents to vector search index
- **Metadata storage**: Store chunk metadata in Firestore

### 4. Enhanced Error Handling
- **Comprehensive logging**: Added detailed logging throughout
- **Proper HTTP status codes**: Return appropriate HTTP status codes
- **User-friendly error messages**: Clear error messages for debugging

## Dependencies Added

The following dependencies were added to `requirements.txt`:

```txt
# PDF and document processing
reportlab>=4.0.0
PyPDF2>=3.0.0
mammoth>=1.6.0

# Firebase Storage
google-cloud-storage>=2.10.0
```

## New Utility Modules

### 1. PDF Generator (`utils/pdf_generator.py`)
- Convert text content to PDF format
- Custom styling for legal documents
- Support for different content types

### 2. Firebase Storage Manager (`utils/firebase_storage.py`)
- Upload files to Firebase Storage
- Generate download URLs
- File management operations

### 3. Document Chunking (`_create_text_chunks`)
- Intelligent text chunking with overlap
- Sentence boundary detection
- Position tracking for chunks

## Testing

A comprehensive test script (`test_fixed_app.py`) has been created to verify all endpoints:

```bash
cd backend
python test_fixed_app.py
```

The test script checks:
- Health endpoint
- Vector search functionality
- Chat functionality
- Legal search functionality
- Upload endpoint structure

## Usage Examples

### 1. Process a Document for Vector Search
```python
import requests

response = requests.post("http://localhost:8000/process-document", json={
    "document_id": "your_document_id",
    "chunk_size": 1000,
    "overlap": 200
})
```

### 2. Search Legal Textbooks
```python
response = requests.post("http://localhost:8000/vector-search", json={
    "query": "contract termination rights",
    "max_results": 10,
    "include_context": True
})
```

### 3. Upload and Process a Document
```python
response = requests.post("http://localhost:8000/upload/project123/doc456")
```

## Configuration

Ensure the following environment variables are set:

```bash
# Firebase Configuration
FIREBASE_SERVICE_ACCOUNT_PATH=config/firebase-service-account.json

# Vector Search Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_EMBEDDINGS_LOCATION=us-central1
VERTEX_AI_VECTOR_SEARCH_LOCATION=asia-southeast1
VECTOR_SEARCH_INDEX_ID=your-index-id
VECTOR_SEARCH_ENDPOINT_ID=your-endpoint-id
VECTOR_SEARCH_DEPLOYED_INDEX_ID=your-deployed-index-id

# Groq API
GROQ_API_KEY=your-groq-api-key
```

## Troubleshooting

### Common Issues

1. **Firebase Storage Errors**
   - Ensure Firebase service account has Storage permissions
   - Check bucket configuration

2. **Vector Search Errors**
   - Verify Vertex AI APIs are enabled
   - Check vector search index configuration
   - Ensure proper region settings

3. **PDF Generation Errors**
   - Check if ReportLab is properly installed
   - Verify text content is not empty

4. **Document Processing Errors**
   - Ensure document has extracted content
   - Check chunk size parameters

### Debug Steps

1. Check application logs in `app.log`
2. Verify environment variables
3. Test individual components using debug scripts
4. Check Firebase document structure

## Future Enhancements

1. **Batch Processing**: Process multiple documents simultaneously
2. **Progress Tracking**: Real-time processing status updates
3. **Advanced Comparison**: Semantic similarity analysis
4. **Version Control**: Track document evolution over time
5. **Caching**: Implement result caching for better performance

## Support

For issues or questions:
1. Check the logs in `app.log`
2. Review the test script output
3. Verify configuration settings
4. Test individual endpoints separately 