// API Configuration
// This file handles API URL configuration for different environments

const API_CONFIG = {
    // Automatically detect environment
    getApiUrl() {
        // Check if we're on localhost
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return 'http://localhost:5000';
        }

        // Production backend URL
        return 'https://roadwatch-ng.onrender.com';
    }
};

console.log('🌐 API Config loaded');
