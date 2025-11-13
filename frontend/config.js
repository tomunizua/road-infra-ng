// API Configuration
// This file handles API URL configuration for different environments

const API_CONFIG = {
    // Automatically detect environment
    getApiUrl() {
        // Check if we're on localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }

        // Production: Replace with your deployed backend URL
        // Example: return 'https://your-backend.onrender.com';
        // For now, use environment variable or default
        return window.ENV_API_URL || 'https://your-backend-url-here.onrender.com';
    }
};

// Export for use in other scripts
const API_BASE_URL = API_CONFIG.getApiUrl();
console.log('🌐 API Base URL:', API_BASE_URL);
