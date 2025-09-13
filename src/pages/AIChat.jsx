import React, { useState, useRef, useEffect } from 'react';
import AIChatSidebar from '../components/AIChatSidebar';
import MessageFormatter from '../components/MessageFormatter';
import chatService from '../services/chatService';
import { useNavigate } from "react-router-dom";

const AIChat = () => {
    const navigate = useNavigate();
    const [messages, setMessages] = useState([
        {
            id: 1,
            type: 'ai',
            content: 'Hello! I\'m AITHENA, your AI legal assistant. I can help you with document analysis, contract review, legal research, and more. How can I assist you today?',
            timestamp: new Date(),
            status: 'sent'
        }
    ]);
    const [inputMessage, setInputMessage] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isBackendConnected, setIsBackendConnected] = useState(true);
    const messagesEndRef = useRef(null);
    const listRef = useRef(null);
    const inputRef = useRef(null);

    const scrollToBottom = () => {
        if (listRef.current) {
            listRef.current.scrollTo({
              top: listRef.current.scrollHeight,
              behavior: "smooth",
            });
      } else {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
    (async () => {
        await checkBackendHealth();
      })();
      inputRef.current?.focus();
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

     const generateFallbackResponse = (userInput) => {
        const input = userInput.toLowerCase();
        if (input.includes("contract") || input.includes("agreement")) {
          return `I can help you review contracts and agreements. Here's what I can do:

    • **Analyze contract terms** and identify potential issues
    • **Review payment terms** and **liability clauses**
    • **Check for compliance** with Singapore law
    • **Suggest improvements** and amendments
    • **Explain legal terminology** in plain language

    Would you like me to review a specific contract or help you draft one?`;
        } else if (input.includes("conflict") || input.includes("dispute")) {
          return `I can assist with conflict resolution by analyzing document versions and identifying discrepancies:

    • **Document comparison** between versions
    • **Conflict detection** in terms and conditions
    • **Legal implications** analysis of clauses
    • **Resolution suggestions** based on Singapore law
    • **Risk assessment** of potential disputes

    What specific conflict would you like me to help resolve?`;
        } else if (input.includes("legal") || input.includes("law")) {
          return `I'm trained on legal documents and can help with research, case analysis, and explaining legal concepts:

    • **Legal research** on Singapore law
    • **Case analysis** and **precedent review**
    • **Plain-language explanations** of legal terms
    • **Regulatory compliance** guidance
    • **Document drafting** assistance

    What specific legal topic would you like to explore?`;
        } else if (input.includes("document") || input.includes("version")) {
          return `I can help you manage document versions, track changes, and ensure consistency:

    • **Version control** and change tracking
    • **Conflict identification** between versions
    • **Consistency checking**
    • **Change history** documentation
    • **Merge assistance** for conflicting changes

    What document management task do you need help with?`;
        } else if (input.includes("singapore") || input.includes("dual legal")) {
          return `Singapore has a **dual legal system** with both **common law** and **civil law** elements:

    • **Common Law**: judicial precedent and case law
    • **Civil Law**: codified statutes and legislation
    • **Parliament**: supreme law-making body
    • **Supreme Court**: highest court
    • **Statutory interpretation** by the courts

    This balances precedent flexibility with statutory clarity.`;
        } else if (input.includes("help") || input.includes("what can you do")) {
          return `I can help you with:

    • **Contract & agreement analysis**
    • **Document version comparison**
    • **Conflict identification & resolution**
    • **Legal research** (SG law)
    • **Document drafting**
    • **Legal education** in plain language

    What would you like to focus on?`;
        }
        return `I understand you're asking about "${userInput}". I can help with:

    • **Legal document analysis**
    • **Contract assessment** and improvement suggestions
    • **Version control** and conflict resolution
    • **Legal research** on Singapore law
    • **Document drafting** assistance

    Could you provide more specific details about what you need?`;
      };

      const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        const userMessage = {
          id: Date.now(),
          type: "user",
          content: inputMessage,
          timestamp: new Date(),
          status: "sent",
        };

        setMessages((prev) => [...prev, userMessage]);
        setInputMessage("");
        setIsTyping(true);

        try {
          let aiResponse;

          if (isBackendConnected) {
            const conversationHistory = messages
              .filter((msg) => msg.type === "user" || msg.type === "ai")
              .map((msg) => ({
                role: msg.type,
                content: msg.content,
                timestamp: msg.timestamp.toISOString(),
              }));

            const response = await chatService.sendMessage(
              userMessage.content,
              conversationHistory,
              "anonymous" // replace with real user id once auth exists
            );

            aiResponse = response.response;
          } else {
            aiResponse = generateFallbackResponse(userMessage.content);
            await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));
          }

          const aiMessage = {
            id: Date.now() + 1,
            type: "ai",
            content: aiResponse,
            timestamp: new Date(),
            status: "sent",
          };
          setMessages((prev) => [...prev, aiMessage]);
        } catch (error) {
          console.error("Failed to get AI response:", error);
          const errorMessage = {
            id: Date.now() + 1,
            type: "ai",
            content:
              "I’m having trouble connecting to my services right now. Please try again in a moment.",
            timestamp: new Date(),
            status: "error",
          };
          setMessages((prev) => [...prev, errorMessage]);
        } finally {
          setIsTyping(false);
        }
      };

      const handleKeyDown = (e) => {
        // Enter to send; Shift+Enter for newline; Cmd/Ctrl+Enter also sends
        const sendCombo = (e.metaKey || e.ctrlKey) && e.key === "Enter";
        if ((e.key === "Enter" && !e.shiftKey) || sendCombo) {
          e.preventDefault();
          handleSendMessage(e);
        }
      };

      const clearChat = () => {
        setMessages([
          {
            id: Date.now(),
            type: "ai",
            content:
              "Hello! I'm AITHENA, your AI legal assistant. I can help you with document analysis, contract review, legal research, and more. How can I assist you today?",
            timestamp: new Date(),
            status: "sent",
          },
        ]);
      };

      const exportChat = () => {
        const chatText = messages
          .map((m) => `${m.type === "user" ? "You" : "AITHENA"}: ${m.content}`)
          .join("\n\n");
        const blob = new Blob([chatText], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `lit-legal-mind-chat-${new Date().toISOString().split("T")[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      };

      return (
        <main className="main-content ai-chat-page">
          <div className="ai-chat-layout">
            {/* Left column */}
            <aside className="ai-left">
              {/* If your AIChatSidebar already renders a header/back link, keep it */}
              <AIChatSidebar />
            </aside>

            {/* Right column */}
            <section className="ai-right">
              <header className="ai-chat-header">
                <div>
                  <h1 className="title">AITHENA</h1>
                  <p className="subtitle">Chat</p>
                </div>
                <div className="ai-top-actions">
                  {!isBackendConnected && (
                    <span className="btn-pill ghost">⚠️ Offline mode</span>
                  )}
                  <button className="btn-pill ghost" onClick={clearChat}>🧹 Clear</button>
                  <button className="btn-pill" onClick={exportChat}>💾 Export</button>
                </div>
              </header>

              <div className="ai-messages" ref={listRef}>
                {messages.map((message) => {
                  const isAI = message.type === "ai";
                  return (
                    <div
                      key={message.id}
                      className={`msg ${isAI ? "assistant" : "user"} ${message.status === "error" ? "error" : ""}`}
                    >
                      <div className="avatar">{isAI ? "🧠" : "🧑‍⚖️"}</div>
                      <div className="bubble">
                        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                          <strong>{isAI ? "AITHENA" : "You"}</strong>
                          <span style={{ color: "var(--text-secondary)", fontSize: ".85rem" }}>
                            {formatTime(message.timestamp)}
                          </span>
                        </div>
                        <div className="message-text">
                          {isAI ? <MessageFormatter content={message.content} /> : message.content}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {isTyping && (
                  <div className="msg assistant">
                    <div className="avatar">🧠</div>
                    <div className="bubble">
                      <span className="typing-indicator">…</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              <div className="ai-composer">
                <form className="row" onSubmit={handleSendMessage}>
                  <textarea
                    ref={inputRef}
                    placeholder="Type your message…  (Enter to send, Shift+Enter for newline, ⌘/Ctrl+Enter to send)"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                    disabled={isTyping}
                    // keep extension overlays from breaking layout
                    data-enable-grammarly="false"
                    data-gramm="false"
                    data-gramm_editor="false"
                    autoComplete="off"
                    spellCheck={true}
                  />
                  <button
                    type="submit"
                    className="button primary send"
                    disabled={!inputMessage.trim() || isTyping}
                    title="Send"
                  >
                    Send
                  </button>
                </form>
                {inputMessage.length > 0 && (
                  <div className="input-counter" style={{ marginTop: 6, color: "var(--text-secondary)" }}>
                    {inputMessage.length} characters
                  </div>
                )}
              </div>
            </section>
          </div>
        </main>
  );
};

export default AIChat;
