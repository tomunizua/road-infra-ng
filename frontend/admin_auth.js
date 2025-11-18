function handleDemoLogin() {
    try {
        const demoToken = 'demo_token_' + Date.now();
        localStorage.setItem(AUTH_TOKEN_KEY, demoToken);
        localStorage.setItem('isDemoMode', 'true');
        console.log('Demo login triggered, token:', demoToken);
        window.location.reload();
    } catch (error) {
        console.error('Error in demo login:', error);
        alert('Failed to start demo mode. Please check browser console.');
    }
}

window.handleDemoLogin = handleDemoLogin;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeAuth);
} else {
    initializeAuth();
}

function initializeAuth() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    const loginFormContainer = document.getElementById('loginFormContainer');
    const dashboardContent = document.getElementById('adminDashboardContent');

    if (token) {
        dashboardContent.classList.remove('hidden');
        loginFormContainer.classList.add('hidden');
        document.getElementById('sidebar').style.transform = 'translateX(0)';
        
        setTimeout(function() {
            try {
                loadDashboardData(); 
                loadReports();
                if (typeof initCharts === 'function') {
                    initCharts();
                }
                if (typeof initDashboard === 'function') {
                    initDashboard();
                }
            } catch (error) {
                console.error('Error initializing dashboard:', error);
            }
        }, 100);

    } else {
        loginFormContainer.classList.remove('hidden');
        dashboardContent.classList.add('hidden');
    }

    document.getElementById('adminLoginForm').addEventListener('submit', handleLogin);
    const demoLoginBtn = document.getElementById('demoLoginBtn');
    if (demoLoginBtn) {
        demoLoginBtn.addEventListener('click', handleDemoLogin);
    }
    const logoutButton = document.getElementById('logoutBtn');
    if (logoutButton) {
        logoutButton.addEventListener('click', handleLogout);
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDisplay = document.getElementById('loginError');
    const submitBtn = document.getElementById('loginSubmitBtn');

    errorDisplay.classList.add('hidden');

    const validationError = validateLoginForm(username, password);
    if (validationError) {
        errorDisplay.textContent = validationError;
        errorDisplay.classList.remove('hidden');
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Authenticating...';

    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const result = await response.json();

        if (response.ok && result.token) {
            localStorage.setItem(AUTH_TOKEN_KEY, result.token);
            window.location.reload();
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
        submitBtn.textContent = 'Sign In';
    }
}

function validateLoginForm(username, password) {
    if (!username) {
        return 'Please enter your username or email address.';
    }
    if (username.length < 3) {
        return 'Username or email must be at least 3 characters long.';
    }
    if (!password) {
        return 'Please enter your password.';
    }
    if (password.length < 6) {
        return 'Password must be at least 6 characters long.';
    }
    return null;
}

function handleLogout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem('isDemoMode');
    window.location.reload();
}