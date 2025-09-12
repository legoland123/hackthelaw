import React, { useState, useRef, useEffect } from 'react';
import AIChatSidebar from '../components/AIChatSidebar';
import MessageFormatter from '../components/MessageFormatter';
import chatService from '../services/chatService';

const AIChat = () => {
    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'ai',
            content: 'Hello! I\'m LIT Legal Mind, your AI legal assistant. I can help you with document analysis, contract review, legal research, and more. How can I assist you today?',
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
                // Use real backend API
                const conversationHistory = messages
                    .filter(msg => msg.type === 'user' || msg.type === 'ai')
                    .map(msg => ({
                        role: msg.type,
                        content: msg.content,
                        timestamp: msg.timestamp.toISOString()
                    }));

                const response = await chatService.sendMessage(
                    inputMessage,
                    conversationHistory,
                    'anonymous' // TODO: Replace with actual user ID when auth is implemented
                );

                aiResponse = response.response;
            } else {
                // Fallback to simulated response
                aiResponse = generateFallbackResponse(inputMessage);
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

    const generateFallbackResponse = (userInput) => {
        const input = userInput.toLowerCase();

        // Fallback response logic when backend is not available
        if (input.includes('contract') || input.includes('agreement')) {
            return 'I can help you review contracts and agreements. Here\'s what I can do:\n\n• **Analyze contract terms** and identify potential issues\n• **Review payment terms** and **liability clauses**\n• **Check for compliance** with Singapore law\n• **Suggest improvements** and amendments\n• **Explain legal terminology** in plain language\n\nWould you like me to review a specific contract or help you draft one?';
        } else if (input.includes('conflict') || input.includes('dispute')) {
            return 'I can assist with conflict resolution by analyzing different versions of documents and identifying discrepancies. My capabilities include:\n\n• **Document comparison** between different versions\n• **Conflict detection** in terms and conditions\n• **Legal implications** analysis of various clauses\n• **Resolution suggestions** based on Singapore law\n• **Risk assessment** of potential disputes\n\nWhat specific conflict would you like me to help resolve?';
        } else if (input.includes('legal') || input.includes('law')) {
            return 'I\'m trained on legal documents and can help with legal research, case analysis, and understanding legal concepts. I can assist with:\n\n• **Legal research** on Singapore law\n• **Case analysis** and **precedent review**\n• **Legal concept explanations** in simple terms\n• **Regulatory compliance** guidance\n• **Document drafting** assistance\n\nWhat specific legal topic would you like to explore?';
        } else if (input.includes('document') || input.includes('version')) {
            return 'I can help you manage document versions, track changes, and ensure consistency across different iterations. My features include:\n\n• **Version control** and change tracking\n• **Conflict identification** between versions\n• **Consistency checking** across documents\n• **Change history** documentation\n• **Merge assistance** for conflicting changes\n\nWhat document management task do you need help with?';
        } else if (input.includes('singapore') || input.includes('dual legal')) {
            return 'Singapore has a **dual legal system** that incorporates both **common law** and **civil law** elements. Here are the key aspects:\n\n• **Common Law**: Based on judicial precedent and case law\n• **Civil Law**: Based on codified statutes and legislation\n• **Parliament**: Supreme law-making body with legislative authority\n• **Supreme Court**: Highest court in the Singapore legal system\n• **Statutory Interpretation**: Courts interpret and apply legislation\n\nThis system ensures both flexibility through precedent and clarity through codified laws.';
        } else if (input.includes('help') || input.includes('what can you do')) {
            return 'I can help you with:\n\n• **Contract and agreement analysis** - Review terms, identify issues, suggest improvements\n• **Document version comparison** - Track changes, detect conflicts, ensure consistency\n• **Conflict identification and resolution** - Analyze discrepancies, suggest solutions\n• **Legal research and case analysis** - Singapore law research, precedent review\n• **Document drafting assistance** - Help create legal documents\n• **Legal education** - Explain legal terms and concepts in plain language\n\nWhat would you like to focus on?';
        } else {
            return 'I understand you\'re asking about "' + userInput + '". I can help with:\n\n• **Legal document analysis** and review\n• **Contract assessment** and improvement suggestions\n• **Version control** and conflict resolution\n• **Legal research** on Singapore law\n• **Document drafting** assistance\n\nCould you provide more specific details about what you need assistance with?';
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
                content: 'Hello! I\'m LIT Legal Mind, your AI legal assistant. I can help you with document analysis, contract review, legal research, and more. How can I assist you today?',
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
        a.download = `lit-legal-mind-chat-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="project-layout">
            <AIChatSidebar />

            <main className="main-content ai-chat-main">
                <div className="chat-container">
                    <div className="chat-header-compact">
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
                                            <MessageFormatter content={message.content} />
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
                                    placeholder="Type your message here... (Press Enter to send, Shift+Enter for new line)"
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
            </main>
        </div>
    );
};

export default AIChat; 