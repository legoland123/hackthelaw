"""
PDF Text Extraction Service
"""

import logging
import PyPDF2
from io import BytesIO
from typing import Dict, List

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract text from PDF files"""
    
    def extract_text_from_bytes(self, pdf_bytes: bytes, filename: str) -> Dict:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes: PDF file as bytes
            filename: Original filename for metadata
            
        Returns:
            Dict with extracted text and metadata
        """
        try:
            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = ""
            page_contents = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content += f"\n\n--- Page {page_num + 1} ---\n\n"
                        text_content += page_text
                        page_contents.append({
                            'page_number': page_num + 1,
                            'text': page_text.strip()
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                    continue
            
            # Extract metadata
            metadata = {
                'filename': filename,
                'total_pages': len(pdf_reader.pages),
                'pages_with_text': len(page_contents)
            }
            
            # Try to get PDF metadata
            if pdf_reader.metadata:
                pdf_info = pdf_reader.metadata
                metadata.update({
                    'title': pdf_info.get('/Title', ''),
                    'author': pdf_info.get('/Author', ''),
                    'subject': pdf_info.get('/Subject', ''),
                    'creator': pdf_info.get('/Creator', ''),
                    'producer': pdf_info.get('/Producer', ''),
                    'creation_date': str(pdf_info.get('/CreationDate', '')),
                    'modification_date': str(pdf_info.get('/ModDate', ''))
                })
            
            if not text_content.strip():
                raise ValueError("No extractable text found in PDF")
            
            logger.info(f"Extracted {len(text_content)} characters from {filename}")
            
            return {
                'text': text_content.strip(),
                'page_contents': page_contents,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {filename}: {e}")
            raise
    
    def extract_text_from_file(self, file_path: str) -> Dict:
        """
        Extract text from PDF file path
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dict with extracted text and metadata
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_bytes = file.read()
                filename = file_path.split('/')[-1]
                return self.extract_text_from_bytes(pdf_bytes, filename)
                
        except Exception as e:
            logger.error(f"Failed to read PDF file {file_path}: {e}")
            raise

# Singleton instance
_pdf_extractor = None

def get_pdf_extractor():
    """Get singleton PDF extractor instance"""
    global _pdf_extractor
    if _pdf_extractor is None:
        _pdf_extractor = PDFExtractor()
    return _pdf_extractor