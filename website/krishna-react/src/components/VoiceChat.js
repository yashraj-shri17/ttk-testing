import React, { useState, useEffect, useRef, useCallback } from 'react';
import VoiceOrb from './VoiceOrb';
import MessageHistory from './MessageHistory';
import VoiceControls from './VoiceControls';
import './VoiceChat.css';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_ENDPOINTS } from '../config/api';

const API_URL = API_ENDPOINTS.ASK;

function VoiceChat() {
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuth();
    const [messages, setMessages] = useState([]);
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [hasStarted, setHasStarted] = useState(false);
    const [activeMessageId, setActiveMessageId] = useState(null);
    const mediaRecorderRef = useRef(null);
    const audioChunksRef = useRef([]);
    const audioContextRef = useRef(null);
    const persistentAudioRef = useRef(null); // Primary audio element for iOS compatibility
    const isAudioUnlockedRef = useRef(false);
    const isCancelledRef = useRef(false);

    // Generate Session ID once per mount
    const [sessionId] = useState(() => 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9));

    const stopAudio = useCallback(() => {
        console.log("Stopping audio...");
        isCancelledRef.current = true; // Signal cancellation

        const audio = persistentAudioRef.current;
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }

        setIsSpeaking(false);
        setActiveMessageId(null);
    }, []);

    const unlockAudio = useCallback(async () => {
        if (isAudioUnlockedRef.current) return;

        console.log("Unlocking audio systems for iOS/Mobile...");
        try {
            // 1. Initialize/Resume AudioContext
            if (!audioContextRef.current) {
                const AudioContextClass = window.AudioContext || window.webkitAudioContext;
                if (AudioContextClass) {
                    audioContextRef.current = new AudioContextClass();
                }
            }

            if (audioContextRef.current) {
                if (audioContextRef.current.state === 'suspended') {
                    await audioContextRef.current.resume();
                }

                // Create and play a very short silent buffer
                // This is the key "gesture" required by iOS to allow future async audio
                const buffer = audioContextRef.current.createBuffer(1, 1, 22050);
                const node = audioContextRef.current.createBufferSource();
                node.buffer = buffer;
                node.connect(audioContextRef.current.destination);
                node.start(0);
                node.onended = () => {
                    node.disconnect();
                    console.log("Web Audio systems primed");
                };
            }

            // 2. Unlock HTMLAudioElement (Fallback)
            if (persistentAudioRef.current) {
                // Ensure playsinline and preload are set
                persistentAudioRef.current.setAttribute('playsinline', 'true');
                persistentAudioRef.current.setAttribute('webkit-playsinline', 'true');
                persistentAudioRef.current.preload = 'auto';

                // Silent wav data to "wake up" the element
                persistentAudioRef.current.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA';
                const playPromise = persistentAudioRef.current.play();
                if (playPromise !== undefined) {
                    await playPromise.catch(e => console.warn("Silent play failed, but intent was registered:", e));
                    persistentAudioRef.current.pause();
                }
            }

            isAudioUnlockedRef.current = true;
            console.log("Audio systems successfully unlocked");
        } catch (err) {
            console.error("Audio systems unlock failed:", err);
        }
    }, []);

    // Global listener to unlock audio on first interaction
    useEffect(() => {
        const handleInteraction = () => {
            console.log("User interaction detected, attempting to unlock audio...");
            unlockAudio();
        };

        window.addEventListener('touchstart', handleInteraction, { once: true, capture: true });
        window.addEventListener('click', handleInteraction, { once: true, capture: true });
        window.addEventListener('mousedown', handleInteraction, { once: true, capture: true });

        return () => {
            window.removeEventListener('touchstart', handleInteraction, { capture: true });
            window.removeEventListener('click', handleInteraction, { capture: true });
            window.removeEventListener('mousedown', handleInteraction, { capture: true });
        };
    }, [unlockAudio]);

    const speakText = useCallback(async (text, messageId = null, audioUrl = null) => {
        if ((isSpeaking) && activeMessageId === messageId && messageId !== null) {
            stopAudio();
            return;
        }

        stopAudio();
        isCancelledRef.current = false;
        setIsSpeaking(true);
        setActiveMessageId(messageId);

        const baseUrl = API_ENDPOINTS.ASK.split('/api/ask')[0];
        const fullUrl = audioUrl ? `${baseUrl}${audioUrl}` : null;

        try {
            const audio = persistentAudioRef.current;
            if (!audio) throw new Error("Audio element missing");

            // Ensure playsinline for iOS
            audio.setAttribute('playsinline', 'true');
            audio.setAttribute('webkit-playsinline', 'true');

            let src;
            if (fullUrl) {
                src = fullUrl;
            } else {
                const response = await axios.post(API_ENDPOINTS.SPEAK, { text }, { responseType: 'blob' });
                src = URL.createObjectURL(response.data);
            }

            audio.src = src;
            audio.load();

            audio.onended = () => {
                setIsSpeaking(false);
                setActiveMessageId(null);
                if (src.startsWith('blob:')) URL.revokeObjectURL(src);
            };

            await audio.play();
            console.log("✅ Audio working (iOS safe)");

        } catch (err) {
            console.error("❌ Playback failed:", err);
            setIsSpeaking(false);
            setActiveMessageId(null);
        }
    }, [stopAudio, isSpeaking, activeMessageId]);

    const handleAudioUpload = async (audioBlob) => {
        setIsLoading(true);
        setTranscript('Transcribing...');

        // Resume audio context on gesture
        if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
            audioContextRef.current.resume().catch(() => { });
        }

        const formData = new FormData();
        formData.append('audio', audioBlob, 'record.webm');

        try {
            const res = await axios.post(API_ENDPOINTS.TRANSCRIBE, formData);
            if (res.data.success && res.data.text) {
                const transcriptText = res.data.text;
                // don't set transcript text as it will flash quickly before answer
                await handleVoiceInput(transcriptText);
            } else {
                setTranscript("Could not transcribe.");
                setIsLoading(false);
            }
        } catch (e) {
            console.error("Transcription error", e);
            setTranscript("Error understanding audio.");
            setIsLoading(false);
        }
    };

    const handleVoiceInput = useCallback(async (text) => {
        if (!text.trim()) return;

        // Keep what you said visible while LLM thinks
        setTranscript(text);

        // Add user message
        const userMessage = {
            id: Date.now(),
            type: 'user',
            text: text,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);

        setIsLoading(true);

        try {
            const startTime = performance.now();

            const response = await axios.post(API_URL, {
                question: text,
                include_audio: true, // Request audio URL directly
                session_id: sessionId,
                user_id: user?.id
            }, {
                timeout: 60000
            });

            const textTime = performance.now() - startTime;
            console.log(`⏱️ Text response received in ${textTime.toFixed(0)}ms`);

            const krishnaMessageId = Date.now() + 1;
            const krishnaMessage = {
                id: krishnaMessageId,
                type: 'krishna',
                text: response.data.answer || 'क्षमा करें, मैं अभी उत्तर देने में असमर्थ हूँ।',
                timestamp: new Date()
            };

            setMessages(prev => [...prev, krishnaMessage]);

            // If audio_url is present, use it directly for faster playback
            if (response.data.audio_url) {
                speakText(krishnaMessage.text, krishnaMessageId, response.data.audio_url);
            } else {
                speakText(krishnaMessage.text, krishnaMessageId);
            }

        } catch (error) {
            console.error('Error:', error);
            const isTimeout = error.code === 'ECONNABORTED' || error.message?.includes('timeout');
            const errorMsgId = Date.now() + 1;
            const errorMsg = {
                id: errorMsgId,
                type: 'krishna',
                text: isTimeout
                    ? 'सर्वर जाग रहा है, कृपया 30 सेकंड बाद पुनः प्रयास करें। 🙏'
                    : 'क्षमा करें, कुछ गलत हो गया। कृपया पुनः प्रयास करें।',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMsg]);
            speakText(errorMsg.text, errorMsgId);
        } finally {
            setIsLoading(false);
            setTranscript('');
        }
    }, [speakText, user, sessionId]);

    // Start Journey Handler
    const handleStartJourney = async () => {
        console.log("Starting journey - unlocking audio and sending welcome...");

        // 1. Unlock audio first (critical user gesture)
        await unlockAudio();

        // 2. Set has started to true to show the interface
        setHasStarted(true);

        // 3. Send welcome message
        const welcomeMsgId = Date.now();
        const welcomeMsg = {
            id: welcomeMsgId,
            type: 'krishna',
            text: 'नमस्ते! मैं कृष्ण हूँ। मुझसे कुछ भी पूछें।',
            timestamp: new Date()
        };

        setMessages([welcomeMsg]);
        speakText(welcomeMsg.text, welcomeMsgId);
    };

    // Remove automatic welcome message timer
    useEffect(() => {
        // We no longer send message automatically on mount
        // It's handled by handleStartJourney
        return () => { };
    }, []);

    // Stop audio when location/route changes
    useEffect(() => {
        return () => {
            console.log("Route changing/unmounting - stopping audio");
            isCancelledRef.current = true;
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.stop();
            }
        };
    }, [location]);

    const toggleListening = () => {
        // Unlock audio on first interaction for iOS
        unlockAudio();

        // Prevent starting a new recording if already processing or speaking
        if (!isListening && (isLoading || isSpeaking)) {
            console.log("Mic blocked: Still loading or speaking");
            if (isSpeaking) stopAudio(); // If speaking, just stop it
            return;
        }

        if (isListening) {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
                mediaRecorderRef.current.stop();
            }
            setIsListening(false);
        } else {
            // Stop speaking if Krishna is talking
            if (isSpeaking) {
                stopAudio();
            }

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('Audio recording is not supported in this browser.');
                return;
            }

            navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
                // Try choosing a widely supported mimeType
                let mimeType = 'audio/webm';
                if (!MediaRecorder.isTypeSupported(mimeType)) {
                    mimeType = 'audio/mp4';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = ''; // fallback to default
                    }
                }

                const mediaRecorder = new MediaRecorder(stream, { mimeType });
                mediaRecorderRef.current = mediaRecorder;
                audioChunksRef.current = [];

                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0) audioChunksRef.current.push(event.data);
                };

                mediaRecorder.onstop = async () => {
                    stream.getTracks().forEach(track => track.stop());
                    if (audioChunksRef.current.length > 0) {
                        // Keep using webm for the blob to not confuse backed
                        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/webm' });
                        await handleAudioUpload(audioBlob);
                    }
                };

                mediaRecorder.start();
                setIsListening(true);
                setHasStarted(true);
            }).catch(e => {
                console.error("Microphone access denied:", e);
                alert("Please allow microphone access to use voice chat.");
            });
        }
    };

    const stopSpeaking = () => {
        stopAudio();
    };

    const clearHistory = () => {
        // Stop any ongoing speech
        if (isSpeaking) {
            stopAudio();
        }
        // Clear all messages
        setMessages([]);
        // Reset to initial state
        setHasStarted(false);
    };

    return (
        <div className="voice-chat-container">
            {/* Header */}
            <header className="app-header">
                <button className="icon-button back-button" onClick={() => {
                    // Stop audio when navigating back
                    stopAudio();
                    navigate('/');
                }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M15 18l-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                </button>

                <div className="header-title-container">
                    <span className="logo-icon">🕉️</span>
                    <span className="header-title">Divine Voice</span>
                </div>

                <button
                    className="icon-button history-toggle"
                    onClick={() => {
                        // Stop audio when toggling history
                        if (isSpeaking) {
                            stopAudio();
                        }
                        setShowHistory(!showHistory);
                    }}
                    title="Toggle history"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="5" r="1" />
                        <circle cx="12" cy="12" r="1" />
                        <circle cx="12" cy="19" r="1" />
                    </svg>
                </button>
            </header>

            {/* Main Voice Interface */}
            <main className="main-content">
                {!hasStarted && (
                    <div className="hero-section">
                        <h1 className="hero-title">
                            Seek Guidance <br />
                            <span className="highlight">From The Divine</span>
                        </h1>
                        <div className="quick-actions">
                            <button className="action-chip active" onClick={handleStartJourney}>
                                Start Journey
                            </button>
                            <button className="action-chip" onClick={() => setShowHistory(true)}>
                                History
                            </button>
                        </div>
                    </div>
                )}

                <div className="orb-section">
                    <h2 className="section-label">Soul Connection</h2>
                    <VoiceOrb
                        isListening={isListening}
                        isSpeaking={isSpeaking}
                        isLoading={isLoading}
                    />
                </div>

                {/* Status Text & Instructions */}
                <div className="status-container">
                    <div className="status-text" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                        {isListening ? (
                            <>
                                <span style={{ color: '#fff', fontSize: '1.2rem', textShadow: '0 0 10px rgba(255,255,255,0.5)' }}>Listening to your soul...</span>
                                <span style={{ color: '#ffb347', fontSize: '0.9rem', animation: 'pulse 2s infinite', fontWeight: 'bold' }}>
                                    (Tap the mic again to finish speaking)
                                </span>
                            </>
                        ) : isSpeaking ? (
                            <span style={{ color: '#fff' }}>Krishna is guiding...</span>
                        ) : isLoading ? (
                            <span style={{ color: '#fff' }}>{transcript === 'Transcribing...' ? 'Transcribing audio...' : 'Consulting the Gita...'}</span>
                        ) : (
                            <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>{transcript ? `"${transcript}"` : 'Tap to Connect'}</span>
                        )}
                    </div>
                </div>

                {/* Voice Controls */}
                <VoiceControls
                    isListening={isListening}
                    isSpeaking={isSpeaking}
                    isLoading={isLoading}
                    onToggleListening={toggleListening}
                    onStopSpeaking={stopSpeaking}
                />
            </main>

            {/* Message History Sidebar */}
            <MessageHistory
                messages={messages}
                isOpen={showHistory}
                onSpeak={speakText}
                activeMessageId={activeMessageId}
                onClose={() => {
                    // Stop audio when closing history
                    if (isSpeaking) {
                        stopAudio();
                    }
                    setShowHistory(false);
                }}
                onClearHistory={clearHistory}
            />

            {/* Hidden fallback audio element */}
            <audio
                ref={persistentAudioRef}
                style={{ display: 'none' }}
                preload="auto"
                playsInline
            />

        </div>
    );
}

export default VoiceChat;
