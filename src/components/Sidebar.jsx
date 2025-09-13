// src/components/Sidebar.jsx
import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Sidebar = ({
  projectId,
  activeView,
  setActiveView,
  documentCount,
  conflictCount,
  projectName,
  onBackToOverview,
}) => {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  // derive current from URL for accurate highlight
  const current =
    pathname.endsWith('/chat') ? 'ai-chat' :
    pathname.endsWith('/statutes') ? 'statutes' :
    'timeline';

  const navItems = [
    { id: 'timeline', label: 'Files', icon: '🗂️', description: 'Project files' },
    { id: 'statutes', label: 'Statute Finder', icon: '⚖️', description: 'Rank applicable statutes' },
    { id: 'ai-chat', label: 'Project Chat', icon: '💬', description: 'Chat for this project' },
  ];

  const handleNavClick = (item) => {
    if (item.id === 'ai-chat') {
      navigate(`/project/${projectId}/chat`);
      return;
    }
    if (item.id === 'statutes') {
      navigate(`/project/${projectId}/statutes`);
      return;
    }
    // files view is internal
    navigate(`/project/${projectId}`);
    setActiveView('timeline');
  };

  return (
    <aside className="sidebar">
      {onBackToOverview && (
        <button className="sidebar-back-button" onClick={onBackToOverview}>
          <span className="back-arrow">←</span>
          <span className="back-text">Back to Overview</span>
        </button>
      )}

      <div className="sidebar-header">
        <h3>{projectName}</h3>
        <p className="sidebar-stats">
          {documentCount} document{documentCount !== 1 ? 's' : ''} in timeline
        </p>
      </div>

      <nav className="sidebar-nav">
        <ul>
          {navItems.map(item => (
            <li key={item.id}>
              <button
                className={current === item.id ? 'active' : ''}
                onClick={() => handleNavClick(item)}
                title={item.description}
              >
                <span className="icon">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
