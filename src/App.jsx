import { app } from './firebase/config';
console.log('[Firebase] projectId:', app.options.projectId);

import { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import './styles/main.css'
import Overview from './pages/Overview'
import ProjectView from './pages/ProjectView'
import NotFound from './pages/NotFound'
import AIChat from './pages/AIChat'
import CreateProjectModal from './components/CreateProjectModal'
//import { projectServices } from './firebase/services'
import StatuteFinder from './pages/StatuteFinder'


function App() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

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
            <span className="user-name">Guest User</span>
            <div className="user-avatar">GU</div>
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
            {/* Overview */}
            <Route
              path="/"
              element={
                <Overview
                  projects={projects}
                  onCreateNewProject={handleCreateProjectClick}
                />
              }
            />

            {/* Global (non-project) chat */}
            <Route path="/ai-chat" element={<AIChat />} />

            {/* Optional global (non-project) statute finder */}
            <Route path="/statutes" element={<StatuteFinder />} />

            {/* Project hub + project-scoped aliases (chat, statutes) */}
            <Route
              path="/project/:projectId/*"
              element={<ProjectView projects={projects} onUpdateProject={handleUpdateProject} />}
            />

            {/* 404 */}
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
