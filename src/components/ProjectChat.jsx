import React, { useState, useRef, useEffect } from 'react';
import MessageFormatter from './MessageFormatter';
import DocumentReference from './DocumentReference';
import chatService from '../services/chatService';
import documentProcessor from '../services/documentProcessor';

const ProjectChat = ({ project, documents, onDocumentSelect }) => {
    const handleDocumentClick = (documentId) => {
        if (onDocumentSelect) {
            const document = documents.find(doc => doc.id === documentId);
            if (document) {
                onDocumentSelect(document);
            }
        }
    };

    const createInitialMessage = () => {
        const validDocuments = documents.filter(doc => {
            const content = doc.content || '';
            return documentProcessor.isValidContent(content);
        });

        let message = `Hello! I'm LIT Legal Mind, your AI legal assistant for the **${project.name}** project. `;

        if (validDocuments.length > 0) {
            message += `I have access to **${validDocuments.length} document${validDocuments.length !== 1 ? 's' : ''}** and can help you analyze them, answer questions, and provide legal insights. `;
        } else {
            message += `I can see ${documents.length} document${documents.length !== 1 ? 's' : ''} in this project. `;
        }

        message += `How can I assist you today?`;

        return message;
    };

    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'ai',
            content: createInitialMessage(),
            timestamp: new Date(),
            status: 'sent'
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isBackendConnected, setIsBackendConnected] = useState(true);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        // Check backend health on component mount
        checkBackendHealth();

        // Auto-focus input on mount
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    useEffect(() => {
        const newInitialMessage = createInitialMessage();
        setMessages(prev => {
            if (prev.length > 0 && prev[0].type === 'ai' && prev[0].id === 1) {
                // Update the first message if it's the initial AI message
                return [
                    {
                        ...prev[0],
                        content: newInitialMessage
                    },
                    ...prev.slice(1)
                ];
            }
            return prev;
        });
    }, [documents, project.name]);

    const checkBackendHealth = async () => {
        try {
            const isHealthy = await chatService.checkHealth();
            setIsBackendConnected(isHealthy);
            if (!isHealthy) {
                console.warn('Backend is not available, using fallback responses');
            }
        } catch (error) {
            console.error('Failed to check backend health:', error);
            setIsBackendConnected(false);
        }
    };

    const formatTime = (timestamp) => {
        return timestamp.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Create project context with document information
    const createProjectContext = () => {
        const projectContext = {
            project_name: project.name,
            project_description: project.description,
            documents: documents.map(doc => {
                const content = doc.content || '';
                const contentStats = doc.content_stats || documentProcessor.getContentStats(content);
                const isValidContent = documentProcessor.isValidContent(content);

                return {
                    id: doc.id, // Include document ID for referencing
                    title: doc.title || 'Untitled Document',
                    version: doc.version || 1,
                    author: doc.author || 'Unknown',
                    description: doc.description || '',
                    changes: doc.changes || [],
                    content: content,
                    content_length: contentStats?.length || 0,
                    word_count: contentStats?.wordCount || 0,
                    has_valid_content: isValidContent,
                    timestamp: doc.timestamp
                };
            }).filter(doc => doc.has_valid_content) // Only include documents with valid content
        };

        console.log('Project context created:', {
            project_name: projectContext.project_name,
            document_count: projectContext.documents.length,
            total_words: projectContext.documents.reduce((sum, doc) => sum + doc.word_count, 0),
            total_content_length: projectContext.documents.reduce((sum, doc) => sum + doc.content_length, 0)
        });

        return projectContext;
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();

        if (!inputMessage.trim()) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputMessage,
            timestamp: new Date(),
            status: 'sent'
        };

        setMessages(prev => [...prev, userMessage]);
        setInputMessage('');
        setIsTyping(true);

        try {
            let aiResponse;

            if (isBackendConnected) {
                // Use real backend API with project context
                const conversationHistory = messages
                    .filter(msg => msg.type === 'user' || msg.type === 'ai')
                    .map(msg => ({
                        role: msg.type,
                        content: msg.content,
                        timestamp: msg.timestamp.toISOString()
                    }));

                const projectContext = createProjectContext();

                const response = await chatService.sendMessage(
                    inputMessage,
                    conversationHistory,
                    'anonymous', // TODO: Replace with actual user ID when auth is implemented
                    project.id,
                    projectContext
                );

                aiResponse = response.response;
            } else {
                // Fallback to simulated response with project context
                aiResponse = generateFallbackResponse(inputMessage, project, documents);
                await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
            }

            const aiMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: aiResponse,
                timestamp: new Date(),
                status: 'sent'
            };

            setMessages(prev => [...prev, aiMessage]);

        } catch (error) {
            console.error('Failed to get AI response:', error);

            // Show error message to user
            const errorMessage = {
                id: Date.now() + 1,
                type: 'ai',
                content: 'I apologize, but I\'m having trouble connecting to my services right now. Please try again in a moment, or check your internet connection.',
                timestamp: new Date(),
                status: 'error'
            };

            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsTyping(false);
        }
    };

    const generateFallbackResponse = (userInput, project, documents) => {
        const input = userInput.toLowerCase();

        // Fallback response logic when backend is not available
        if (input.includes('document') || input.includes('version')) {
            return `I can see you have **${documents.length} document${documents.length !== 1 ? 's' : ''}** in the **${project.name}** project:\n\n${documents.map((doc, index) =>
                `• **${doc.title}** (Version ${doc.version}) by ${doc.author || 'Unknown'}\n  ${doc.description || 'No description available'}`
            ).join('\n\n')}\n\nWhat specific questions do you have about these documents?`;
        } else if (input.includes('project') || input.includes('overview')) {
            return `Here's an overview of the **${project.name}** project:\n\n• **Description**: ${project.description || 'No description available'}\n• **Total Documents**: ${documents.length}\n• **Latest Version**: ${documents.length > 0 ? `Version ${documents[0].version}` : 'No documents yet'}\n\nI can help you analyze specific documents, compare versions, or answer questions about the project content.`;
        } else if (input.includes('analyze') || input.includes('review')) {
            return `I can help you analyze the documents in the **${project.name}** project. Here's what I can do:\n\n• **Document comparison** between different versions\n• **Content analysis** and key points extraction\n• **Legal term identification** and explanation\n• **Conflict detection** between versions\n• **Compliance review** for Singapore law\n\nWhich document would you like me to analyze?`;
        } else if (input.includes('conflict') || input.includes('difference')) {
            return `I can help identify conflicts and differences between document versions in the **${project.name}** project. With ${documents.length} document${documents.length !== 1 ? 's' : ''}, I can:\n\n• **Compare versions** and highlight changes\n• **Identify conflicting terms** or clauses\n• **Track modifications** across versions\n• **Suggest resolutions** for conflicts\n• **Maintain consistency** across documents\n\nWould you like me to compare specific versions?`;
        } else {
            return `I understand you're asking about "${userInput}" in the context of the **${project.name}** project. I have access to ${documents.length} document${documents.length !== 1 ? 's' : ''} and can help with:\n\n• **Legal document analysis** and review\n• **Contract assessment** and improvement suggestions\n• **Version control** and conflict resolution\n• **Legal research** on Singapore law\n• **Document drafting** assistance\n\nCould you provide more specific details about what you need assistance with?`;
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const clearChat = () => {
        setMessages([
            {
                id: Date.now(),
                type: 'ai',
                content: createInitialMessage(),
                timestamp: new Date(),
                status: 'sent'
            }
        ]);
    };

    const exportChat = () => {
        const chatText = messages.map(msg =>
            `${msg.type === 'user' ? 'You' : 'LIT Legal Mind'}: ${msg.content}`
        ).join('\n\n');

        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${project.name}-chat-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="chat-container">
            <div className="chat-header-compact">
                <div className="project-chat-info">
                    <h3>🤖 LIT Legal Mind - {project.name}</h3>
                    <p>{documents.length} document{documents.length !== 1 ? 's' : ''} available for analysis</p>
                </div>
                {!isBackendConnected && (
                    <div className="connection-status offline">
                        ⚠️ Offline Mode - Using fallback responses
                    </div>
                )}
                <div className="chat-actions">
                    <button className="btn btn-secondary" onClick={clearChat}>
                        🗑️ Clear
                    </button>
                    <button className="btn btn-secondary" onClick={exportChat}>
                        📥 Export
                    </button>
                </div>
            </div>

            <div className="chat-messages">
                {messages.map((message) => (
                    <div key={message.id} className={`message ${message.type} ${message.status === 'error' ? 'error' : ''}`}>
                        <div className="message-avatar">
                            {message.type === 'ai' ? '🤖' : '👤'}
                        </div>
                        <div className="message-content">
                            <div className="message-header">
                                <span className="message-sender">
                                    {message.type === 'ai' ? 'LIT Legal Mind' : 'You'}
                                </span>
                                <span className="message-time">
                                    {formatTime(message.timestamp)}
                                </span>
                            </div>
                            <div className="message-text">
                                {message.type === 'ai' ? (
                                    <MessageFormatter
                                        content={message.content}
                                        documents={documents}
                                        onDocumentClick={handleDocumentClick}
                                    />
                                ) : (
                                    message.content
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {isTyping && (
                    <div className="message ai">
                        <div className="message-avatar">🤖</div>
                        <div className="message-content">
                            <div className="message-header">
                                <span className="message-sender">LIT Legal Mind</span>
                            </div>
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-container">
                <form onSubmit={handleSendMessage} className="chat-input-form">
                    <div className="chat-input-wrapper">
                        <textarea
                            ref={inputRef}
                            className="chat-input"
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="Ask about your project documents, legal analysis, or version comparisons..."
                            rows="1"
                            disabled={isTyping}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary send-button"
                            disabled={!inputMessage.trim() || isTyping}
                        >
                            📤
                        </button>
                    </div>
                    {inputMessage.length > 0 && (
                        <div className="input-counter">
                            {inputMessage.length} characters
                        </div>
                    )}
                </form>
            </div>
        </div>
    );
};

export default ProjectChat; 