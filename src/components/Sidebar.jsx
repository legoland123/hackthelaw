import React from 'react'
import { useNavigate } from 'react-router-dom'

const Sidebar = ({ activeView, setActiveView, documentCount, conflictCount, projectName, onBackToOverview }) => {
    const navigate = useNavigate();

    const navItems = [
        {
            id: 'timeline',
            label: 'Timeline',
            icon: '📅',
            description: 'View document history'
        },
        {
            id: 'upload',
            label: 'Upload Document',
            icon: '📄',
            description: 'Add new document'
        },
        {
            id: 'conflicts',
            label: 'Conflicts',
            icon: '⚠️',
            description: 'Resolve conflicts',
            badge: conflictCount
        },
        {
            id: 'rules',
            label: 'Rules',
            icon: '❗',
            description: 'Manage project rules'
        },
        {
            id: 'ai-chat',
            label: 'LIT Legal Mind',
            icon: '🤖',
            description: 'Chat with LIT Legal Mind',
            isExternal: false
        }
    ]

    const handleNavClick = (item) => {
        if (item.isExternal) {
            navigate('/ai-chat');
        } else {
            setActiveView(item.id);
        }
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
                                className={activeView === item.id ? 'active' : ''}
                                onClick={() => handleNavClick(item)}
                                title={item.description}
                            >
                                <span className="icon">{item.icon}</span>
                                <span>{item.label}</span>
                                {item.badge && item.badge > 0 && (
                                    <span className="badge">{item.badge}</span>
                                )}
                                {item.isExternal && (
                                    <span className="external-indicator">↗</span>
                                )}
                            </button>
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    )
}

export default Sidebar 