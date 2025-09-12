"""
Firebase Storage Utility
"""

import os
import logging
from datetime import datetime
from firebase_admin import storage
from firebase.config import get_firebase_config

# Ensure Firebase is initialized before using storage
get_firebase_config()

logger = logging.getLogger(__name__)

class FirebaseStorageManager:
    """Utility class for Firebase Storage operations"""
    
    def __init__(self):
        self.bucket = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize Firebase Storage bucket"""
        try:
            # Get the default bucket
            self.bucket = storage.bucket()
            logger.info("Firebase Storage initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage: {e}")
            raise
    
    def upload_pdf_bytes(self, pdf_bytes: bytes, filename: str, folder: str = "documents") -> str:
        """
        Upload PDF bytes to Firebase Storage
        
        Args:
            pdf_bytes: PDF content as bytes
            filename: Name of the file
            folder: Storage folder path
            
        Returns:
            Download URL of the uploaded file
        """
        try:
            # Create the full path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename.replace(' ', '_')}"
            storage_path = f"{folder}/{safe_filename}"
            
            # Create a blob
            blob = self.bucket.blob(storage_path)
            
            # Upload the bytes
            blob.upload_from_string(
                pdf_bytes,
                content_type='application/pdf'
            )
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Get the download URL
            download_url = blob.public_url
            
            logger.info(f"PDF uploaded successfully to: {storage_path}")
            logger.info(f"Download URL: {download_url}")
            
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload PDF to Firebase Storage: {e}")
            raise
    
    def upload_file(self, file_path: str, filename: str = None, folder: str = "documents") -> str:
        """
        Upload a file to Firebase Storage
        
        Args:
            file_path: Path to the file to upload
            filename: Optional custom filename
            folder: Storage folder path
            
        Returns:
            Download URL of the uploaded file
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Use provided filename or extract from path
            if not filename:
                filename = os.path.basename(file_path)
            
            # Create the full path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename.replace(' ', '_')}"
            storage_path = f"{folder}/{safe_filename}"
            
            # Create a blob
            blob = self.bucket.blob(storage_path)
            
            # Upload the file
            blob.upload_from_filename(file_path)
            
            # Make the blob publicly readable
            blob.make_public()
            
            # Get the download URL
            download_url = blob.public_url
            
            logger.info(f"File uploaded successfully to: {storage_path}")
            logger.info(f"Download URL: {download_url}")
            
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to Firebase Storage: {e}")
            raise
    
    def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from Firebase Storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            True if deletion was successful
        """
        try:
            blob = self.bucket.blob(storage_path)
            blob.delete()
            
            logger.info(f"File deleted successfully: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from Firebase Storage: {e}")
            return False
    
    def get_file_info(self, storage_path: str) -> dict:
        """
        Get information about a file in Firebase Storage
        
        Args:
            storage_path: Path to the file in storage
            
        Returns:
            Dictionary with file information
        """
        try:
            blob = self.bucket.blob(storage_path)
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'public_url': blob.public_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info from Firebase Storage: {e}")
            raise