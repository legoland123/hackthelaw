import React from 'react'
import { useNavigate } from 'react-router-dom'

const AIChatSidebar = () => {
    const navigate = useNavigate();

    return (
        <aside className="sidebar ai-chat-sidebar">
            <h4 className="sidebar-back-button" onClick={() => navigate('/')}>
                <span className="back-arrow">←</span>
                <span className="back-text">Back to Projects</span>
            </h4>

            <div className="sidebar-footer">
                <div className="sidebar-info">
                    <span>Capabilities:</span>
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