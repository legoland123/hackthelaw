import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";

export default function CreateProjectModal({ isOpen, onClose, onCreateProject }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState("active");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  // Lock scroll when open
  useEffect(() => {
    if (!isOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, [isOpen]);

  // Close on ESC
  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, onClose]);

  const reset = () => {
    setName(""); setDescription(""); setStatus("active");
    setSubmitting(false); setError("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter a project name.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        status,
        createdAt: new Date().toISOString(),
        lastUpdated: new Date().toISOString(),
        documentIds: [],
        conflicts: [],
      };
      await onCreateProject?.(payload);
      reset();
    } catch (err) {
      setError(err?.message || "Failed to create project.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const modalContent = (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Create New Project</h3>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <form className="modal-body" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="proj-name">Project name</label>
            <input
              id="proj-name"
              type="text"
              placeholder="e.g., PDPA Data Leak Investigation"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
            />
          </div>

          <div className="field">
            <label htmlFor="proj-desc">Description</label>
            <textarea
              id="proj-desc"
              placeholder="What is this project about?"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="proj-status">Status</label>
            <select id="proj-status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="active">Active</option>
              <option value="on-hold">On hold</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          {error && <div style={{ color: "#fca5a5", fontSize: ".95rem" }}>{error}</div>}

          <div className="modal-footer">
            <button type="button" className="btn btn-outline" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Creating…" : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // Render above everything to avoid z-index/layout issues
  return ReactDOM.createPortal(modalContent, document.body);
}
