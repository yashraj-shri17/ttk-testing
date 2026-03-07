import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../config/api';
import './AdminDashboard.css';

function AdminDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedUser, setExpandedUser] = useState(null);
    const [selectedInteraction, setSelectedInteraction] = useState(null);

    useEffect(() => {
        const isAdmin = user && user.email === 'abhishek@justlearnindia.in';
        if (!isAdmin) {
            navigate('/');
            return;
        }

        const fetchMetrics = async () => {
            try {
                const response = await fetch(`${API_ENDPOINTS.ADMIN_METRICS}?user_id=${user.id}`);

                // If backend returns a 404 page (e.g. backend not deployed yet), handled safely
                if (!response.ok) {
                    throw new Error(`Backend API returned ${response.status} ${response.statusText}`);
                }

                // Safely parse JSON
                const text = await response.text();
                try {
                    const data = JSON.parse(text);
                    if (data.success) {
                        setMetrics(data.metrics);
                    } else {
                        setError(data.error || 'Failed to load metrics from API');
                    }
                } catch (parseError) {
                    console.error('API returned non-JSON:', text.substring(0, 150));

                    let hint = "Backend returned invalid JSON.";
                    if (text.includes("<!DOCTYPE html>") || text.includes("<html")) {
                        hint = `Vercel intercepted the API call and returned the Frontend HTML instead of backend data. This happens if REACT_APP_API_URL is wrong. URL used: ${API_ENDPOINTS.ADMIN_METRICS}`;
                    }

                    throw new Error(`${hint} Data snippet: ${text.substring(0, 40)}...`);
                }

            } catch (err) {
                console.error('Error fetching admin metrics:', err);
                if (err.message.includes('fetch')) {
                    setError(`Network error: Could not reach backend at ${API_ENDPOINTS.ADMIN_METRICS}. Is it running?`);
                } else {
                    setError(`Backend issue: ${err.message}`);
                }
            } finally {
                setLoading(false);
            }
        };

        fetchMetrics();
    }, [user, navigate]);

    const toggleUserExpand = (userId) => {
        setExpandedUser(expandedUser === userId ? null : userId);
    };

    if (loading) {
        return (
            <div className="admin-dashboard">
                <div className="dashboard-header">
                    <h1>Admin Dashboard</h1>
                    <p>Loading analytics and metrics...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="admin-dashboard">
                <div className="dashboard-header">
                    <h1>Admin Dashboard</h1>
                    <div className="error-message">{error}</div>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-dashboard">
            <div className="dashboard-header">
                <h1>Admin Dashboard</h1>
                <p>Welcome back, {user?.name.split(' ')[0]}! Here are the system analytics.</p>
            </div>

            <div className="dashboard-metrics">
                <div className="metric-card glass">
                    <h3>Total Registered Users</h3>
                    <div className="metric-value">{metrics?.total_users || 0}</div>
                </div>
                <div className="metric-card glass">
                    <h3>Total Conversations</h3>
                    <div className="metric-value">{metrics?.total_conversations || 0}</div>
                </div>
            </div>

            <div className="dashboard-logs">
                <h2>User Interactions</h2>
                <div className="users-list">
                    {metrics?.user_interactions?.map((interaction) => (
                        <div key={interaction.user_id} className={`user-accordion ${expandedUser === interaction.user_id ? 'expanded' : ''}`}>
                            <div className="user-header" onClick={() => toggleUserExpand(interaction.user_id)}>
                                <div className="user-info">
                                    <span className="user-name">{interaction.user_name}</span>
                                    <span className="user-email">{interaction.user_email}</span>
                                </div>
                                <div className="user-stats">
                                    <span className="conv-count">{interaction.conversation_count} conversations</span>
                                    <span className="last-active">Last active: {new Date(interaction.last_active).toLocaleDateString()}</span>
                                    <span className="expand-icon">{expandedUser === interaction.user_id ? '▼' : '▶'}</span>
                                </div>
                            </div>

                            {expandedUser === interaction.user_id && (
                                <div className="user-conversations">
                                    <div className="logs-table-container">
                                        <table className="logs-table">
                                            <thead>
                                                <tr>
                                                    <th>S.No</th>
                                                    <th>Timestamp</th>
                                                    <th>User Asked</th>
                                                    <th>Model</th>
                                                    <th>AI Response Snippet</th>
                                                    <th>Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {interaction.conversations.map((conv, idx) => (
                                                    <tr key={conv.id}>
                                                        <td className="serial-cell" data-label="S.No">{idx + 1}</td>
                                                        <td className="time-cell" data-label="Time">{new Date(conv.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
                                                        <td className="question-cell" data-label="Question" title={conv.question}>{conv.question}</td>
                                                        <td className="model-cell" data-label="Model"><span className="model-badge">{conv.model_used}</span></td>
                                                        <td className="answer-cell" data-label="Snippet" title={conv.answer}>{conv.answer}</td>
                                                        <td className="action-cell" data-label="Option">
                                                            <button
                                                                className="view-btn"
                                                                onClick={() => setSelectedInteraction(conv)}
                                                            >
                                                                View Full Chat
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}

                    {!metrics?.user_interactions?.length && (
                        <p style={{ textAlign: 'center', padding: '20px' }}>No user interactions recorded yet.</p>
                    )}
                </div>
            </div>
            {/* Full Conversation Modal */}
            {selectedInteraction && (
                <div className="modal-overlay" onClick={() => setSelectedInteraction(null)}>
                    <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>Conversation Detail</h3>
                            <button className="close-btn" onClick={() => setSelectedInteraction(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="admin-q-block">
                                <h4>User Question</h4>
                                <p>{selectedInteraction.question}</p>
                            </div>
                            <div className="admin-a-block">
                                <h4>Krishna AI Response ({selectedInteraction.model_used})</h4>
                                <p>{selectedInteraction.answer}</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminDashboard;
