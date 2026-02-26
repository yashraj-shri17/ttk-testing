import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { useNavigate, Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../config/api';
import './Auth.css';

function Signup() {
    const navigate = useNavigate();

    // Form state
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
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

    // Calculate password strength in real-time
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

    const handleSignup = async (e) => {
        e.preventDefault();
        setError('');

        // Client-side validation
        if (passwordStrength.score < 5) {
            setError('Please meet all password requirements');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(API_ENDPOINTS.SIGNUP, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name, email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                // Auto redirect to login after signup
                navigate('/login', { state: { message: 'Account created! Please log in.' } });
            } else {
                setError(data.error || 'Signup failed');
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
                    <h2>Create Account</h2>
                    <p>Start your journey with Krishna</p>
                </div>

                {error && <div className="error-message">{error}</div>}

                <form onSubmit={handleSignup} className="auth-form">
                    <div className="form-group">
                        <label>Full Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Arjuna"
                            required
                            disabled={loading}
                            minLength="2"
                        />
                    </div>

                    <div className="form-group">
                        <label>Email Address</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@example.com"
                            required
                            disabled={loading}
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                disabled={loading}
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

                        {/* Password Requirements Checklist */}
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

                    <button
                        type="submit"
                        className="btn-primary btn-block"
                        disabled={loading || (password && passwordStrength.score < 5)}
                    >
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Creating Account...
                            </>
                        ) : 'Sign Up'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already have an account? <Link to="/login">Log In</Link></p>
                </div>
            </div>
        </div>
    );
}

export default Signup;
