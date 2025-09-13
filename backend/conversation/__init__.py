"""
Conversation package for LIT Legal Mind

This package handles conversation context building and management
for the legal AI assistant.
"""

from .context_builder import (
    ConversationContextBuilder,
    CaseVisualizationBuilder,
    ChatMessage,
    create_conversation_context,
    create_enhanced_conversation_context,
    create_comprehensive_conversation_context,
    create_case_relevance_visualization
)

__all__ = [
    'ConversationContextBuilder',
    'CaseVisualizationBuilder', 
    'ChatMessage',
    'create_conversation_context',
    'create_enhanced_conversation_context',
    'create_comprehensive_conversation_context',
    'create_case_relevance_visualization'
]
