/**
 * Document Processor Service - Handles document content extraction and processing
 */

import mammoth from 'mammoth';

class DocumentProcessor {
    constructor() {
        this.pdfjsLib = null;
        this.isPDFJSLoaded = false;
        this.loadPDFJS();
    }

    /**
     * Load PDF.js library for PDF text extraction
     */
    async loadPDFJS() {
        try {
            // Check if PDF.js is already loaded
            if (window.pdfjsLib) {
                this.pdfjsLib = window.pdfjsLib;
                this.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                this.isPDFJSLoaded = true;
                console.log('PDF.js already loaded');
                return;
            }

            // Load PDF.js from CDN
            const script = document.createElement('script');
            script.src = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js';
            script.onload = () => {
                this.pdfjsLib = window.pdfjsLib;
                this.pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                this.isPDFJSLoaded = true;
                console.log('PDF.js loaded successfully');
            };
            script.onerror = (error) => {
                console.error('Failed to load PDF.js script:', error);
            };
            document.head.appendChild(script);
        } catch (error) {
            console.error('Failed to load PDF.js:', error);
        }
    }

    /**
     * Extract text content from a PDF file
     * @param {File|string} file - PDF file or URL
     * @returns {Promise<string>} Extracted text content
     */
    async extractPDFText(file) {
        if (!this.isPDFJSLoaded) {
            await this.waitForPDFJS();
        }

        try {
            let pdfData;

            if (typeof file === 'string') {
                // URL
                console.log('Loading PDF from URL:', file);
                pdfData = await this.pdfjsLib.getDocument(file).promise;
            } else {
                // File object
                console.log('Loading PDF from file:', file.name);
                const arrayBuffer = await file.arrayBuffer();
                pdfData = await this.pdfjsLib.getDocument({ data: arrayBuffer }).promise;
            }

            let fullText = '';
            const numPages = pdfData.numPages;
            console.log(`Extracting text from ${numPages} pages`);

            // Extract text from each page
            for (let pageNum = 1; pageNum <= numPages; pageNum++) {
                try {
                    const page = await pdfData.getPage(pageNum);
                    const textContent = await page.getTextContent();

                    const pageText = textContent.items
                        .map(item => item.str)
                        .join(' ');

                    fullText += `Page ${pageNum}: ${pageText}\n`;

                    // Log progress for large documents
                    if (pageNum % 10 === 0) {
                        console.log(`Processed ${pageNum}/${numPages} pages`);
                    }
                } catch (pageError) {
                    console.warn(`Failed to extract text from page ${pageNum}:`, pageError);
                    fullText += `Page ${pageNum}: [Text extraction failed]\n`;
                }
            }

            const cleanedText = this.cleanContent(fullText);
            console.log(`Successfully processed ${cleanedText.length} characters from PDF`);
            return cleanedText;
        } catch (error) {
            console.error('Failed to extract PDF text:', error);
            throw new Error(`Failed to extract text from PDF: ${error.message}`);
        }
    }

    /**
     * Wait for PDF.js to be loaded
     */
    async waitForPDFJS() {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50; // 5 seconds max wait

            const checkLoaded = () => {
                attempts++;
                if (this.isPDFJSLoaded) {
                    resolve();
                } else if (attempts >= maxAttempts) {
                    reject(new Error('PDF.js failed to load within timeout'));
                } else {
                    setTimeout(checkLoaded, 100);
                }
            };
            checkLoaded();
        });
    }

    /**
     * Extract text from various document types
     * @param {File} file - Document file
     * @returns {Promise<string>} Extracted text content
     */
    async extractDocumentText(file) {
        const fileType = file.type.toLowerCase();
        const fileName = file.name.toLowerCase();

        console.log(`Processing document: ${file.name} (${fileType})`);

        try {
            if (fileType.includes('pdf') || fileName.endsWith('.pdf')) {
                const content = await this.extractPDFText(file);
                return content || `[No content processed from PDF: ${file.name}]`;
            } else if (fileType.includes('text') || fileName.endsWith('.txt')) {
                const content = await this.extractTextFile(file);
                return content || `[No content in file: ${file.name}]`;
            } else if (fileType.includes('word') || fileName.endsWith('.docx')) {
                // Handle DOCX files with mammoth
                const content = await this.extractWordDocument(file);
                return content || `[No content extracted from Word document: ${file.name}]`;
            } else if (fileName.endsWith('.doc')) {
                // For older .doc files, provide guidance
                return `[Legacy Word document (.doc): ${file.name} - Please convert to .docx format for processing. Legacy .doc files are not supported.]`;
            } else {
                return `[Unsupported file type: ${fileType} for file: ${file.name}. Supported formats: PDF, TXT, DOCX]`;
            }
        } catch (error) {
            console.error('Document processing failed:', error);
            return `[Failed to process ${file.name}: ${error.message}]`;
        }
    }

    /**
     * Extract text from a text file
     * @param {File} file - Text file
     * @returns {Promise<string>} File content
     */
    async extractTextFile(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const content = e.target.result;
                console.log(`Successfully read text file: ${file.name} (${content.length} characters)`);
                resolve(content);
            };
            reader.onerror = (e) => {
                console.error('Failed to read text file:', e);
                reject(new Error(`Failed to read text file: ${file.name}`));
            };
            reader.readAsText(file);
        });
    }

    /**
     * Extract text from a Word document (DOCX)
     * @param {File} file - Word document file
     * @returns {Promise<string>} Extracted text content
     */
    async extractWordDocument(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = async (e) => {
                try {
                    const arrayBuffer = e.target.result;
                    const result = await mammoth.extractRawText({ arrayBuffer });

                    if (result.messages.length > 0) {
                        console.warn('Word document processing warnings:', result.messages);
                    }

                    const content = result.value;
                    console.log(`Successfully extracted text from Word document: ${file.name} (${content.length} characters)`);
                    resolve(content);
                } catch (error) {
                    console.error('Failed to extract text from Word document:', error);
                    reject(new Error(`Failed to extract text from Word document: ${file.name} - ${error.message}`));
                }
            };
            reader.onerror = (e) => {
                console.error('Failed to read Word document file:', e);
                reject(new Error(`Failed to read Word document file: ${file.name}`));
            };
            reader.readAsArrayBuffer(file);
        });
    }

    /**
     * Process document content for AI context
     * @param {Object} document - Document object with metadata
     * @param {string} content - Extracted text content
     * @returns {Object} Processed document context
     */
    processDocumentForContext(document, content) {
        const processedContent = this.cleanContent(content);
        const summary = this.getDocumentSummary(processedContent, 1000);

        return {
            title: document.title || 'Untitled Document',
            version: document.version || 1,
            author: document.author || 'Unknown',
            description: document.description || '',
            changes: document.changes || [],
            content: processedContent,
            summary: summary,
            content_length: processedContent.length,
            timestamp: document.timestamp
        };
    }

    /**
     * Clean and format content for AI processing
     * @param {string} content - Raw content
     * @param {number} maxLength - Maximum content length (default: 15000)
     * @returns {string} Cleaned content
     */
    cleanContent(content, maxLength = 15000) {
        if (!content) return '';

        return content
            .replace(/\s+/g, ' ') // Replace multiple spaces with single space
            .replace(/\n\s*\n/g, '\n') // Remove empty lines
            .replace(/\t/g, ' ') // Replace tabs with spaces
            .replace(/[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\'\n]/g, '') // Remove special characters but keep punctuation
            .trim()
            .substring(0, maxLength); // Configurable limit
    }

    /**
     * Get document summary for context
     * @param {string} content - Document content
     * @param {number} maxLength - Maximum summary length
     * @returns {string} Document summary
     */
    getDocumentSummary(content, maxLength = 1000) {
        if (!content) return '';

        const cleaned = this.cleanContent(content);
        if (cleaned.length <= maxLength) {
            return cleaned;
        }

        // Try to find a good breaking point
        const truncated = cleaned.substring(0, maxLength);
        const lastPeriod = truncated.lastIndexOf('.');
        const lastSpace = truncated.lastIndexOf(' ');

        if (lastPeriod > maxLength * 0.8) {
            return truncated.substring(0, lastPeriod + 1);
        } else if (lastSpace > maxLength * 0.8) {
            return truncated.substring(0, lastSpace) + '...';
        } else {
            return truncated + '...';
        }
    }

    /**
     * Validate if content was successfully processed
     * @param {string} content - Processed content
     * @returns {boolean} Whether content is valid
     */
    isValidContent(content) {
        if (!content) return false;

        // Check if content is just an error message
        if (content.startsWith('[') && content.includes('Failed to process')) {
            return false;
        }

        // Check if content is too short (likely not real content)
        if (content.length < 10) {
            return false;
        }

        return true;
    }

    /**
     * Get content statistics for debugging
     * @param {string} content - Document content
     * @returns {Object} Content statistics
     */
    getContentStats(content) {
        if (!content) {
            return { length: 0, wordCount: 0, lineCount: 0, isValid: false };
        }

        const words = content.split(/\s+/).filter(word => word.length > 0);
        const lines = content.split('\n').filter(line => line.trim().length > 0);

        return {
            length: content.length,
            wordCount: words.length,
            lineCount: lines.length,
            isValid: this.isValidContent(content)
        };
    }

    /**
     * Get recommended content limits based on use case
     * @returns {Object} Recommended limits for different scenarios
     */
    getRecommendedLimits() {
        return {
            conservative: {
                maxCharsPerDoc: 10000,    // ~1,500-2,000 words
                maxDocsPerProject: 10,
                maxTotalWords: 20000,
                description: "Reliable performance, fast responses"
            },
            moderate: {
                maxCharsPerDoc: 15000,    // ~2,500-3,000 words
                maxDocsPerProject: 12,
                maxTotalWords: 36000,
                description: "Balanced coverage and performance"
            },
            aggressive: {
                maxCharsPerDoc: 25000,    // ~4,000-5,000 words
                maxDocsPerProject: 8,
                maxTotalWords: 40000,
                description: "Maximum content coverage"
            },
            unlimited: {
                maxCharsPerDoc: 50000,    // ~8,000-10,000 words
                maxDocsPerProject: 5,
                maxTotalWords: 50000,
                description: "Maximum possible (may hit AI limits)"
            }
        };
    }

    /**
     * Estimate word count from character count
     * @param {number} charCount - Number of characters
     * @returns {number} Estimated word count
     */
    estimateWordCount(charCount) {
        // Average English word is ~5 characters + 1 space
        return Math.round(charCount / 6);
    }

    /**
     * Estimate token count from word count
     * @param {number} wordCount - Number of words
     * @returns {number} Estimated token count
     */
    estimateTokenCount(wordCount) {
        // Rough estimate: 1.3 tokens per word for English text
        return Math.round(wordCount * 1.3);
    }
}

// Export singleton instance
export const documentProcessor = new DocumentProcessor();
export default documentProcessor; 