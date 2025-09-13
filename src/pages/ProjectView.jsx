// src/pages/ProjectView.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';

import Sidebar from '../components/Sidebar';
import Breadcrumb from '../components/Breadcrumb';
import FileManager from '../components/FileManager';
import ConflictResolver from '../components/ConflictResolver';
import DocumentViewer from '../components/DocumentViewer';
import ProjectChat from '../components/ProjectChat';
// import ProjectRules from '../components/ProjectRules';
import { documentServices, conflictServices } from '../firebase/services';

const ProjectView = ({ projects = [], onUpdateProject }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // files == our default “timeline”
  const [activeView, setActiveView] = useState('timeline');
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);

  const project = projects.find((p) => p.id === projectId);

  // Derive the view from URL (chat/statutes/files)
  useEffect(() => {
    if (pathname.endsWith('/chat')) setActiveView('ai-chat');
    else if (pathname.endsWith('/statutes')) setActiveView('statutes');
    else setActiveView('timeline');
  }, [pathname]);

  // Load docs for this project
  useEffect(() => {
    if (!project) return;
    (async () => {
      setLoading(true);
      try {
        let docs = [];
        if (project.documentIds?.length) {
          const reads = project.documentIds.map((id) => documentServices.getDocumentById(id));
          docs = (await Promise.all(reads)).filter(Boolean);
        }
        setDocuments(docs);

        // Conflicts are optional; don’t break page if not available
        try {
          const confs = await conflictServices.getConflictsByProjectId(projectId);
          setConflicts(confs || []);
        } catch {
          setConflicts([]);
        }
      } catch (e) {
        console.error('Failed to fetch project data:', e);
      } finally {
        setLoading(false);
      }
    })();
  }, [projectId, project]);

  const handleBackToOverview = () => navigate('/');

  // FileManager handlers
  const handleCreate = async (file, title) => {
    const payload = {
      title: title || file.name,
      description: '',
      author: 'Anonymous',
      changes: [],
    };
    const created = await documentServices.createDocument(projectId, payload, file);
    setDocuments((prev) => [created, ...prev]);
    onUpdateProject?.({
      ...project,
      documentIds: [...(project.documentIds || []), created.id],
    });
  };

  const handleDelete = async (docId) => {
    await documentServices.deleteDocument(docId);
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
    onUpdateProject?.({
      ...project,
      documentIds: (project.documentIds || []).filter((id) => id !== docId),
    });
    if (selectedDocument?.id === docId) setSelectedDocument(null);
  };

  if (!project) {
    return (
      <div className="app-container">
        <main className="main-content">
          <div className="empty-state">
            <div className="empty-state-icon">⏳</div>
            <h3 className="empty-state-title">Loading Project…</h3>
            <p className="empty-state-description">
              Please wait while we fetch the project details.
            </p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app-container">
      <Sidebar
        projectId={projectId}
        activeView={activeView}
        setActiveView={setActiveView}
        documentCount={documents.length}
        conflictCount={conflicts.length}
        projectName={project.name}
        onBackToOverview={handleBackToOverview}
      />

      <main className="main-content">
        <Breadcrumb projectName={project.name} />

        {loading ? (
          <div className="loading"><div className="spinner" />Loading project data…</div>
        ) : (
          <>
            {activeView === 'timeline' && (
              <FileManager
                projectId={projectId}
                documents={documents}
                onOpen={setSelectedDocument}
                onCreate={handleCreate}
                onDelete={handleDelete}
              />
            )}

            {activeView === 'ai-chat' && (
              <ProjectChat
                project={project}
                documents={documents}
                onDocumentSelect={setSelectedDocument}
              />
            )}

            {activeView === 'statutes' && (
              <div className="card">
                <h3>Statute Finder (Project Scoped)</h3>
                <p>
                  You’re on <code>/project/{projectId}/statutes</code>. Hook this up to your
                  project-specific statute UI when ready.
                </p>
              </div>
            )}

            {selectedDocument && (
              <DocumentViewer
                document={selectedDocument}
                onClose={() => setSelectedDocument(null)}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
};

export default ProjectView;
