#!/usr/bin/env python3
"""
Test script to verify logging is working
"""

import logging
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logging():
    """Test basic logging functionality"""
    
    print("🧪 Testing logging configuration...")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Test different log levels
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    print("✅ Logging test completed. Check the console output and test.log file.")
    
    # Test importing app
    try:
        print("📦 Testing app import...")
        from app import app, logger as app_logger
        
        app_logger.info("✅ App imported successfully")
        print("✅ App import test passed")
        
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_logging()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
        sys.exit(1) 