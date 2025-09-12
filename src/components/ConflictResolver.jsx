import React, { useState } from 'react'

const ConflictResolver = ({ conflicts = [], onResolve }) => {
    const [selectedConflict, setSelectedConflict] = useState(null)
    const [resolutions, setResolutions] = useState({})
    const [resolutionMode, setResolutionMode] = useState('quick') // 'manual' or 'quick'

    // Function to get conflict icon
    const getConflictIcon = (type) => {
        switch (type) {
            case 'clause_conflict': return '📋'
            case 'section_conflict': return '📄'
            case 'formatting_conflict': return '📝'
            default: return '⚠️'
        }
    }

    const handleQuickResolve = (conflictId, choice) => {
        const conflict = conflicts.find(c => c.id === conflictId)
        if (!conflict) return

        let resolvedContent = ''
        if (choice === 'current') {
            resolvedContent = conflict.document1.content
        } else if (choice === 'proposed') {
            resolvedContent = conflict.document2.content
        } else if (choice === 'both') {
            resolvedContent = `${conflict.document1.content}\n\n${conflict.document2.content}`
        }

        setResolutions(prev => ({
            ...prev,
            [conflictId]: {
                type: 'quick',
                choice,
                content: resolvedContent
            }
        }))
    }

    const handleManualResolve = (conflictId) => {
        const resolution = resolutions[conflictId]
        if (resolution && resolution.content && resolution.content.trim()) {
            onResolve(conflictId, resolution.content)
            setResolutions(prev => {
                const newResolutions = { ...prev }
                delete newResolutions[conflictId]
                return newResolutions
            })
            setSelectedConflict(null)
        }
    }

    const handleManualResolveAll = () => {
        Object.keys(resolutions).forEach(conflictId => {
            const resolution = resolutions[conflictId]
            if (resolution && resolution.content && resolution.content.trim()) {
                onResolve(conflictId, resolution.content)
            }
        })
        setResolutions({})
        setSelectedConflict(null)
    }

    const updateManualResolution = (conflictId, content) => {
        setResolutions(prev => ({
            ...prev,
            [conflictId]: {
                type: 'manual',
                content
            }
        }))
    }

    const renderLegalStyleDiff = (conflict) => {
        const { document1, document2, diff, lineNumbers } = conflict

        return (
            <div className="legal-diff-container">
                <div className="diff-header">
                    <div className="diff-version-info">
                        <div className="version-label current">
                            <span className="version-name">{document1.versionName}</span>
                            <span className="version-author">by {document1.author}</span>
                        </div>
                        <div className="version-label proposed">
                            <span className="version-name">{document2.versionName}</span>
                            <span className="version-author">by {document2.author}</span>
                        </div>
                    </div>
                    <div className="diff-actions">
                        <button
                            className="btn btn-sm btn-outline"
                            onClick={() => handleQuickResolve(conflict.id, 'current')}
                            title="Keep current version"
                        >
                            Keep Current
                        </button>
                        <button
                            className="btn btn-sm btn-outline"
                            onClick={() => handleQuickResolve(conflict.id, 'proposed')}
                            title="Accept proposed version"
                        >
                            Accept Proposed
                        </button>
                    </div>
                </div>

                <div className="diff-content">
                    <div className="diff-lines">
                        {diff && diff.map((line, index) => (
                            <div key={index} className={`diff-line ${line.type}`}>
                                <div className="line-content">
                                    <span className={`line-marker ${line.type}`}>
                                        {line.type === 'removed' ? '−' :
                                            line.type === 'added' ? '+' : ' '}
                                    </span>
                                    <span className={`line-text ${line.type}`}>
                                        {line.content}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="conflict-summary">
                    <div className="summary-item current">
                        <span className="summary-label">Current Version:</span>
                        <span className="summary-content">{document1.content || 'No content'}</span>
                    </div>
                    <div className="summary-item proposed">
                        <span className="summary-label">Proposed Version:</span>
                        <span className="summary-content">{document2.content || 'No content'}</span>
                    </div>
                </div>
            </div>
        )
    }

    const renderResolutionEditor = (conflict) => {
        const resolution = resolutions[conflict.id]
        const isResolved = resolution && resolution.content && resolution.content.trim()

        return (
            <div className="resolution-editor">
                <div className="editor-header">
                    <h4>Resolution Editor</h4>
                    <div className="editor-mode-toggle">
                        <button
                            className={`btn btn-sm ${resolutionMode === 'manual' ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setResolutionMode('manual')}
                        >
                            Custom Edit
                        </button>
                        <button
                            className={`btn btn-sm ${resolutionMode === 'quick' ? 'btn-primary' : 'btn-outline'}`}
                            onClick={() => setResolutionMode('quick')}
                        >
                            Quick Options
                        </button>
                    </div>
                </div>

                {resolutionMode === 'manual' ? (
                    <div className="manual-editor">
                        <div className="editor-instructions">
                            <p>Edit the text below to create your final version of this clause:</p>
                        </div>
                        <textarea
                            className="form-input form-textarea resolution-textarea"
                            placeholder="Enter your final version of this clause..."
                            value={resolution?.content || ''}
                            onChange={(e) => updateManualResolution(conflict.id, e.target.value)}
                            rows="8"
                        />
                        <div className="editor-actions">
                            <button
                                className="btn btn-success"
                                onClick={() => handleManualResolve(conflict.id)}
                                disabled={!isResolved}
                            >
                                ✅ Apply Resolution
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={() => updateManualResolution(conflict.id, '')}
                            >
                                Clear
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="quick-actions">
                        <div className="quick-action-buttons">
                            <button
                                className="btn btn-outline"
                                onClick={() => handleQuickResolve(conflict.id, 'current')}
                            >
                                <span className="action-icon">📋</span>
                                Keep Current Version
                                <span className="action-preview">{conflict.document1.content}</span>
                            </button>
                            <button
                                className="btn btn-outline"
                                onClick={() => handleQuickResolve(conflict.id, 'proposed')}
                            >
                                <span className="action-icon">📝</span>
                                Accept Proposed Version
                                <span className="action-preview">{conflict.document2.content}</span>
                            </button>
                        </div>
                        {isResolved && (
                            <div className="quick-resolution-preview">
                                <h5>Final Version Preview:</h5>
                                <div className="preview-content">
                                    {resolution.content}
                                </div>
                                <button
                                    className="btn btn-success"
                                    onClick={() => handleManualResolve(conflict.id)}
                                >
                                    ✅ Apply This Version
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>
        )
    }

    // Handle no conflicts case
    if (!conflicts || conflicts.length === 0) {
        return (
            <div className="conflict-resolver">
                <div className="conflict-header">
                    <h2>Document Conflict Resolution</h2>
                    <p>Review and resolve conflicts between document versions</p>
                </div>

                <div className="empty-state">
                    <div className="empty-state-icon">✅</div>
                    <h3 className="empty-state-title">No Conflicts Found</h3>
                    <p className="empty-state-description">
                        All document versions are consistent. No conflicts to resolve.
                    </p>
                </div>
            </div>
        )
    }

    const resolvedCount = Object.keys(resolutions).length
    const hasResolutions = resolvedCount > 0

    return (
        <div className="conflict-resolver">
            <div className="conflict-header">
                <div className="header-main">
                    <h2>Document Conflict Resolution</h2>
                    <p>{conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} found between document versions</p>
                </div>
                {hasResolutions && (
                    <div className="header-actions">
                        <span className="resolution-count">
                            {resolvedCount} of {conflicts.length} resolved
                        </span>
                        <button
                            className="btn btn-success"
                            onClick={handleManualResolveAll}
                        >
                            ✅ Apply All Resolutions ({resolvedCount})
                        </button>
                    </div>
                )}
            </div>

            <div className="conflicts-list">
                {conflicts.map(conflict => {
                    const resolution = resolutions[conflict.id]
                    const isResolved = resolution && resolution.content && resolution.content.trim()

                    return (
                        <div key={conflict.id} className={`conflict-item ${isResolved ? 'resolved' : ''}`}>
                            <div className="conflict-header">
                                <div className="conflict-info">
                                    <div className="conflict-icon">{getConflictIcon(conflict.type)}</div>
                                    <div>
                                        <h3 className="conflict-title">
                                            {conflict.title}
                                            {isResolved && <span className="resolved-badge">✅</span>}
                                        </h3>
                                        <p className="conflict-description">{conflict.description}</p>
                                        {conflict.lineNumbers && (
                                            <div className="conflict-location">
                                                Section {conflict.lineNumbers.start}-{conflict.lineNumbers.end}
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="conflict-meta">
                                    <button
                                        className="btn btn-primary"
                                        onClick={() => setSelectedConflict(selectedConflict === conflict.id ? null : conflict.id)}
                                    >
                                        {selectedConflict === conflict.id ? 'Hide Details' : 'Review Conflict'}
                                    </button>
                                </div>
                            </div>

                            {selectedConflict === conflict.id && (
                                <div className="conflict-details">
                                    {renderLegalStyleDiff(conflict)}
                                    {renderResolutionEditor(conflict)}
                                </div>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default ConflictResolver 