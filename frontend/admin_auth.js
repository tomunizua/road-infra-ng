// --- Global Configuration ---

const API_BASE_URL = 'https://roadwatch-ng.onrender.com'; 
const AUTH_TOKEN_KEY = 'adminAuthToken'; 

document.addEventListener('DOMContentLoaded', initializeAuth);

function initializeAuth() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const loginFormContainer = document.getElementById('loginFormContainer');
    const dashboardContent = document.getElementById('adminDashboardContent');

    if (token) {
        // Token exists: Try to validate it (e.g., check if expired)
        // For now, we assume a token in storage is valid until proven otherwise by a failed API request
        dashboardContent.classList.remove('hidden');
        loginFormContainer.classList.add('hidden');
        // Initialize dashboard components (admin.js functions)
        loadDashboardData(); 
        loadReports();
        initCharts();
        // Set initial sidebar state (otherwise it starts translated)
        document.getElementById('sidebar').style.transform = 'translateX(0)';

    } else {
        // No token: Show login form
        loginFormContainer.classList.remove('hidden');
        dashboardContent.classList.add('hidden');
    }

    // Attach event listeners for login and logout
    document.getElementById('adminLoginForm').addEventListener('submit', handleLogin);
    const logoutButton = document.getElementById('logoutBtn');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDisplay = document.getElementById('loginError');
    const submitBtn = document.getElementById('loginSubmitBtn');

    errorDisplay.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Authenticating...';

    // 🚨 IMPORTANT: The /api/admin/login endpoint MUST be created in your Flask backend.
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (response.ok && result.token) {
            localStorage.setItem(AUTH_TOKEN_KEY, result.token);
            window.location.reload(); // Reload to show the dashboard
        } else {
            const errorMessage = result.error || 'Invalid username or password.';
            errorDisplay.textContent = errorMessage;
            errorDisplay.classList.remove('hidden');
        }

    } catch (error) {
        errorDisplay.textContent = 'Network error or backend is unavailable.';
        errorDisplay.classList.remove('hidden');
        console.error('Login error:', error);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Log In';
    }
}

function handleLogout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    window.location.reload(); // Reload to show the login screen
}

// Utility function to get the stored token for protected API calls
function getAuthHeader() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
        return { 'Authorization': `Bearer ${token}` };
    }
    return {};
}