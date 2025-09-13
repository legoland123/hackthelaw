import { app } from './firebase/config';
console.log('[Firebase] projectId:', app.options.projectId);

import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import './styles/main.css'
import Overview from './pages/Overview'
import ProjectView from './pages/ProjectView'
import NotFound from './pages/NotFound'
import AIChat from './pages/AIChat'
import CreateProjectModal from './components/CreateProjectModal'
import LoginPage from './pages/Login'
import SignupPage from './pages/Signup'
//import { projectServices } from './firebase/services'
import StatuteFinder from './pages/StatuteFinder'


function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    // restore session from localStorage
    const saved = localStorage.getItem('authUser')
    if (saved) {
      try { setUser(JSON.parse(saved)) } catch (e) { localStorage.removeItem('authUser') }
    }
  }, [])

  useEffect(() => {
    const fetchProjects = async () => {
      try {
       const hasKey = !!import.meta.env.VITE_FIREBASE_API_KEY;
       if (!hasKey) {
         console.warn('Firebase not configured (VITE_FIREBASE_API_KEY missing). Running in demo mode.');
         setProjects([]);           // show empty overview instead of crashing
         setLoading(false);
         return;
       }
       const { projectServices } = await import('./firebase/services');
        const fetchedProjects = await projectServices.getAllProjects();
        setProjects(fetchedProjects);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const handleLogin = (u) => {
    // persist minimal session locally (for local / demo auth)
    localStorage.setItem('authUser', JSON.stringify(u))
    setUser(u)
    navigate('/', { replace: true })
  }

  const handleLogout = () => {
    localStorage.removeItem('authUser')
    setUser(null)
    navigate('/login', { replace: true })
  }

  const handleUpdateProject = async (updatedProject) => {
    try {
      //const { projectServices } = await import('./firebase/services');
      //await projectServices.updateProject(updatedProject.id, updatedProject);
      //setProjects(projects.map(p => p.id === updatedProject.id ? updatedProject : p));
      setProjects([] );
    } catch (error) {
      //console.error("Failed to update project:", error);
      console.warn("Projects unavailable (dev):", error?.message || error);
    }
  };

  const handleCreateNewProject = async (projectData) => {
    try {
      const { projectServices } = await import('./firebase/services');
      const newProject = await projectServices.createProject(projectData);
      setProjects(prev => [newProject, ...prev]);
      return newProject.id;
    } catch (error) {
      console.error("Failed to create project:", error);
      throw error;
    }
  }

  const handleCreateProjectClick = () => {
    setIsCreateModalOpen(true);
  };

  const handleCreateProjectSuccess = async (projectData) => {
    try {
      const newProjectId = await handleCreateNewProject(projectData);
      if (newProjectId) {
        // Navigate to the new project
        window.location.href = `/project/${newProjectId}`;
      }
    } catch (error) {
      // Error is handled in the modal component
      console.error("Failed to create project:", error);
    }
  };

  function RequireAuth({ children }) {
    if (!user) {
      return <Navigate to="/login" replace />
    }
    return children
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-logo">
          <img src="/logo.png" alt="LIT Logo" className="logo" />
          <div className="header-title">
            <h1>AITHENA DWOM</h1>
            <p>Legal Innovation & Technology</p>
          </div>
        </div>
        <div className="header-nav"></div>
        <div className="header-actions">
          <div className="user-profile">
            {user ? (
              <>
                <span className="user-name">{user.email}</span>
                <button onClick={handleLogout} className="btn-ghost">Logout</button>
                <div className="user-avatar">{(user.email || 'U').slice(0,2).toUpperCase()}</div>
              </>
            ) : (
              <>
                <span className="user-name">Guest User</span>
                <div className="user-avatar">GU</div>
              </>
            )}
          </div>
        </div>
      </header>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          Loading projects...
        </div>
      ) : (
        <>
          <Routes>
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/signup" element={<SignupPage onLogin={handleLogin} />} />

            <Route
              path="/"
              element={
                <RequireAuth>
                  <Overview
                    projects={projects}
                    onCreateNewProject={handleCreateProjectClick}
                  />
                </RequireAuth>
              }
            />

            {/* Global (non-project) chat */}
            <Route path="/ai-chat" element={<AIChat />} />

            {/* Optional global (non-project) statute finder */}
            <Route path="/statutes" element={<StatuteFinder />} />

            {/* Project hub + project-scoped aliases (chat, statutes) */}
            <Route
              path="/project/:projectId"
              element={
                <RequireAuth>
                  <ProjectView
                    projects={projects}
                    onUpdateProject={handleUpdateProject}
                  />
                </RequireAuth>
              }
            />
            <Route path="/ai-chat" element={
              <RequireAuth>
                <AIChat />
              </RequireAuth>
            } />
            <Route path="/404" element={<NotFound />} />
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>


          <CreateProjectModal
            isOpen={isCreateModalOpen}
            onClose={() => setIsCreateModalOpen(false)}
            onCreateProject={handleCreateProjectSuccess}
          />
        </>
      )}
    </div>
  );
}

export default App
