"""
Text Chunking Service for Legal Documents
"""

import logging
import os
import re
from typing import List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    text: str
    chunk_id: str
    document_id: str
    page_number: int
    chunk_index: int
    start_char: int
    end_char: int
    section_title: str = ""

class LegalTextChunker:
    """Chunk legal text documents with overlap and section awareness"""
    
    def __init__(self):
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
        
        # Legal section patterns
        self.section_patterns = [
            r'^Chapter\s+\d+[:\-\s]',  # Chapter 1:
            r'^Section\s+\d+[:\-\s]',  # Section 1:
            r'^Part\s+[IVX]+[:\-\s]',  # Part I:
            r'^\d+\.\s+[A-Z]',         # 1. TITLE
            r'^\d+\.\d+\s',            # 1.1 
            r'^[A-Z][A-Z\s]{10,}$',    # ALL CAPS HEADINGS
        ]
    
    def chunk_document(self, text: str, document_id: str, page_contents: List[Dict] = None) -> List[TextChunk]:
        """
        Chunk a document into overlapping segments
        
        Args:
            text: Full document text
            document_id: Unique document identifier
            page_contents: Optional page-by-page content for better tracking
            
        Returns:
            List of TextChunk objects
        """
        try:
            # Clean the text
            cleaned_text = self._clean_text(text)
            
            # Detect sections for better chunking
            sections = self._detect_sections(cleaned_text)
            
            chunks = []
            chunk_index = 0
            
            # Create chunks with overlap
            start = 0
            while start < len(cleaned_text):
                end = min(start + self.chunk_size, len(cleaned_text))
                
                # Try to break at sentence boundaries
                if end < len(cleaned_text):
                    end = self._find_sentence_boundary(cleaned_text, end)
                
                chunk_text = cleaned_text[start:end].strip()
                
                if chunk_text:
                    # Find which page this chunk belongs to
                    page_number = self._find_page_number(start, page_contents) if page_contents else 1
                    
                    # Find section title for this chunk
                    section_title = self._find_section_title(start, sections)
                    
                    # Create chunk ID
                    chunk_id = f"{document_id}_chunk_{chunk_index:04d}"
                    
                    chunk = TextChunk(
                        text=chunk_text,
                        chunk_id=chunk_id,
                        document_id=document_id,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        start_char=start,
                        end_char=end,
                        section_title=section_title
                    )
                    
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                if start >= len(cleaned_text):
                    break
            
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to chunk document {document_id}: {e}")
            raise
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page headers/footers patterns
        text = re.sub(r'--- Page \d+ ---', '', text)
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        return text.strip()
    
    def _detect_sections(self, text: str) -> List[Dict]:
        """Detect section headings in legal text"""
        sections = []
        lines = text.split('\n')
        char_position = 0
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if line:
                # Check if line matches any section pattern
                for pattern in self.section_patterns:
                    if re.match(pattern, line, re.IGNORECASE):
                        sections.append({
                            'title': line,
                            'start_char': char_position,
                            'line_number': line_num
                        })
                        break
            
            char_position += len(line) + 1  # +1 for newline
        
        return sections
    
    def _find_sentence_boundary(self, text: str, position: int) -> int:
        """Find the nearest sentence boundary before the position"""
        # Look for sentence endings within 100 characters before position
        search_start = max(0, position - 100)
        search_text = text[search_start:position]
        
        # Find last sentence ending
        sentence_endings = ['.', '!', '?', ':', ';']
        last_ending = -1
        
        for ending in sentence_endings:
            pos = search_text.rfind(ending)
            if pos > last_ending:
                last_ending = pos
        
        if last_ending > 0:
            # Make sure we're not breaking in the middle of abbreviations
            if last_ending < len(search_text) - 1 and search_text[last_ending + 1] == ' ':
                return search_start + last_ending + 1
        
        # If no good sentence boundary found, use original position
        return position
    
    def _find_page_number(self, char_position: int, page_contents: List[Dict]) -> int:
        """Find which page a character position belongs to"""
        if not page_contents:
            return 1
        
        current_pos = 0
        for page in page_contents:
            page_text_length = len(page['text'])
            if char_position <= current_pos + page_text_length:
                return page['page_number']
            current_pos += page_text_length
        
        return page_contents[-1]['page_number'] if page_contents else 1
    
    def _find_section_title(self, char_position: int, sections: List[Dict]) -> str:
        """Find the section title for a given character position"""
        current_section = ""
        
        for section in sections:
            if section['start_char'] <= char_position:
                current_section = section['title']
            else:
                break
        
        return current_section

# Singleton instance
_text_chunker = None

def get_text_chunker():
    """Get singleton text chunker instance"""
    global _text_chunker
    if _text_chunker is None:
        _text_chunker = LegalTextChunker()
    return _text_chunker