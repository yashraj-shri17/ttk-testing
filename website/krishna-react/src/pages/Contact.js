import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import './Contact.css';

function Contact() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        subject: '',
        message: ''
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        alert('Thank you for contacting us! We will get back to you soon.');
        setFormData({ name: '', email: '', subject: '', message: '' });
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    return (
        <div className="page-container contact-page">
            <Navbar />

            <section className="contact-hero">
                <div className="container">
                    <div className="contact-hero-content">
                        <span className="section-badge">Get In Touch</span>
                        <h1 className="contact-title">
                            We're Here to <span className="gradient-text">Help</span>
                        </h1>
                        <p className="contact-subtitle">
                            Have questions or feedback? We'd love to hear from you.
                        </p>
                    </div>
                </div>
            </section>

            <section className="contact-content">
                <div className="container">
                    <div className="contact-grid">
                        <div className="contact-info">
                            <h2>Contact Information</h2>
                            <p className="info-subtitle">Fill out the form and our team will get back to you within 24 hours.</p>

                            <div className="contact-cards">
                                <div className="contact-card">
                                    <div className="contact-icon">📧</div>
                                    <h3>Email</h3>
                                    <p>support@talktokrishna.com</p>
                                </div>

                                <div className="contact-card">
                                    <div className="contact-icon">💬</div>
                                    <h3>Live Chat</h3>
                                    <p>Available 24/7</p>
                                </div>

                                <div className="contact-card">
                                    <div className="contact-icon">🌐</div>
                                    <h3>Social Media</h3>
                                    <div className="social-links">
                                        <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="social-link">Twitter</a>
                                        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="social-link">LinkedIn</a>
                                        <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" className="social-link">Instagram</a>
                                    </div>
                                </div>
                            </div>

                            <div className="faq-section">
                                <h3>Frequently Asked Questions</h3>
                                <div className="faq-item">
                                    <strong>How does the AI work?</strong>
                                    <p>Our AI uses RAG technology to search through 700+ authentic Bhagavad Gita verses.</p>
                                </div>
                                <div className="faq-item">
                                    <strong>Is it free to use?</strong>
                                    <p>Yes! Talk to Krishna is completely free for all users.</p>
                                </div>
                                <div className="faq-item">
                                    <strong>What languages are supported?</strong>
                                    <p>Currently we support English and Hindi (Hinglish).</p>
                                </div>
                            </div>
                        </div>

                        <div className="contact-form-wrapper">
                            <form onSubmit={handleSubmit} className="contact-form">
                                <h2>Send us a Message</h2>

                                <div className="form-group">
                                    <label>Your Name</label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleChange}
                                        placeholder="Arjuna"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Email Address</label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleChange}
                                        placeholder="you@example.com"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Subject</label>
                                    <input
                                        type="text"
                                        name="subject"
                                        value={formData.subject}
                                        onChange={handleChange}
                                        placeholder="How can we help?"
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Message</label>
                                    <textarea
                                        name="message"
                                        value={formData.message}
                                        onChange={handleChange}
                                        placeholder="Tell us more about your question or feedback..."
                                        rows="5"
                                        required
                                    ></textarea>
                                </div>

                                <button type="submit" className="btn-premium-primary btn-large">
                                    <span className="btn-icon">📨</span>
                                    Send Message
                                    <span className="btn-arrow">→</span>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default Contact;
