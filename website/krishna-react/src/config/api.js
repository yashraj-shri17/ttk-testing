// API Configuration
// This file centralizes all API endpoint URLs

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export const API_ENDPOINTS = {
    // Authentication
    LOGIN: `${API_BASE_URL}/api/login`,
    SIGNUP: `${API_BASE_URL}/api/signup`,
    FORGOT_PASSWORD: `${API_BASE_URL}/api/forgot-password`,
    RESET_PASSWORD: `${API_BASE_URL}/api/reset-password`,

    // AI Chat
    ASK: `${API_BASE_URL}/api/ask`,

    // Audio (if needed)
    SPEAK: `${API_BASE_URL}/api/speak`,
    TRANSCRIBE: `${API_BASE_URL}/api/transcribe`,
};

export default API_BASE_URL;
