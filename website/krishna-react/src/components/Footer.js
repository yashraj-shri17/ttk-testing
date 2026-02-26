import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="footer-premium">
            <div className="container">
                <div className="footer-content">
                    <div className="footer-brand">
                        <div className="footer-logo">
                            <span className="logo-icon">🕉️</span>
                            <span>Talk To Krishna</span>
                        </div>
                        <p>Ancient wisdom meets modern technology</p>
                    </div>
                    <div className="footer-links">
                        <Link to="/about">About</Link>
                        <Link to="/contact">Contact</Link>
                        <Link to="/privacy">Privacy</Link>
                        <Link to="/login">Login</Link>
                        <Link to="/signup">Sign Up</Link>
                    </div>
                </div>
                <div className="footer-bottom">
                    <p>© 2026 Talk To Krishna. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
