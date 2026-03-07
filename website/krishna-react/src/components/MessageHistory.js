
import React, { useState } from 'react';
import './MessageHistory.css';

function MessageHistory({ messages, isOpen, onClose, onClearHistory, onSpeak, activeMessageId }) {
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);

    const formatMessage = (text) => {
        const rawLines = text.split('\n').map(l => l.trim()).filter(l => l !== '');
        if (rawLines.length === 0) return null;

        const sections = {
            general: [],
            shloka: [],
            explanation: [],
            steps: []
        };

        const isCitation = (l) => l.includes('भगवद गीता') || (l.includes('अध्याय') && l.includes('श्लोक'));

        let citationIdx = rawLines.findIndex(isCitation);
        let shlokaEnd = citationIdx;

        if (citationIdx !== -1) {
            let foundDoubleDanda = false;
            for (let i = citationIdx + 1; i < Math.min(citationIdx + 5, rawLines.length); i++) {
                if (rawLines[i].includes('॥') || rawLines[i].includes('||')) {
                    shlokaEnd = i;
                    foundDoubleDanda = true;
                    break;
                }
            }
            if (!foundDoubleDanda) {
                for (let i = citationIdx + 1; i < Math.min(citationIdx + 3, rawLines.length); i++) {
                    if (!/^\d+[.)]/.test(rawLines[i]) && !/^(मार्गदर्शन|उपाय|कदम|steps|अतः|आगे बढ़ो)/i.test(rawLines[i])) {
                        shlokaEnd = i;
                    }
                }
            }
        }

        let firstStepIdx = -1;
        let startSearch = shlokaEnd !== -1 ? shlokaEnd + 1 : (citationIdx !== -1 ? citationIdx + 1 : 0);
        for (let i = startSearch; i < rawLines.length; i++) {
            if (/^\d+[.)]\s/.test(rawLines[i]) || /^\*\s/.test(rawLines[i]) || /^-\s/.test(rawLines[i])) {
                firstStepIdx = i;
                break;
            }
        }

        let stepsStart = firstStepIdx;
        if (firstStepIdx > startSearch) {
            const prevLine = rawLines[firstStepIdx - 1];
            if (prevLine.length < 100 && (prevLine.endsWith(':') || /मार्गदर्शन|उपाय|कदम|steps|अतः|आगे बढ़ो|अभ्यास करो|याद रखें|ध्यान दें|ये कदम/i.test(prevLine))) {
                stepsStart = firstStepIdx - 1;
            }
        }

        if (citationIdx !== -1) {
            sections.general = rawLines.slice(0, citationIdx);
            sections.shloka = rawLines.slice(citationIdx, shlokaEnd + 1).map(l => l.replace(/[।॥|]\s*[0-9०-९]+\s*[।॥|]\s*$/, '॥'));

            if (stepsStart !== -1) {
                sections.explanation = rawLines.slice(shlokaEnd + 1, stepsStart);
                sections.steps = rawLines.slice(stepsStart);
            } else {
                sections.explanation = rawLines.slice(shlokaEnd + 1);
            }
        } else {
            if (stepsStart !== -1) {
                sections.general = rawLines.slice(0, stepsStart);
                sections.steps = rawLines.slice(stepsStart);
            } else {
                sections.general = rawLines;
            }
        }

        return (
            <div className="response-boxes">
                {sections.general.length > 0 && (
                    <div className="response-box general-box">
                        <div className="box-title">आरंभ (Introduction)</div>
                        {sections.general.map((l, i) => <p key={`g-${i}`}>{l}</p>)}
                    </div>
                )}
                {sections.shloka.length > 0 && (
                    <div className="response-box shloka-box">
                        <div className="box-title">श्लोक (Divine Verse)</div>
                        <div className="shloka-content">
                            {sections.shloka.map((l, i) => <div key={`s-${i}`}>{l}</div>)}
                        </div>
                    </div>
                )}
                {sections.explanation.length > 0 && (
                    <div className="response-box explanation-box">
                        <div className="box-title">अर्थ (Explanation)</div>
                        {sections.explanation.map((l, i) => <p key={`e-${i}`}>{l}</p>)}
                    </div>
                )}
                {sections.steps.length > 0 && (
                    <div className="response-box steps-box">
                        <div className="box-title">मार्गदर्शन (Guidance & Steps)</div>
                        {sections.steps.map((l, i) => <p key={`st-${i}`}>{l}</p>)}
                    </div>
                )}
            </div>
        );
    };

    const handleClearHistory = () => {
        onClearHistory();
        setShowConfirmDialog(false);
    };

    return (
        <>
            {/* Overlay */}
            {isOpen && <div className="history-overlay" onClick={onClose}></div>}

            {/* Sidebar */}
            <div className={`message-history ${isOpen ? 'open' : ''}`}>
                <div className="history-header">
                    <h2>Divine Dialogue</h2>
                    <div className="header-actions">
                        {messages.length > 0 && (
                            <button
                                className="clear-history-button"
                                onClick={() => setShowConfirmDialog(true)}
                                title="Clear history"
                            >
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </button>
                        )}
                        <button className="close-button" onClick={onClose}>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M18 6L6 18M6 6l12 12" strokeWidth="2" strokeLinecap="round" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div className="history-content">
                    {messages.length === 0 ? (
                        <p className="empty-state">Your journey has just begun...</p>
                    ) : (
                        messages.map((message) => (
                            <div key={message.id} className={`history-message ${message.type}`}>
                                <div className="message-header">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                        <span className="message-author">
                                            {message.type === 'krishna' ? '🪈 Krishna' : '👤 You'}
                                        </span>
                                        {message.type === 'krishna' && (
                                            <button
                                                className={`speak-button ${activeMessageId === message.id ? 'speaking' : ''}`}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onSpeak(message.text, message.id);
                                                }}
                                                title={activeMessageId === message.id ? "Stop reading" : "Read aloud"}
                                            >
                                                {activeMessageId === message.id ? (
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <rect x="6" y="6" width="12" height="12" />
                                                    </svg>
                                                ) : (
                                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M11 5L6 9H2V15H6L11 19V5Z" fill="currentColor" />
                                                        <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
                                                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
                                                    </svg>
                                                )}
                                            </button>
                                        )}
                                    </div>
                                    <span className="message-time">
                                        {(() => {
                                            try {
                                                const date = message.timestamp instanceof Date ? message.timestamp : new Date(message.timestamp);
                                                return date.toLocaleTimeString('en-US', {
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                });
                                            } catch (e) {
                                                return '';
                                            }
                                        })()}
                                    </span>
                                </div>
                                <div className="message-body">
                                    {message.type === 'krishna' ? (
                                        formatMessage(message.text)
                                    ) : (
                                        <p>{message.text}</p>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <div className="confirm-overlay" onClick={() => setShowConfirmDialog(false)}>
                    <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
                        <div className="confirm-icon">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                        </div>
                        <h3>Clear Chat History?</h3>
                        <p>This will permanently delete all your conversations. This action cannot be undone.</p>
                        <div className="confirm-actions">
                            <button className="btn-cancel" onClick={() => setShowConfirmDialog(false)}>
                                Cancel
                            </button>
                            <button className="btn-confirm" onClick={handleClearHistory}>
                                Clear History
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default React.memo(MessageHistory);
