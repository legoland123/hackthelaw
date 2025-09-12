"""
Vertex AI Vector Search Service - Fixed for Batch Updates
"""

import logging
import os
import tempfile
import json
from typing import List, Dict
from google.cloud import aiplatform
from google.cloud import aiplatform_v1beta1 as beta
from google.cloud.aiplatform import MatchingEngineIndex, MatchingEngineIndexEndpoint
from google.cloud import storage

logger = logging.getLogger(__name__)

class VertexVectorStore:
    """Handle vector storage and retrieval with Vertex AI Vector Search using batch updates"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # Use Singapore region for vector search (where your index is)
        self.vector_search_location = os.getenv('VERTEX_AI_VECTOR_SEARCH_LOCATION', 'asia-southeast1')
        
        self.index_id = os.getenv('VECTOR_SEARCH_INDEX_ID')
        self.endpoint_id = os.getenv('VECTOR_SEARCH_ENDPOINT_ID')
        self.deployed_index_id = os.getenv('VECTOR_SEARCH_DEPLOYED_INDEX_ID')
        
        # Storage bucket for batch updates
        self.storage_bucket = os.getenv('GCS_UPDATE_BUCKET') or os.getenv('FIREBASE_STORAGE_BUCKET')
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.storage_bucket)
        if not self.bucket.exists():
            raise ValueError(f"GCS bucket '{self.storage_bucket}' does not exist")
        
        # Validate required environment variables
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        if not self.index_id:
            raise ValueError("VECTOR_SEARCH_INDEX_ID environment variable not set")
        if not self.endpoint_id:
            raise ValueError("VECTOR_SEARCH_ENDPOINT_ID environment variable not set")
        if not self.deployed_index_id:
            raise ValueError("VECTOR_SEARCH_DEPLOYED_INDEX_ID environment variable not set")
        
        # Initialize Vertex AI for vector search region
        try:
            aiplatform.init(project=self.project_id, location=self.vector_search_location)
            logger.info(f"Initialized Vertex AI for vector search in {self.vector_search_location}")
            
            # Get index and endpoint references
            self.index = MatchingEngineIndex(index_name=self._get_index_name())
            self.endpoint = MatchingEngineIndexEndpoint(index_endpoint_name=self._get_endpoint_name())
            
            # Initialize storage client for batch updates
            if self.storage_bucket:
                self.storage_client = storage.Client()
                self.bucket = self.storage_client.bucket(self.storage_bucket)
            else:
                logger.warning("No storage bucket configured - batch updates will use temp files")
                self.storage_client = None
                self.bucket = None
            
            logger.info(f"Initialized Vector Store with index {self.index_id} in {self.vector_search_location}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI Vector Store: {e}")
            raise
    
    def add_vectors(self, vectors_data: List[Dict]) -> bool:
        try:
            logger.info(f"Adding {len(vectors_data)} vectors to index {self.index_id} using batch update")
            # validation as you have now...
            try:
                logger.info("Attempting stream update...")
                return self._try_stream_update(vectors_data)
            except Exception as stream_error:
                if "StreamUpdate is not enabled" in str(stream_error):
                    logger.warning("Stream update not available, falling back to batch update")
                    # Let any batch error raise out so caller sees it
                    return self._batch_update(vectors_data)

                else:
                    raise
        except Exception as e:
            logger.error("Failed to add vectors to index", exc_info=True)
            # re-raise so caller gets the message
            raise

    
    def _try_stream_update(self, vectors_data: List[Dict]) -> bool:
        """Try to use stream update (upsert_datapoints)"""
        try:
            # Prepare datapoints for batch upsert
            datapoints = []
            
            for data in vectors_data:
                datapoint = {
                    'datapoint_id': data['id'],
                    'feature_vector': data['embedding']
                }
                
                # Add metadata if available (for filtering)
                if 'metadata' in data and data['metadata']:
                    # Convert metadata to restricts format if needed
                    restricts = self._convert_metadata_to_restricts(data['metadata'])
                    if restricts:
                        datapoint['restricts'] = restricts
                
                datapoints.append(datapoint)
            
            logger.info(f"Prepared {len(datapoints)} datapoints for stream upsert")
            
            # Attempt stream upsert
            self.index.upsert_datapoints(datapoints=datapoints)
            logger.info(f"Successfully added {len(datapoints)} vectors via stream update")
            return True
            
        except Exception as e:
            logger.error(f"Stream update failed: {e}")
            raise
    
    def _batch_update(self, vectors_data: List[Dict]) -> dict:
        """Stage a JSON file to GCS for Console Batch Update (no API call)."""
        try:
            # One JSON object per line, with the exact keys Vertex expects
            lines = []
            for data in vectors_data:
                rec = {
                    "datapoint_id": data["id"],
                    "feature_vector": data["embedding"],
                }
                meta = data.get("metadata") or {}
                restricts = []
                for key, value in meta.items():
                    if value is None or value == "":
                        continue
                    vals = value if isinstance(value, list) else [value]
                    vals = [str(v) for v in vals if v]
                    if vals:
                        restricts.append({
                            "namespace": str(key),
                            "allow_list": vals     # <-- correct field name
                        })
                if restricts:
                    rec["restricts"] = restricts
                lines.append(json.dumps(rec))

            # Write a .json file (Console doesn’t accept .jsonl)
            blob_name = f"vector_updates/batch_{len(vectors_data)}.json"
            payload = "\n".join(lines)  # JSON-lines in a .json file is OK
            self.bucket.blob(blob_name).upload_from_string(
                payload,
                content_type="application/json"
            )
            gcs_uri = f"gs://{self.storage_bucket}/{blob_name}"
            logger.info(f"Uploaded JSON to {gcs_uri}")

            # IMPORTANT: don’t call import_index_datapoints on this version
            logger.info("Batch file staged; run 'Batch update' in Console on the folder.")
            return {"staged_gcs_uri": gcs_uri}

        except Exception as e:
            logger.error(f"Batch update staging failed: {e}", exc_info=True)
            raise



    def search_vectors(self, query_vector: List[float], num_neighbors: int = 10,
                   metadata_filters: Dict = None) -> List[Dict]:
        """Search for neighbors using dict payloads (works with aiplatform 1.71.x)."""
        try:
            logger.info(f"Searching for {num_neighbors} similar vectors in {self.vector_search_location}")

            # Validate vector
            if not isinstance(query_vector, list) or not query_vector:
                raise ValueError("Invalid or empty query vector")
            query_vector = [float(x) for x in query_vector]
            
            # Optional restricts as plain dicts
            restricts = []
            if metadata_filters:
                for k, v in metadata_filters.items():
                    if v is None or v == "":
                        continue
                    vals = v if isinstance(v, list) else [v]
                    vals = [str(x) for x in vals if x]
                    if vals:
                        restricts.append({
                            "namespace": str(k),
                            "allow_list": vals,   # IMPORTANT: allow_list
                        })

            # The wrapper expects queries like this (dicts, not typed protos)
            q = {
                "datapoint": {
                    "datapoint_id": "__query__",
                    "feature_vector": query_vector,
                },
                "neighbor_count": int(num_neighbors),
            }
            if restricts:
                q["datapoint"]["restricts"] = restricts

            queries = [q]
            # Optional: uncomment to see the final payload
            # logger.debug("find_neighbors queries payload: %s", queries)

            resp = self.endpoint.find_neighbors(
                deployed_index_id=self.deployed_index_id,
                queries=queries,
                return_full_datapoint=False,
            )

            results = []
            if resp and len(resp) > 0:
                for n in resp[0]:
                    try:
                        results.append({
                            "id": n.datapoint.datapoint_id,
                            "distance": float(n.distance),
                            "similarity_score": max(0.0, 1.0 - float(n.distance)),
                        })
                    except Exception as e:
                        logger.warning(f"Failed to parse neighbor: {e}")
                        continue

            logger.info(f"Found {len(results)} similar vectors in {self.vector_search_location}")
            return results

        except Exception as e:
            logger.error(f"Vector search failed: {e}", exc_info=True)
            return []

    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """
        Delete vectors from index (may also require batch operation)
        
        Args:
            vector_ids: List of vector IDs to delete
            
        Returns:
            bool: Success status
        """
        try:
            if not vector_ids:
                logger.warning("No vector IDs provided for deletion")
                return True
            
            logger.info(f"Deleting {len(vector_ids)} vectors from index in {self.vector_search_location}")
            
            # Validate vector IDs
            for i, vector_id in enumerate(vector_ids):
                if not vector_id or not isinstance(vector_id, str):
                    raise ValueError(f"Invalid vector ID at index {i}: {vector_id}")
            
            # Try to delete from index
            try:
                self.index.remove_datapoints(datapoint_ids=vector_ids)
                logger.info(f"Successfully deleted {len(vector_ids)} vectors from index in {self.vector_search_location}")
                return True
            except Exception as delete_error:
                if "StreamUpdate is not enabled" in str(delete_error):
                    logger.warning("Stream delete not available - deletion may require batch operation")
                    return False
                else:
                    logger.error(f"Vertex AI deletion failed in {self.vector_search_location}: {delete_error}")
                    raise
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
            logger.exception("Detailed vector deletion error:")
            return False
    
    def _get_index_name(self) -> str:
        """Get full index resource name"""
        return f"projects/{self.project_id}/locations/{self.vector_search_location}/indexes/{self.index_id}"
    
    def _get_endpoint_name(self) -> str:
        """Get full endpoint resource name"""
        return f"projects/{self.project_id}/locations/{self.vector_search_location}/indexEndpoints/{self.endpoint_id}"
    
    def _convert_metadata_to_restricts(self, metadata: Dict) -> List[Dict]:
        """Convert metadata to Vertex AI restricts format"""
        restricts = []
        
        try:
            for key, value in metadata.items():
                if not key or not value:
                    continue
                
                if isinstance(value, str):
                    restricts.append({
                        'namespace': str(key),
                        'allow_list': [str(value)]
                    })
                elif isinstance(value, list):
                    # Filter out empty values
                    non_empty_values = [str(v) for v in value if v]
                    if non_empty_values:
                        restricts.append({
                            'namespace': str(key),
                            'allow_list': non_empty_values
                        })
                else:
                    # Convert other types to string
                    restricts.append({
                        'namespace': str(key),
                        'allow_list': [str(value)]
                    })
        
        except Exception as e:
            logger.warning(f"Failed to convert metadata to restricts: {e}")
        
        return restricts

# Singleton instance
_vector_store = None

def get_vector_store():
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VertexVectorStore()
    return _vector_store