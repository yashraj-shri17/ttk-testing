import React from 'react';
import Navbar from '../components/Navbar';
import './About.css';

function About() {
    return (
        <div className="page-container about-page">
            <Navbar />

            <section className="about-hero">
                <div className="container">
                    <div className="about-hero-content">
                        <span className="section-badge">Our Mission</span>
                        <h1 className="about-title">
                            Bridging <span className="gradient-text">Ancient Wisdom</span>
                            <br />& Modern Technology
                        </h1>
                        <p className="about-subtitle">
                            Making the timeless teachings of the Bhagavad Gita accessible to everyone through the power of AI
                        </p>
                    </div>
                </div>
            </section>

            <section className="vision-section">
                <div className="container">
                    <div className="vision-grid">
                        <div className="vision-content">
                            <h2 className="section-heading">The Vision</h2>
                            <p className="vision-text">
                                In a world full of noise and confusion, finding clear, ethical, and spiritual guidance can be difficult.
                                "Talk to Krishna" was born from the idea of making the timeless wisdom of the Bhagavad Gita accessible
                                to everyone, everywhere, in real-time.
                            </p>
                            <p className="vision-text">
                                By combining advanced Large Language Models (LLMs) with authentic scriptural data, we have created an
                                entity that doesn't just answer questions—it guides you with the compassion and authority of the Divine.
                            </p>

                            <div className="vision-stats">
                                <div className="vision-stat-card">
                                    <div className="stat-icon">📜</div>
                                    <div className="stat-info">
                                        <div className="stat-value">700+</div>
                                        <div className="stat-desc">Authentic Shlokas</div>
                                    </div>
                                </div>
                                <div className="vision-stat-card">
                                    <div className="stat-icon">🌍</div>
                                    <div className="stat-info">
                                        <div className="stat-value">Global</div>
                                        <div className="stat-desc">Accessibility</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="vision-visual">
                            <div className="visual-card">
                                <div className="visual-icon">🧠</div>
                                <div className="visual-plus">+</div>
                                <div className="visual-icon">📖</div>
                                <div className="visual-equals">=</div>
                                <div className="visual-icon">✨</div>
                            </div>
                            <p className="visual-caption">AI meets Ancient Scripture</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="tech-section">
                <div className="container">
                    <div className="section-header-center">
                        <span className="section-badge">Technology</span>
                        <h2 className="section-heading-center">
                            Powered by <span className="gradient-text">Cutting-Edge AI</span>
                        </h2>
                        <p className="section-desc">
                            Our platform combines multiple advanced technologies to deliver authentic spiritual guidance
                        </p>
                    </div>

                    <div className="tech-grid">
                        <div className="tech-card">
                            <div className="tech-icon-wrapper">
                                <div className="tech-icon">🔍</div>
                            </div>
                            <h3>RAG Architecture</h3>
                            <p>Retrieval Augmented Generation ensures every answer is grounded in actual Shlokas from the Bhagavad Gita.</p>
                            <ul className="tech-features">
                                <li>Semantic search</li>
                                <li>Context-aware retrieval</li>
                                <li>Verified sources</li>
                            </ul>
                        </div>

                        <div className="tech-card featured-tech">
                            <div className="tech-badge">Core Technology</div>
                            <div className="tech-icon-wrapper">
                                <div className="tech-icon">🎙️</div>
                            </div>
                            <h3>Neural Voice</h3>
                            <p>State-of-the-art Text-to-Speech models provide a lifelike, calming auditory experience in Hindi.</p>
                            <ul className="tech-features">
                                <li>Natural intonation</li>
                                <li>Emotional expression</li>
                                <li>Real-time generation</li>
                            </ul>
                        </div>

                        <div className="tech-card">
                            <div className="tech-icon-wrapper">
                                <div className="tech-icon">🧠</div>
                            </div>
                            <h3>LLM Processing</h3>
                            <p>Advanced language models understand the intent behind your questions, not just keywords.</p>
                            <ul className="tech-features">
                                <li>Context understanding</li>
                                <li>Multilingual support</li>
                                <li>Personalized responses</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            <section className="values-section">
                <div className="container">
                    <div className="section-header-center">
                        <span className="section-badge">Our Values</span>
                        <h2 className="section-heading-center">
                            Built on <span className="gradient-text">Authenticity</span>
                        </h2>
                    </div>

                    <div className="values-grid">
                        <div className="value-card">
                            <div className="value-number">01</div>
                            <h3>Scriptural Accuracy</h3>
                            <p>Every response is verified against authentic Bhagavad Gita verses. We never fabricate or misrepresent the teachings.</p>
                        </div>
                        <div className="value-card">
                            <div className="value-number">02</div>
                            <h3>Accessibility</h3>
                            <p>Making ancient wisdom available to everyone, regardless of their background or technical expertise.</p>
                        </div>
                        <div className="value-card">
                            <div className="value-number">03</div>
                            <h3>Privacy</h3>
                            <p>Your spiritual journey is personal. We respect your privacy and never share your conversations.</p>
                        </div>
                        <div className="value-card">
                            <div className="value-number">04</div>
                            <h3>Innovation</h3>
                            <p>Continuously improving our technology to provide better, more meaningful spiritual guidance.</p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="founder-section">
                <div className="container">
                    <div className="section-header-center">
                        <span className="section-badge">Leadership</span>
                        <h2 className="section-heading-center">
                            Meet the <span className="gradient-text">Founder</span>
                        </h2>
                    </div>

                    <div className="founder-card">
                        <div className="founder-image-wrapper">
                            <div className="founder-image-bg"></div>
                            <img
                                src="/founder.jpg"
                                alt="Abhishek Chola - Founder & CEO"
                                className="founder-image"
                                onError={(e) => {
                                    e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="400"%3E%3Crect fill="%23f0f0f0" width="400" height="400"/%3E%3Ctext fill="%23999" font-family="sans-serif" font-size="24" dy="10.5" font-weight="bold" x="50%25" y="50%25" text-anchor="middle"%3EFounder%3C/text%3E%3C/svg%3E';
                                }}
                            />
                        </div>
                        <div className="founder-content">
                            <h3 className="founder-name">Abhishek Chola</h3>
                            <p className="founder-title">Founder & CEO, Just Learn</p>
                            <div className="founder-divider"></div>
                            <p className="founder-bio">
                                A global EdTech and SkillTech innovator with a mission to democratize education and future-ready skills.
                                Abhishek leads strategic initiatives across multiple countries, fostering collaborations in education and technology.
                            </p>
                            <p className="founder-bio">
                                His leadership focuses on scalable learning solutions powered by AI, AR/VR, and immersive technologies,
                                bringing cutting-edge innovation to learners worldwide.
                            </p>
                            <div className="founder-highlights">
                                <div className="highlight-item">
                                    <div className="highlight-icon">🌍</div>
                                    <div className="highlight-text">
                                        <strong>Global Impact</strong>
                                        <span>Multi-country operations</span>
                                    </div>
                                </div>
                                <div className="highlight-item">
                                    <div className="highlight-icon">🚀</div>
                                    <div className="highlight-text">
                                        <strong>Innovation Leader</strong>
                                        <span>AI, AR/VR, Immersive Tech</span>
                                    </div>
                                </div>
                                <div className="highlight-item">
                                    <div className="highlight-icon">🎓</div>
                                    <div className="highlight-text">
                                        <strong>EdTech Pioneer</strong>
                                        <span>Democratizing education</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="cta-about">
                <div className="container">
                    <div className="cta-about-card">
                        <h2>Ready to Experience Divine Wisdom?</h2>
                        <p>Start your spiritual journey with AI-powered guidance from the Bhagavad Gita</p>
                        <button className="btn-premium-primary btn-large" onClick={() => window.location.href = '/chat'}>
                            <span className="btn-icon">🕉️</span>
                            Talk to Krishna Now
                            <span className="btn-arrow">→</span>
                        </button>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default About;
