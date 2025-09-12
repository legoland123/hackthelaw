import React, { useState, useEffect } from 'react'

const CreateProjectModal = ({ isOpen, onClose, onCreateProject }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        category: 'contract'
    })
    const [errors, setErrors] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)

    useEffect(() => {
        if (isOpen) {
            // Reset form when modal opens
            setFormData({
                name: '',
                description: '',
                category: 'contract'
            })
            setErrors({})
            setIsSubmitting(false)
        }
    }, [isOpen])

    const validateForm = () => {
        const newErrors = {}

        if (!formData.name.trim()) {
            newErrors.name = 'Project name is required'
        } else if (formData.name.trim().length < 3) {
            newErrors.name = 'Project name must be at least 3 characters'
        } else if (formData.name.trim().length > 100) {
            newErrors.name = 'Project name must be less than 100 characters'
        }

        if (formData.description.trim().length > 500) {
            newErrors.description = 'Description must be less than 500 characters'
        }

        setErrors(newErrors)
        return Object.keys(newErrors).length === 0
    }

    const handleInputChange = (e) => {
        const { name, value } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: value
        }))

        // Clear error when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }))
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()

        if (!validateForm()) {
            return
        }

        setIsSubmitting(true)

        try {
            const projectData = {
                name: formData.name.trim(),
                description: formData.description.trim() || 'Please provide a description for this project.',
                category: formData.category,
                status: 'New'
            }

            await onCreateProject(projectData)
            onClose()
        } catch (error) {
            console.error('Failed to create project:', error)
            setErrors({ submit: 'Failed to create project. Please try again.' })
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            onClose()
        }
    }

    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Create New Project</h2>
                    <button
                        className="modal-close"
                        onClick={onClose}
                        aria-label="Close modal"
                    >
                        ×
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="modal-form">
                    <div className="form-group">
                        <label htmlFor="project-name" className="form-label">
                            Project Name *
                        </label>
                        <input
                            id="project-name"
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                            className={`form-input ${errors.name ? 'form-input-error' : ''}`}
                            placeholder="Enter project name..."
                            autoFocus
                            disabled={isSubmitting}
                        />
                        {errors.name && (
                            <div className="form-error">{errors.name}</div>
                        )}
                    </div>

                    <div className="form-group">
                        <label htmlFor="project-description" className="form-label">
                            Description
                        </label>
                        <textarea
                            id="project-description"
                            name="description"
                            value={formData.description}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                            className={`form-textarea ${errors.description ? 'form-input-error' : ''}`}
                            placeholder="Describe the purpose and scope of this project..."
                            rows="3"
                            disabled={isSubmitting}
                        />
                        {errors.description && (
                            <div className="form-error">{errors.description}</div>
                        )}
                        <div className="form-help">
                            {formData.description.length}/500 characters
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="project-category" className="form-label">
                            Category
                        </label>
                        <select
                            id="project-category"
                            name="category"
                            value={formData.category}
                            onChange={handleInputChange}
                            className="form-select"
                            disabled={isSubmitting}
                        >
                            <option value="contract">Contract</option>
                            <option value="agreement">Agreement</option>
                            <option value="policy">Policy</option>
                            <option value="terms">Terms & Conditions</option>
                            <option value="legal">Legal Document</option>
                            <option value="other">Other</option>
                        </select>
                    </div>

                    {errors.submit && (
                        <div className="form-error form-error-global">
                            {errors.submit}
                        </div>
                    )}

                    <div className="modal-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onClose}
                            disabled={isSubmitting}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={isSubmitting || !formData.name.trim()}
                        >
                            {isSubmitting ? (
                                <>
                                    <span className="spinner-small"></span>
                                    Creating...
                                </>
                            ) : (
                                'Create Project'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}

export default CreateProjectModal 