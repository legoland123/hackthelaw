# Backend Upload Process Documentation

## Overview

The backend upload process handles document processing and AI analysis after documents are uploaded to Firebase Storage. This process extracts text content from uploaded documents, compares them with master copies, and stores the results for AI-powered legal analysis.

## Endpoint Details

### POST `/upload/{proj_id}/{doc_id}`

**Purpose**: Process uploaded legal content for AI analysis

**Parameters**:
- `proj_id` (string): Project identifier
- `doc_id` (string): Document identifier

**Request Body**: None (uses path parameters)

**Response Format**:
```json
{
  "status": "success",
  "message": "Document processed successfully",
  "document_id": "doc_123",
  "extracted_content_length": 1500,
  "comparison_performed": true,
  "comparison_result": {
    "added_clauses": [...],
    "removed_clauses": [...],
    "modified_clauses": [...]
  }
}
```

## Processing Flow

### 1. Document Retrieval
```python
# Fetch the uploaded document from Firestore
doc_ref = db.collection('documents').document(doc_id)
doc = doc_ref.get()

if not doc.exists:
    raise HTTPException(status_code=404, detail="Document not found")

doc_data = doc.to_dict()
```

### 2. File URL Validation
```python
# Check if document has file information
if not doc_data.get('fileInfo') or not doc_data['fileInfo'].get('downloadURL'):
    raise HTTPException(status_code=400, detail="Document has no file URL")
```

### 3. Text Extraction
```python
# Extract text from the uploaded document using Groq
extracted_doc_text = groq_convert_media_to_text(doc_data['fileInfo']['downloadURL'])
```

### 4. Project and Master Copy Handling
```python
# Fetch project data
proj_ref = db.collection('projects').document(proj_id)
proj = proj_ref.get()

if not proj.exists:
    raise HTTPException(status_code=404, detail="Project not found")

proj_data = proj.to_dict()

# Check if project has a master copy
if not proj_data.get('masterCopyId'):
    # Skip comparison, just store extracted content
    await db.update_document(doc_id, {
        'extractedContent': extracted_doc_text,
        'processedAt': datetime.now().isoformat(),
        'processingStatus': 'completed'
    })
```

### 5. Master Copy Processing
```python
# Fetch master copy document
master_doc_ref = db.collection('documents').document(proj_data['masterCopyId'])
master_doc = master_doc_ref.get()

if not master_doc.exists:
    # Skip comparison, just store extracted content
    await db.update_document(doc_id, {
        'extractedContent': extracted_doc_text,
        'processedAt': datetime.now().isoformat(),
        'processingStatus': 'completed'
    })

master_doc_data = master_doc.to_dict()

# Extract text from master copy if not already done
if not master_doc_data.get('extractedContent'):
    extracted_master_text = groq_convert_media_to_text(master_doc_data['fileInfo']['downloadURL'])
    # Update master copy with extracted content
    await db.update_document(proj_data['masterCopyId'], {
        'extractedContent': extracted_master_text,
        'processedAt': datetime.now().isoformat()
    })
else:
    extracted_master_text = master_doc_data['extractedContent']
```

### 6. Document Comparison
```python
# Perform clause comparison if both documents have content
comparison_result = None
if extracted_doc_text and extracted_master_text:
    try:
        # Convert both documents to clause format
        doc_clauses = groq_convert_input_to_clause(extracted_doc_text)
        master_clauses = groq_convert_input_to_clause(extracted_master_text)
        
        # Find differences between clauses
        comparison_result = groq_find_clause_diff(doc_clauses, master_clauses)
        
        logger.info(f"Successfully compared document {doc_id} with master copy")
    except Exception as e:
        logger.error(f"Failed to compare documents: {e}")
        comparison_result = {"error": str(e)}
```

### 7. Result Storage
```python
# Update document with extracted content and comparison results
update_data = {
    'extractedContent': extracted_doc_text,
    'processedAt': datetime.now().isoformat(),
    'processingStatus': 'completed'
}

if comparison_result:
    update_data['comparisonResult'] = comparison_result

await db.update_document(doc_id, update_data)
```

## Error Handling

### HTTP Status Codes
- `200`: Success - Document processed successfully
- `400`: Bad Request - Document has no file URL
- `404`: Not Found - Document or project not found
- `500`: Internal Server Error - Processing failed

### Error Scenarios
1. **Document not found**: Returns 404 with appropriate message
2. **Project not found**: Returns 404 with appropriate message
3. **Missing file URL**: Returns 400 with appropriate message
4. **Text extraction failure**: Returns 500 with error details
5. **Comparison failure**: Continues processing but logs error
6. **Database update failure**: Returns 500 with error details

## Database Schema Updates

### Document Collection Updates
The process adds the following fields to document records:

```json
{
  "extractedContent": "Extracted text content from the document",
  "processedAt": "2024-01-15T10:30:00.000Z",
  "processingStatus": "completed",
  "comparisonResult": {
    "added_clauses": [...],
    "removed_clauses": [...],
    "modified_clauses": [...],
    "error": "Error message if comparison failed"
  }
}
```

## Dependencies

### Required Python Packages
- `fastapi`: Web framework
- `firebase-admin`: Firebase integration
- `google-generativeai`: LLM processing
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation

### External Services
- **Firebase Firestore**: Document storage
- **Firebase Storage**: File storage
- **Groq API**: Text extraction and processing
- **Google Generative AI**: LLM processing

## Testing

### Manual Testing
1. **Start the backend server**:
   ```bash
   cd backend
   python run_app.py
   ```

2. **Use the test script**:
   ```bash
   python test_upload_endpoint.py
   ```

3. **Test with curl**:
   ```bash
   curl -X POST http://localhost:8000/upload/test_project_id/test_document_id
   ```

### Test Scenarios
1. **Valid document with master copy**: Should perform comparison
2. **Valid document without master copy**: Should skip comparison
3. **Non-existent document**: Should return 404
4. **Non-existent project**: Should return 404
5. **Document without file URL**: Should return 400

## Logging

### Log Levels
- `INFO`: Successful operations
- `WARNING`: Non-critical issues (e.g., missing master copy)
- `ERROR`: Processing failures

### Log Messages
```
INFO: Successfully extracted text from document doc_123
INFO: Successfully compared document doc_123 with master copy
WARNING: Master copy document not found, skipping comparison
ERROR: Failed to extract text from document doc_123: [error details]
```

## Performance Considerations

### Processing Time
- **Text extraction**: 5-30 seconds (depending on document size)
- **Clause conversion**: 10-60 seconds (depending on content complexity)
- **Comparison**: 15-90 seconds (depending on document differences)

### Optimization Strategies
1. **Caching**: Extracted content is stored to avoid re-processing
2. **Async processing**: Non-blocking operations where possible
3. **Error recovery**: Graceful handling of partial failures

## Security Considerations

### Input Validation
- Validates document and project existence
- Checks file URL availability
- Sanitizes error messages

### Access Control
- Relies on Firebase security rules
- No direct file system access
- Secure API key management

## Monitoring and Maintenance

### Health Checks
- Endpoint availability: `GET /health`
- Database connectivity: Firebase connection status
- External service status: Groq API availability

### Maintenance Tasks
1. **Clean up old processing logs**
2. **Monitor API rate limits**
3. **Update external service credentials**
4. **Review and optimize processing times**

## Troubleshooting

### Common Issues
1. **Firebase connection errors**: Check credentials and network
2. **Groq API failures**: Verify API key and rate limits
3. **Memory issues**: Monitor document size limits
4. **Timeout errors**: Adjust processing timeouts

### Debug Steps
1. Check application logs
2. Verify Firebase document structure
3. Test external API connectivity
4. Review error response details

## Future Enhancements

### Planned Features
1. **Batch processing**: Handle multiple documents
2. **Progress tracking**: Real-time processing status
3. **Advanced comparison**: Semantic similarity analysis
4. **Version control**: Track document evolution over time

### Performance Improvements
1. **Parallel processing**: Multiple documents simultaneously
2. **Caching layer**: Redis for frequently accessed data
3. **CDN integration**: Faster file access
4. **Queue system**: Background job processing 