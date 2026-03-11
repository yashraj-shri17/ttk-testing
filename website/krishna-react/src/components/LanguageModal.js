import React from 'react';
import './LanguageModal.css';

function LanguageModal({ onSelect }) {
    return (
        <div className="lang-modal-overlay">
            <div className="lang-modal-card">
                {/* Glow orb top */}
                <div className="lang-modal-orb">
                    <span className="lang-modal-icon">🕉️</span>
                </div>

                <h2 className="lang-modal-title">
                    Welcome to<br />
                    <span className="lang-modal-name">Talk to Krishna</span>
                </h2>

                <p className="lang-modal-subtitle">
                    Choose the language in which<br />you'd like Lord Krishna to respond
                </p>

                <div className="lang-modal-options">
                    <button
                        className="lang-btn lang-btn-english"
                        onClick={() => onSelect('en')}
                    >
                        <span className="lang-btn-flag">🇬🇧</span>
                        <span className="lang-btn-label">English</span>
                        <span className="lang-btn-sub">Respond in English</span>
                    </button>

                    <div className="lang-divider">or</div>

                    <button
                        className="lang-btn lang-btn-hindi"
                        onClick={() => onSelect('hi')}
                    >
                        <span className="lang-btn-flag">🇮🇳</span>
                        <span className="lang-btn-label">हिंदी</span>
                        <span className="lang-btn-sub">हिंदी में उत्तर दें</span>
                    </button>
                </div>

                <p className="lang-modal-note">
                    You can speak in any language — Krishna will always respond in your chosen language.
                </p>
            </div>
        </div>
    );
}

export default LanguageModal;
