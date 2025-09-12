import React from 'react';
import { useNavigate, Link } from 'react-router-dom';

const Overview = ({ projects, onCreateNewProject }) => {
    const navigate = useNavigate();

    const getProjectStatusClass = (status) => {
        if (!status) return 'status-new';

        switch (status.toLowerCase()) {
            case 'active': return 'status-active';
            case 'completed': return 'status-completed';
            case 'on-hold': return 'status-on-hold';
            default: return 'status-new';
        }
    };

    const handleProjectClick = (projectId) => {
        navigate(`/project/${projectId}`);
    };

    const handleCreateProject = () => {
        onCreateNewProject();
    };

    return (
        <main className="main-content overview-page">
            <div className="overview-header">
                <div className="overview-header-main">
                    <h1>Projects Overview</h1>
                    <p className="overview-description">
                        Select a project to view its timeline, manage documents, and resolve conflicts.
                    </p>
                </div>
                <div className="overview-header-actions">
                    <Link to="/ai-chat" className="ai-legal-btn" title="LIT Legal Mind">
                        🤖
                    </Link>
                    <button className="btn btn-primary" onClick={handleCreateProject}>
                        + Create New Project
                    </button>
                </div>
            </div>

            {projects.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-state-icon">📂</div>
                    <h3 className="empty-state-title">No Projects Found</h3>
                    <p className="empty-state-description">
                        Get started by creating your first project.
                    </p>
                    <div className="empty-state-actions">
                        <button className="btn btn-primary" onClick={handleCreateProject}>
                            Create New Project
                        </button>
                        <Link to="/ai-chat" className="ai-legal-btn" title="LIT Legal Mind">
                            🤖
                        </Link>
                    </div>
                </div>
            ) : (
                <div className="project-list">
                    {projects.map(project => (
                        <div key={project.id} className="project-card" onClick={() => handleProjectClick(project.id)}>
                            <div className="project-card-header">
                                <h3>{project.name || 'Untitled Project'}</h3>
                                <span className={`project-status ${getProjectStatusClass(project.status || 'new')}`}>
                                    {project.status || 'New'}
                                </span>
                            </div>
                            <p className="project-description">{project.description || 'No description available'}</p>
                            <div className="project-card-footer">
                                <span className="project-meta">
                                    <span className="meta-icon">📄</span>
                                    {(project.documentIds || []).length} version{(project.documentIds || []).length !== 1 ? 's' : ''}
                                </span>
                                <span className="project-meta">
                                    <span className="meta-icon">⚠️</span>
                                    {(project.conflicts || []).length} conflict{(project.conflicts || []).length !== 1 ? 's' : ''}
                                </span>
                                <span className="project-meta">
                                    <span className="meta-icon">📅</span>
                                    Last updated: {project.lastUpdated ? new Date(project.lastUpdated).toLocaleDateString() : 'Never'}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </main>
    );
};

export default Overview;