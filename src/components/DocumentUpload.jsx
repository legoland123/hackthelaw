import React, { useState, useRef } from 'react'
import { documentServices } from '../firebase/services'
import documentProcessor from '../services/documentProcessor'

const DocumentUpload = ({ projectId, onUpload, existingDocuments }) => {
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        author: '',
        changes: '',
        file: null
    })
    const [isDragging, setIsDragging] = useState(false)
    const [isUploading, setIsUploading] = useState(false)
    const [uploadProgress, setUploadProgress] = useState(0)
    const [extractionStatus, setExtractionStatus] = useState('')
    const fileInputRef = useRef(null)
    const [error, setError] = useState('')

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragging(false)

        const files = e.dataTransfer.files
        if (files.length > 0) {
            handleFileSelect(files[0])
        }
    }

    const handleFileSelect = (file) => {
        if (file) {
            setFormData(prev => ({
                ...prev,
                file: file,
                filename: file.name,
                title: prev.title || file.name.replace(/\.[^/.]+$/, '')
            }))
        }
    }

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: value
        }))
    }

    const handleFileInputChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            handleFileSelect(file)
        }
    }

    const simulateUpload = async () => {
        setIsUploading(true)
        setUploadProgress(0)

        // Simulate upload progress
        for (let i = 0; i <= 100; i += 10) {
            await new Promise(resolve => setTimeout(resolve, 100))
            setUploadProgress(i)
        }

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, 500))

        setIsUploading(false)
        setUploadProgress(0)
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!formData.file) {
            setError('Please select a file to upload')
            return
        }

        setIsUploading(true)
        setUploadProgress(0)
        setError('')
        setExtractionStatus('')

        try {
            // Extract document content for AI context
            setExtractionStatus('Processing document content...')
            let documentContent = '';
            let contentStats = null;

            try {
                documentContent = await documentProcessor.extractDocumentText(formData.file);
                contentStats = documentProcessor.getContentStats(documentContent);

                if (documentProcessor.isValidContent(documentContent)) {
                    setExtractionStatus(`✅ Document processed successfully (${contentStats.wordCount} words, ${contentStats.length} characters)`);
                    console.log('Document content processed successfully:', contentStats);
                } else {
                    setExtractionStatus('⚠️ Document processing completed but content may be limited');
                    console.warn('Document processing completed but content may be limited:', contentStats);
                }
            } catch (contentError) {
                console.warn('Failed to process document content:', contentError);
                documentContent = `[Content processing failed for ${formData.file.name}: ${contentError.message}]`;
                setExtractionStatus('❌ Document processing failed - document will be uploaded without content');
            }

            const documentData = {
                title: formData.title,
                author: formData.author,
                description: formData.description,
                changes: formData.changes.split(',').map(c => c.trim()).filter(Boolean),
                version: existingDocuments.length + 1,
                content: documentContent, // Add processed content
                content_stats: contentStats // Add content statistics for debugging
            }

            setExtractionStatus('Uploading document...')
            const onUploadProgress = (progress) => {
                setUploadProgress(progress)
            }

            const newDocument = await documentServices.createDocument(
                projectId,
                documentData,
                formData.file,
                onUploadProgress
            )

            setExtractionStatus('✅ Document uploaded successfully')
            onUpload(newDocument)

        } catch (err) {
            setError('Failed to upload document. Please try again.')
            setExtractionStatus('❌ Upload failed')
            console.error(err)
        } finally {
            setIsUploading(false)
            setUploadProgress(0)
            // Clear extraction status after a delay
            setTimeout(() => setExtractionStatus(''), 3000)
        }
    }

    const getFileIcon = (filename) => {
        if (!filename) return '📄'
        const ext = filename.split('.').pop().toLowerCase()
        switch (ext) {
            case 'pdf': return '📕'
            case 'docx': return '📘'
            case 'doc': return '⚠️' // Legacy format not supported
            case 'txt': return '📄'
            default: return '📄'
        }
    }

    const handleTranscribe = () => {
        // TODO: Implement transcription functionality
        console.log('Transcribe button clicked - functionality not implemented yet')
    }

    return (
        <div className="upload-section">
            <div className="upload-card">
                {/* Transcribe Button */}
                <button
                    type="button"
                    className="transcribe-btn"
                    onClick={handleTranscribe}
                    title="Transcribe audio to text"
                >
                    🎤 Transcribe
                </button>

                <h2>Upload New Document</h2>
                <p>Add a new version to your master contract timeline</p>

                <form onSubmit={handleSubmit} className="upload-form">
                    {/* File Upload Area */}
                    <div className="form-group">
                        <label className="form-label">Document File</label>
                        <div
                            className={`upload-area ${isDragging ? 'dragover' : ''}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            {formData.file ? (
                                <div className="file-selected">
                                    <div className="file-icon">{getFileIcon(formData.file.name)}</div>
                                    <div className="file-info">
                                        <div className="file-name">{formData.file.name}</div>
                                        <div className="file-size">
                                            {(formData.file.size / 1024 / 1024).toFixed(2)} MB
                                        </div>
                                    </div>
                                    <button
                                        type="button"
                                        className="btn btn-secondary"
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            setFormData(prev => ({ ...prev, file: null }))
                                            if (fileInputRef.current) fileInputRef.current.value = ''
                                        }}
                                    >
                                        Remove
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <div className="upload-icon">📄</div>
                                    <div className="upload-text">
                                        <strong>Click to select</strong> or drag and drop your document here
                                    </div>
                                    <div className="upload-hint">
                                        Supports PDF, DOCX, TXT files (DOCX content will be extracted for AI analysis)
                                    </div>
                                </>
                            )}
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".pdf,.docx,.txt"
                            onChange={handleFileInputChange}
                            style={{ display: 'none' }}
                        />
                    </div>

                    {/* Document Metadata */}
                    <div className="form-group">
                        <label className="form-label">Document Title</label>
                        <input
                            type="text"
                            name="title"
                            className="form-input"
                            value={formData.title}
                            onChange={handleInputChange}
                            placeholder="Enter document title"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Author</label>
                        <input
                            type="text"
                            name="author"
                            className="form-input"
                            value={formData.author}
                            onChange={handleInputChange}
                            placeholder="Enter author name"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Description</label>
                        <textarea
                            name="description"
                            className="form-input form-textarea"
                            value={formData.description}
                            onChange={handleInputChange}
                            placeholder="Brief description of this document version"
                            rows="3"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Key Changes</label>
                        <textarea
                            name="changes"
                            className="form-input form-textarea"
                            value={formData.changes}
                            onChange={handleInputChange}
                            placeholder="List the key changes in this version (one per line)"
                            rows="4"
                        />
                    </div>

                    {/* Upload Progress */}
                    {isUploading && (
                        <div className="upload-progress">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${uploadProgress}%` }}
                                ></div>
                            </div>
                            <div className="progress-text">
                                Uploading... {Math.round(uploadProgress)}%
                            </div>
                        </div>
                    )}

                    {/* Extraction Status */}
                    {extractionStatus && (
                        <div className={`extraction-status ${extractionStatus.includes('✅') ? 'success' : extractionStatus.includes('❌') ? 'error' : 'info'}`}>
                            <div className="extraction-status-icon">
                                {extractionStatus.includes('✅') ? '✅' : extractionStatus.includes('❌') ? '❌' : '⏳'}
                            </div>
                            <div className="extraction-status-text">
                                {extractionStatus}
                            </div>
                        </div>
                    )}

                    {/* Submit Button */}
                    <div className="form-actions">
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={isUploading || !formData.file}
                        >
                            {isUploading ? (
                                <>
                                    <span className="spinner"></span>
                                    Uploading...
                                </>
                            ) : (
                                <>
                                    📤 Upload Document
                                </>
                            )}
                        </button>
                    </div>
                </form>

                {/* Upload Guidelines */}
                <div className="upload-guidelines">
                    <h4>Upload Guidelines</h4>
                    <ul>
                        <li>Ensure the document is the latest version</li>
                        <li>Provide clear descriptions of changes</li>
                        <li>Include author information for tracking</li>
                        <li>System will automatically detect conflicts</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default DocumentUpload 