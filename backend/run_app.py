#!/usr/bin/env python3
"""
Run script for LIT Legal Mind Backend API
"""

import os
import sys
import uvicorn
import logging
import platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # replace this with:



def main():
    """Main function to run the FastAPI server"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if GOOGLE_AI_API_KEY is set
    api_key = os.getenv('GOOGLE_AI_API_KEY')
    if not api_key:
        print("❌ Error: GOOGLE_AI_API_KEY environment variable is not set")
        print("Please create a .env file in the backend directory with:")
        print("GOOGLE_AI_API_KEY=your_google_ai_api_key_here")
        sys.exit(1)
    
    # Choose port: macOS (Darwin) users use 5050, others use 5000
    port = 5050 if platform.system() == "Darwin" else 5000

    print("🚀 Starting LIT Legal Mind Backend API...")
    print(f"📍 API Key configured: {'*' * (len(api_key) - 4) + api_key[-4:] if len(api_key) > 4 else '***'}")
    print(f"🌐 Server will be available at: http://localhost:{port}")
    print(f"📚 API Documentation: http://localhost:{port}/docs")

    # Run the server
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 