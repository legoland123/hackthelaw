"""
Firebase Authentication
"""

import logging
from firebase_admin import auth
from .config import get_firebase_config

logger = logging.getLogger(__name__)

class FirebaseAuth:
    """Handle Firebase authentication"""
    
    def __init__(self):
        self.config = get_firebase_config()
    
    def verify_token(self, id_token):
        """
        Verify Firebase ID token
        
        Args:
            id_token: Firebase ID token from client
            
        Returns:
            dict: Decoded token with user info
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    def get_user(self, uid):
        """
        Get user by UID
        
        Args:
            uid: User ID
            
        Returns:
            UserRecord: Firebase user record
        """
        try:
            user = auth.get_user(uid)
            return user
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None
    
    def create_custom_token(self, uid, additional_claims=None):
        """
        Create custom token for user
        
        Args:
            uid: User ID
            additional_claims: Additional claims to include
            
        Returns:
            str: Custom token
        """
        try:
            token = auth.create_custom_token(uid, additional_claims)
            return token
        except Exception as e:
            logger.error(f"Failed to create custom token: {e}")
            return None

def verify_user_token(id_token):
    """Helper function to verify user token"""
    firebase_auth = FirebaseAuth()
    return firebase_auth.verify_token(id_token)