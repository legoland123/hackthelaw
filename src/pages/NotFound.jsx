import React from 'react';
import { useNavigate } from 'react-router-dom';

const NotFound = () => {
    const navigate = useNavigate();

    return (
        <div className="app-container">
            <div className="main-content">
                <div className="empty-state">
                    <div className="empty-state-icon">🔍</div>
                    <h3 className="empty-state-title">Page Not Found</h3>
                    <p className="empty-state-description">
                        The page you're looking for doesn't exist or has been moved.
                    </p>
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/')}>
                            Go to Overview
                        </button>
                        <button className="btn btn-secondary" onClick={() => navigate(-1)}>
                            Go Back
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NotFound; 