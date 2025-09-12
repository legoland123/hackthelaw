import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Breadcrumb from '../components/Breadcrumb';
import VersionTimeline from '../components/VersionTimeline';
import DocumentUpload from '../components/DocumentUpload';
import ConflictResolver from '../components/ConflictResolver';
import DocumentViewer from '../components/DocumentViewer';
import ProjectChat from '../components/ProjectChat';
import ProjectRules from '../components/ProjectRules';
import { documentServices, conflictServices } from '../firebase/services';

const ProjectView = ({ projects, onUpdateProject }) => {
    const { projectId } = useParams();
    const navigate = useNavigate();

    const [activeView, setActiveView] = useState('timeline');
    const [selectedDocument, setSelectedDocument] = useState(null);
    const [documents, setDocuments] = useState([]);
    const [conflicts, setConflicts] = useState([]);
    const [loading, setLoading] = useState(true);

    const project = projects.find(p => p.id === projectId);

    useEffect(() => {
        if (project) {
            const fetchData = async () => {
                try {
                    setLoading(true);

                    let docs = [];
                    if (project.documentIds && project.documentIds.length > 0) {
                        const docPromises = project.documentIds.map(id => documentServices.getDocumentById(id));
                        docs = await Promise.all(docPromises);
                    }

                    // Set documents first, regardless of conflicts
                    setDocuments(docs.filter(Boolean));

                    // Try to fetch conflicts, but don't let it fail the entire operation
                    try {
                        const confs = await conflictServices.getConflictsByProjectId(projectId);
                        setConflicts(confs);
                    } catch (conflictError) {
                        console.warn('Failed to fetch conflicts (this is expected if no index is set up):', conflictError);
                        setConflicts([]);
                    }
                } catch (error) {
                    console.error("Failed to fetch project data:", error);
                } finally {
                    setLoading(false);
                }
            };
            fetchData();
        }
    }, [projectId, project]);

    if (!project) {
        return (
            <div className="app-container">
                <div className="main-content">
                    <div className="empty-state">
                        <div className="empty-state-icon">⏳</div>
                        <h3 className="empty-state-title">Loading Project...</h3>
                        <p className="empty-state-description">
                            Please wait while we fetch the project details. If you've just created a new project, this may take a moment.
                        </p>
                    </div>
                </div>
            </div>
        );
    }

    const handleDocumentUpload = (newDocument) => {
        setDocuments(prev => [newDocument, ...prev]);
        const updatedProject = {
            ...project,
            documentIds: [...(project.documentIds || []), newDocument.id]
        };
        onUpdateProject(updatedProject);
        setActiveView('timeline');
    };

    const handleConflictResolved = (conflictId, resolution) => {
        setConflicts(prev => prev.filter(c => c.id !== conflictId));
    };

    const handleBackToOverview = () => {
        navigate('/');
    };

    return (
        <div className="app-container">
            <Sidebar
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
                    <div className="loading">
                        <div className="spinner"></div>
                        Loading project data...
                    </div>
                ) : (
                    <>
                        {activeView === 'timeline' && (
                            <VersionTimeline
                                documents={documents}
                                onDocumentSelect={setSelectedDocument}
                                selectedDocument={selectedDocument}
                                setActiveView={setActiveView}
                            />
                        )}
                        {activeView === 'upload' && (
                            <DocumentUpload
                                projectId={projectId}
                                onUpload={handleDocumentUpload}
                                existingDocuments={documents}
                            />
                        )}
                        {activeView === 'conflicts' && (
                            <ConflictResolver
                                conflicts={conflicts}
                                onResolve={handleConflictResolved}
                            />
                        )}
                        {activeView === 'ai-chat' && (
                            <ProjectChat
                                project={project}
                                documents={documents}
                                onDocumentSelect={setSelectedDocument}
                            />
                        )}
                        {activeView === 'rules' && (
                            <ProjectRules
                                projectId={projectId}
                                projectName={project.name}
                            />
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