import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import { Link } from 'react-router-dom';
import { API_ENDPOINTS } from '../config/api';
import './Auth.css';

function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await fetch(API_ENDPOINTS.FORGOT_PASSWORD, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email }),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess(true);
            } else {
                setError(data.error || 'Request failed');
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
                    <h2>Forgot Password?</h2>
                    <p>Enter your email to reset your password</p>
                </div>

                {error && <div className="error-message">{error}</div>}

                {success ? (
                    <div className="success-container">
                        <div className="success-message">
                            Check your email for the reset link!
                        </div>



                        <div className="auth-footer" style={{ marginTop: '20px' }}>
                            <p><Link to="/login">Back to Login</Link></p>
                        </div>
                    </div>
                ) : (
                    <>
                        <form onSubmit={handleSubmit} className="auth-form">
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

                            <button
                                type="submit"
                                className="btn-primary btn-block"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner"></span>
                                        Sending...
                                    </>
                                ) : 'Send Reset Link'}
                            </button>
                        </form>

                        <div className="auth-footer">
                            <p>Remember your password? <Link to="/login">Log In</Link></p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export default ForgotPassword;
