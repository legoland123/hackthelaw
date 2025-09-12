# Frontend Documentation

Welcome to the LIT Version Control frontend documentation. This section covers the React-based frontend application.

## 📋 Table of Contents

### 🎨 Styling & Design
- **[CSS Architecture](CSS_ARCHITECTURE.md)** - Styling system and component structure
- **[AI Chat Styling](AI_CHAT_STYLING.md)** - AI chat component styling modules

### 🧩 Components
- **[Component Library](COMPONENTS.md)** - Reusable React components
- **[Page Components](PAGES.md)** - Main page components and routing

### 🔧 Development
- **[Development Guide](DEVELOPMENT.md)** - Frontend development setup and guidelines
- **[State Management](STATE_MANAGEMENT.md)** - Application state and data flow

## 🏗️ Architecture Overview

The frontend is built with **React 18** and **Vite** and provides:

### Core Features
- **Document Management**: Upload, view, and manage legal documents
- **Version Control**: Track document versions with timeline visualization
- **Conflict Resolution**: Professional interface for resolving document conflicts
- **AI Chat**: Conversational AI assistant for legal analysis
- **Project Management**: Organize documents into projects

### Key Technologies
- **React 18**: Modern React with hooks and concurrent features
- **Vite**: Fast build tool and development server
- **Firebase**: Authentication and real-time data
- **CSS Modules**: Modular styling system
- **React Router**: Client-side routing

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Backend API running on port 5000

### Installation
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

## 📁 Project Structure

```
src/
├── components/               # Reusable React components
│   ├── CreateProjectModal.jsx    # Project creation modal
│   ├── ConflictResolver.jsx      # Conflict resolution interface
│   ├── DocumentUpload.jsx        # Document upload component
│   ├── DocumentViewer.jsx        # Document viewing interface
│   ├── ProjectChat.jsx           # AI chat interface
│   ├── Sidebar.jsx               # Navigation sidebar
│   └── ...                     # Other components
├── pages/                    # Page components
│   ├── Overview.jsx             # Projects overview page
│   ├── ProjectView.jsx          # Individual project view
│   ├── AIChat.jsx               # AI chat page
│   └── NotFound.jsx             # 404 page
├── services/                  # API and utility services
│   ├── chatService.js           # AI chat API integration
│   └── documentProcessor.js     # Document processing utilities
├── styles/                    # CSS styles and themes
│   ├── main.css                 # Main stylesheet
│   ├── variables.css            # CSS custom properties
│   ├── base.css                 # Global styles
│   ├── ai-chat/                 # AI chat component styles
│   └── ...                     # Component-specific styles
├── firebase/                  # Firebase configuration
│   ├── config.js               # Firebase config
│   └── services.js             # Firebase services
└── utils/                     # Utility functions
    ├── capacityAnalyzer.js     # Document analysis utilities
    └── documentReferenceParser.js # Document reference parsing
```

## 🎨 Styling System

### CSS Architecture
The application uses a modular CSS architecture:

- **Variables**: Design tokens in `variables.css`
- **Base Styles**: Global styles and resets in `base.css`
- **Component Styles**: Isolated styles for each component
- **AI Chat Module**: Specialized styling for the AI chat feature

### Design Principles
- **Modularity**: Each component has its own CSS file
- **Consistency**: Use CSS variables for colors, spacing, and typography
- **Responsiveness**: Mobile-first responsive design
- **Accessibility**: WCAG compliant design patterns

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:
```env
VITE_API_BASE_URL=http://localhost:5000
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

### Firebase Configuration
Configure Firebase in `src/firebase/config.js`:
```javascript
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};
```

## 🧪 Testing

### Development Testing
```bash
# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality
```bash
# Lint code
npm run lint

# Format code
npm run format
```

## 🐛 Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure port 5173 is available
2. **API Connection**: Verify backend is running on port 5000
3. **Firebase Issues**: Check Firebase configuration
4. **Build Errors**: Clear node_modules and reinstall

### Debugging
- Check browser console for errors
- Verify environment variables are loaded
- Test API endpoints directly
- Check Firebase console for authentication issues

## 📖 Additional Resources

- **[Backend Documentation](../backend/README.md)** - API documentation
- **[Project Architecture](../ARCHITECTURE.md)** - Overall system architecture
- **[Development Guidelines](../DEVELOPMENT.md)** - Coding standards

---

*For specific component documentation, see the individual files listed above.* 