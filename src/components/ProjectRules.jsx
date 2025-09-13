import React, { useState } from 'react';
import { projectServices } from '../firebase/services';

const ProjectRules = ({ projectId, projectName }) => {
  const [ruleText, setRuleText] = useState('');
  const [rules, setRules] = useState([]);

  const addRule = () => {
    const t = ruleText.trim();
    if (!t) return;
    setRules(prev => [...prev, { id: Date.now(), text: t }]);
    setRuleText('');
  };

  const removeRule = (id) => setRules(prev => prev.filter(r => r.id !== id));

  const saveRules = async () => {
    try {
      // persist on project doc if you like
      await projectServices.updateProject(projectId, { rules });
      alert('Rules saved.');
    } catch (e) {
      console.error(e);
      alert('Failed to save rules (see console).');
    }
  };

  return (
    <div className="rules-page">
      <div className="page-header">
        <div>
          <h1 className="title">LLM Rules</h1>
          <p className="subtitle">Define rules and guardrails for “{projectName}”.</p>
        </div>
        <div className="right">
          <button className="button primary" onClick={saveRules} disabled={!rules.length}>Save Rules</button>
        </div>
      </div>

      <div className="card rules-grid">
        <div className="left">
          <label className="form-field">
            <span>Add a new rule</span>
            <textarea
              rows={6}
              value={ruleText}
              onChange={e => setRuleText(e.target.value)}
              placeholder={`(1) Ensure the model provides a fair opportunity to remedy any alleged breach before termination.\n(2) Avoid generating personally identifiable information.`}
            />
          </label>
          <button className="button primary" onClick={addRule}>Add Rule</button>
        </div>

        <div className="right">
          <div className="pane-header">
            <h2>Current Rules ({rules.length})</h2>
          </div>
          {!rules.length ? (
            <div className="empty">No rules defined yet. Add your first rule on the left.</div>
          ) : (
            <ul className="rules-list">
              {rules.map(r => (
                <li key={r.id} className="rule-row">
                  <div className="txt">{r.text}</div>
                  <button className="button danger" onClick={() => removeRule(r.id)}>Remove</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectRules;
