import React from 'react';

const VersionTimeline = ({ documents = [], onDocumentSelect, selectedDocument, setActiveView }) => {
  const formatDate = (ts) => {
    const d = ts && ts.toDate ? ts.toDate() : new Date(ts || Date.now());
    return d.toLocaleString('en-US', { year:'numeric', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
  };

  if (!documents.length) {
    return (
      <div className="timeline">
        <div className="timeline-header">
          <h2>Document Timeline</h2>
          <p>Track the evolution of your contract</p>
        </div>

        <div className="empty-state">
          <div className="empty-state-icon">📄</div>
          <h3 className="empty-state-title">No Documents Yet</h3>
          <p className="empty-state-description">
            Start by uploading your first document to begin building the timeline.
          </p>
          <button className="btn btn-primary" onClick={() => setActiveView('upload')}>Upload First Document</button>
        </div>
      </div>
    );
  }

  // Sort newest first if your data isn't already sorted
  const sorted = [...documents].sort((a, b) => {
    const ta = a.timestamp?.toMillis?.() ?? new Date(a.timestamp || 0).getTime();
    const tb = b.timestamp?.toMillis?.() ?? new Date(b.timestamp || 0).getTime();
    return tb - ta;
  });

  return (
    <div className="timeline">
      <div className="timeline-header">
        <h2>Document Timeline</h2>
        <p>{sorted.length} version{sorted.length !== 1 ? 's' : ''}</p>
      </div>

      <div className="timeline-list">
        {sorted.map((doc) => {
          const isSelected = selectedDocument?.id === doc.id;
          return (
            <div key={doc.id} className="timeline-item">
              <div className="timeline-version-header">
                <h3 className="version-title">Version {doc.version ?? '-'}</h3>
                <span className="version-date">{formatDate(doc.timestamp)}</span>
              </div>

              <div className="timeline-card-container">
                <div
                  className={`timeline-card original-doc ${isSelected ? 'selected' : ''}`}
                  onClick={() => onDocumentSelect(doc)}
                >
                  <div className="timeline-card-header">
                    <div>
                      <h4 className="timeline-card-title">{doc.title || 'Original Document'}</h4>
                      <div className="timeline-card-meta">
                        <span>{doc.fileInfo?.type || 'PDF'} • {doc.fileInfo?.fileName || ''}</span>
                      </div>
                    </div>
                    <div className="timeline-card-version">Original</div>
                  </div>

                  {doc.description && (
                    <div className="timeline-card-content">
                      <p>{doc.description}</p>
                    </div>
                  )}

                  <div className="timeline-card-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={(e) => { e.stopPropagation(); onDocumentSelect(doc); }}
                    >
                      View Original
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VersionTimeline;
