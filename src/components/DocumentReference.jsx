import React from 'react';

const DocumentReference = ({ documentId, documentTitle, version, onDocumentClick }) => {
    const handleClick = () => {
        if (onDocumentClick && documentId) {
            onDocumentClick(documentId);
        }
    };

    return (
        <span
            className="document-reference"
            onClick={handleClick}
            title={`Click to view ${documentTitle} (Version ${version})`}
        >
            <strong>📄 {documentTitle}</strong> (Version {version})
        </span>
    );
};

export default DocumentReference; 