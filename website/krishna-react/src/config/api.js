// API Configuration
// This file centralizes all API endpoint URLs

let API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
// Remove trailing slash if present to avoid double-slash issues in endpoints
API_BASE_URL = API_BASE_URL.replace(/\/$/, '');

export const API_ENDPOINTS = {
    // Authentication
    LOGIN: `${API_BASE_URL}/api/login`,
    SIGNUP: `${API_BASE_URL}/api/signup`,
    FORGOT_PASSWORD: `${API_BASE_URL}/api/forgot-password`,
    RESET_PASSWORD: `${API_BASE_URL}/api/reset-password`,

    // AI Chat
    ASK: `${API_BASE_URL}/api/ask`,
    HISTORY: `${API_BASE_URL}/api/history`,

    // Audio (if needed)
    SPEAK:         `${API_BASE_URL}/api/speak`,
    SPEAK_STREAM:  `${API_BASE_URL}/api/speak-stream`,
    TRANSCRIBE:    `${API_BASE_URL}/api/transcribe`,

    // Admin
    ADMIN_METRICS: `${API_BASE_URL}/api/admin/metrics`,
    CREATE_ADMIN: `${API_BASE_URL}/api/admin/create-admin`,
    GRANT_ACCESS: `${API_BASE_URL}/api/admin/grant-access`,
    ADMIN_COUPONS: `${API_BASE_URL}/api/admin/coupons`,

    // Checkout
    VALIDATE_COUPON: `${API_BASE_URL}/api/coupons/validate`,
};

export default API_BASE_URL;
