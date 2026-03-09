import React from 'react';
import Navbar from '../components/Navbar';
import { useNavigate } from 'react-router-dom';
import './Pricing.css';

function Pricing() {
    const navigate = useNavigate();

    const plans = [
        {
            id: '1-month',
            title: '1 Month',
            price: '₹199',
            period: '/mo',
            description: 'Perfect for trying out the divine spiritual journey.',
            features: [
                'Unlimited Voice Chats',
                'Access to all 700+ Shlokas',
                'Personalized Guidance',
                '24/7 Availability',
                'Basic Support'
            ],
            isPopular: false,
            buttonText: 'Choose 1 Month',
            gradient: 'plan-basic'
        },
        {
            id: '3-months',
            title: '3 Months',
            price: '₹499',
            period: '/3 mos',
            description: 'Our most popular plan for sustained spiritual growth.',
            features: [
                'Everything in 1 Month',
                'Prioritized Voice Generation',
                'Save Conversations (History)',
                'Curated Daily Quotes',
                'Priority Support'
            ],
            isPopular: true,
            buttonText: 'Choose 3 Months',
            gradient: 'plan-premium'
        },
        {
            id: '6-months',
            title: '6 Months',
            price: '₹899',
            period: '/6 mos',
            description: 'A deep commitment to lifelong learning and peace.',
            features: [
                'Everything in 3 Months',
                'Ad-Free Experience',
                'Early Access to New Features',
                'Direct Feedback to Developers',
                'Premium 24/7 Support'
            ],
            isPopular: false,
            buttonText: 'Choose 6 Months',
            gradient: 'plan-pro'
        }
    ];

    return (
        <div className="pricing-page">
            <Navbar />

            {/* Floating Elements Background */}
            <div className="floating-elements">
                <div className="float-element lotus">🪷</div>
                <div className="float-element om-symbol-2">ॐ</div>
                <div className="float-element diya">🪔</div>
            </div>

            <section className="pricing-section-premium fade-in-section animate-in">
                <div className="container">
                    <div className="section-header-premium pricing-header">
                        <span className="section-badge">Pricing</span>
                        <h2 className="section-title-premium">
                            Choose Your <span className="gradient-text">Journey</span>
                        </h2>
                        <p className="section-subtitle">
                            Invest in your spiritual growth with affordable plans tailored for your needs.
                        </p>
                    </div>

                    <div className="pricing-grid-premium">
                        {plans.map((plan) => (
                            <div className={`pricing-card-premium ${plan.isPopular ? 'popular' : ''} ${plan.gradient}`} key={plan.id}>
                                {plan.isPopular && <div className="popular-badge">Most Popular</div>}

                                <div className="pricing-card-header">
                                    <h3 className="plan-title">{plan.title}</h3>
                                    <div className="plan-price">
                                        <span className="amount">{plan.price}</span>
                                        <span className="period">{plan.period}</span>
                                    </div>
                                    <p className="plan-desc">{plan.description}</p>
                                </div>

                                <div className="pricing-card-body">
                                    <ul className="plan-features">
                                        {plan.features.map((feature, idx) => (
                                            <li key={idx}>
                                                <span className="feature-check">✓</span>
                                                {feature}
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <div className="pricing-card-footer">
                                    <button
                                        className={`btn-premium-${plan.isPopular ? 'primary' : 'secondary'} w-100`}
                                        onClick={() => navigate(`/checkout?plan=${plan.id}`)}
                                    >
                                        {plan.buttonText}
                                    </button>
                                </div>
                                <div className="card-glow-effect"></div>
                            </div>
                        ))}
                    </div>

                    <div className="pricing-faq fade-in-section animate-in">
                        <div className="cta-card-premium">
                            <div className="cta-content" style={{ textAlign: 'center', width: '100%' }}>
                                <h2>Have questions about our plans?</h2>
                                <p>We're here to help you choose the right path for your spiritual journey.</p>
                                <button className="btn-premium-secondary btn-large" onClick={() => navigate('/contact')}>
                                    <span className="btn-icon">💬</span>
                                    Contact Support
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default Pricing;
