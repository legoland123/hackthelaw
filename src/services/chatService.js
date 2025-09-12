/**
 * Chat Service - Handles communication with LIT Legal Mind backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

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