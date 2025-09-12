/**
 * Chat Service - Handles communication with LIT Legal Mind backend
 */

// Default localhost port: macOS clients use 5050, other OSes use 5000
const getDefaultLocalhostPort = () => {
    try {
        if (typeof navigator !== 'undefined' && navigator.platform) {
            // navigator.platform examples: 'MacIntel', 'MacPPC', 'Win32', 'Linux x86_64'
            if (/Mac|iPhone|iPad|iPod/.test(navigator.platform)) {
                return 5050;
            }
        }
    } catch (e) {
        // ignore and fall back
    }
    return 5000;
};

const DEFAULT_PORT = getDefaultLocalhostPort();
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://localhost:${DEFAULT_PORT}`;

class ChatService {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    /**
     * Send a message to LIT Legal Mind
     * @param {string} message - User's message
     * @param {Array} conversationHistory - Previous conversation messages
     * @param {string} userId - User identifier (optional)
     * @param {string} projectId - Project identifier (optional)
     * @param {Object} projectContext - Project context with documents (optional)
     * @returns {Promise<Object>} AI response
     */
    async sendMessage(message, conversationHistory = [], userId = 'anonymous', projectId = null, projectContext = null) {
        try {
            const requestBody = {
                message,
                conversation_history: conversationHistory,
                user_id: userId
            };

            // Add project context if available
            if (projectId) {
                requestBody.project_id = projectId;
            }
            if (projectContext) {
                requestBody.project_context = projectContext;
            }

            const response = await fetch(`${this.baseURL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Chat API error:', error);
            throw error;
        }
    }

    /**
     * Check if the backend is healthy
     * @returns {Promise<boolean>} Health status
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    /**
     * Search legal content
     * @param {string} query - Search query
     * @param {string} searchType - Type of search (hansard, lawnet, both)
     * @param {string} userId - User identifier (optional)
     * @returns {Promise<Object>} Search results
     */
    async searchLegalContent(query, searchType = 'both', userId = 'anonymous') {
        try {
            const response = await fetch(`${this.baseURL}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query,
                    search_type: searchType,
                    user_id: userId
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Search API error:', error);
            throw error;
        }
    }
}

// Export singleton instance
export const chatService = new ChatService();
export default chatService; 