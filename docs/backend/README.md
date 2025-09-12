# Backend Documentation

Welcome to the LIT Version Control backend documentation. This section covers all aspects of the FastAPI-based backend system.

## 📋 Table of Contents

### 🚀 Getting Started
- **[API Overview](API.md)** - Complete API reference and endpoints
- **[Setup Guide](SETUP.md)** - Installation and configuration instructions

### 🔧 Core Features
- **[Upload Process](UPLOAD_PROCESS.md)** - Document upload and processing workflow
- **[Conflicts Storage](CONFLICTS_STORAGE.md)** - Conflict detection and storage system
- **[Vector Search](VECTOR_SEARCH.md)** - Semantic search capabilities
- **[AI Chat](AI_CHAT.md)** - Conversational AI integration

### 🛠️ Development & Operations
- **[Logging & Troubleshooting](LOGGING_TROUBLESHOOTING.md)** - Debugging and logging guide
- **[Testing Guide](TESTING.md)** - Testing strategies and procedures
- **[Deployment](DEPLOYMENT.md)** - Production deployment instructions

## 🏗️ Architecture Overview

The backend is built with **FastAPI** and provides the following core services:

### Core Components
- **Document Processing**: PDF extraction, text processing, and vector indexing
- **Vector Search**: Semantic search using embeddings and vector similarity
- **Legal Research**: Integration with Hansard and LawNet
- **AI Chat**: Conversational AI for legal assistance
- **Document Comparison**: Automated clause comparison and conflict detection

### Key Technologies
- **FastAPI**: Modern Python web framework
- **Firebase**: Document storage and authentication
- **Google AI**: LLM processing and text generation
- **Groq**: Document processing and text extraction
- **Vector Search**: Semantic document search

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google AI API key
- Firebase project (optional for local development)

### Installation
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Google AI API key
echo "GOOGLE_AI_API_KEY=your_api_key_here" > .env

# Start the server
python run_app.py
```

The backend API will be available at `http://localhost:5000`

## 📚 API Documentation

### Core Endpoints
- `GET /health` - Health check and backend status
- `POST /chat` - Chat with LIT Legal Mind AI assistant
- `POST /search` - Legal content search and analysis
- `POST /vector-search` - Semantic search using vector similarity
- `POST /upload/{proj_id}/{doc_id}` - Process uploaded documents
- `POST /process-document` - Process documents for vector search

### Interactive Documentation
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

## 🔧 Configuration

### Environment Variables
```env
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
FIREBASE_SERVICE_ACCOUNT_PATH=path/to/service-account.json
```

### Firebase Configuration
For full functionality, configure Firebase in your environment:
- Firestore for document storage
- Storage for file uploads
- Authentication for user management

## 🧪 Testing

Run the test suite to verify functionality:
```bash
cd backend
python -m pytest tests/
```

Individual test files:
- `test_app.py` - Main application tests
- `test_upload_endpoint.py` - Upload functionality tests
- `test_conflicts_storage.py` - Conflict storage tests
- `test_custom_search.py` - Search functionality tests
- `test_logging.py` - Logging configuration tests

## 🐛 Troubleshooting

### Common Issues
1. **API Key Issues**: Check `GOOGLE_AI_API_KEY` environment variable
2. **Firebase Connection**: Verify Firebase configuration
3. **Port Conflicts**: Ensure port 5000 is available
4. **Dependencies**: Check all requirements are installed

### Debugging
- Check logs in `app.log` file
- Use the logging test script: `python test_logging.py`
- Verify environment variables: `python -c "import os; print(os.getenv('GOOGLE_AI_API_KEY'))"`

## 📖 Additional Resources

- **[Frontend Documentation](../frontend/README.md)** - React frontend documentation
- **[Project Architecture](../ARCHITECTURE.md)** - Overall system architecture
- **[Development Guidelines](../DEVELOPMENT.md)** - Coding standards and best practices

---

*For specific feature documentation, see the individual files listed above.* 