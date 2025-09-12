/**
 * Document Reference Parser - Parses AI responses for document references
 */

import DocumentReference from '../components/DocumentReference';
import React from 'react';

/**
 * Parse AI response for document references and convert them to React components
 * @param {string} content - AI response content
 * @param {Array} documents - Array of project documents
 * @param {Function} onDocumentClick - Function to handle document clicks
 * @returns {Array} Array of text and React components
 */
export const parseDocumentReferences = (content, documents, onDocumentClick) => {
    if (!content || !documents || documents.length === 0) {
        return [content];
    }

    const parts = [];
    let lastIndex = 0;

    const documentPattern = /\[\[Document (\d+)\]\]|Document\s+(\d+)/gi;
    let match;

    while ((match = documentPattern.exec(content)) !== null) {
        const fullMatch = match[0];
        const documentNumber = parseInt(match[1] || match[2], 10);

        if (match.index > lastIndex) {
            parts.push(content.substring(lastIndex, match.index));
        }

        let targetDocument = null;
        if (documentNumber > 0 && documentNumber <= documents.length) {
            targetDocument = documents[documentNumber - 1];
        }

        if (targetDocument) {
            parts.push(
                React.createElement(DocumentReference, {
                    key: `doc-${targetDocument.id}-${match.index}`,
                    documentId: targetDocument.id,
                    documentTitle: targetDocument.title,
                    version: targetDocument.version,
                    onDocumentClick: onDocumentClick
                })
            );
        } else {
            parts.push(fullMatch);
        }

        lastIndex = match.index + fullMatch.length;
    }

    if (lastIndex < content.length) {
        parts.push(content.substring(lastIndex));
    }

    return parts.length > 0 ? parts : [content];
};

/**
 * Check if content contains document references
 * @param {string} content - Content to check
 * @returns {boolean} True if content contains document references
 */
export const hasDocumentReferences = (content) => {
    if (!content) return false;
    const documentPattern = /\[\[Document \d+\]\]|Document\s+\d+/i;
    return documentPattern.test(content);
}; 