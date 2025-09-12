import React, { useState, useEffect } from 'react';

const ProjectRules = ({ projectId, projectName }) => {
    const [rules, setRules] = useState([]);
    const [newRule, setNewRule] = useState('');
    const [loading, setLoading] = useState(false);

    // Load existing rules for this project
    useEffect(() => {
        loadProjectRules();
    }, [projectId]);

    const loadProjectRules = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual API call to load project rules
            // For now, we'll use localStorage as a simple storage
            const storedRules = localStorage.getItem(`project_rules_${projectId}`);
            if (storedRules) {
                setRules(JSON.parse(storedRules));
            }
        } catch (error) {
            console.error('Failed to load project rules:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!newRule.trim()) return;

        try {
            const rule = {
                id: Date.now(),
                text: newRule.trim(),
                createdAt: new Date().toISOString(),
                projectId: projectId
            };

            const updatedRules = [...rules, rule];
            setRules(updatedRules);
            setNewRule('');

            // TODO: Replace with actual API call to save project rules
            // For now, we'll use localStorage as a simple storage
            localStorage.setItem(`project_rules_${projectId}`, JSON.stringify(updatedRules));

            console.log('Rule added:', rule);
        } catch (error) {
            console.error('Failed to add rule:', error);
            alert('Failed to add rule. Please try again.');
        }
    };

    const handleDeleteRule = async (ruleId) => {
        try {
            const updatedRules = rules.filter(rule => rule.id !== ruleId);
            setRules(updatedRules);

            // TODO: Replace with actual API call to delete project rule
            localStorage.setItem(`project_rules_${projectId}`, JSON.stringify(updatedRules));

            console.log('Rule deleted:', ruleId);
        } catch (error) {
            console.error('Failed to delete rule:', error);
            alert('Failed to delete rule. Please try again.');
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    if (loading) {
        return (
            <div className="rules-container">
                <div className="loading">
                    <div className="spinner"></div>
                    Loading project rules...
                </div>
            </div>
        );
    }

    return (
        <div className="rules-container">
            <div className="rules-header">
                <h1>LLM Rules</h1>
                <p className="rules-description">
                    Define rules and guidelines.
                </p>
            </div>

            <div className="rules-content">
                <form onSubmit={handleSubmit} className="rules-form">
                    <div className="form-group">
                        <label htmlFor="newRule" className="form-label">
                            Add a new rule:
                        </label>
                        <textarea
                            id="newRule"
                            className="form-textarea"
                            value={newRule}
                            onChange={(e) => setNewRule(e.target.value)}
                            placeholder="(1) Ensure that it is given a fair opportunity to remedy any alleged breach before the contract is terminated, typically through a clearly defined cure period;
(2) Protect itself from wrongful or arbitrary termination by the main contractor, ideally by including a right to compensation or recovery of costs if terminated without cause; and
(3) Retain a balanced right to terminate the subcontract if the main contractor fails to make timely payment or causes prolonged suspension, to safeguard Sanitec’s cashflow and project continuity."
                            rows="4"
                            required
                        />
                    </div>
                    <div className="form-actions">
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={false}
                        >
                            Add Rule
                        </button>
                    </div>
                </form>

                <div className="rules-list">
                    <h3>Current Rules ({rules.length})</h3>
                    {rules.length === 0 ? (
                        <div className="empty-rules">
                            <p>No rules defined yet. Add your first rule above.</p>
                        </div>
                    ) : (
                        <div className="rules-items">
                            {rules.map((rule) => (
                                <div key={rule.id} className="rule-item">
                                    <div className="rule-content">
                                        <p className="rule-text">{rule.text}</p>
                                        <span className="rule-date">
                                            Added: {formatDate(rule.createdAt)}
                                        </span>
                                    </div>
                                    <button
                                        className="btn btn-danger rule-delete"
                                        onClick={() => handleDeleteRule(rule.id)}
                                        title="Delete rule"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProjectRules; 