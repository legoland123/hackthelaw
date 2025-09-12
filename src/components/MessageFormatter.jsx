import React from 'react';
import { parseDocumentReferences } from '../utils/documentReferenceParser';

const MessageFormatter = ({ content, documents, onDocumentClick }) => {
    if (!content) return null;

    // Function to process bold text within a string
    const processBoldText = (text) => {
        if (!text.includes('**')) return text;

        const parts = text.split('**');
        const processedParts = [];

        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];

            // Skip empty parts
            if (part === '') continue;

            // If this is an odd-indexed part (should be bold), wrap it in strong
            if (i % 2 === 1) {
                processedParts.push(<strong key={i}>{part}</strong>);
            } else {
                processedParts.push(part);
            }
        }

        return processedParts.length > 0 ? processedParts : text;
    };

    // Function to process document references
    const processDocumentReferences = (text) => {
        if (!documents || documents.length === 0) {
            return processBoldText(text);
        }

        const parsedParts = parseDocumentReferences(text, documents, onDocumentClick);
        return parsedParts.map((part, partIndex) => {
            if (React.isValidElement(part)) {
                return part;
            } else {
                return processBoldText(part);
            }
        });
    };

    // Split content into lines
    const lines = content.split('\n');

    return (
        <div className="formatted-message">
            {lines.map((line, index) => {
                const indentation = line.length - line.trimStart().length;
                const trimmedLine = line.trim();

                const style = {
                    paddingLeft: `${indentation * 0.75}em`,
                };

                const bulletMatch = trimmedLine.match(/^[•*-]\s+(.*)/);
                if (bulletMatch) {
                    const bulletContent = bulletMatch[1];
                    return (
                        <div key={index} className="message-bullet-container" style={style}>
                            <div className="message-bullet">
                                {processDocumentReferences(bulletContent)}
                            </div>
                        </div>
                    );
                }

                const numberedMatch = trimmedLine.match(/^(\d+\.)\s*(.*)/);
                if (numberedMatch) {
                    const listNumber = numberedMatch[1];
                    const listContent = numberedMatch[2];
                    return (
                        <div key={index} className="message-numbered" style={style}>
                            <span className="message-list-number">{listNumber}</span>
                            <span>{processDocumentReferences(listContent)}</span>
                        </div>
                    );
                }

                if (trimmedLine === '') {
                    return <div key={index} className="message-spacer"></div>;
                }

                return (
                    <div key={index} className="message-line">
                        {processDocumentReferences(line)}
                    </div>
                );
            })}
        </div>
    );
};

export default MessageFormatter; 