"""
Firestore Database Operations
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from firebase_admin import firestore
from .config import get_db

logger = logging.getLogger(__name__)

class FirestoreDB:
    """Handle Firestore database operations"""
    
    def __init__(self):
        self.db = get_db()
    
    def store_search_result(self, query: str, search_type: str, results: Dict, user_id: str = "anonymous"):
        """
        Store search results in Firestore
        
        Args:
            query: Search query
            search_type: Type of search (hansard, lawnet, both)
            results: Processed results from LLM
            user_id: User identifier
            
        Returns:
            str: Document ID
        """
        try:
            doc_data = {
                'query': query,
                'search_type': search_type,
                'results': results,
                'user_id': user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'cache_key': self._generate_cache_key(query, search_type)
            }
            
            doc_ref = self.db.collection('search_results').add(doc_data)
            doc_id = doc_ref[1].id
            logger.info(f"Stored search result with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store search result: {e}")
            raise
    
    def get_cached_result(self, query: str, search_type: str, max_age_hours: int = 24) -> Optional[Dict]:
        """
        Get cached search result if available and not expired
        
        Args:
            query: Search query
            search_type: Type of search
            max_age_hours: Maximum age of cache in hours
            
        Returns:
            Cached results or None
        """
        try:
            cache_key = self._generate_cache_key(query, search_type)
            
            docs = (self.db.collection('search_results')
                   .where('cache_key', '==', cache_key)
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(1)
                   .get())
            
            if docs:
                doc = docs[0]
                data = doc.to_dict()
                
                # Check if cache is still valid
                timestamp = data.get('timestamp')
                if timestamp:
                    age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
                    if age_hours <= max_age_hours:
                        logger.info(f"Found valid cached result for: {query}")
                        return data['results']
                    else:
                        logger.info(f"Cache expired for: {query} (age: {age_hours:.1f} hours)")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None
    
    def store_search_history(self, user_id: str, query: str, search_type: str, results_count: int):
        """
        Store user search history
        
        Args:
            user_id: User identifier
            query: Search query
            search_type: Type of search
            results_count: Number of results found
        """
        try:
            doc_data = {
                'user_id': user_id,
                'query': query,
                'search_type': search_type,
                'results_count': results_count,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('search_history').add(doc_data)
            logger.info(f"Stored search history for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store search history: {e}")
    
    def get_user_search_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        """
        Get user's search history
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of search history records
        """
        try:
            docs = (self.db.collection('search_history')
                   .where('user_id', '==', user_id)
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .get())
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append(data)
            
            logger.info(f"Retrieved {len(history)} search history records for user: {user_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get search history: {e}")
            return []
    
    def store_user_preferences(self, user_id: str, preferences: Dict):
        """
        Store user preferences
        
        Args:
            user_id: User identifier
            preferences: User preference settings
        """
        try:
            doc_ref = self.db.collection('user_preferences').document(user_id)
            doc_ref.set({
                'preferences': preferences,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            logger.info(f"Stored preferences for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to store user preferences: {e}")
    
    def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """
        Get user preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            User preferences or None
        """
        try:
            doc = self.db.collection('user_preferences').document(user_id).get()
            if doc.exists:
                return doc.to_dict().get('preferences')
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return None
    
    def store_conversation(self, user_id: str, user_message: str, ai_response: str, conversation_history: List[Dict] = None, project_id: str = None) -> str:
        """
        Store chat conversation in Firestore
        
        Args:
            user_id: User identifier
            user_message: User's message
            ai_response: AI's response
            conversation_history: Previous conversation messages
            project_id: Project identifier (optional)
            
        Returns:
            str: Conversation ID
        """
        try:
            doc_data = {
                'user_id': user_id,
                'user_message': user_message,
                'ai_response': ai_response,
                'conversation_history': conversation_history or [],
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            # Add project_id if provided
            if project_id:
                doc_data['project_id'] = project_id
            
            doc_ref = self.db.collection('conversations').add(doc_data)
            doc_id = doc_ref[1].id
            logger.info(f"Stored conversation with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
            raise
    
    def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict]:
        """
        Get user's conversation history
        
        Args:
            user_id: User identifier
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation records
        """
        try:
            docs = (self.db.collection('conversations')
                   .where('user_id', '==', user_id)
                   .order_by('timestamp', direction=firestore.Query.DESCENDING)
                   .limit(limit)
                   .get())
            
            conversations = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                conversations.append(data)
            
            logger.info(f"Retrieved {len(conversations)} conversations for user: {user_id}")
            return conversations
            
        except Exception as e:
            logger.error(f"Failed to get user conversations: {e}")
            return []
    
    def update_document(self, document_id: str, update_data: Dict):
        """
        Update a document in Firestore
        
        Args:
            document_id: Document identifier
            update_data: Data to update
            
        Returns:
            bool: Success status
        """
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            doc_ref.update(update_data)
            logger.info(f"Updated document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise
    
    def get_document(self, document_id: str):
        """
        Get a document from Firestore
        
        Args:
            document_id: Document identifier
            
        Returns:
            DocumentSnapshot or None
        """
        try:
            doc_ref = self.db.collection('documents').document(document_id)
            return doc_ref.get()
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise
    
    def get_project(self, project_id: str):
        """
        Get a project from Firestore
        
        Args:
            project_id: Project identifier
            
        Returns:
            DocumentSnapshot or None
        """
        try:
            doc_ref = self.db.collection('projects').document(project_id)
            return doc_ref.get()
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise
    
    def get_document_collection(self):
        """
        Get the documents collection reference
        
        Returns:
            CollectionReference
        """
        return self.db.collection('documents')
    
    def get_project_collection(self):
        """
        Get the projects collection reference
        
        Returns:
            CollectionReference
        """
        return self.db.collection('projects')
    
    def store_conflict(self, doc_id: str, search_results: Dict) -> str:
        """
        Store search results in conflicts collection
        
        Args:
            doc_id: Document identifier that triggered the search
            search_results: Search results to store
            
        Returns:
            str: Conflict document ID
        """
        try:
            doc_data = {
                'doc_id': doc_id,
                'search_results': search_results,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection('conflicts').add(doc_data)
            conflict_id = doc_ref[1].id
            logger.info(f"Stored conflict with ID: {conflict_id} for document: {doc_id}")
            return conflict_id
            
        except Exception as e:
            logger.error(f"Failed to store conflict for document {doc_id}: {e}")
            raise
    
    def _generate_cache_key(self, query: str, search_type: str) -> str:
        """Generate cache key for query and search type"""
        return f"{search_type}_{hash(query.lower().strip())}"

# Singleton instance
_firestore_db = None

def get_firestore_db():
    """Get singleton Firestore DB instance"""
    global _firestore_db
    if _firestore_db is None:
        _firestore_db = FirestoreDB()
    return _firestore_db