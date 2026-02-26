import React from 'react';
import Navbar from '../components/Navbar';
import './Privacy.css';

function Privacy() {
    return (
        <div className="page-container privacy-page">
            <Navbar />

            <section className="privacy-hero">
                <div className="container">
                    <div className="privacy-hero-content">
                        <span className="section-badge">Legal</span>
                        <h1 className="privacy-title">
                            Privacy <span className="gradient-text">Policy</span>
                        </h1>
                        <p className="privacy-subtitle">
                            Last updated: February 6, 2026
                        </p>
                    </div>
                </div>
            </section>

            <section className="privacy-content">
                <div className="container">
                    <div className="privacy-wrapper">
                        <div className="privacy-section">
                            <h2>Introduction</h2>
                            <p>
                                Welcome to Talk to Krishna. We respect your privacy and are committed to protecting your personal data.
                                This privacy policy will inform you about how we look after your personal data when you visit our website
                                and tell you about your privacy rights.
                            </p>
                        </div>

                        <div className="privacy-section">
                            <h2>Information We Collect</h2>
                            <p>We may collect, use, store and transfer different kinds of personal data about you:</p>
                            <ul>
                                <li><strong>Identity Data:</strong> First name, last name, username</li>
                                <li><strong>Contact Data:</strong> Email address</li>
                                <li><strong>Technical Data:</strong> IP address, browser type, device information</li>
                                <li><strong>Usage Data:</strong> Information about how you use our website and services</li>
                                <li><strong>Conversation Data:</strong> Your questions and interactions with the AI</li>
                            </ul>
                        </div>

                        <div className="privacy-section">
                            <h2>How We Use Your Information</h2>
                            <p>We use your personal data for the following purposes:</p>
                            <ul>
                                <li>To provide and maintain our service</li>
                                <li>To improve and personalize your experience</li>
                                <li>To communicate with you about updates and support</li>
                                <li>To analyze usage patterns and improve our AI</li>
                                <li>To ensure the security of our platform</li>
                            </ul>
                        </div>

                        <div className="privacy-section">
                            <h2>Data Security</h2>
                            <p>
                                We have implemented appropriate security measures to prevent your personal data from being accidentally lost,
                                used, or accessed in an unauthorized way. We limit access to your personal data to those employees, agents,
                                contractors, and other third parties who have a business need to know.
                            </p>
                        </div>

                        <div className="privacy-section">
                            <h2>Your Privacy Rights</h2>
                            <p>Under data protection laws, you have rights including:</p>
                            <ul>
                                <li><strong>Right to Access:</strong> Request copies of your personal data</li>
                                <li><strong>Right to Rectification:</strong> Request correction of inaccurate data</li>
                                <li><strong>Right to Erasure:</strong> Request deletion of your personal data</li>
                                <li><strong>Right to Restrict Processing:</strong> Request limitation of processing</li>
                                <li><strong>Right to Data Portability:</strong> Request transfer of your data</li>
                                <li><strong>Right to Object:</strong> Object to processing of your personal data</li>
                            </ul>
                        </div>

                        <div className="privacy-section">
                            <h2>Cookies</h2>
                            <p>
                                We use cookies and similar tracking technologies to track activity on our service and store certain information.
                                You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent.
                            </p>
                        </div>

                        <div className="privacy-section">
                            <h2>Third-Party Services</h2>
                            <p>We may employ third-party companies and individuals to facilitate our service, including:</p>
                            <ul>
                                <li>Cloud hosting providers</li>
                                <li>Analytics services</li>
                                <li>AI and machine learning platforms</li>
                                <li>Email service providers</li>
                            </ul>
                            <p>These third parties have access to your personal data only to perform specific tasks on our behalf and are obligated not to disclose or use it for any other purpose.</p>
                        </div>

                        <div className="privacy-section">
                            <h2>Children's Privacy</h2>
                            <p>
                                Our service is not intended for children under the age of 13. We do not knowingly collect personally
                                identifiable information from children under 13. If you are a parent or guardian and you are aware that
                                your child has provided us with personal data, please contact us.
                            </p>
                        </div>

                        <div className="privacy-section">
                            <h2>Changes to This Privacy Policy</h2>
                            <p>
                                We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new
                                Privacy Policy on this page and updating the "Last updated" date at the top of this Privacy Policy.
                            </p>
                        </div>

                        <div className="privacy-section">
                            <h2>Contact Us</h2>
                            <p>If you have any questions about this Privacy Policy, please contact us:</p>
                            <ul>
                                <li>Email: privacy@talktokrishna.com</li>
                                <li>Website: <a href="/contact">Contact Form</a></li>
                            </ul>
                        </div>

                        <div className="privacy-footer-note">
                            <p>
                                <strong>Note:</strong> Your spiritual journey is personal to you. We respect your privacy and never share
                                your conversations or personal information with third parties for marketing purposes.
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default Privacy;
