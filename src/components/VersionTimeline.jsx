import React from 'react'

const VersionTimeline = ({ documents, onDocumentSelect, selectedDocument, setActiveView }) => {
    // Generate Master Contract data dynamically based on original documents
    const generateMasterContracts = () => {
        if (!documents || documents.length === 0) return [];

        return documents.map((doc, index) => {
            const version = doc.version || (documents.length - index);
            const baseDate = new Date('2024-01-15T10:00:00');
            const timestamp = new Date(baseDate.getTime() + (index * 30 * 24 * 60 * 60 * 1000)); // 30 days apart

            return {
                id: `master-${version}`,
                version: version,
                title: `Master Contract v${version}`,
                timestamp: timestamp,
                description: `Master contract version ${version}`,
                processingStatus: 'completed',
                pdfPath: `/pdf/${version}.pdf`,
                fileInfo: {
                    downloadURL: `/pdf/${version}.pdf`,
                    type: 'application/pdf',
                    fileName: `${version}.pdf`,
                    size: 1024000 + (index * 128000) // Increasing file size
                }
            };
        });
    };

    const masterContracts = generateMasterContracts();

    const formatDate = (timestamp) => {
        // Handle Firestore timestamp objects
        const date = timestamp && timestamp.toDate ? timestamp.toDate() : new Date(timestamp)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const getDocumentType = (document) => {
        return 'Master Contract PDF'
    }

    const getConflictStatus = (document) => {
        // Remove conflict logic - no conflicts shown
        return false
    }

    if (masterContracts.length === 0) {
        return (
            <div className="timeline">
                <div className="timeline-header">
                    <h2>Document Timeline</h2>
                    <p>Track the evolution of your master contract</p>
                </div>

                <div className="empty-state">
                    <div className="empty-state-icon">📄</div>
                    <h3 className="empty-state-title">No Documents Yet</h3>
                    <p className="empty-state-description">
                        Start by uploading your first document to begin building the timeline.
                    </p>
                    <button className="btn btn-primary" onClick={() => setActiveView('upload')}>
                        Upload First Document
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="timeline">
            <div className="timeline-header">
                <h2>Document Timeline</h2>
                <p>Master Contract - {masterContracts.length} version{masterContracts.length !== 1 ? 's' : ''}</p>
            </div>

            <div className="timeline-list">
                {masterContracts
                    .sort((a, b) => b.version - a.version)
                    .map((document, index) => {
                        const hasConflicts = getConflictStatus(document)
                        const isSelected = selectedDocument && selectedDocument.id === document.id

                        return (
                            <div
                                key={document.id}
                                className={`timeline-item ${hasConflicts ? 'conflict' : ''}`}
                            >
                                <div className="timeline-version-header">
                                    <h3 className="version-title">Version {document.version}</h3>
                                    <span className="version-date">{formatDate(document.timestamp)}</span>
                                </div>

                                <div className="timeline-dual-cards">
                                    {/* Original Document Card */}
                                    <div className="timeline-card-container">
                                        <div className="card-label">Original Document</div>
                                        <div
                                            className={`timeline-card original-doc ${isSelected && !selectedDocument.isMasterCopy ? 'selected' : ''}`}
                                            onClick={() => {
                                                // Use original documents prop for original document selection
                                                const originalDoc = documents.find(doc => doc.version === document.version) || document;
                                                onDocumentSelect({ ...originalDoc, isMasterCopy: false });
                                            }}
                                        >
                                            <div className="timeline-card-header">
                                                <div>
                                                    <h4 className="timeline-card-title">
                                                        {`Original Contract v${document.version}`}
                                                    </h4>
                                                    <div className="timeline-card-meta">
                                                        <span>{getDocumentType(document)}</span>
                                                        <span>PDF File: {document.version}.pdf</span>
                                                    </div>
                                                </div>
                                                <div className="timeline-card-version">
                                                    Original
                                                </div>
                                            </div>

                                            <div className="timeline-card-content">
                                                {document.description && (
                                                    <p>{document.description}</p>
                                                )}
                                                <div className="timeline-changes">
                                                    <strong>File:</strong>
                                                    <p>Located at: {document.pdfPath}</p>
                                                </div>
                                            </div>

                                            <div className="timeline-card-actions">
                                                <button
                                                    className="btn btn-secondary"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        // Use original documents prop for original document selection
                                                        const originalDoc = documents.find(doc => doc.version === document.version) || document;
                                                        onDocumentSelect({ ...originalDoc, isMasterCopy: false });
                                                    }}
                                                >
                                                    View Original
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Master Copy Card */}
                                    <div className="timeline-card-container">
                                        <div className="card-label">Master Copy</div>
                                        <div
                                            className={`timeline-card master-copy ${isSelected && selectedDocument.isMasterCopy ? 'selected' : ''}`}
                                            onClick={() => onDocumentSelect({ ...document, isMasterCopy: true, originalVersion: document.version })}
                                        >
                                            <div className="timeline-card-header">
                                                <div>
                                                    <h4 className="timeline-card-title">
                                                        {document.title}
                                                    </h4>
                                                    <div className="timeline-card-meta">
                                                        <span>AI-Processed</span>
                                                        <span>Consolidated</span>
                                                        {document.processingStatus && (
                                                            <span className={`status-badge ${document.processingStatus}`}>
                                                                {document.processingStatus}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="timeline-card-version">
                                                    Master
                                                </div>
                                            </div>

                                            <div className="timeline-card-content">
                                                {document.description && (
                                                    <p>{document.description}</p>
                                                )}
                                            </div>

                                            <div className="timeline-card-actions">
                                                <button
                                                    className="btn btn-primary"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onDocumentSelect({ ...document, isMasterCopy: true, originalVersion: document.version });
                                                    }}
                                                >
                                                    View Master Copy
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )
                    })}
            </div>

            {/* Removed timeline-footer section with Timeline Summary */}
        </div>
    )
}

export default VersionTimeline 