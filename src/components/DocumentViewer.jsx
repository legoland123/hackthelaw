import React from 'react';

const DocumentViewer = ({ document, onClose }) => {
    const formatDate = (timestamp) => {
        // Handle Firestore timestamp objects
        const date = timestamp?.toDate ? timestamp.toDate() : new Date(timestamp);
        if (isNaN(date.getTime())) {
            return 'Invalid Date';
        }
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const formatFileSize = (bytes) => {
        if (!bytes) return '0 Bytes';
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const renderFileContent = () => {
        if (document.fileInfo && document.fileInfo.downloadURL) {
            const { type, downloadURL, size } = document.fileInfo;
            const fileType = type || 'application/pdf';

            if (fileType.includes('pdf')) {
                return (
                    <iframe
                        src={`${downloadURL}#toolbar=0`}
                        title={document.title}
                        width="100%"
                        height="100%"
                        style={{ border: 'none' }}
                    />
                );
            } else if (fileType.includes('image')) {
                return (
                    <div className="image-preview">
                        <img
                            src={downloadURL}
                            alt={document.title}
                            style={{ maxWidth: '100%', height: 'auto', borderRadius: '4px' }}
                        />
                    </div>
                );
            } else {
                return (
                    <div className="file-preview">
                        <h4>📄 Document Preview not available</h4>
                        <p>You can download the file to view it.</p>
                        <a
                            href={downloadURL}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn btn-primary"
                        >
                            Download {formatFileSize(size)}
                        </a>
                    </div>
                );
            }
        }
        return <div className="file-preview"><h4>📄 Document not available</h4></div>;
    };

    return (
        <div className="document-viewer" onClick={onClose}>
            <div className="document-viewer-content" onClick={(e) => e.stopPropagation()}>
                <div className="document-viewer-header">
                    <div className="document-viewer-title">
                        <h2>{document.title || 'Document'}</h2>
                        <p>Version {document.version} • Uploaded on {formatDate(document.timestamp)}</p>
                    </div>
                    <button className="btn btn-secondary close-button" onClick={onClose}>
                        ✕
                    </button>
                </div>

                <div className="document-viewer-body">
                    {renderFileContent()}
                </div>

                <div className="document-viewer-actions">
                    <a
                        href={document.fileInfo?.downloadURL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-primary"
                        download
                    >
                        📥 Download
                    </a>
                </div>
            </div>
        </div>
    );
};

export default DocumentViewer;