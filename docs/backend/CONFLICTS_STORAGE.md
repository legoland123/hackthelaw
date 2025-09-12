# Conflicts Storage Feature

## Overview

The `/search` endpoint now supports storing search results in a dedicated `conflicts` collection when a document ID is provided. This allows tracking which search results are associated with specific documents for conflict resolution purposes.

## How It Works

### 1. Search Request with Document ID

When calling the `/search` endpoint, you can now include a `doc_id` parameter:

```json
{
  "query": "contract law",
  "search_type": "both",
  "user_id": "user123",
  "doc_id": "document_456"
}
```

### 2. Automatic Storage

If a `doc_id` is provided:
- The search results are stored in the `conflicts` collection
- A new document is created with an auto-generated ID
- The document contains:
  - `doc_id`: The original document ID that triggered the search
  - `search_results`: The complete search results JSON
  - `timestamp`: When the conflict was stored

### 3. Response Enhancement

The search response now includes a `conflict_id` field when a document ID was provided:

```json
{
  "status": "success",
  "data": { /* search results */ },
  "cached": false,
  "conflict_id": "auto_generated_conflict_id"
}
```

## Database Schema

### Conflicts Collection

```
conflicts/{auto_id}
├── doc_id: string          // Original document ID
├── search_results: object  // Complete search results
└── timestamp: timestamp    // When stored
```

## Usage Examples

### 1. Direct API Call

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "contract law",
    "search_type": "both",
    "user_id": "user123",
    "doc_id": "document_456"
  }'
```

### 2. From Upload Endpoint

The `/upload/{proj_id}/{doc_id}` endpoint automatically passes the document ID when performing legal searches for conflict resolution.

### 3. Without Document ID

If no `doc_id` is provided, the search works as before without storing in the conflicts collection:

```json
{
  "query": "contract law",
  "search_type": "both",
  "user_id": "user123"
  // No doc_id - won't store in conflicts
}
```

## Benefits

1. **Conflict Tracking**: Associate search results with specific documents
2. **Audit Trail**: Track when conflicts were identified
3. **Document Association**: Link legal research to document versions
4. **Conflict Resolution**: Enable UI to show conflicts for specific documents

## Testing

Run the test script to verify functionality:

```bash
cd backend
python test_conflicts_storage.py
```

## Error Handling

- If storing in conflicts collection fails, the search still completes successfully
- A warning is logged but the error doesn't affect the main search functionality
- The `conflict_id` is only included in the response if storage was successful 