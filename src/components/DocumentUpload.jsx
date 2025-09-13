import React, { useState } from 'react';
import { documentServices } from '../firebase/services';

const DocumentUpload = ({ projectId, onUpload }) => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [description, setDescription] = useState('');
  const [keyChanges, setKeyChanges] = useState('');
  const [uploading, setUploading] = useState(false);

  const onPickFile = (e) => setFile(e.target.files?.[0] ?? null);

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files?.[0]) setFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    try {
      setUploading(true);
      const payload = {
        title: title || file.name,
        author,
        description,
        keyChanges: keyChanges.split('\n').filter(Boolean),
      };

      const created = await documentServices.createDocument(projectId, payload, file, (pct) => {});
      onUpload(created);
      setFile(null); setTitle(''); setAuthor(''); setDescription(''); setKeyChanges('');
    } catch (err) {
      console.error('Upload failed', err);
      alert('Upload failed. See console for details.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="page-header">
        <div>
          <h1 className="title">Upload New Document</h1>
          <p className="subtitle">Add a new version to your contract timeline.</p>
        </div>
      </div>

      <div className="card">
        <form className="upload-form" onSubmit={handleUpload}>
          <div className="upload-grid">
            {/* Dropzone */}
            <label
              className="dropzone"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
            >
              <input type="file" onChange={onPickFile} hidden />
              {!file ? (
                <div className="dropzone-inner">
                  <div className="drop-icon">📄</div>
                  <div>Click to select or drag & drop your document here</div>
                  <small>PDF, DOCX, or TXT</small>
                </div>
              ) : (
                <div className="dropzone-selected">
                  <div className="file-name">{file.name}</div>
                  <small>{(file.size / 1024 / 1024).toFixed(2)} MB</small>
                </div>
              )}
            </label>

            {/* Fields */}
            <div className="fields">
              <label className="form-field">
                <span>Document Title</span>
                <input value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g., Master Contract v6" />
              </label>

              <label className="form-field">
                <span>Author</span>
                <input value={author} onChange={e => setAuthor(e.target.value)} placeholder="Enter author name" />
              </label>

              <label className="form-field">
                <span>Description</span>
                <textarea rows={4} value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description of this version" />
              </label>

              <label className="form-field">
                <span>Key Changes (one per line)</span>
                <textarea rows={4} value={keyChanges} onChange={e => setKeyChanges(e.target.value)} placeholder="- Updated payment terms&#10;- Narrowed indemnity scope" />
              </label>

              <div className="actions">
                <button className="button primary" disabled={!file || uploading}>
                  {uploading ? 'Uploading…' : 'Upload Document'}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>

      <div className="card tips">
        <h3>Upload Guidelines</h3>
        <ul>
          <li>Ensure the document is the latest version.</li>
          <li>Provide clear descriptions of changes.</li>
          <li>Include author information for tracking.</li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentUpload;
