import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

function Profile() {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    if (!user) {
        navigate('/login');
        return null;
    }

    // Get user initials for avatar
    const getInitials = (name) => {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    // Get member since date (from user creation or current date)
    const getMemberSince = () => {
        // In a real app, this would come from the database
        return new Date().toLocaleDateString('en-US', {
            month: 'long',
            year: 'numeric'
        });
    };

    return (
        <div className="page-container profile-page">
            <Navbar />

            <div className="profile-container">
                {/* Profile Header */}
                <div className="profile-header glass">
                    <div className="profile-avatar">
                        <div className="avatar-circle">
                            {getInitials(user.name)}
                        </div>
                        <div className="avatar-glow"></div>
                    </div>

                    <div className="profile-info">
                        <h1 className="profile-name">{user.name}</h1>
                        <p className="profile-email">{user.email}</p>
                        <p className="profile-member-since">
                            🕉️ Seeker since {getMemberSince()}
                        </p>
                    </div>
                </div>

                {/* Profile Stats */}
                <div className="profile-stats">
                    <div className="stat-card glass">
                        <div className="stat-icon">💬</div>
                        <div className="stat-value">--</div>
                        <div className="stat-label">Conversations</div>
                    </div>

                    <div className="stat-card glass">
                        <div className="stat-icon">📖</div>
                        <div className="stat-value">--</div>
                        <div className="stat-label">Shlokas Learned</div>
                    </div>

                    <div className="stat-card glass">
                        <div className="stat-icon">⏱️</div>
                        <div className="stat-value">--</div>
                        <div className="stat-label">Hours of Wisdom</div>
                    </div>
                </div>

                {/* Profile Actions */}
                <div className="profile-actions">
                    <div className="action-card glass">
                        <h3>Account Settings</h3>
                        <div className="action-list">
                            <button className="action-item" onClick={() => navigate('/chat')}>
                                <span className="action-icon">💬</span>
                                <span className="action-text">Continue Conversation</span>
                                <span className="action-arrow">→</span>
                            </button>

                            <button className="action-item" disabled>
                                <span className="action-icon">✏️</span>
                                <span className="action-text">Edit Profile</span>
                                <span className="action-badge">Coming Soon</span>
                            </button>

                            <button className="action-item" disabled>
                                <span className="action-icon">🔔</span>
                                <span className="action-text">Notifications</span>
                                <span className="action-badge">Coming Soon</span>
                            </button>

                            <button className="action-item" onClick={() => navigate('/reset-password')}>
                                <span className="action-icon">🔒</span>
                                <span className="action-text">Change Password</span>
                                <span className="action-arrow">→</span>
                            </button>
                        </div>
                    </div>

                    <div className="action-card glass danger-zone">
                        <h3>Danger Zone</h3>
                        <div className="action-list">
                            <button
                                className="action-item danger"
                                onClick={() => setShowLogoutConfirm(true)}
                            >
                                <span className="action-icon">🚪</span>
                                <span className="action-text">Logout</span>
                                <span className="action-arrow">→</span>
                            </button>

                            <button className="action-item danger" disabled>
                                <span className="action-icon">🗑️</span>
                                <span className="action-text">Delete Account</span>
                                <span className="action-badge">Coming Soon</span>
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Logout Confirmation Dialog */}
            {showLogoutConfirm && (
                <div className="confirm-overlay" onClick={() => setShowLogoutConfirm(false)}>
                    <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="confirm-icon logout-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Logout Confirmation</h3>
                        <p>Are you sure you want to logout? You can always come back for more divine wisdom.</p>
                        <div className="confirm-actions">
                            <button className="btn-cancel" onClick={() => setShowLogoutConfirm(false)}>
                                Stay
                            </button>
                            <button className="btn-confirm logout-btn" onClick={handleLogout}>
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Profile;
