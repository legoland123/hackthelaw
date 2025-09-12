#!/usr/bin/env python3
"""
Script to create Firebase service account JSON file from environment variables
"""

import os
import json
from dotenv import load_dotenv

def create_firebase_config():
    """Create Firebase service account JSON file from environment variables"""
    
    # Load environment variables
    load_dotenv()
    
    # Get Firebase configuration from environment variables
    firebase_config = {
        "type": "service_account",
        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
    }
    
    # Create config directory if it doesn't exist
    os.makedirs('config', exist_ok=True)
    
    # Write the configuration to JSON file
    config_path = 'config/firebase-service-account.json'
    with open(config_path, 'w') as f:
        json.dump(firebase_config, f, indent=2)
    
    print(f"✅ Firebase service account configuration created at: {config_path}")
    print(f"📁 Project ID: {firebase_config['project_id']}")
    print(f"📧 Client Email: {firebase_config['client_email']}")

if __name__ == "__main__":
    create_firebase_config() 