"""
PDF Generator Utility
"""

import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import logging

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Utility class for generating PDF documents"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for legal documents"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='LegalTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='#2c3e50'
        ))
        
        # Section style
        self.styles.add(ParagraphStyle(
            name='LegalSection',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            spaceBefore=20,
            textColor='#34495e'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='LegalBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_JUSTIFY,
            leading=14
        ))
        
        # Clause style
        self.styles.add(ParagraphStyle(
            name='LegalClause',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=20,
            alignment=TA_JUSTIFY,
            leading=13
        ))
    
    def text_to_pdf(self, text: str, title: str = "Legal Document") -> bytes:
        """
        Convert text content to PDF format
        
        Args:
            text: The text content to convert
            title: Document title
            
        Returns:
            PDF content as bytes
        """
        try:
            # Create a buffer to store the PDF
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build the PDF content
            story = []
            
            # Add title
            story.append(Paragraph(title, self.styles['LegalTitle']))
            story.append(Spacer(1, 20))
            
            # Add generation timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            story.append(Paragraph(f"Generated on: {timestamp}", self.styles['LegalBody']))
            story.append(Spacer(1, 30))
            
            # Process the text content
            lines = text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a section header (starts with a word and ends with colon)
                if line.endswith(':') and len(line.split()) <= 5:
                    current_section = line
                    story.append(Paragraph(line, self.styles['LegalSection']))
                    story.append(Spacer(1, 10))
                # Check if this is a clause (starts with dash or bullet)
                elif line.startswith('-') or line.startswith('•'):
                    # Remove the bullet/dash and format as clause
                    clause_text = line[1:].strip()
                    if clause_text:
                        story.append(Paragraph(f"• {clause_text}", self.styles['LegalClause']))
                # Check if this is a sub-clause (indented)
                elif line.startswith('    ') or line.startswith('\t'):
                    # Format as sub-clause
                    sub_clause_text = line.strip()
                    if sub_clause_text:
                        story.append(Paragraph(f"  - {sub_clause_text}", self.styles['LegalClause']))
                # Regular paragraph
                else:
                    story.append(Paragraph(line, self.styles['LegalBody']))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Successfully generated PDF with {len(pdf_content)} bytes")
            return pdf_content
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise
    
    def save_pdf_to_file(self, text: str, filepath: str, title: str = "Legal Document") -> str:
        """
        Convert text to PDF and save to file
        
        Args:
            text: The text content to convert
            filepath: Path where to save the PDF
            title: Document title
            
        Returns:
            Path to the saved PDF file
        """
        try:
            pdf_content = self.text_to_pdf(text, title)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Write PDF to file
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            
            logger.info(f"PDF saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save PDF to file: {e}")
            raise 