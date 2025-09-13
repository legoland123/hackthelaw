"""
Conversation Context Builder for LIT Legal Mind

This module handles building conversation contexts for the LLM with various
types of legal information including project context, statutes, amendments,
and case law.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message model for conversation history"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None


class ConversationContextBuilder:
    """
    Builds conversation contexts for LIT Legal Mind with various legal information
    """
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the base system prompt for LIT Legal Mind"""
        return """
    
You are LIT Legal Mind, an expert AI legal assistant designed for Singapore legal professionals. 
You specialize in statute retrieval, amendment tracking, and case law analysis.

Your capabilities include:
- Identifying relevant statutes and statutory provisions for a given fact scenario
- Checking if cited statutes or sections have been amended, repealed, or renumbered
- Retrieving and ranking related Singapore case law (with emphasis on precedential value and relevance)
- Explaining statutory obligations and how courts have interpreted them
- Providing concise, accurate, and practical legal insights tailored to the Singapore context

Guidelines:
- Focus on Singapore law, statutes, and case law when relevant
- Clearly distinguish between statutory text, amendments, and case law interpretations
- Prioritize accuracy, recency, and court hierarchy (Court of Appeal > High Court > lower courts)
- When referencing documents, use the format `[[Document X]]`. 
- When referencing case law, cite using standard Singapore legal citations (e.g., [2022] SGCA 60).
- Keep explanations concise, structured, and professional — assume you are speaking to a lawyer.

Formatting Guidelines:
- Use bullet points (•) for key obligations, holdings, or amendments
- Use **bold text** for statutes, sections, or important legal concepts
- Use clear headings (e.g., "Relevant Statutes", "Amendments", "Case Law") to organize responses
- Keep paragraphs short and easy to scan

Example of a good response:
As stated in [[Document 1]], the payment terms are defined in section 3.2. However, [[Document 2]] suggests a revised payment schedule.

Current conversation context:"""

    def create_basic_context(
        self, 
        conversation_history: List[ChatMessage], 
        current_message: str, 
        project_context: Optional[Dict] = None
    ) -> str:
        """
        Create basic conversation context with project information
        
        Args:
            conversation_history: Previous messages in the conversation
            current_message: Current user message
            project_context: Optional project context with documents
            
        Returns:
            Formatted conversation context string
        """
        conversation_text = self.system_prompt + "\n\n"
        
        # Add conversation history (keep last 5 messages for context)
        if conversation_history:
            for msg in conversation_history[-5:]:
                role = "User" if msg.role == "user" else "LIT Legal Mind"
                conversation_text += f"{role}: {msg.content}\n\n"
        
        # Add project context if available
        if project_context:
            conversation_text += self._format_project_context(project_context)
        
        # Add current message
        conversation_text += f"User: {current_message}\n\nLIT Legal Mind:"
        
        return conversation_text

    def create_enhanced_context(
        self,
        conversation_history: List[ChatMessage], 
        current_message: str, 
        project_context: Optional[Dict] = None,
        statute_search_results: Optional[Dict] = None,
        amendment_search_results: Optional[Dict] = None
    ) -> str:
        """
        Create enhanced conversation context with statute and amendment information
        
        Args:
            conversation_history: Previous messages in the conversation
            current_message: Current user message
            project_context: Optional project context with documents
            statute_search_results: Results from statute search
            amendment_search_results: Results from amendment search
            
        Returns:
            Enhanced conversation context string with legal information
        """
        # Start with basic context
        conversation_text = self.create_basic_context(
            conversation_history, current_message, project_context
        )
        
        # Add statute search results if available
        if statute_search_results and statute_search_results.get('status') == 'success':
            conversation_text += self._format_statute_results(statute_search_results)
        
        # Add amendment search results if available
        if amendment_search_results and amendment_search_results.get('status') == 'success':
            conversation_text += self._format_amendment_results(amendment_search_results)
        
        conversation_text += "\n**INSTRUCTIONS:** Use the above statute and amendment information to provide accurate, up-to-date legal guidance. Reference specific statutes and their current status in your response.\n"
        
        return conversation_text

    def create_comprehensive_context(
        self,
        conversation_history: List[ChatMessage], 
        current_message: str, 
        project_context: Optional[Dict] = None,
        statute_search_results: Optional[Dict] = None,
        amendment_search_results: Optional[Dict] = None,
        elitigation_results: Optional[Dict] = None
    ) -> str:
        """
        Create comprehensive conversation context with statutes, amendments, and case law
        
        Args:
            conversation_history: Previous messages in the conversation
            current_message: Current user message
            project_context: Optional project context with documents
            statute_search_results: Results from statute search
            amendment_search_results: Results from amendment search
            elitigation_results: Results from eLitigation case search
            
        Returns:
            Comprehensive conversation context string with all legal information
        """
        # Start with enhanced context (includes statutes + amendments)
        conversation_text = self.create_enhanced_context(
            conversation_history, 
            current_message, 
            project_context,
            statute_search_results,
            amendment_search_results
        )
        
        # Add eLitigation case results if available
        if elitigation_results and elitigation_results.get('status') == 'success':
            conversation_text += self._format_case_law_results(elitigation_results)
        
        conversation_text += "\n**COMPREHENSIVE LEGAL GUIDANCE:** "
        conversation_text += "You now have access to relevant statutes, recent amendments, and case law. "
        conversation_text += "Provide a comprehensive legal analysis that integrates all available sources. "
        conversation_text += "Structure your response to address statutory requirements, recent changes, and judicial interpretations.\n"
        
        return conversation_text

    def _format_project_context(self, project_context: Dict) -> str:
        """Format project context information"""
        context_text = "PROJECT CONTEXT:\n"
        
        if project_context.get('project_name'):
            context_text += f"Project: {project_context['project_name']}\n"
        if project_context.get('project_description'):
            context_text += f"Description: {project_context['project_description']}\n"
        
        if project_context.get('documents') and len(project_context['documents']) > 0:
            context_text += f"\nPROJECT DOCUMENTS ({len(project_context['documents'])} documents):\n"
            
            for i, doc in enumerate(project_context['documents'], 1):
                context_text += f"\nDocument {i} (ID: {doc.get('id', 'unknown')}): {doc.get('title', 'Untitled')}\n"
                context_text += f"Version: {doc.get('version', 'Unknown')}\n"
                context_text += f"Author: {doc.get('author', 'Unknown')}\n"
                
                if doc.get('description'):
                    context_text += f"Description: {doc['description']}\n"
                
                if doc.get('content'):
                    # Truncate content to avoid token limits
                    content = doc['content'][:2000] + "..." if len(doc['content']) > 2000 else doc['content']
                    context_text += f"Content: {content}\n"
                
                if doc.get('changes'):
                    changes = ", ".join(doc['changes'])
                    context_text += f"Key Changes: {changes}\n"
                
                context_text += "-" * 50 + "\n"
        
        context_text += "\n"
        return context_text

    def _format_statute_results(self, statute_search_results: Dict) -> str:
        """Format statute search results"""
        statutes = statute_search_results.get('statutes', [])
        if not statutes:
            return ""
        
        context_text = "\n\n**RELEVANT STATUTES FOUND:**\n"
        
        for i, statute in enumerate(statutes, 1):
            context_text += f"\n{i}. **{statute.get('name and section', statute.get('name', 'Unknown Statute'))}**\n"
            
            if statute.get('description'):
                context_text += f"   Description: {statute['description']}\n"
            if statute.get('chapter'):
                context_text += f"   Chapter: {statute['chapter']}\n"
            if statute.get('relevance'):
                context_text += f"   Relevance: {statute['relevance']}\n"
            if statute.get('key_sections'):
                sections = ", ".join(statute['key_sections'])
                context_text += f"   Key Sections: {sections}\n"
            if statute.get('summary'):
                context_text += f"   Summary: {statute['summary']}\n"
            if statute.get('source'):
                context_text += f"   Source: {statute['source']}\n"
            
            context_text += "\n"
        
        if statute_search_results.get('reasoning'):
            context_text += f"**Legal Framework Analysis:** {statute_search_results['reasoning']}\n"
        
        return context_text

    def _format_amendment_results(self, amendment_search_results: Dict) -> str:
        """Format amendment search results"""
        amendment_results = amendment_search_results.get('results', [])
        amendments_found = [
            r for r in amendment_results 
            if r.get('amendment_analysis', {}).get('has_amendments', False)
        ]
        
        if amendments_found:
            context_text = "\n\n**RECENT AMENDMENTS FOUND:**\n"
            
            for result in amendments_found:
                statute_name = result.get('statute', 'Unknown Statute')
                analysis = result.get('amendment_analysis', {})
                
                context_text += f"\n**{statute_name}** (Confidence: {analysis.get('confidence', 0.0):.1f})\n"
                
                if analysis.get('summary'):
                    context_text += f"   Amendment Summary: {analysis['summary']}\n"
                
                if analysis.get('key_changes'):
                    changes = "\n   • ".join(analysis['key_changes'])
                    context_text += f"   Key Changes:\n   • {changes}\n"
                
                if analysis.get('amendment_dates'):
                    dates = ", ".join(analysis['amendment_dates'])
                    context_text += f"   Amendment Dates: {dates}\n"
                
                context_text += "\n"
        else:
            context_text = "\n\n**AMENDMENT STATUS:** No recent amendments found for the identified statutes.\n"
        
        return context_text

    def _format_case_law_results(self, elitigation_results: Dict) -> str:
        """Format eLitigation case law results"""
        cases = elitigation_results.get('cases', [])
        if not cases:
            return ""
        
        context_text = "\n\n**RELEVANT CASE LAW:**\n"
        context_text += "The following Singapore court cases are relevant to your query:\n\n"
        
        for i, case in enumerate(cases, 1):
            title = case.get('title', 'Unknown Case')
            court = case.get('court', '')
            year = case.get('case_year', '')
            url = case.get('url', '')
            snippet = case.get('snippet', '')
            full_content = case.get('full_content', '')
            relevance_score = case.get('relevance_score')
            
            # Case header
            context_text += f"**Case {i}: {title}**\n"
            
            if court:
                context_text += f"   Court: {court}\n"
            if year:
                context_text += f"   Year: {year}\n"
            if url:
                context_text += f"   URL: {url}\n"
            if relevance_score is not None:
                context_text += f"   Relevance Score: {relevance_score:.3f}\n"
            
            # Case content - prioritize full content over snippet
            if full_content and len(full_content.strip()) > 100:
                # Truncate very long content
                content = full_content[:3000] + "..." if len(full_content) > 3000 else full_content
                context_text += f"   **Full Case Content:**\n   {content}\n\n"
            elif snippet:
                context_text += f"   **Summary:** {snippet}\n\n"
            
            # Add separator between cases
            if i < len(cases):
                context_text += "---\n\n"
        
        context_text += "\n**CASE LAW ANALYSIS INSTRUCTIONS:** "
        context_text += "Use the above case law to support your legal analysis. "
        context_text += "Reference specific cases, their holdings, and how they apply to the current query. "
        context_text += "Consider the court hierarchy and precedential value.\n"
        
        return context_text


class CaseVisualizationBuilder:
    """
    Builds visual representations of case law relevance rankings
    """
    
    @staticmethod
    def create_case_relevance_visualization(ranked_cases: List[Dict]) -> str:
        """
        Create a visual representation of ranked eLitigation cases with relevance scores
        
        Args:
            ranked_cases: List of cases with relevance scores
            
        Returns:
            Formatted string with case relevance visualization
        """
        if not ranked_cases:
            return ""
        
        visualization = "\n\n---\n\n## 📋 **Relevant Case Law Analysis**\n\n"
        visualization += "*Based on AI-powered relevance ranking considering statutory citations, factual similarity, and judicial precedence.*\n\n"
        
        for i, case in enumerate(ranked_cases[:5]):  # Show top 5 cases
            score = case.get('relevance_score', 0)
            title = case.get('title', 'Unknown Case')
            url = case.get('url', '#')
            
            # Create visual relevance bar
            score_percentage = min(int(score * 100), 100)
            filled_bars = "█" * (score_percentage // 10)
            empty_bars = "░" * (10 - (score_percentage // 10))
            relevance_bar = f"{filled_bars}{empty_bars}"
            
            # Determine relevance level
            if score >= 0.8:
                relevance_level = "🔥 **Highly Relevant**"
                color_indicator = "🟢"
            elif score >= 0.6:
                relevance_level = "⚡ **Very Relevant**"
                color_indicator = "🟡"
            elif score >= 0.4:
                relevance_level = "📊 **Moderately Relevant**"
                color_indicator = "🟠"
            else:
                relevance_level = "📋 **Somewhat Relevant**"
                color_indicator = "🔴"
            
            visualization += f"### {i+1}. {color_indicator} [{title}]({url})\n\n"
            visualization += f"**Relevance Score:** `{score:.3f}` {relevance_level}\n\n"
            visualization += f"**Visual Score:** `{relevance_bar}` ({score_percentage}%)\n\n"
            
            # Add case details if available
            if case.get('summary'):
                summary = case['summary'][:200] + "..." if len(case.get('summary', '')) > 200 else case.get('summary', '')
                visualization += f"**Case Summary:** {summary}\n\n"
            
            # Add statute citations if available
            statute_citations = case.get('statute_citations', [])
            if statute_citations:
                citations_text = ", ".join(statute_citations[:3])  # Show first 3 citations
                if len(statute_citations) > 3:
                    citations_text += f" (+{len(statute_citations) - 3} more)"
                visualization += f"**Key Statutes:** {citations_text}\n\n"
            
            visualization += "---\n\n"
        
        # Add footer note
        total_cases = len(ranked_cases)
        if total_cases > 5:
            visualization += f"*Showing top 5 of {total_cases} relevant cases found.*\n\n"
        
        visualization += "💡 **Note:** Relevance scores are calculated using advanced AI analysis considering multiple factors including statutory alignment, factual similarity, and precedential value.\n\n"
        
        return visualization


# Convenience functions for backward compatibility and ease of use
def create_conversation_context(
    conversation_history: List[ChatMessage], 
    current_message: str, 
    project_context: Optional[Dict] = None
) -> str:
    """Create basic conversation context - convenience function"""
    builder = ConversationContextBuilder()
    return builder.create_basic_context(conversation_history, current_message, project_context)


def create_enhanced_conversation_context(
    conversation_history: List[ChatMessage], 
    current_message: str, 
    project_context: Optional[Dict] = None,
    statute_search_results: Optional[Dict] = None,
    amendment_search_results: Optional[Dict] = None
) -> str:
    """Create enhanced conversation context - convenience function"""
    builder = ConversationContextBuilder()
    return builder.create_enhanced_context(
        conversation_history, 
        current_message, 
        project_context,
        statute_search_results,
        amendment_search_results
    )


def create_comprehensive_conversation_context(
    conversation_history: List[ChatMessage], 
    current_message: str, 
    project_context: Optional[Dict] = None,
    statute_search_results: Optional[Dict] = None,
    amendment_search_results: Optional[Dict] = None,
    elitigation_results: Optional[Dict] = None
) -> str:
    """Create comprehensive conversation context - convenience function"""
    builder = ConversationContextBuilder()
    return builder.create_comprehensive_context(
        conversation_history, 
        current_message, 
        project_context,
        statute_search_results,
        amendment_search_results,
        elitigation_results
    )


def create_case_relevance_visualization(ranked_cases: List[Dict]) -> str:
    """Create case relevance visualization - convenience function"""
    return CaseVisualizationBuilder.create_case_relevance_visualization(ranked_cases)
