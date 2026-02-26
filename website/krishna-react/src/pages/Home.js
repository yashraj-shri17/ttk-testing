import React, { useEffect, useRef } from 'react';
import Navbar from '../components/Navbar';
import { useNavigate } from 'react-router-dom';
import './Home.css';

function Home() {
    const navigate = useNavigate();
    const observerRef = useRef(null);

    useEffect(() => {
        // Intersection Observer for scroll animations
        observerRef.current = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animate-in');
                    }
                });
            },
            { threshold: 0.1 }
        );

        // Observe all animated elements
        const animatedElements = document.querySelectorAll('.fade-in-section');
        animatedElements.forEach((el) => observerRef.current.observe(el));

        return () => {
            if (observerRef.current) {
                observerRef.current.disconnect();
            }
        };
    }, []);

    return (
        <div className="home-page">
            <Navbar />

            {/* Floating Elements Background */}
            <div className="floating-elements">
                <div className="float-element om-symbol">🕉️</div>
                <div className="float-element lotus">🪷</div>
                <div className="float-element peacock">🦚</div>
                <div className="float-element om-symbol-2">ॐ</div>
            </div>

            {/* Hero Section */}
            <section className="hero-section-premium">
                <div className="container hero-grid">
                    <div className="hero-content-left">
                        <div className="badge-premium">
                            <span className="badge-dot"></span>
                            AI-Powered Spiritual Guidance
                        </div>

                        <h1 className="hero-headline-premium">
                            Ancient Wisdom,
                            <br />
                            <span className="gradient-text-animated">Modern Voice</span>
                        </h1>

                        <p className="hero-description-premium">
                            Experience the timeless teachings of the Bhagavad Gita through cutting-edge AI voice technology.
                            Get personalized spiritual guidance in real-time conversations with Krishna.
                        </p>

                        <div className="hero-cta-group">
                            <button className="btn-premium-primary" onClick={() => navigate('/chat')}>
                                <span className="btn-icon">🎙️</span>
                                Start Conversation
                                <span className="btn-arrow">→</span>
                            </button>
                            <button className="btn-premium-secondary" onClick={() => navigate('/about')}>
                                <span className="btn-icon">📖</span>
                                Learn More
                            </button>
                        </div>

                        <div className="stats-row">
                            <div className="stat-item">
                                <div className="stat-number">700+</div>
                                <div className="stat-label">Shlokas</div>
                            </div>
                            <div className="stat-divider"></div>
                            <div className="stat-item">
                                <div className="stat-number">24/7</div>
                                <div className="stat-label">Available</div>
                            </div>
                            <div className="stat-divider"></div>
                            <div className="stat-item">
                                <div className="stat-number">∞</div>
                                <div className="stat-label">Wisdom</div>
                            </div>
                        </div>
                    </div>

                    <div className="hero-visual-right">
                        {/* 3D Orb Illustration */}
                        <div className="orb-container-3d">
                            <div className="orb-main">
                                <div className="orb-inner-glow"></div>
                                <div className="orb-particles">
                                    {[...Array(20)].map((_, i) => (
                                        <div key={i} className={`particle p-${i}`}></div>
                                    ))}
                                </div>
                                <div className="orb-rings">
                                    <div className="ring ring-1"></div>
                                    <div className="ring ring-2"></div>
                                    <div className="ring ring-3"></div>
                                </div>
                                <div className="orb-center-icon">🕉️</div>
                            </div>

                            {/* Floating Cards */}
                            <div className="floating-card card-1">
                                <div className="card-icon">🎯</div>
                                <div className="card-content">
                                    <strong>Instant Answers</strong>
                                    <span>Real-time guidance</span>
                                </div>
                            </div>

                            <div className="floating-card card-2">
                                <div className="card-icon">🧘</div>
                                <div className="card-content">
                                    <strong>Spiritual Growth</strong>
                                    <span>Personal journey</span>
                                </div>
                            </div>

                            <div className="floating-card card-3">
                                <div className="card-icon">💬</div>
                                <div className="card-content">
                                    <strong>Voice Chat</strong>
                                    <span>Natural conversation</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section - Premium Design */}
            <section className="features-section-premium fade-in-section">
                <div className="container">
                    <div className="section-header-premium">
                        <span className="section-badge">Features</span>
                        <h2 className="section-title-premium">
                            Why Choose <span className="gradient-text">Talk to Krishna</span>
                        </h2>
                        <p className="section-subtitle">
                            Combining ancient wisdom with modern AI to provide you with personalized spiritual guidance
                        </p>
                    </div>

                    <div className="features-grid-premium">
                        <div className="feature-card-premium">
                            <div className="feature-icon-wrapper">
                                <div className="feature-icon-bg"></div>
                                <div className="feature-icon">🎙️</div>
                            </div>
                            <h3>Voice-to-Voice AI</h3>
                            <p>Speak naturally in Hindi or English and receive authentic, spoken responses powered by neural TTS technology.</p>
                            <div className="feature-tags">
                                <span className="tag">Real-time</span>
                                <span className="tag">Natural</span>
                            </div>
                        </div>

                        <div className="feature-card-premium featured">
                            <div className="featured-badge">Most Popular</div>
                            <div className="feature-icon-wrapper">
                                <div className="feature-icon-bg"></div>
                                <div className="feature-icon">📜</div>
                            </div>
                            <h3>Scriptural Accuracy</h3>
                            <p>Every answer is grounded in authentic verses from the Bhagavad Gita using advanced RAG architecture.</p>
                            <div className="feature-tags">
                                <span className="tag">Verified</span>
                                <span className="tag">Authentic</span>
                            </div>
                        </div>

                        <div className="feature-card-premium">
                            <div className="feature-icon-wrapper">
                                <div className="feature-icon-bg"></div>
                                <div className="feature-icon">✨</div>
                            </div>
                            <h3>Personalized Wisdom</h3>
                            <p>Get advice tailored to your specific life situations, emotional state, and spiritual journey.</p>
                            <div className="feature-tags">
                                <span className="tag">Custom</span>
                                <span className="tag">Contextual</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* How It Works Section */}
            <section className="how-it-works-section fade-in-section">
                <div className="container">
                    <div className="section-header-premium">
                        <span className="section-badge">Process</span>
                        <h2 className="section-title-premium">
                            How It <span className="gradient-text">Works</span>
                        </h2>
                    </div>

                    <div className="steps-container">
                        <div className="step-card">
                            <div className="step-number">01</div>
                            <div className="step-icon">🎤</div>
                            <h3>Speak Your Question</h3>
                            <p>Ask anything about life, dharma, karma, or any spiritual guidance you seek</p>
                        </div>

                        <div className="step-connector"></div>

                        <div className="step-card">
                            <div className="step-number">02</div>
                            <div className="step-icon">🧠</div>
                            <h3>AI Processes</h3>
                            <p>Our RAG system searches through 700+ shlokas to find the perfect answer</p>
                        </div>

                        <div className="step-connector"></div>

                        <div className="step-card">
                            <div className="step-number">03</div>
                            <div className="step-icon">🔊</div>
                            <h3>Receive Wisdom</h3>
                            <p>Hear Krishna's voice with authentic guidance based on the Gita</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="cta-section-premium fade-in-section">
                <div className="container">
                    <div className="cta-card-premium">
                        <div className="cta-content">
                            <h2>Ready to Begin Your Spiritual Journey?</h2>
                            <p>Join thousands seeking wisdom and guidance through AI-powered conversations</p>
                            <button className="btn-premium-primary btn-large" onClick={() => navigate('/chat')}>
                                <span className="btn-icon">🕉️</span>
                                Start Talking to Krishna
                                <span className="btn-arrow">→</span>
                            </button>
                        </div>
                        <div className="cta-decoration">
                            <div className="decoration-circle c1"></div>
                            <div className="decoration-circle c2"></div>
                            <div className="decoration-circle c3"></div>
                        </div>
                    </div>
                </div>
            </section>




        </div>
    );
}

export default Home;
