# Backend Logging Troubleshooting Guide

## Issue: Backend app.py not showing logs

### Possible Causes and Solutions

## 1. **Uvicorn Log Level Configuration**

**Problem**: Uvicorn might be overriding the logging configuration.

**Solution**: Check the `run_app.py` file and ensure proper log level:

```python
uvicorn.run(
    "app:app",
    host="0.0.0.0",
    port=8000,
    reload=True,
    log_level="info",  # Make sure this is set to "info"
    access_log=True    # Enable access logs
)
```

## 2. **Logging Configuration Issues**

**Problem**: Logging might not be properly configured.

**Solution**: The app.py now has enhanced logging configuration:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
```

## 3. **Environment Variables**

**Problem**: Missing environment variables might cause silent failures.

**Solution**: Check if these environment variables are set:
- `GOOGLE_AI_API_KEY`
- `FIREBASE_SERVICE_ACCOUNT_PATH` (optional)

## 4. **Port Configuration**

**Problem**: Wrong port configuration.

**Solution**: Ensure the backend runs on port 8000 (not 5000) to match the frontend proxy.

## 5. **Virtual Environment Issues**

**Problem**: Running in wrong Python environment.

**Solution**: Ensure you're using the correct virtual environment:

```bash
# Activate virtual environment
source venv/bin/activate  # or .venv/bin/activate

# Check Python path
which python
```

## Testing Steps

### Step 1: Test Basic Logging

Run the logging test script:

```bash
cd backend
python test_logging.py
```

Expected output:
```
🧪 Testing logging configuration...
2024-01-15 10:30:00,123 - __main__ - INFO - This is an INFO message
2024-01-15 10:30:00,124 - __main__ - WARNING - This is a WARNING message
2024-01-15 10:30:00,125 - __main__ - ERROR - This is an ERROR message
✅ Logging test completed. Check the console output and test.log file.
📦 Testing app import...
✅ App imported successfully
✅ App import test passed
🎉 All tests passed!
```

### Step 2: Test Server Startup

Start the server and check for startup logs:

```bash
python run_app.py
```

Expected output:
```
🚀 Starting LIT Legal Mind Backend API...
📍 API Key configured: ****abcd
🌐 Server will be available at: http://localhost:8000
📚 API Documentation: http://localhost:8000/docs
2024-01-15 10:30:00,123 - app - INFO - 🚀 Starting LIT Legal Mind Backend API...
2024-01-15 10:30:00,124 - app - INFO - Python version: 3.9.0
2024-01-15 10:30:00,125 - app - INFO - Working directory: /path/to/backend
2024-01-15 10:30:00,126 - app - INFO - ✅ FastAPI app initialized with CORS middleware
```

### Step 3: Test Health Endpoint

Test the health endpoint to see if logs appear:

```bash
curl http://localhost:8000/health
```

Expected server logs:
```
2024-01-15 10:30:05,123 - app - INFO - 🏥 Health check endpoint called
```

### Step 4: Test Upload Endpoint

Test the upload endpoint with a sample request:

```bash
curl -X POST http://localhost:8000/upload/test_project/test_document
```

Expected server logs:
```
2024-01-15 10:30:10,123 - app - INFO - 📤 Upload endpoint called - Project: test_project, Document: test_document
2024-01-15 10:30:10,124 - app - INFO - ✅ Firestore database connection established
2024-01-15 10:30:10,125 - app - INFO - 📄 Attempting to fetch document: test_document
```

## Common Issues and Fixes

### Issue 1: No logs at all

**Cause**: Uvicorn might be suppressing logs
**Fix**: Add `--log-level info` to uvicorn command or check `run_app.py`

### Issue 2: Only access logs visible

**Cause**: Application logs might be at different level
**Fix**: Ensure `log_level="info"` in uvicorn.run()

### Issue 3: Logs in file but not console

**Cause**: Console handler not configured
**Fix**: Check that `StreamHandler(sys.stdout)` is included

### Issue 4: Import errors suppressing logs

**Cause**: Module import failures
**Fix**: Check all dependencies are installed and environment variables set

## Debugging Commands

### Check if server is running:
```bash
lsof -i :8000
```

### Check log files:
```bash
tail -f app.log
tail -f test.log
```

### Check environment:
```bash
echo $GOOGLE_AI_API_KEY
python -c "import os; print(os.getenv('GOOGLE_AI_API_KEY'))"
```

### Check Python path:
```bash
python -c "import sys; print(sys.path)"
```

## File Locations

- **Application logs**: `backend/app.log`
- **Test logs**: `backend/test.log`
- **Uvicorn logs**: Console output
- **Access logs**: Console output (if enabled)

## Expected Log Format

```
2024-01-15 10:30:00,123 - app - INFO - 🚀 Starting LIT Legal Mind Backend API...
2024-01-15 10:30:00,124 - app - INFO - Python version: 3.9.0
2024-01-15 10:30:00,125 - app - INFO - Working directory: /path/to/backend
2024-01-15 10:30:00,126 - app - INFO - ✅ FastAPI app initialized with CORS middleware
2024-01-15 10:30:05,123 - app - INFO - 🏥 Health check endpoint called
2024-01-15 10:30:10,123 - app - INFO - 📤 Upload endpoint called - Project: test_project, Document: test_document
```

## If Still No Logs

1. **Check if the server is actually running** on the correct port
2. **Verify the terminal/console** where you started the server
3. **Check for any error messages** during startup
4. **Try running with explicit logging**:
   ```bash
   python -u run_app.py
   ```
5. **Check if there are any firewall or network issues** preventing connections

## Contact Support

If none of the above solutions work, please provide:
1. The exact command used to start the server
2. Any error messages during startup
3. The contents of `app.log` file (if it exists)
4. Your operating system and Python version 