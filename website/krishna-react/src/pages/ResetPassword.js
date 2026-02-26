import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../config/api';
import './Auth.css';

function ResetPassword() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [token, setToken] = useState('');
    const [passwordStrength, setPasswordStrength] = useState({
        score: 0,
        label: '',
        color: '',
        checks: {
            length: false,
            uppercase: false,
            lowercase: false,
            number: false,
            special: false
        }
    });

    useEffect(() => {
        const tokenFromUrl = searchParams.get('token');
        if (!tokenFromUrl) {
            setError('Invalid reset link. Please request a new password reset.');
        } else {
            setToken(tokenFromUrl);
        }
    }, [searchParams]);

    // Calculate password strength
    useEffect(() => {
        if (!password) {
            setPasswordStrength({
                score: 0,
                label: '',
                color: '',
                checks: {
                    length: false,
                    uppercase: false,
                    lowercase: false,
                    number: false,
                    special: false
                }
            });
            return;
        }

        const checks = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };

        const score = Object.values(checks).filter(Boolean).length;

        let label = '';
        let color = '';

        if (score === 0) {
            label = '';
            color = '';
        } else if (score <= 2) {
            label = 'Weak';
            color = '#ef4444';
        } else if (score === 3) {
            label = 'Fair';
            color = '#f59e0b';
        } else if (score === 4) {
            label = 'Good';
            color = '#3b82f6';
        } else {
            label = 'Strong';
            color = '#10b981';
        }

        setPasswordStrength({ score, label, color, checks });
    }, [password]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        if (!token) {
            setError('Invalid reset link');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (passwordStrength.score < 5) {
            setError('Please meet all password requirements');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(API_ENDPOINTS.RESET_PASSWORD, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token, password }),
            });

            const data = await response.json();

            if (response.ok) {
                navigate('/login', { state: { message: 'Password reset successful! Please log in with your new password.' } });
            } else {
                setError(data.error || 'Password reset failed');
            }
        } catch (err) {
            setError('Connection error. Please check your internet and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container auth-page">
            <Navbar />
            <div className="auth-card glass">
                <div className="auth-header">
                    <h2>Reset Password</h2>
                    <p>Enter your new password</p>
                </div>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label>New Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={loading || !token}
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowPassword(!showPassword)}
                                tabIndex="-1"
                            >
                                {showPassword ? '👁️' : '👁️‍🗨️'}
                            </button>
                        </div>

                        {/* Password Strength Meter */}
                        {password && (
                            <div className="password-strength">
                                <div className="strength-bars">
                                    {[1, 2, 3, 4, 5].map((bar) => (
                                        <div
                                            key={bar}
                                            className={`strength-bar ${bar <= passwordStrength.score ? 'active' : ''}`}
                                            style={{
                                                backgroundColor: bar <= passwordStrength.score ? passwordStrength.color : '#e5e7eb'
                                            }}
                                        ></div>
                                    ))}
                                </div>
                                {passwordStrength.label && (
                                    <span className="strength-label" style={{ color: passwordStrength.color }}>
                                        {passwordStrength.label}
                                    </span>
                                )}
                            </div>
                        )}

                        {/* Password Requirements */}
                        {password && (
                            <div className="password-requirements">
                                <div className={`requirement ${passwordStrength.checks.length ? 'met' : ''}`}>
                                    {passwordStrength.checks.length ? '✓' : '○'} At least 8 characters
                                </div>
                                <div className={`requirement ${passwordStrength.checks.uppercase ? 'met' : ''}`}>
                                    {passwordStrength.checks.uppercase ? '✓' : '○'} One uppercase letter
                                </div>
                                <div className={`requirement ${passwordStrength.checks.lowercase ? 'met' : ''}`}>
                                    {passwordStrength.checks.lowercase ? '✓' : '○'} One lowercase letter
                                </div>
                                <div className={`requirement ${passwordStrength.checks.number ? 'met' : ''}`}>
                                    {passwordStrength.checks.number ? '✓' : '○'} One number
                                </div>
                                <div className={`requirement ${passwordStrength.checks.special ? 'met' : ''}`}>
                                    {passwordStrength.checks.special ? '✓' : '○'} One special character
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label>Confirm New Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showConfirmPassword ? "text" : "password"}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={loading || !token}
                            />
                            <button
                                type="button"
                                className="password-toggle"
                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                tabIndex="-1"
                            >
                                {showConfirmPassword ? '👁️' : '👁️‍🗨️'}
                            </button>
                        </div>
                        {confirmPassword && password !== confirmPassword && (
                            <p style={{ color: '#ef4444', fontSize: '0.8rem', marginTop: '6px' }}>
                                Passwords do not match
                            </p>
                        )}
                    </div>

                    <button
                        type="submit"
                        className="btn-primary btn-block"
                        disabled={loading || !token || (password && passwordStrength.score < 5) || password !== confirmPassword}
                    >
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Resetting Password...
                            </>
                        ) : 'Reset Password'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Remember your password? <Link to="/login">Log In</Link></p>
                </div>
            </div>
        </div>
    );
}

export default ResetPassword;
