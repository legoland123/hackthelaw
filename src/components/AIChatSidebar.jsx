import React from 'react'
import { useNavigate } from 'react-router-dom'

const AIChatSidebar = () => {
    const navigate = useNavigate();

    return (
        <aside className="sidebar ai-chat-sidebar">
            <div className="sidebar-back-button" onClick={() => navigate('/')}>
                <span className="back-arrow">←</span>
                <span className="back-text">Back to Projects</span>
            </div>

            <div className="sidebar-header">
                <h3>LIT Legal Mind</h3>
                <p className="sidebar-stats">
                    Your intelligent legal companion
                </p>
            </div>

            <nav className="sidebar-nav">
                <ul>
                    <li>
                        <button className="active">
                            <span className="icon">💬</span>
                            <span>Chat</span>
                        </button>
                    </li>
                </ul>
            </nav>

            <div className="sidebar-footer">
                <div className="sidebar-info">
                    <h4>AI Capabilities</h4>
                    <div className="capability-item">
                        <span className="capability-icon">📋</span>
                        <span>Contract Analysis</span>
                    </div>
                    <div className="capability-item">
                        <span className="capability-icon">⚖️</span>
                        <span>Legal Research</span>
                    </div>
                    <div className="capability-item">
                        <span className="capability-icon">🔍</span>
                        <span>Document Comparison</span>
                    </div>
                    <div className="capability-item">
                        <span className="capability-icon">⚠️</span>
                        <span>Conflict Detection</span>
                    </div>
                    <div className="capability-item">
                        <span className="capability-icon">📝</span>
                        <span>Document Drafting</span>
                    </div>
                    <div className="capability-item">
                        <span className="capability-icon">📚</span>
                        <span>Legal Education</span>
                    </div>
                </div>
            </div>
        </aside>
    )
}

export default AIChatSidebar 