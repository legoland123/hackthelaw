"""
Firebase Configuration
"""

import os
import firebase_admin
from firebase_admin import credentials, firestore
import logging

logger = logging.getLogger(__name__)

class FirebaseConfig:
    """Firebase configuration and initialization"""
    
    def __init__(self):
        self.app = None
        self.db = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Firebase app and Firestore client"""
        try:
            # Check if already initialized
            if not firebase_admin._apps:
                # Try service account file first
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
                logger.info(f"Service account path from env: {service_account_path}")
                
                if service_account_path:
                    # Make path absolute if it's relative
                    if not os.path.isabs(service_account_path):
                        service_account_path = os.path.abspath(service_account_path)
                        logger.info(f"Converted to absolute path: {service_account_path}")
                    
                    logger.info(f"Checking if file exists: {service_account_path}")
                    if os.path.exists(service_account_path):
                        logger.info(f"Service account file found, initializing with credentials")
                        cred = credentials.Certificate(service_account_path)
                        
                        storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
                        if not storage_bucket:
                            raise ValueError("FIREBASE_STORAGE_BUCKET environment variable is not set.")
                        
                        self.app = firebase_admin.initialize_app(cred, {
                            'storageBucket': storage_bucket
                        })
                        logger.info("Firebase initialized with service account")
                    else:
                        logger.warning(f"Service account file not found at: {service_account_path}")
                        # Use default credentials
                        self.app = firebase_admin.initialize_app()
                        logger.info("Firebase initialized with default credentials")
                else:
                    logger.warning("No FIREBASE_SERVICE_ACCOUNT_PATH found in environment")
                    # Use default credentials
                    self.app = firebase_admin.initialize_app()
                    logger.info("Firebase initialized with default credentials")
            else:
                self.app = firebase_admin.get_app()
            
            # Initialize Firestore
            self.db = firestore.client()
            logger.info("Firestore client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def get_db(self):
        """Get Firestore database client"""
        return self.db
    
    def get_app(self):
        """Get Firebase app instance"""
        return self.app

# Singleton instance
_firebase_config = None

def get_firebase_config():
    """Get singleton Firebase config instance"""
    global _firebase_config
    if _firebase_config is None:
        _firebase_config = FirebaseConfig()
    return _firebase_config

def get_db():
    """Get Firestore database client"""
    config = get_firebase_config()
    return config.get_db()