// --- Global Configuration ---
let API_BASE_URL = 'https://roadwatch-ng.onrender.com';
if (typeof API_CONFIG !== 'undefined') {
    API_BASE_URL = API_CONFIG.getApiUrl();
}
const AUTH_TOKEN_KEY = 'adminAuthToken';

// Chart Global Variables (To prevent "Canvas already in use" error)
window.reportsChartInstance = null;
window.damageChartInstance = null;
window.budgetChartInstance = null;

// Function to get the current auth header
function getAuthHeader() {
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
        return { 'Authorization': `Bearer ${token}` };
    }
    return {};
}

// Global variables
let allReports = [];
let currentFilter = 'all';

// Toast notification system
function showToast(title, message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconMap = {
        success: 'fa-check-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle',
        error: 'fa-times-circle'
    };

    toast.innerHTML = `
        <i class="fas ${iconMap[type]} toast-icon text-lg"></i>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 4000);
}

// Navigation handling
function initDashboard() {
    const dashboardContent = document.getElementById('adminDashboardContent');
    if (!dashboardContent || dashboardContent.classList.contains('hidden')) {
        return;
    }
    
    // --- Dashboard Initialization (Only runs if token exists) ---

    // Mobile menu toggle
    document.getElementById('mobileMenuToggle').addEventListener('click', function() {
        document.getElementById('sidebar').style.transform = 'translateX(0)';
        document.getElementById('sidebarOverlay').classList.remove('hidden');
    });

    document.getElementById('sidebarToggle').addEventListener('click', function() {
        document.getElementById('sidebar').style.transform = 'translateX(-100%)';
        document.getElementById('sidebarOverlay').classList.add('hidden');
    });

    document.getElementById('sidebarOverlay').addEventListener('click', function() {
        document.getElementById('sidebar').style.transform = 'translateX(-100%)';
        this.classList.add('hidden');
    });

    // Notification bell click handler
    document.getElementById('notificationBtn').addEventListener('click', function() {
        showToast('Notifications', '3 new notifications: New report submitted, Report approved for repair, Budget update available', 'info');
    });

    // Profile button click handler
    document.getElementById('profileBtn').addEventListener('click', function() {
        openProfileModal();
    });

    // Profile modal overlay click handler
    document.getElementById('profileModal').addEventListener('click', function(event) {
        if (event.target === this) {
            closeProfileModal();
        }
    });

    // Logout handler
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(nav => {
                nav.classList.remove('active', 'bg-green-700', 'text-white');
                nav.classList.add('text-gray-700', 'hover:bg-gray-100');
            });
            this.classList.add('active', 'bg-green-700', 'text-white');
            this.classList.remove('text-gray-700', 'hover:bg-gray-100');
            const section = this.dataset.section;
            showSection(section);
        });
    });

    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => {
                b.classList.remove('filter-active');
                b.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white', 'shadow-md', 'hover:shadow-lg');
                b.classList.add('text-gray-600', 'bg-gray-100', 'hover:bg-gray-200');
            });
            this.classList.add('filter-active');
            this.classList.add('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white', 'shadow-md', 'hover:shadow-lg');
            this.classList.remove('text-gray-600', 'bg-gray-100', 'hover:bg-gray-200');
            const filter = this.dataset.filter;
            filterReports(filter);
        });
    });

    // Map filter listeners
    document.getElementById('mapSeverityFilter').addEventListener('change', refreshMapMarkers);
    document.getElementById('mapStatusFilter').addEventListener('change', refreshMapMarkers);
    document.getElementById('mapDamageFilter').addEventListener('change', refreshMapMarkers);

    // LGA filter listener
    const lgaFilterElement = document.getElementById('lgaFilter');
    if (lgaFilterElement) {
        lgaFilterElement.addEventListener('change', function() {
            filterReports(currentFilter);
        });
    }

    // Load initial data (only if authenticated)
    loadDashboardData();
    loadReports();
    initCharts();
}

function showSection(sectionName) {
    document.querySelectorAll('.section-content').forEach(section => {
        section.style.display = 'none';
    });

    document.getElementById(sectionName + 'Section').style.display = 'block';

    const titles = {
        dashboard: 'Dashboard',
        reports: 'All Reports',
        map: 'Map View',
        budget: 'Budget Optimization',
        users: 'Users',
        settings: 'Settings'
    };
    document.getElementById('pageTitle').textContent = titles[sectionName] || 'Dashboard';

    if (sectionName === 'map') {
        setTimeout(() => {
            initializeMap();
        }, 300);
    }

    if (sectionName === 'budget') {
        setTimeout(() => {
            loadBudgetOptimization();
        }, 100);
    }
}

function getStatusColor(status) {
    const statusColorMap = {
        'submitted': 'bg-blue-100 text-blue-800',
        'under_review': 'bg-yellow-100 text-yellow-800',
        'scheduled': 'bg-purple-100 text-purple-800',
        'in_progress': 'bg-orange-100 text-orange-800',
        'completed': 'bg-green-100 text-green-800'
    };
    return statusColorMap[status] || 'bg-gray-100 text-gray-800';
}

function getSeverityColor(severityScore) {
    if (severityScore >= 0.7) {
        return 'bg-red-500';
    } else if (severityScore >= 0.3) {
        return 'bg-orange-500';
    } else {
        return 'bg-yellow-500';
    }
}

function getSeverityLabel(severityScore) {
    if (severityScore >= 0.7) {
        return 'High';
    } else if (severityScore >= 0.3) {
        return 'Medium';
    } else {
        return 'Low';
    }
}

function getSeverityColorName(severityScore) {
    if (severityScore >= 0.7) {
        return 'red';
    } else if (severityScore >= 0.3) {
        return 'orange';
    } else {
        return 'yellow';
    }
}

function loadBudgetOptimization() {
    try {
        console.log('Loading budget optimization data...');
        const budgetContent = document.getElementById('budgetSection');
        if (budgetContent) {
            // budgetContent.innerHTML = '<div class="p-8"><p class="text-gray-500">Budget optimization data will be loaded here.</p></div>';
        }
    } catch (error) {
        console.error('Error loading budget optimization:', error);
    }
}

// Load dashboard statistics
async function loadDashboardData() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });
        if (!response.ok) {
            if (response.status === 401) {
                window.handleLogout(); 
                return;
            }
            throw new Error('Failed to fetch reports');
        }
        const data = await response.json();
        const reports = data.reports || data;

        const stats = {
            total: reports.length,
            submitted: reports.filter(r => r.status === 'submitted').length,
            under_review: reports.filter(r => r.status === 'under_review').length,
            scheduled: reports.filter(r => r.status === 'scheduled').length,
            in_progress: reports.filter(r => r.status === 'in_progress').length,
            completed: reports.filter(r => r.status === 'completed').length
        };

        document.getElementById('totalReports').textContent = stats.total;
        document.getElementById('scheduledReports').textContent = stats.scheduled;
        document.getElementById('inProgressReports').textContent = stats.in_progress;
        document.getElementById('completedReports').textContent = stats.completed;

        loadRecentReports(reports.slice(0, 5));

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        document.getElementById('totalReports').textContent = '0';
        document.getElementById('scheduledReports').textContent = '0';
        document.getElementById('inProgressReports').textContent = '0';
        document.getElementById('completedReports').textContent = '0';
    }
}

// Load all reports
async function loadReports() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch reports');
        const data = await response.json();
        allReports = data.reports || data;
        filterReports(currentFilter);

    } catch (error) {
        console.error('Error loading reports:', error);
        const tbody = document.getElementById('reportsTableBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">Failed to load reports</td></tr>';
        }
    }
}

function loadRecentReports(reports) {
    const container = document.getElementById('recentReportsList');
    container.innerHTML = '';

    if (reports.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center col-span-full">No recent reports</p>';
        return;
    }

    reports.forEach(report => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden hover:shadow-lg transition card-hover';

        const statusColor = getStatusColor(report.status);
        const severityColor = getSeverityColor(report.severity_score);

        card.innerHTML = `
            <div class="relative h-40 bg-gray-200 overflow-hidden">
                <img src="${report.photo_url || 'https://via.placeholder.com/300x200?text=Road+Damage'}" alt="${report.location}" class="w-full h-full object-cover">
                <div class="absolute top-2 right-2 px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                    ${report.status.replace('_', ' ')}
                </div>
            </div>
            <div class="p-4">
                <h4 class="font-semibold text-gray-900 mb-2">${report.location}</h4>
                <p class="text-sm text-gray-600 mb-3">${report.damage_type || 'Analysis pending'}</p>
                <div class="flex items-center justify-between">
                    <span class="text-xs font-medium text-gray-500">${new Date(report.created_at).toLocaleDateString()}</span>
                    <div class="flex items-center space-x-1">
                        <div class="w-6 h-6 ${severityColor} rounded flex items-center justify-center">
                            <span class="text-white text-xs font-bold">${report.severity_score ? Math.round(report.severity_score * 100) : '?'}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}

function filterReports(filter) {
    currentFilter = filter;
    const tbody = document.getElementById('reportsTableBody');
    tbody.innerHTML = '';

    let filteredReports = allReports;
    
    if (filter !== 'all') {
        filteredReports = allReports.filter(report => report.status === filter);
    }

    const lgaFilterElement = document.getElementById('lgaFilter');
    if (lgaFilterElement) {
        const selectedLga = lgaFilterElement.value;
        if (selectedLga !== 'all') {
            filteredReports = filteredReports.filter(report => report.lga === selectedLga);
        }
    }

    if (filteredReports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-gray-500">No reports found</td></tr>';
        return;
    }

    filteredReports.forEach(report => {
        const row = createReportRow(report);
        tbody.appendChild(row);
    });
}

function createReportRow(report) {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50';

    const statusColor = getStatusColor(report.status);
    const severityColor = getSeverityColor(report.severity_score);
    const isStuck = report.damage_type === 'processing' || report.status === 'processing';

    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${report.tracking_number}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <div>${report.location}</div>
            <div class="text-xs text-gray-500">${report.lga || ''}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <div class="flex flex-col">
                <span class="font-medium">${report.damage_type || 'Analyzing...'}</span>
                <span class="text-xs text-gray-500">${report.confidence ? (report.confidence * 100).toFixed(1) + '%' : 'Pending'}</span>
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <span class="px-2 py-1 text-xs font-medium rounded-full text-white ${severityColor}">
                ${report.severity_score ? Math.round(report.severity_score * 100) : 'TBD'}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                ${report.status.replace('_', ' ')}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${new Date(report.created_at).toLocaleDateString()}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
            <button onclick="viewReport('${report.tracking_number}')" class="text-green-600 hover:text-green-900 font-medium">View</button>
            ${isStuck ? 
                `<button onclick="forceReprocess(${report.id})" class="text-orange-600 hover:text-orange-900 font-medium" title="Retry AI">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>` 
            : ''}
        </td>
    `;

    return row;
}

function getStatusColor(status) {
    const colors = {
        submitted: 'bg-orange-100 text-orange-800',
        under_review: 'bg-blue-100 text-blue-800',
        scheduled: 'bg-purple-100 text-purple-800',
        completed: 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
}

function getSeverityColor(score) {
    if (!score) return 'bg-gray-500';
    if (score >= 0.7) return 'bg-red-500'; // High
    if (score >= 0.3) return 'bg-yellow-500'; // Medium
    if (score > 0) return 'bg-orange-500'; // Low
    return 'bg-green-500'; // None
}

// View report details
async function viewReport(trackingNumber) {
    try {
        const report = allReports.find(r => r.tracking_number === trackingNumber);

        if (!report) {
            console.error('Report not found in loaded data');
            showToast('Error', 'Report not found', 'error');
            return;
        }

        console.log('Report data:', {
            tracking_number: report.tracking_number,
            image_filename: report.image_filename,
            photo_url: report.photo_url,
            status: report.status
        });

        showReportModal(report);

    } catch (error) {
        console.error('Error loading report:', error);
        showToast('Error', 'Failed to load report details', 'error');
    }
}

function showReportModal(report) {
    const modal = document.getElementById('reportModal');
    const content = document.getElementById('modalContent');

    const statusColor = getStatusColor(report.status);
    const severityColor = getSeverityColor(report.severity_score);

    content.innerHTML = `
        <div class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-900">Report ID</h4>
                    <p class="text-gray-600">${report.tracking_number}</p>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Status</h4>
                    <span class="px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                        ${report.status.replace('_', ' ')}
                    </span>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Location</h4>
                    <p class="text-gray-600">${report.location}</p>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Severity Score</h4>
                    <span class="px-2 py-1 text-xs font-medium rounded-full text-white ${severityColor}">
                        ${report.severity_score ? Math.round(report.severity_score * 100) : 'TBD'}
                    </span>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Estimated Cost</h4>
                    <p class="text-lg font-semibold text-orange-600">₦${report.estimated_cost ? report.estimated_cost.toLocaleString() : '0'}</p>
                </div>
            </div>

            ${report.damage_type ? `
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-900">AI Damage Type</h4>
                    <p class="text-gray-600">${report.damage_type}</p>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">AI Confidence</h4>
                    <p class="text-gray-600">${report.confidence ? (report.confidence * 100).toFixed(1) + '%' : 'N/A'}</p>
                </div>
            </div>
            ` : ''}

            <div>
                <h4 class="font-medium text-gray-900 mb-2">Description</h4>
                <p class="text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100">
                    ${report.description || 'No description provided.'}
                </p>
            </div>

            ${report.gps ? `
            <div>
                <h4 class="font-medium text-gray-900 mb-2">GPS Coordinates</h4>
                <p class="text-gray-600">${report.gps}</p>
            </div>
            ` : ''}

            ${report.contact ? `
            <div>
                <h4 class="font-medium text-gray-900 mb-2">Contact Information</h4>
                <p class="text-gray-600">${report.contact}</p>
            </div>
            ` : ''}

            ${report.photo_url || report.image_filename ? `
            <div>
                <h4 class="font-medium text-gray-900 mb-2">Reported Image</h4>
                <img src="${report.photo_url || `${API_BASE_URL}/api/uploads/${report.image_filename}`}"
                    alt="Road damage"
                    class="w-full h-48 object-cover rounded-lg hover:shadow-lg transition"
                    onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\'w-full h-48 bg-gray-100 rounded-lg flex flex-col items-center justify-center text-gray-400\'><i class=\'fas fa-image-slash text-3xl mb-2\'></i><span class=\'text-sm\'>Image not found (Server Restarted)</span></div>'">
            </div>
            ` : `
            <div>
                <h4 class="font-medium text-gray-900 mb-2">Reported Image</h4>
                <div class="w-full h-48 bg-gray-200 rounded-lg flex items-center justify-center">
                    <div class="text-center">
                        <i class="fas fa-image text-gray-400 text-3xl mb-2"></i>
                        <p class="text-gray-500 text-sm">No image attached</p>
                    </div>
                </div>
            </div>
            `}

            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 class="font-semibold text-gray-900 mb-3">Update Status</h4>
                <div class="flex gap-2 items-center">
                    <select id="statusSelect" class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 text-gray-700 font-medium">
                        <option value="">-- Select Status --</option>
                        <option value="submitted">Submitted</option>
                        <option value="under_review">Under Review</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="in_progress">In Progress</option>
                        <option value="completed">Completed</option>
                    </select>
                    <button onclick="updateReportStatusFromModal(${report.id})" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition font-medium">
                        Update
                    </button>
                </div>
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
}

function updateReportStatusFromModal(reportId) {
    const selectElement = document.getElementById('statusSelect');
    const newStatus = selectElement.value;

    if (!newStatus) {
        alert('Please select a status');
        return;
    }

    updateReportStatus(reportId, newStatus);
}

async function updateReportStatus(reportId, newStatus) {
    try {
        console.log(`Updating report ${reportId} to status: ${newStatus}`);

        const response = await fetch(`${API_BASE_URL}/api/admin/update-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({
                report_id: String(reportId),
                status: newStatus
            })
        });

        const data = await response.json();
        console.log('Response:', data);

        if (!response.ok) {
            throw new Error(data.error || `Server error: ${response.status}`);
        }

        console.log('Status updated successfully');

        const statusText = newStatus.replace('_', ' ').toUpperCase();

        showToast('Status Updated', `Report status changed to ${statusText}`, 'success');

        closeModal();
        const currentSection = document.querySelector('.section-content:not(.hidden)');
        if (currentSection && currentSection.id === 'reportsSection') {
            loadReports();
        } else if (currentSection && currentSection.id === 'budgetSection') {
            loadBudgetOptimization();
        }
        loadDashboardData();

    } catch (error) {
        console.error('Error updating status:', error);
        showToast('Update Failed', error.message, 'error');
    }
}

function closeModal() {
    document.getElementById('reportModal').classList.add('hidden');
}

function openProfileModal() {
    const profileModal = document.getElementById('profileModal');
    profileModal.classList.remove('hidden');
    
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (token) {
        fetch(`${API_BASE_URL}/api/admin/profile`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data) {
                document.getElementById('profileName').textContent = data.name || 'Administrator';
                document.getElementById('profileEmail').textContent = data.email || 'admin@roadwatch.ng';
                document.getElementById('profileUsername').textContent = data.username || 'admin';
                document.getElementById('profileRole').textContent = data.role || 'System Administrator';
                document.getElementById('profileDept').textContent = data.department || 'Infrastructure Management';
                document.getElementById('profileLastLogin').textContent = data.last_login || 'Today';
            }
        })
        .catch(error => console.error('Error loading profile:', error));
    }
}

function closeProfileModal() {
    document.getElementById('profileModal').classList.add('hidden');
}

function refreshReports() {
    loadReports();
    loadDashboardData();
}

// Edit report modal
function showEditReportModal(report) {
    const modal = document.getElementById('reportModal');
    const content = document.getElementById('modalContent');

    const statusColor = getStatusColor(report.status);
    const severityColor = getSeverityColor(report.severity_score);

    content.innerHTML = `
        <div class="space-y-6">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-900">Report ID</h4>
                    <p class="text-gray-600">${report.tracking_number}</p>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Update Status</h4>
                    <select id="statusSelect" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500" value="${report.status}">
                        <option value="submitted">Submitted</option>
                        <option value="under_review">Under Review</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="completed">Completed</option>
                    </select>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Location</h4>
                    <input type="text" id="locationEdit" value="${report.location}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Severity (0-10)</h4>
                    <input type="number" id="severityEdit" min="0" max="10" value="${report.severity_score || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <h4 class="font-medium text-gray-900">Damage Type</h4>
                    <input type="text" id="damageTypeEdit" value="${report.damage_type || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">Estimated Cost (₦)</h4>
                    <input type="number" id="costEdit" value="${report.estimated_cost || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
                </div>
            </div>

            <div>
                <h4 class="font-medium text-gray-900 mb-2">Description</h4>
                <textarea id="descriptionEdit" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 h-24">${report.description || ''}</textarea>
            </div>

            ${report.photo_url ? `
            <div>
                <h4 class="font-medium text-gray-900 mb-2">Reported Image</h4>
                <img src="${report.photo_url}" alt="Road damage" class="w-full h-48 object-cover rounded-lg">
            </div>
            ` : ''}

            <div class="flex space-x-3 pt-4 border-t">
                <button onclick="saveReportEdits(${report.id})" class="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700">
                    <i class="fas fa-save mr-2"></i>Save Changes
                </button>
                <button onclick="closeModal()" class="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700">
                    Cancel
                </button>
            </div>
        </div>
    `;

    document.getElementById('statusSelect').value = report.status;
    modal.classList.remove('hidden');
}

async function saveReportEdits(reportId) {
    try {
        const newStatus = document.getElementById('statusSelect').value;

        // Note: You should update this endpoint to support PATCH/PUT requests
        // for full editing, but for now, we only confirm the status update
        const statusResponse = await fetch(`${API_BASE_URL}/api/admin/update-status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({
                report_id: String(reportId),
                status: newStatus
            })
        });

        if (!statusResponse.ok) {
            const error = await statusResponse.json();
            throw new Error(error.error || 'Failed to update report status');
        }

        showToast('Report Updated', 'Status has been successfully updated', 'success');
        closeModal();
        loadReports();
        loadDashboardData();

    } catch (error) {
        console.error('Error saving changes:', error);
        showToast('Save Failed', error.message, 'error');
    }
}

// Budget optimization functions
async function loadBudgetOptimization() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });

        if (!response.ok) throw new Error('Failed to fetch reports');

        const data = await response.json();
        const reports = data.reports || data;

        let totalCost = 0;
        const damageTypeCosts = {};

        reports.forEach(report => {
            const cost = report.estimated_cost || 0;
            totalCost += cost;

            const damageType = report.damage_type || 'Unknown';
            if (!damageTypeCosts[damageType]) {
                damageTypeCosts[damageType] = 0;
            }
            damageTypeCosts[damageType] += cost;
        });

        const totalBudget = 5000000;
        const remaining = totalBudget - totalCost;

        document.getElementById('estimatedRepairCost').textContent = '₦' + totalCost.toLocaleString();
        document.getElementById('budgetRemaining').textContent = '₦' + Math.max(0, remaining).toLocaleString();
        document.getElementById('estimatedReports').textContent = reports.length;

        loadBudgetChart(damageTypeCosts);
        loadPriorityQueue(reports);

    } catch (error) {
        console.error('Error loading budget data:', error);
    }
}

function loadBudgetChart(damageTypeCosts) {
    const ctx = document.getElementById('budgetDoughnutChart');
    if (!ctx) return;

    if (window.budgetChartInstance) {
        window.budgetChartInstance.destroy();
    }

    window.budgetChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(damageTypeCosts),
            datasets: [{
                data: Object.values(damageTypeCosts),
                backgroundColor: ['#22c55e', '#16a34a', '#10b981', '#6ee7b7', '#a7f3d0', '#d1fae5']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function loadPriorityQueue(reports, budget = 5000000) {
    const sorted = [...reports].sort((a, b) => {
        const severityDiff = (b.severity_score || 0) - (a.severity_score || 0);
        if (severityDiff !== 0) return severityDiff;
        return (b.estimated_cost || 0) - (a.estimated_cost || 0);
    });

    const tbody = document.getElementById('priorityQueueBody');
    tbody.innerHTML = '';

    let totalBudget = budget;
    let spent = 0;
    let affordableCount = 0;

    sorted.slice(0, 20).forEach((report, index) => {
        const cost = report.estimated_cost || 0;
        const canAfford = spent + cost <= totalBudget;
        if (canAfford) affordableCount++;

        const row = document.createElement('tr');
        row.className = !canAfford ? 'bg-red-50' : 'bg-white';
        row.dataset.reportId = report.id;
        row.dataset.cost = cost;
        row.dataset.canAfford = canAfford;

        const statusColor = getStatusColor(report.status);
        const severityColor = getSeverityColor(report.severity_score);

        row.innerHTML = `
            <td class="px-4 py-4 whitespace-nowrap">
                <input type="checkbox" class="report-checkbox rounded cursor-pointer" data-cost="${cost}" onchange="updateBulkSelectUI()">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full" style="background-color: ${canAfford ? '#e5e7eb' : '#fee2f2'}; color: ${canAfford ? '#374151' : '#991b1b'};">
                    #${index + 1}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${report.tracking_number}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${report.location}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-medium rounded-full text-white ${severityColor}">
                    ${report.severity_score ? Math.round(report.severity_score * 100) : 'TBD'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">₦${(cost).toLocaleString()}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="viewReport('${report.tracking_number}')" class="text-green-600 hover:text-green-900">View</button>
            </td>
        `;

        tbody.appendChild(row);
        if (canAfford) spent += cost;
    });

    document.getElementById('affordableCount').textContent = affordableCount;
}


// Updated Budget Optimization Function
async function optimizeBudget() {
    try {
        let budgetInput = parseFloat(document.getElementById('budgetInput')?.value) || 5000000;

        if (isNaN(budgetInput) || budgetInput <= 0) {
            showToast('Invalid Budget', 'Please enter a valid budget amount', 'error');
            return;
        }

        // 1. Get Reports from DB
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });

        if (!response.ok) throw new Error('Failed to fetch reports');
        const data = await response.json();
        const reports = data.reports || data;

        // 2. Send to AI Budget API
        showToast('Optimizing', 'Calculating AI allocation...', 'info');
        
        const optResponse = await fetch(`${API_BASE_URL}/api/budget/optimize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeader()
            },
            body: JSON.stringify({
                repairs: reports,
                total_budget: budgetInput,
                strategy: 'priority_weighted'
            })
        });

        if (!optResponse.ok) throw new Error('Optimization failed');
        const result = await optResponse.json();
        const allocations = result.allocations;

        // 3. Update UI
        if (document.getElementById('currentBudgetCard')) {
            document.getElementById('currentBudgetCard').textContent = '₦' + budgetInput.toLocaleString();
        }
        
        // 4. Render Priority Queue using API Data
        renderOptimizedQueue(reports, allocations);
        showToast('Success', 'Budget optimized successfully', 'success');

    } catch (error) {
        console.error('Error optimizing budget:', error);
        showToast('Optimization Failed', error.message, 'error');
    }
}

function renderOptimizedQueue(reports, allocations) {
    const tbody = document.getElementById('priorityQueueBody');
    tbody.innerHTML = '';

    // Sort by Funding Status (Funded First) -> Priority Score
    const sortedReports = [...reports].sort((a, b) => {
        const allocA = allocations[a.tracking_number];
        const allocB = allocations[b.tracking_number];
        
        if (!allocA) return 1;
        if (!allocB) return -1;

        // Prioritize funded items
        if (allocA.Can_Complete !== allocB.Can_Complete) {
            return allocA.Can_Complete ? -1 : 1;
        }
        // Tie-breaker: Priority Score
        return (allocB.Priority_Score || 0) - (allocA.Priority_Score || 0);
    });

    let affordableCount = 0;

    sortedReports.slice(0, 20).forEach((report, index) => {
        const alloc = allocations[report.tracking_number];
        if (!alloc) return;

        const canAfford = alloc.Can_Complete;
        if (canAfford) affordableCount++;

        const row = document.createElement('tr');
        row.className = canAfford ? 'bg-green-50' : 'bg-red-50';

        const severityColor = getSeverityColor(report.severity_score);

        row.innerHTML = `
            <td class="px-4 py-4 whitespace-nowrap">
                <input type="checkbox" class="report-checkbox rounded cursor-pointer">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full" 
                      style="background-color: ${canAfford ? '#dcfce7' : '#fee2f2'}; color: ${canAfford ? '#166534' : '#991b1b'};">
                    ${canAfford ? 'FUNDED' : 'DEFERRED'}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${report.tracking_number}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${report.location}</td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-medium rounded-full text-white ${severityColor}">
                    ${report.severity_score ? Math.round(report.severity_score * 100) : 'TBD'}
                </span>
                <div class="text-xs text-gray-500 mt-1">Score: ${alloc.Priority_Score.toFixed(2)}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                <div>Est: ₦${(alloc['Estimated Cost (₦)']).toLocaleString()}</div>
                <div class="text-xs text-gray-500">Alloc: ₦${(alloc['Allocated Budget (₦)']).toLocaleString()}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button onclick="viewReport('${report.tracking_number}')" class="text-green-600 hover:text-green-900">View</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('affordableCount').textContent = affordableCount;
}

// Bulk select checkboxes
function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.report-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
    updateBulkSelectUI();
}

// Update bulk select UI
function updateBulkSelectUI() {
    const checkboxes = document.querySelectorAll('.report-checkbox:checked');
    const bulkBtn = document.getElementById('bulkScheduleBtn');
    const selectedCount = document.getElementById('selectedCount');

    if (checkboxes.length > 0) {
        bulkBtn.style.display = 'flex';
        selectedCount.textContent = checkboxes.length;
    } else {
        bulkBtn.style.display = 'none';
    }
}

// Bulk schedule selected reports
async function scheduleSelected() {
    const checkboxes = document.querySelectorAll('.report-checkbox:checked');
    if (checkboxes.length === 0) {
        showToast('No Selection', 'Please select at least one report', 'info');
        return;
    }

    const reportIds = [];
    checkboxes.forEach(cb => {
        const row = cb.closest('tr');
        const reportIdCell = row.querySelector('td:nth-child(3)');
        const trackingNumber = reportIdCell.textContent.trim();

        const report = allReports.find(r => r.tracking_number === trackingNumber);
        if (report) reportIds.push(report.id);
    });

    if (reportIds.length === 0) {
        showToast('Error', 'Could not find report IDs', 'error');
        return;
    }

    try {
        let successCount = 0;
        let errorCount = 0;

        for (const reportId of reportIds) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/admin/update-status`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    },
                    body: JSON.stringify({
                        report_id: String(reportId),
                        status: 'scheduled'
                    })
                });

                if (response.ok) {
                    successCount++;
                } else {
                    errorCount++;
                }
            } catch (err) {
                errorCount++;
            }
        }

        if (successCount > 0) {
            showToast('Scheduled', `${successCount} report(s) scheduled successfully`, 'success');

            document.querySelectorAll('.report-checkbox').forEach(cb => cb.checked = false);
            document.getElementById('selectAllCheckbox').checked = false;
            updateBulkSelectUI();

            loadBudgetOptimization();
        }

        if (errorCount > 0) {
            showToast('Partial Error', `${errorCount} report(s) failed to schedule`, 'warning');
        }

    } catch (error) {
        console.error('Error scheduling reports:', error);
        showToast('Error', 'Failed to schedule reports', 'error');
    }
}

// Initialize charts
async function initCharts() {
    let reports = [];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });
        if (!response.ok) throw new Error('Failed to fetch reports');
        const data = await response.json();
        reports = data.reports || data;

        // 1. Reports Over Time Chart
        const ctx1 = document.getElementById('reportsChart');
        if (ctx1) {
            // DESTROY EXISTING CHART IF IT EXISTS
            if (window.reportsChartInstance) {
                window.reportsChartInstance.destroy();
            }

            const dateMap = {};
            const today = new Date();

            for (let i = 29; i >= 0; i--) {
                const date = new Date(today);
                date.setDate(date.getDate() - i);
                const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                dateMap[dateStr] = 0;
            }

            reports.forEach(report => {
                const reportDate = new Date(report.date || report.created_at || new Date());
                const dateStr = reportDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                if (dateStr in dateMap) {
                    dateMap[dateStr]++;
                }
            });

            const labels = Object.keys(dateMap);
            const chartData = Object.values(dateMap);

            const gradient = ctx1.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(22, 163, 74, 0.3)');
            gradient.addColorStop(1, 'rgba(22, 163, 74, 0)');

            window.reportsChartInstance = new Chart(ctx1, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Reports',
                        data: chartData,
                        borderColor: '#16a34a',
                        borderWidth: 3,
                        backgroundColor: gradient,
                        tension: 0.4,
                        fill: true,
                        pointBackgroundColor: '#16a34a',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(200, 200, 200, 0.1)'
                            }
                        }
                    }
                }
            });
        }

        // 2. Damage Types Chart
        const ctx2 = document.getElementById('damageTypesChart');
        if (ctx2) {
            // DESTROY EXISTING CHART IF IT EXISTS
            if (window.damageChartInstance) {
                window.damageChartInstance.destroy();
            }

            const damageTypeMap = { 
                'Pothole': 0, 
                'Longitudinal Crack': 0, 
                'Transverse Crack': 0, 
                'Alligator Crack': 0, 
                'Other Corruption': 0 
            };
            reports.forEach(report => {
                const damageType = report.damage_type || 'Unknown';
                let mapKey = 'Other Corruption';
                
                if (damageType.includes('pothole')) mapKey = 'Pothole';
                else if (damageType.includes('longitudinal')) mapKey = 'Longitudinal Crack';
                else if (damageType.includes('transverse')) mapKey = 'Transverse Crack';
                else if (damageType.includes('alligator')) mapKey = 'Alligator Crack';
                else if (damageType.includes('corruption')) mapKey = 'Other Corruption';
                
                if (mapKey in damageTypeMap) {
                    damageTypeMap[mapKey]++;
                }
            });

            window.damageChartInstance = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(damageTypeMap),
                    datasets: [{
                        data: Object.values(damageTypeMap),
                        backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#86efac', '#6ee7b7']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// Map functionality
let mapInstance = null;
let markerClusterGroup = null;
let allMapMarkers = [];

function initializeMap() {
    try {
        console.log('Initializing map...');
        const lagosCenterCoords = [6.5244, 3.3792];

        if (mapInstance) {
            mapInstance.remove();
        }

        const mapContainer = document.getElementById('reportMap');
        console.log('Map container exists:', !!mapContainer, 'Size:', mapContainer ? mapContainer.offsetWidth + 'x' + mapContainer.offsetHeight : 'N/A');

        mapInstance = L.map('reportMap').setView(lagosCenterCoords, 12);
        console.log('Map instance created:', !!mapInstance);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(mapInstance);

        markerClusterGroup = L.markerClusterGroup({
            chunkedLoading: true,
            maxClusterRadius: 50,
            disableClusteringAtZoom: 15
        });
        mapInstance.addLayer(markerClusterGroup);
        console.log('Marker cluster group added');

        setTimeout(() => {
            mapInstance.invalidateSize();
            console.log('Map size invalidated');
            refreshMapMarkers();
        }, 100);

    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

function getSeverityLabel(score) {
    if (!score) return 'None';
    if (score >= 0.7) return 'High';
    if (score >= 0.3) return 'Medium';
    if (score > 0) return 'Low';
    return 'None';
}

function getSeverityColorName(score) {
    if (!score) return 'gray';
    if (score >= 0.7) return 'red';
    if (score >= 0.3) return 'orange';
    if (score > 0) return 'yellow';
    return 'green';
}

function createMarkerIcon(severity, damageType) {
    const colors = {
        'red': '#ef4444',
        'orange': '#f59e0b',
        'yellow': '#eab308',
        'green': '#22c55e',
        'gray': '#9ca3af'
    };
    const color = colors[severity] || colors['gray'];

    const svgString = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 70" width="50" height="70"><defs><filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.5"/></filter></defs><path d="M25 0 C11 0 0 11 0 25 C0 45 25 70 25 70 S50 45 50 25 C50 11 39 0 25 0 Z" fill="${color}" stroke="white" stroke-width="3" filter="url(#shadow)"/><circle cx="25" cy="25" r="8" fill="white"/></svg>`;
    
    return L.icon({
        iconUrl: 'data:image/svg+xml;base64,' + btoa(svgString),
        iconSize: [50, 70],
        iconAnchor: [25, 70],
        popupAnchor: [0, -70]
    });
}

async function refreshMapMarkers() {
    try {
        markerClusterGroup.clearLayers();
        allMapMarkers = [];

        const severityFilter = document.getElementById('mapSeverityFilter').value;
        const statusFilter = document.getElementById('mapStatusFilter').value;
        const damageFilter = document.getElementById('mapDamageFilter').value;

        let reports;
        
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });

        if (!response.ok) throw new Error('Failed to fetch reports');

        const data = await response.json();
        reports = data.reports || data;
        console.log('Fetched reports from API, count:', reports.length);

        const filteredReports = reports.filter(report => {
            let pass = true;

            if (severityFilter !== 'all') {
                const reportSeverity = getSeverityLabel(report.severity_score);
                if (reportSeverity.toLowerCase() !== severityFilter) pass = false;
            }

            if (statusFilter !== 'all') {
                if (report.status !== statusFilter) pass = false;
            }

            if (damageFilter !== 'all') {
                if (report.damage_type !== damageFilter) pass = false;
            }

            return pass;
        });

        console.log('Creating markers for', filteredReports.length, 'reports');
        
        filteredReports.forEach((report, index) => {
            let lat, lon;

            // Use GPS coordinates from database if available
            if (report.gps_latitude && report.gps_longitude) {
                lat = parseFloat(report.gps_latitude);
                lon = parseFloat(report.gps_longitude);
            } else {
                // Skip reports without GPS coordinates
                return;
            }

            if (!isNaN(lat) && !isNaN(lon)) {
                const severity = getSeverityColorName(report.severity_score);
                const colorMap = {
                    'red': '#ef4444',
                    'orange': '#f59e0b',
                    'yellow': '#eab308',
                    'green': '#22c55e',
                    'gray': '#9ca3af'
                };
                const color = colorMap[severity] || '#9ca3af';

                const circleMarker = L.circleMarker([lat, lon], {
                    radius: 12,
                    fillColor: color,
                    color: '#ffffff',
                    weight: 3,
                    opacity: 1,
                    fillOpacity: 0.9
                });

                const popupContent = `
                    <div class="marker-popup" style="min-width: 250px;">
                        <h4>${report.tracking_number}</h4>
                        <p><strong>Location:</strong> ${report.location}</p>
                        <p><strong>Status:</strong> <span style="color: #6b7280;">${report.status.replace('_', ' ')}</span></p>
                        <p><strong>Damage Type:</strong> ${report.damage_type || 'Unknown'}</p>
                        <p><strong>Severity:</strong> ${report.severity_score ? Math.round(report.severity_score * 100) + '/100' : 'TBD'}</p>
                        ${report.estimated_cost ? `<p><strong>Est. Cost:</strong> ₦${report.estimated_cost.toLocaleString()}</p>` : ''}
                        <p style="font-size: 12px; color: #9ca3af; margin-top: 8px;">
                            Submitted: ${new Date(report.created_at).toLocaleDateString()}
                        </p>
                    </div>
                `;

                circleMarker.bindPopup(popupContent);
                markerClusterGroup.addLayer(circleMarker);
                allMapMarkers.push(circleMarker);
                
                if (index === 0) {
                    console.log('First marker added at', [lat, lon], 'with severity', severity, 'color', color);
                }
            }
        });
        
        console.log('Total markers added:', allMapMarkers.length);

    } catch (error) {
        console.error('Error refreshing map markers:', error);
    }
}

function addNewUser() {
    alert('Add new user functionality would be implemented here');
}

// ADD THIS NEW FUNCTION AT THE BOTTOM OF ADMIN.JS
async function forceReprocess(reportId) {
    try {
        showToast('Processing', 'Triggering AI analysis...', 'info');
        const response = await fetch(`${API_BASE_URL}/api/admin/reprocess/${reportId}`, {
            method: 'POST',
            headers: getAuthHeader()
        });
        
        if (response.ok) {
            showToast('Success', 'AI analysis restarted in background. Refresh in 1 min.', 'success');
        } else {
            throw new Error('Failed to start');
        }
    } catch (e) {
        showToast('Error', 'Could not reprocess report', 'error');
    }
}