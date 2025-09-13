// src/components/FileManager.jsx
import React, { useRef, useState } from 'react';
import '../styles/fileManager.css';

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '—';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), sizes.length - 1);
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

function toDate(ts) {
  if (!ts) return null;
  const d = ts.toDate ? ts.toDate() : new Date(ts);
  return isNaN(d) ? null : d;
}

const FileManager = ({
  projectId,
  documents = [],
  onOpen,     // (doc) => void
  onCreate,   // async (file, title) => createdDoc
  onDelete,   // async (docId) => void
}) => {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    try {
      await onCreate(file, title.trim());
      setFile(null);
      setTitle('');
      if (fileRef.current) fileRef.current.value = ''; // clear chooser UI
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = async (doc) => {
    const ok = window.confirm(`Delete "${doc.title || doc.fileInfo?.fileName || 'this file'}"?`);
    if (!ok) return;
    await onDelete(doc.id);
  };

  return (
    <div className="file-manager">
      <div className="page-header">
        <div>
          <h2 className="title">Project Files</h2>
          <p className="subtitle">Upload, view, download, and delete files.</p>
        </div>
      </div>

      <div className="card upload-card">
        <form onSubmit={handleUpload} className="drive-upload">
          <input
            ref={fileRef}
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <input
            type="text"
            placeholder="Title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="drive-title"
          />
          <button className="btn btn-primary" type="submit" disabled={!file || busy}>
            {busy ? 'Uploading…' : 'Upload'}
          </button>
        </form>
      </div>

      <div className="card">
        {documents.length === 0 ? (
          <div className="empty">
            <div className="empty-icon">📄</div>
            <h3>No files yet</h3>
            <p>Choose a file and click Upload to start your project library.</p>
          </div>
        ) : (
          <div className="drive-table-wrapper">
            <table className="drive-table">
              <thead>
                <tr>
                  <th style={{ width: '44%' }}>Name</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Uploaded</th>
                  <th style={{ width: 220, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {[...documents]
                  .sort((a, b) => {
                    const ad = toDate(a.timestamp) || new Date(0);
                    const bd = toDate(b.timestamp) || new Date(0);
                    return bd - ad; // newest first
                  })
                  .map((doc) => {
                    const name = doc.title || doc.fileInfo?.fileName || 'Untitled';
                    const size = formatBytes(doc.fileInfo?.size);
                    const type =
                      doc.fileInfo?.type?.split('/')[1]?.toUpperCase() ||
                      (doc.fileInfo?.fileName?.split('.').pop()?.toUpperCase() ?? 'FILE');
                    const date = toDate(doc.timestamp);

                    return (
                      <tr key={doc.id}>
                        <td className="drive-name">
                          <span className="drive-icon">📄</span>
                          <button className="link" onClick={() => onOpen(doc)} title="Open">
                            {name}
                          </button>
                        </td>
                        <td>{type}</td>
                        <td>{size}</td>
                        <td>{date ? date.toLocaleString() : '—'}</td>
                        <td style={{ textAlign: 'right' }}>
                          <div className="drive-actions">
                            <button className="btn btn-sm btn-outline" onClick={() => onOpen(doc)}>
                              View
                            </button>
                            {doc.fileInfo?.downloadURL && (
                              <a
                                className="btn btn-sm btn-outline"
                                href={doc.fileInfo.downloadURL}
                                target="_blank"
                                rel="noreferrer"
                              >
                                Download
                              </a>
                            )}
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => confirmDelete(doc)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileManager;
