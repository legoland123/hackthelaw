import React, { useState, useRef, useEffect } from 'react';
import MessageFormatter from './MessageFormatter';
import DocumentReference from './DocumentReference';
import chatService from '../services/chatService';
import documentProcessor from '../services/documentProcessor';

const ProjectChat = ({ project = {}, documents = [], onDocumentSelect }) => {
  const safeDocs = Array.isArray(documents) ? documents : [];

  const handleDocumentClick = (documentId) => {
    if (!onDocumentSelect) return;
    const doc = safeDocs.find(d => d.id === documentId);
    if (doc) onDocumentSelect(doc);
  };

  const createInitialMessage = () => {
    const validDocs = safeDocs.filter(doc =>
      documentProcessor.isValidContent(doc.content || '')
    );

    const name = project.name || 'This Project';
    let message = `Hello! I'm LIT Legal Mind, your AI legal assistant for the **${name}** project. `;

    if (validDocs.length > 0) {
      message += `I have access to **${validDocs.length} document${validDocs.length !== 1 ? 's' : ''}** and can help you analyze them, answer questions, and provide legal insights. `;
    } else {
      message += `I can see ${safeDocs.length} document${safeDocs.length !== 1 ? 's' : ''} in this project. `;
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

  useEffect(() => { scrollToBottom(); }, [messages]);

  useEffect(() => {
    checkBackendHealth();
    inputRef.current?.focus();
  }, []);

  // Refresh the opening message if docs/project name change
  useEffect(() => {
    const updated = createInitialMessage();
    setMessages(prev => {
      if (prev.length && prev[0].id === 1 && prev[0].type === 'ai') {
        return [{ ...prev[0], content: updated }, ...prev.slice(1)];
      }
      return prev;
    });
  }, [safeDocs, project?.name]);

  const checkBackendHealth = async () => {
    try {
      const ok = await chatService.checkHealth();
      setIsBackendConnected(ok);
      if (!ok) console.warn('Backend offline; using fallback responses');
    } catch (e) {
      console.error('Health check failed:', e);
      setIsBackendConnected(false);
    }
  };

  const formatTime = (timestamp) =>
    timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const createProjectContext = () => {
    const ctx = {
      project_name: project.name,
      project_description: project.description,
      documents: safeDocs
        .map(doc => {
          const content = doc.content || '';
          const stats = doc.content_stats || documentProcessor.getContentStats(content);
          const ok = documentProcessor.isValidContent(content);
          return {
            id: doc.id,
            title: doc.title || 'Untitled Document',
            version: doc.version || 1,
            author: doc.author || 'Unknown',
            description: doc.description || '',
            changes: doc.changes || [],
            content,
            content_length: stats?.length || 0,
            word_count: stats?.wordCount || 0,
            has_valid_content: ok,
            timestamp: doc.timestamp
          };
        })
        .filter(d => d.has_valid_content)
    };
    return ctx;
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const userMsg = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date(),
      status: 'sent'
    };

    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsTyping(true);

    try {
      let aiResponse = '';

      if (isBackendConnected) {
        const history = messages
          .filter(m => m.type === 'user' || m.type === 'ai')
          .map(m => ({
            role: m.type,
            content: m.content,
            timestamp: m.timestamp.toISOString()
          }));

        const ctx = createProjectContext();
        const res = await chatService.sendMessage(
          userMsg.content,
          history,
          'anonymous',
          project.id,
          ctx
        );
        aiResponse = res.response;
      } else {
        aiResponse = generateFallbackResponse(userMsg.content, project, safeDocs);
        await new Promise(r => setTimeout(r, 600 + Math.random() * 800));
      }

      const aiMsg = {
        id: Date.now() + 1,
        type: 'ai',
        content: aiResponse,
        timestamp: new Date(),
        status: 'sent'
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          id: Date.now() + 1,
          type: 'ai',
          content:
            "I’m having trouble connecting right now. Please try again shortly.",
          timestamp: new Date(),
          status: 'error'
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const generateFallbackResponse = (userInput, project, documents) => {
    const input = (userInput || '').toLowerCase();
    if (input.includes('document') || input.includes('version')) {
      return `I can see **${documents.length} document${documents.length !== 1 ? 's' : ''}** in **${project?.name || 'this project'}**:\n\n${documents
        .map(
          (d) =>
            `• **${d.title || 'Untitled'}** (Version ${d.version || 1})${
              d.author ? ` by ${d.author}` : ''
            }\n  ${d.description || 'No description available'}`
        )
        .join('\n\n')}\n\nWhat would you like to analyze?`;
    }
    if (input.includes('overview') || input.includes('project')) {
      return `**${project?.name || 'This Project'}**\n\n• Description: ${
        project?.description || 'No description provided'
      }\n• Total Documents: ${documents.length}\n\nAsk me to analyze a file, compare versions, or extract key points.`;
    }
    return `You're asking about "${userInput}". I have access to ${documents.length} document${
      documents.length !== 1 ? 's' : ''
    }. I can help with:\n\n• Document analysis\n• Version comparison\n• Legal concept explanations\n\nWhat should we start with?`;
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
    const chatText = messages
      .map((m) => `${m.type === 'user' ? 'You' : 'LIT Legal Mind'}: ${m.content}`)
      .join('\n\n');
    const blob = new Blob([chatText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project?.name || 'project'}-chat-${new Date()
      .toISOString()
      .split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* HEADER */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          flexWrap: 'wrap'
        }}
      >
        <div>
          <h3 style={{ margin: 0 }}>
            🤖 AITHENA – {project?.name || 'Project'}
          </h3>
          <p style={{ margin: '4px 0 0 0', opacity: 0.85 }}>
            {safeDocs.length} document{safeDocs.length !== 1 ? 's' : ''} available for analysis
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-secondary" onClick={clearChat}>🧹 Clear</button>
          <button className="btn btn-secondary" onClick={exportChat}>⬇️ Export</button>
        </div>
      </div>

      {/* MESSAGES */}
      <div
        style={{
          minHeight: 320,
          maxHeight: 'calc(100vh - 320px)',
          overflowY: 'auto',
          padding: 12,
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 12
        }}
      >
        {messages.map((m) => (
          <div key={m.id} style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <div style={{ width: 28, textAlign: 'center' }}>
              {m.type === 'ai' ? '🤖' : '👤'}
            </div>
            <div
              style={{
                background: 'rgba(255,255,255,0.05)',
                borderRadius: 10,
                padding: '10px 12px',
                maxWidth: 900
              }}
            >
              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  alignItems: 'baseline',
                  marginBottom: 6
                }}
              >
                <strong>{m.type === 'ai' ? 'LIT Legal Mind' : 'You'}</strong>
                <span style={{ opacity: 0.7, fontSize: 12 }}>
                  {formatTime(m.timestamp)}
                </span>
              </div>

              <div>
                {m.type === 'ai' ? (
                  <MessageFormatter
                    content={m.content}
                    documents={safeDocs}
                    onDocumentClick={handleDocumentClick}
                  />
                ) : (
                  m.content
                )}
              </div>
            </div>
          </div>
        ))}

        {isTyping && (
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ width: 28, textAlign: 'center' }}>🤖</div>
            <div>
              <div style={{ display: 'flex', gap: 6 }}>
                <span style={dotStyle} />
                <span style={{ ...dotStyle, animationDelay: '.15s' }} />
                <span style={{ ...dotStyle, animationDelay: '.30s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* INPUT */}
      <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: 10 }}>
        <textarea
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask about your project documents, legal analysis, or version comparisons..."
          rows={1}
          disabled={isTyping}
          style={{
            flex: 1,
            minHeight: 44,
            padding: '10px 12px',
            borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.08)',
            background: 'transparent',
            color: 'inherit',
            resize: 'none'
          }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!inputMessage.trim() || isTyping}
          style={{ minWidth: 52 }}
        >
          📤
        </button>
      </form>
    </div>
  );
};

const dotStyle = {
  width: 6,
  height: 6,
  borderRadius: '50%',
  background: '#a9acb1',
  animation: 'bubble 1.2s infinite ease-in-out'
};

export default ProjectChat;
