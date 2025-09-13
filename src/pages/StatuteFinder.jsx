import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
//import "../styles/ai-chat.css";
import "../styles/base.css";
//import "../styles/upload.css";

export default function StatuteFinder() {
  const [facts, setFacts] = useState("");
  const [jurisdiction, setJurisdiction] = useState("SG");
  const [area, setArea] = useState("auto");
  const [confidence, setConfidence] = useState(0.6);
  const [sortBy, setSortBy] = useState("score");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // naive local extraction for demo – replace with backend call
  const issues = useMemo(() => {
    if (!facts.trim()) return [];
    const lowers = facts.toLowerCase();
    const tags = [];
    if (/contract|agreement|consideration|breach/.test(lowers)) tags.push("Contract");
    if (/assault|theft|penal|criminal|ipc/.test(lowers)) tags.push("Criminal");
    if (/negligence|duty of care|tort/.test(lowers)) tags.push("Tort");
    if (/privacy|pdpa|data protection/.test(lowers)) tags.push("PDPA");
    return Array.from(new Set(tags));
  }, [facts]);

  const sampleFacts = `On 12 March 2024, the defendant accessed the plaintiff's customer list without consent
and used it for marketing a separate business. The data was exported from a company CRM
by an employee who had left. The plaintiff alleges breach of confidence and PDPA contraventions,
seeking injunctions and statutory damages.`;

  async function handleFind() {
    setLoading(true);
    try {
      // TODO: swap to your backend /chatService endpoint
      // Example payload the backend can expect for retrieval
      const payload = {
        query: facts,
        track: "statute",
        jurisdiction,
        area: area === "auto" ? issues[0] || null : area,
        top_k: 10,
        rerank: true,
        min_confidence: confidence,
        sort: sortBy,
      };

      // Fake results for UI wiring. Replace with real fetch.
      const fake = [
        {
          id: "PDPA-13",
          statute: "Personal Data Protection Act 2012",
          section: "s 13 (Consent to collection, use or disclosure of personal data)",
          score: 0.91,
          snippet:
            "An organisation shall not, on or after the appointed day, collect, use or disclose personal data about an individual unless the individual gives, or is deemed to give, consent to the collection, use or disclosure of the personal data...",
          link: "https://sso.agc.gov.sg/Act/PDPA2012",
        },
        {
          id: "PDPA-48O",
          statute: "Personal Data Protection Act 2012",
          section: "s 48O (Statutory damages)",
          score: 0.84,
          snippet:
            "The Court may order a person in breach of any provision of this Act to pay a sum by way of damages to the person aggrieved by the breach...",
          link: "https://sso.agc.gov.sg/Act/PDPA2012",
        },
        {
          id: "EC-17",
          statute: "Evidence Act 1893",
          section: "s 17 (Admissions defined)",
          score: 0.62,
          snippet:
            "An admission is a statement, oral or documentary which suggests an inference as to any fact in issue or relevant fact...",
          link: "https://sso.agc.gov.sg/Act/EvidenceAct",
        },
      ];
      await new Promise((r) => setTimeout(r, 600));
      setResults(fake);
    } finally {
      setLoading(false);
    }
  }

  function copyText(text) {
    navigator.clipboard.writeText(text);
  }

  return (
    <main className="main-content statute-page" style={{paddingBottom: 24}}>

      <header className="page-header">
        <div className="left">
          <h1 className="title">Statute Finder</h1>
          <p className="subtitle">Paste case facts → extract issues → rank the most applicable statutes & sections.</p>
        </div>
        <div className="right">
          <Link className="button ghost" to="/">← Back to Overview</Link>
        </div>
      </header>

      <div className="two-col">
        {/* LEFT: FACTS & ISSUES */}
        <section className="pane card">
          <div className="pane-header">
            <h2>Case Facts</h2>
            <div className="actions">
              <button className="button ghost" onClick={() => setFacts(sampleFacts)}>Sample</button>
              <button className="button ghost" onClick={() => navigator.clipboard.readText().then(setFacts)}>Paste</button>
              <button className="button danger ghost" onClick={() => setFacts("")}>Clear</button>
            </div>
          </div>
          <textarea
            className="facts-input"
            rows={14}
            placeholder="Paste the scenario / query facts here..."
            value={facts}
            onChange={(e) => setFacts(e.target.value)}
          />

          <div className="chips">
            {issues.length === 0 ? (
              <span className="chip muted">No issues detected yet</span>
            ) : (
              issues.map((i) => (
                <span className="chip" key={i}>{i}</span>
              ))
            )}
          </div>
        </section>

        {/* RIGHT: CONTROLS + RESULTS */}
        <section className="pane card">
          <div className="pane-header">
            <h2>Controls & Results</h2>
          </div>

          <div className="controls-grid">
            <label className="form-field">
              <span>Jurisdiction</span>
              <select value={jurisdiction} onChange={(e) => setJurisdiction(e.target.value)}>
                <option value="SG">Singapore</option>
                <option value="MY">Malaysia</option>
                <option value="UK">UK</option>
                <option value="AU">Australia</option>
              </select>
            </label>

            <label className="form-field">
              <span>Area of Law</span>
              <select value={area} onChange={(e) => setArea(e.target.value)}>
                <option value="auto">Auto-detect</option>
                <option value="Contract">Contract</option>
                <option value="Criminal">Criminal</option>
                <option value="Tort">Tort</option>
                <option value="PDPA">PDPA / Data Protection</option>
                <option value="Evidence">Evidence</option>
              </select>
            </label>

            <label className="form-field">
              <span>Min Confidence</span>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
              />
              <small>{(confidence * 100).toFixed(0)}%</small>
            </label>

            <label className="form-field">
              <span>Sort</span>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="score">Relevance</option>
                <option value="score">Score</option>
                <option value="alpha">Alphabetical</option>
                <option value="statute">By Statute</option>
              </select>
            </label>

            <div className="form-field" style={{alignSelf: "end"}}>
              <button className="button primary" disabled={!facts.trim() || loading} onClick={handleFind}>
                {loading ? "Searching…" : "Find Statutes"}
              </button>
            </div>
          </div>

          <div className="results">
            {results.length === 0 && !loading && (
              <div className="empty">No results yet. Enter facts and click <b>Find Statutes</b>.</div>
            )}

            {results.map((r) => (
              <article className="result card" key={r.id}>
                <div className="result-top">
                  <div>
                    <div className="result-title">{r.statute}</div>
                    <div className="result-section">{r.section}</div>
                  </div>
                  <div className="score" title="Relevance score">{Math.round(r.score * 100)}%</div>
                </div>
                <p className="snippet">{r.snippet}</p>
                <div className="result-actions">
                  <a className="button ghost" href={r.link} target="_blank" rel="noreferrer">Open in SSO</a>
                  <button className="button ghost" onClick={() => copyText(`${r.statute} – ${r.section}`)}>Copy citation</button>
                  <button className="button">Save to Project</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
