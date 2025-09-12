# LIT Version Control - Legal Innovation & Technology

A comprehensive legal document version control system with AI-powered analysis and conflict resolution, specifically designed for Singapore law practitioners and legal teams.

## 🚀 Features

### Core Functionality
- **📄 Document Version Control**: Track multiple versions of legal documents with detailed change history and timeline visualization
- **🤖 AI-Powered Analysis**: LIT Legal Mind AI assistant for contract review, legal insights, and document analysis
- **⚡ Conflict Detection & Resolution**: Advanced conflict detection with professional resolution interface
- **🇸🇬 Singapore Law Compliance**: Specialized analysis for Singapore legal framework and regulations
- **📁 Project Management**: Organize legal documents into projects with categories and descriptions
- **🔄 Real-time Collaboration**: Firebase-powered backend for seamless document management

### Enhanced User Experience
- **🎨 Modern UI/UX**: Professional, responsive design with intuitive navigation
- **📱 Mobile Responsive**: Works seamlessly on desktop, tablet, and mobile devices
- **⚡ Fast Performance**: Optimized with Vite for rapid development and deployment
- **🔍 Advanced Search**: Powerful document search and filtering capabilities
- **📊 Visual Analytics**: Timeline views and conflict resolution summaries

## 📋 Document Support

The system supports comprehensive document processing with full content extraction:

| Format | Support | Features |
|--------|---------|----------|
| **PDF** | ✅ Full | Text extraction, content analysis, version comparison |
| **DOCX** | ✅ Full | Word document processing, formatting preservation |
| **TXT** | ✅ Full | Plain text with encoding detection |
| **DOC** | ❌ Legacy | Please convert to DOCX format |

### Document Processing Capabilities
- **Content Extraction**: Automatic text extraction from all supported formats
- **Version Comparison**: Side-by-side diff views with highlighted changes
- **Conflict Detection**: Intelligent identification of conflicting terms and clauses
- **Legal Analysis**: AI-powered review of legal terms and compliance

## 🛠️ Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+
- Google AI API key
- Firebase project (optional for local development)

### Frontend Setup (React + Vite)

```bash
# Clone the repository
git clone <repository-url>
cd hackthelaw_smulit

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Backend Setup (FastAPI + Gemini)

#### Option 1: Automated Setup (Recommended)

```bash
# Make sure you have a Google AI API key
# Create backend/.env file with:
# GOOGLE_AI_API_KEY=your_api_key_here

# Run the startup script
chmod +x start_backend.sh
./start_backend.sh
```

#### Option 2: Manual Setup

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

## ⚙️ Configuration

### Environment Variables

#### Backend (.env file in backend directory)
```env
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
```

#### Frontend (.env file in root directory)
```env
VITE_API_BASE_URL=http://localhost:5000
```

### Firebase Configuration (Optional)
For full functionality, configure Firebase in `src/firebase/config.js`:
```javascript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "your-sender-id",
  appId: "your-app-id"
};
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /health` - Health check and backend status
- `POST /chat` - Chat with LIT Legal Mind AI assistant
- `POST /search` - Legal content search and analysis

### Document Management
- `POST /documents/upload` - Upload and process documents
- `GET /documents/{id}` - Retrieve document details
- `PUT /documents/{id}` - Update document metadata

### Project Management
- `GET /projects` - List all projects
- `POST /projects` - Create new project
- `PUT /projects/{id}` - Update project details

## 🎯 Getting Started Guide

### 1. Create Your First Project
1. Click "Create New Project" on the overview page
2. Fill in the project details:
   - **Name**: Enter a descriptive project name
   - **Description**: Describe the project scope and purpose
   - **Category**: Select the appropriate document type
3. Click "Create Project" to proceed

### 2. Upload Documents
1. Navigate to your project
2. Click "Upload Document" in the sidebar
3. Select your document file (PDF, DOCX, or TXT)
4. Fill in document metadata (title, author, changes)
5. Upload and wait for processing

### 3. Review and Resolve Conflicts
1. Check the "Conflicts" tab for any detected issues
2. Review each conflict with the diff viewer
3. Choose resolution method:
   - **Quick Options**: Keep current, accept proposed, or combine both
   - **Manual Edit**: Custom resolution with text editor
4. Apply resolutions to finalize the document

### 4. Use AI Assistant
1. Click the AI chat icon (🤖) in the header
2. Ask questions about your documents
3. Get legal insights and analysis
4. Request document comparisons and summaries

## 🏗️ Project Structure

```
hackthelaw_smulit/
├── src/                          # Frontend React application
│   ├── components/               # Reusable React components
│   │   ├── CreateProjectModal.jsx    # Project creation modal
│   │   ├── ConflictResolver.jsx      # Conflict resolution interface
│   │   ├── DocumentUpload.jsx        # Document upload component
│   │   ├── DocumentViewer.jsx        # Document viewing interface
│   │   ├── ProjectChat.jsx           # AI chat interface
│   │   └── ...                     # Other components
│   ├── pages/                    # Page components
│   │   ├── Overview.jsx             # Projects overview page
│   │   ├── ProjectView.jsx          # Individual project view
│   │   ├── AIChat.jsx               # AI chat page
│   │   └── NotFound.jsx             # 404 page
│   ├── services/                  # API and utility services
│   ├── styles/                    # CSS styles and themes
│   │   ├── modal.css                  # Modal component styles
│   │   ├── conflict-resolver.css      # Conflict resolution styles
│   │   └── ...                        # Other style files
│   └── firebase/                  # Firebase configuration
├── backend/                       # Backend FastAPI application
│   ├── app.py                    # Main FastAPI application
│   ├── legal_memory/             # Legal processing modules
│   ├── firebase/                 # Firebase integration
│   ├── groqFunc/                 # AI processing functions
│   └── requirements.txt          # Python dependencies
├── start_backend.sh              # Backend startup script
├── package.json                  # Frontend dependencies
└── README.md                     # This file
```

## 🔧 Development

### Frontend Development
- **Framework**: React 18 with Vite for fast development
- **Styling**: CSS modules with CSS variables for theming
- **State Management**: React hooks and context
- **Build Tool**: Vite for optimized builds

### Backend Development
- **Framework**: FastAPI for high-performance API
- **AI Integration**: Google Gemini for intelligent processing
- **Database**: Firebase Firestore for document storage
- **File Storage**: Firebase Storage for document files

### Key Technologies
- **Frontend**: React, Vite, CSS3, JavaScript ES6+
- **Backend**: Python, FastAPI, Google AI, Firebase
- **AI/ML**: Google Gemini, Natural Language Processing
- **Database**: Firebase Firestore (NoSQL)
- **Storage**: Firebase Storage

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues
- **API Key Error**: Ensure `GOOGLE_AI_API_KEY` is set in `backend/.env`
- **Port Conflict**: Change port in `run_app.py` or kill process on port 5000
- **Import Errors**: Reinstall dependencies with `pip install -r requirements.txt`
- **Virtual Environment**: Activate with `source venv/bin/activate`

#### Frontend Issues
- **API Connection**: Verify backend is running and `VITE_API_BASE_URL` is correct
- **Build Errors**: Clear cache with `npm run clean` and reinstall dependencies
- **Module Errors**: Update Node.js to version 18+ and reinstall packages

#### Document Processing Issues
- **Upload Failures**: Check file format and size limits
- **Content Extraction**: Ensure documents are not password-protected
- **Processing Delays**: Large documents may take longer to process

### Performance Optimization
- **Large Documents**: Consider splitting very large documents
- **Multiple Uploads**: Upload documents sequentially for better performance
- **Browser Cache**: Clear cache if experiencing UI issues

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow existing code style and conventions
- Add tests for new features
- Update documentation for API changes
- Test thoroughly before submitting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google AI** for providing the Gemini API
- **Firebase** for backend services
- **React Team** for the amazing frontend framework
- **FastAPI** for the high-performance backend framework

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the API documentation

---

**LIT Version Control** - Empowering legal professionals with intelligent document management and AI-powered analysis.
