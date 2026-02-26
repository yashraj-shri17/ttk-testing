import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import './Navbar.css';

function Navbar() {
    const location = useLocation();
    const { user } = useAuth();
    const [scrolled, setScrolled] = useState(false);
    const [isOpen, setIsOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 50);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const toggleMenu = () => setIsOpen(!isOpen);

    const closeMenu = () => setIsOpen(false);

    const getInitials = (name) => {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <nav className={`navbar glass ${scrolled ? 'scrolled' : ''}`}>
            <div className="container navbar-content">
                <Link to="/" className="navbar-logo" onClick={closeMenu}>
                    <span className="logo-icon">🕉️</span>
                    <span className="logo-text">Talk To Krishna</span>
                </Link>

                <div className="mobile-toggle" onClick={toggleMenu}>
                    <div className={`hamburger ${isOpen ? 'active' : ''}`}>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>

                <div className={`navbar-links ${isOpen ? 'active' : ''}`}>
                    <Link to="/" className={`nav-link ${location.pathname === '/' ? 'active' : ''}`} onClick={closeMenu}>Home</Link>
                    <Link to="/about" className={`nav-link ${location.pathname === '/about' ? 'active' : ''}`} onClick={closeMenu}>About</Link>
                    <Link to="/contact" className={`nav-link ${location.pathname === '/contact' ? 'active' : ''}`} onClick={closeMenu}>Contact</Link>
                    <Link to="/privacy" className={`nav-link ${location.pathname === '/privacy' ? 'active' : ''}`} onClick={closeMenu}>Privacy</Link>

                    {user ? (
                        <>
                            <Link to="/chat" className={`nav-link ${location.pathname === '/chat' ? 'active' : ''}`} onClick={closeMenu}>Chat</Link>
                            <Link to="/profile" className="nav-link profile-link" onClick={closeMenu}>
                                <div className="nav-avatar">
                                    {getInitials(user.name)}
                                </div>
                                <span>{user.name.split(' ')[0]}</span>
                            </Link>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className={`nav-link ${location.pathname === '/login' ? 'active' : ''}`} onClick={closeMenu}>Login</Link>
                            <Link to="/signup" className="btn-primary" onClick={closeMenu}>Sign Up</Link>
                        </>
                    )}

                    <ThemeToggle />
                </div>
            </div>
        </nav>
    );
}

export default Navbar;
