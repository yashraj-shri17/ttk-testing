import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { API_ENDPOINTS } from '../config/api';
import './AdminDashboard.css';

// Simple icons as SVG constants
const Icons = {
    Stats: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" /></svg>,
    History: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>,
    Shield: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>,
    Users: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" /></svg>,
    Alert: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>,
    Tag: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" /><line x1="7" y1="7" x2="7.01" y2="7" /></svg>,
    Home: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></svg>
};

function AdminDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('stats');
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expandedUser, setExpandedUser] = useState(null);
    const [selectedInteraction, setSelectedInteraction] = useState(null);

    // Form states
    const [adminForm, setAdminForm] = useState({ email: '', password: '' });
    const [userForm, setUserForm] = useState({ email: '', password: '', access: true });
    const [couponForm, setCouponForm] = useState({ code: '', type: 'percent', discount: '' });
    const [coupons, setCoupons] = useState([]);
    const [actionLoading, setActionLoading] = useState(null);
    const [actionMsg, setActionMsg] = useState({ type: '', text: '' });

    const fetchMetrics = useCallback(async () => {
        if (!user) return;
        try {
            const response = await fetch(`${API_ENDPOINTS.ADMIN_METRICS}?user_id=${user.id}`);
            if (!response.ok) throw new Error(`API error ${response.status}`);
            const data = await response.json();
            if (data.success) {
                setMetrics(data.metrics);
            } else {
                setError(data.error || 'Failed to fetch metrics');
            }
        } catch (err) {
            console.error('Metrics fetch error:', err);
            setError('System link lost. Backend connection failed.');
        } finally {
            setLoading(false);
        }
    }, [user]);

    const fetchCoupons = useCallback(async () => {
        if (!user) return;
        try {
            const response = await fetch(`${API_ENDPOINTS.ADMIN_COUPONS}?user_id=${user.id}`);
            const data = await response.json();
            if (data.success) {
                setCoupons(data.coupons);
            }
        } catch (err) {
            console.error('Coupon fetch error:', err);
        }
    }, [user]);

    useEffect(() => {
        const isAdmin = user && (user.role === 'admin' || user.email === 'abhishek@justlearnindia.in');
        if (!isAdmin) {
            navigate('/');
            return;
        }
        fetchMetrics();
        if (activeTab === 'coupons') fetchCoupons();
    }, [user, navigate, fetchMetrics, fetchCoupons, activeTab]);

    const handleCouponAction = async (action, id = null) => {
        setActionLoading(action);
        setActionMsg({ type: '', text: '' });

        try {
            if (action === 'create') {
                const response = await fetch(`${API_ENDPOINTS.ADMIN_COUPONS}?user_id=${user.id}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: user.id,
                        code: couponForm.code,
                        discount_type: couponForm.type,
                        discount_value: parseFloat(couponForm.discount)
                    })
                });
                const data = await response.json();
                if (data.success) {
                    setActionMsg({ type: 'success', text: 'COUPON_CREATED_SUCCESSFULLY.' });
                    setCouponForm({ code: '', type: 'percent', discount: '' });
                    fetchCoupons();
                } else {
                    setActionMsg({ type: 'error', text: data.error || 'Failed to create coupon' });
                }
            } else if (action === 'delete') {
                const response = await fetch(`${API_ENDPOINTS.ADMIN_COUPONS}/${id}?user_id=${user.id}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: user.id })
                });
                const data = await response.json();
                if (data.success) {
                    fetchCoupons();
                }
            }
        } catch (err) {
            setActionMsg({ type: 'error', text: 'SYNC_ERROR: NETWORK REQUEST FAILED.' });
        } finally {
            setActionLoading(null);
        }
    };

    const handleAction = async (type) => {
        setActionLoading(type);
        setActionMsg({ type: '', text: '' });

        const endpoint = type === 'admin' ? API_ENDPOINTS.CREATE_ADMIN : API_ENDPOINTS.GRANT_ACCESS;
        const payload = type === 'admin'
            ? { admin_id: user.id, ...adminForm }
            : { admin_id: user.id, ...userForm };

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (data.success) {
                setActionMsg({ type: 'success', text: `CORE_SYNC: ${data.message.toUpperCase()}.` });
                if (type === 'admin') setAdminForm({ email: '', password: '' });
                else setUserForm({ email: '', password: '', access: true });
                fetchMetrics();
            } else {
                setActionMsg({ type: 'error', text: `ERROR: ${data.error.toUpperCase()}.` });
            }
        } catch (err) {
            setActionMsg({ type: 'error', text: 'SYNC_ERROR: NETWORK REQUEST FAILED.' });
        } finally {
            setActionLoading(null);
        }
    };

    if (loading) {
        return (
            <div className="admin-dashboard">
                <div className="loader-container">
                    <div className="crystal-loader"></div>
                </div>
            </div>
        );
    }

    const renderContent = () => {
        switch (activeTab) {
            case 'stats':
                return (
                    <div className="stats-view">
                        <div className="stats-grid">
                            <div className="stat-item admin-glass-card">
                                <div className="stat-label">TOTAL REGISTERED NODES</div>
                                <div className="stat-value">{metrics?.total_users || 0}</div>
                            </div>
                            <div className="stat-item admin-glass-card">
                                <div className="stat-label">ACTIVE INTERACTIONS (24H)</div>
                                <div className="stat-value">{metrics?.today_users || 0}</div>
                            </div>
                            <div className="stat-item admin-glass-card">
                                <div className="stat-label">TOTAL NEURAL PATHS</div>
                                <div className="stat-value">{metrics?.total_conversations || 0}</div>
                            </div>
                        </div>
                    </div>
                );
            case 'history':
                if (expandedUser) {
                    const node = metrics?.user_interactions?.find(u => u.user_id === expandedUser);
                    return (
                        <div className="history-detail-view">
                            <div className="detail-header">
                                <button className="back-btn" onClick={() => setExpandedUser(null)}>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
                                    Back to Registry
                                </button>
                                <h2>NEURAL STREAM: {node?.user_name}</h2>
                            </div>
                            <div className="registry-container">
                                <table className="registry-table">
                                    <thead>
                                        <tr>
                                            <th>TIMESTAMP</th>
                                            <th>PROMPT</th>
                                            <th>AI SYNTHESIS</th>
                                            <th>ACTION</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {node?.conversations?.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).map((conv) => (
                                            <tr key={conv.id} className="registry-row">
                                                <td>{new Date(conv.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
                                                <td className="table-text-cell">{conv.question}</td>
                                                <td className="table-text-cell">{conv.answer}</td>
                                                <td>
                                                    <button className="view-btn" onClick={() => setSelectedInteraction({ ...conv, user_email: node.user_email })}>EXAMINE</button>
                                                </td>
                                            </tr>
                                        ))}
                                        {(!node?.conversations || node.conversations.length === 0) && (
                                            <tr><td colSpan="4" style={{ textAlign: 'center', padding: '40px' }}>No neural paths detected for this node.</td></tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    );
                }
                return (
                    <div className="history-view">
                        <div className="registry-container">
                            <table className="registry-table">
                                <thead>
                                    <tr>
                                        <th>NEURAL ID</th>
                                        <th>INTERACTION COUNT</th>
                                        <th>LAST PULSED</th>
                                        <th>ACTION</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {metrics?.user_interactions?.filter(u => u.conversation_count > 0).map((node) => (
                                        <tr key={node.user_id} className="registry-row summary-row">
                                            <td>
                                                <div className="neural-id-cell">
                                                    <span className="node-name">{node.user_name}</span>
                                                    <span className="node-email">{node.user_email}</span>
                                                </div>
                                            </td>
                                            <td>{node.conversation_count} Segments</td>
                                            <td>{node.last_active === 'Never' ? 'Never' : new Date(node.last_active).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                                            <td>
                                                <button className="retrieve-stream-btn" onClick={() => setExpandedUser(node.user_id)}>
                                                    Retrieve Stream <span className="arrow">›</span>
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {(!metrics?.user_interactions || metrics.user_interactions.filter(u => u.conversation_count > 0).length === 0) && (
                                        <tr><td colSpan="4" style={{ textAlign: 'center', padding: '40px' }}>No conversation data available.</td></tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                );
            case 'access':
                return (
                    <div className="access-view">
                        {actionMsg.type === 'success' && activeTab === 'access' && (
                            <div className="success-banner">{actionMsg.text}</div>
                        )}
                        <div className="admin-glass-card" style={{ maxWidth: '600px' }}>
                            <h2 className="form-title">Assign Neural Access</h2>
                            <div className="form-field">
                                <label className="form-label">TARGET USER EMAIL</label>
                                <input
                                    className="form-input" type="email" placeholder="user@justlearn.in"
                                    value={userForm.email} onChange={e => setUserForm({ ...userForm, email: e.target.value })}
                                />
                            </div>
                            <div className="form-field">
                                <label className="form-label">TEMPORARY SECURITY PASS</label>
                                <input
                                    className="form-input" type="password" placeholder="••••••••"
                                    value={userForm.password} onChange={e => setUserForm({ ...userForm, password: e.target.value })}
                                />
                            </div>
                            <button
                                className="submit-btn" disabled={actionLoading === 'user'}
                                onClick={() => handleAction('user')}
                            >
                                {actionLoading === 'user' ? 'SYNCHRONIZING...' : 'GRANT ACCESS'}
                            </button>
                            {actionMsg.type === 'error' && <p className="msg-text error">{actionMsg.text}</p>}
                        </div>
                    </div>
                );
            case 'elevate':
                return (
                    <div className="elevate-view">
                        {actionMsg.type === 'success' && activeTab === 'elevate' && (
                            <div className="success-banner">{actionMsg.text}</div>
                        )}
                        <div className="admin-glass-card" style={{ maxWidth: '600px' }}>
                            <h2 className="form-title">Elevate Authority Level</h2>
                            <div className="form-field">
                                <label className="form-label">ADMINISTRATOR NAME</label>
                                <input
                                    className="form-input" type="text" placeholder="Full Name"
                                    onChange={e => setAdminForm({ ...adminForm, name: e.target.value })}
                                />
                            </div>
                            <div className="form-field">
                                <label className="form-label">SECURE EMAIL</label>
                                <input
                                    className="form-input" type="email" placeholder="admin@justlearnindia.in"
                                    value={adminForm.email} onChange={e => setAdminForm({ ...adminForm, email: e.target.value })}
                                />
                            </div>
                            <div className="form-field">
                                <label className="form-label">ENCRYPTED PASSCODE</label>
                                <input
                                    className="form-input" type="password" placeholder="••••••••"
                                    value={adminForm.password} onChange={e => setAdminForm({ ...adminForm, password: e.target.value })}
                                />
                            </div>
                            <button
                                className="submit-btn" disabled={actionLoading === 'admin'}
                                onClick={() => handleAction('admin')}
                            >
                                {actionLoading === 'admin' ? 'INITIALIZING...' : 'ELEVATE PRIVILEGES'}
                            </button>
                            {actionMsg.type === 'error' && <p className="msg-text error">{actionMsg.text}</p>}
                        </div>
                    </div>
                );
            case 'registry':
                return (
                    <div className="registry-view">
                        <div className="registry-container">
                            <table className="registry-table">
                                <thead>
                                    <tr>
                                        <th>NODE NAME</th>
                                        <th>IDENTIFIER</th>
                                        <th>RANK</th>
                                        <th>STATUS</th>
                                        <th>LAST ACTIVE</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {metrics?.user_interactions?.map((node) => (
                                        <tr key={node.user_id} className="registry-row" onClick={() => {
                                            setExpandedUser(node.user_id);
                                            setActiveTab('history');
                                        }}>
                                            <td className="admin-name">{node.user_name}</td>
                                            <td>{node.user_email}</td>
                                            <td>
                                                <span className={`role-badge role-${node.role}`}>{node.role}</span>
                                            </td>
                                            <td>
                                                <span className={`access-dot ${node.has_chat_access ? 'access-on' : 'access-off'}`}></span>
                                                {node.has_chat_access ? 'ONLINE' : 'LOCKED'}
                                            </td>
                                            <td>{node.last_active === 'Never' ? 'Never' : new Date(node.last_active).toLocaleDateString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                );
            case 'coupons':
                return (
                    <div className="coupons-view">
                        <div className="admin-grid">
                            <div className="admin-glass-card">
                                <h2 className="form-title">Create New Coupon</h2>
                                <div className="form-field">
                                    <label className="form-label">COUPON CODE</label>
                                    <input
                                        className="form-input" type="text" placeholder="KRISHNA20"
                                        value={couponForm.code} onChange={e => setCouponForm({ ...couponForm, code: e.target.value.toUpperCase() })}
                                    />
                                </div>
                                <div className="form-field">
                                    <label className="form-label">DISCOUNT TYPE</label>
                                    <select
                                        className="form-input"
                                        value={couponForm.type}
                                        onChange={e => setCouponForm({ ...couponForm, type: e.target.value })}
                                        style={{ background: 'var(--admin-input-bg)', color: 'white' }}
                                    >
                                        <option value="percent">Percentage (%)</option>
                                        <option value="flat">Flat Amount (₹)</option>
                                    </select>
                                </div>
                                <div className="form-field">
                                    <label className="form-label">DISCOUNT VALUE</label>
                                    <input
                                        className="form-input" type="number" placeholder="Value (e.g. 10 or 50)"
                                        value={couponForm.discount} onChange={e => setCouponForm({ ...couponForm, discount: e.target.value })}
                                    />
                                </div>
                                <button
                                    className="submit-btn" disabled={actionLoading === 'create'}
                                    onClick={() => handleCouponAction('create')}
                                >
                                    {actionLoading === 'create' ? 'GENERATING...' : 'CREATE COUPON'}
                                </button>
                                {actionMsg.text && activeTab === 'coupons' && <p className={`msg-text ${actionMsg.type}`}>{actionMsg.text}</p>}
                            </div>

                            <div className="admin-glass-card">
                                <h2 className="form-title">Active Neural Coupons</h2>
                                <div className="registry-container" style={{ maxHeight: '400px' }}>
                                    <table className="registry-table">
                                        <thead>
                                            <tr>
                                                <th>CODE</th>
                                                <th>TYPE</th>
                                                <th>VALUE</th>
                                                <th>STATUS</th>
                                                <th>ACTION</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {coupons.map((c) => (
                                                <tr key={c.id} className="registry-row">
                                                    <td style={{ fontWeight: 'bold', color: 'var(--admin-primary)' }}>{c.code}</td>
                                                    <td>{c.discount_type.toUpperCase()}</td>
                                                    <td>{c.discount_type === 'percent' ? `${c.discount_value}%` : `₹${c.discount_value}`}</td>
                                                    <td>
                                                        <span className={`access-dot ${c.is_active ? 'access-on' : 'access-off'}`}></span>
                                                        {c.is_active ? 'ACTIVE' : 'INACTIVE'}
                                                    </td>
                                                    <td>
                                                        <button
                                                            className="view-btn"
                                                            style={{ color: 'var(--admin-error)', borderColor: 'rgba(255, 51, 102, 0.3)' }}
                                                            onClick={() => handleCouponAction('delete', c.id)}
                                                        >
                                                            DELETE
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                            {coupons.length === 0 && (
                                                <tr><td colSpan="5" style={{ textAlign: 'center', padding: '40px' }}>No coupons active in neural net.</td></tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="admin-dashboard">
            <aside className="admin-sidebar">
                <div className="sidebar-brand">KRISHNA COMMAND</div>
                <nav className="sidebar-menu">
                    <div className={`menu-item ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>
                        <Icons.Stats /> <span>System Stats</span>
                    </div>
                    <div className={`menu-item ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>
                        <Icons.History /> <span>Neural history</span>
                    </div>
                    <div className={`menu-item ${activeTab === 'access' ? 'active' : ''}`} onClick={() => setActiveTab('access')}>
                        <Icons.Shield /> <span>Access control</span>
                    </div>
                    <div className={`menu-item ${activeTab === 'elevate' ? 'active' : ''}`} onClick={() => setActiveTab('elevate')}>
                        <Icons.Alert /> <span>Elevate admin</span>
                    </div>
                    <div className={`menu-item ${activeTab === 'registry' ? 'active' : ''}`} onClick={() => setActiveTab('registry')}>
                        <Icons.Users /> <span>Node Registry</span>
                    </div>
                    <div className={`menu-item ${activeTab === 'coupons' ? 'active' : ''}`} onClick={() => setActiveTab('coupons')}>
                        <Icons.Tag /> <span>Coupons</span>
                    </div>
                    <div className="menu-item back-home" onClick={() => navigate('/')}>
                        <Icons.Home /> <span>Back to Home</span>
                    </div>
                </nav>
            </aside>

            <main className="admin-main">
                <nav className="admin-top-nav">
                    <h1 className="section-title">
                        {activeTab === 'stats' && 'System Diagnostics'}
                        {activeTab === 'history' && 'Neural Memory Logs'}
                        {activeTab === 'access' && 'Access Control'}
                        {activeTab === 'elevate' && 'Create Admin'}
                        {activeTab === 'registry' && 'Node Registry'}
                        {activeTab === 'coupons' && 'Coupon Management'}
                    </h1>
                    <div className="admin-profile-badge">
                        <span className="ops-badge">ADMIN_OPS</span>
                        <span className="admin-name">Admin {user?.name}</span>
                    </div>
                </nav>

                <div className="content-area">
                    {error && <div className="msg-text error" style={{ marginBottom: '25px', padding: '15px', background: 'rgba(255, 51, 102, 0.1)', borderRadius: '12px', border: '1px solid var(--admin-border)' }}>{error}</div>}
                    {renderContent()}
                </div>
            </main>

            {selectedInteraction && (
                <div className="modal-overlay" onClick={() => setSelectedInteraction(null)}>
                    <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>NEURAL INTERACTION AUDIT</h3>
                            <button className="close-btn" onClick={() => setSelectedInteraction(null)}>×</button>
                        </div>
                        <div className="modal-body">
                            <div className="admin-q-block">
                                <h4>INGESTED PROMPT</h4>
                                <p>{selectedInteraction.question}</p>
                            </div>
                            <div className="admin-a-block">
                                <h4>AI SYNTHESIS RESPONSE</h4>
                                <p>{selectedInteraction.answer}</p>
                            </div>
                            <div className="admin-meta">
                                <span>TIMESTAMP: {new Date(selectedInteraction.timestamp).toLocaleString()}</span>
                                <span>ORIGIN: {selectedInteraction.user_email || 'SECURE_NODE'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdminDashboard;
