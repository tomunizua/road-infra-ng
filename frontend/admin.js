// --- Global Configuration ---
const API_BASE_URL = 'https://roadwatch-ng.onrender.com'; 
const AUTH_TOKEN_KEY = 'adminAuthToken'; // Shared with admin_auth.js

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
document.addEventListener('DOMContentLoaded', function() {
    // If not authenticated, the script stops here (handled by admin_auth.js)
    if (document.getElementById('adminDashboardContent').classList.contains('hidden')) {
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
        showToast('Admin Profile', 'Username: admin@roadwatch.ng | Role: Administrator | Status: Active', 'info');
    });

    // Logout handler
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Navigation items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.nav-item').forEach(nav => {
                nav.classList.remove('active', 'bg-white', 'bg-opacity-20', 'text-white');
                nav.classList.add('text-green-100', 'hover:bg-white', 'hover:bg-opacity-10');
            });
            this.classList.add('active', 'bg-white', 'bg-opacity-20', 'text-white');
            this.classList.remove('text-green-100', 'hover:bg-white', 'hover:bg-opacity-10');
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

    // Load initial data (only if authenticated)
    loadDashboardData();
    loadReports();
    initCharts();
});

function showSection(sectionName) {
    document.querySelectorAll('.section-content').forEach(section => {
        section.classList.add('hidden');
    });

    document.getElementById(sectionName + 'Section').classList.remove('hidden');

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
        }, 100);
    }

    if (sectionName === 'budget') {
        setTimeout(() => {
            loadBudgetOptimization();
        }, 100);
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
                // If API rejects token, force logout (assuming handleLogout is globally available)
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
            in_progress: reports.filter(r => r.status === 'under_review').length,
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
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">Failed to load reports</td></tr>';
    }
}

function loadRecentReports(reports) {
    const container = document.getElementById('recentReportsList');
    container.innerHTML = '';

    if (reports.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center">No recent reports</p>';
        return;
    }

    reports.forEach(report => {
        const div = document.createElement('div');
        div.className = 'flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50';

        const statusColor = getStatusColor(report.status);
        const severityColor = getSeverityColor(report.severity_score);

        div.innerHTML = `
            <div class="flex items-center space-x-4">
                <div class="w-12 h-12 ${severityColor} rounded-lg flex items-center justify-center">
                    <i class="fas fa-exclamation-triangle text-white"></i>
                </div>
                <div>
                    <h4 class="font-medium text-gray-900">${report.location}</h4>
                    <p class="text-sm text-gray-600">${report.damage_type || 'Analysis pending'} • Severity: ${report.severity_score || 'TBD'}/10</p>
                </div>
            </div>
            <div class="text-right">
                <span class="px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                    ${report.status.replace('_', ' ')}
                </span>
                <p class="text-xs text-gray-500 mt-1">${new Date(report.created_at).toLocaleDateString()}</p>
            </div>
        `;

        container.appendChild(div);
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

    if (filteredReports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500">No reports found</td></tr>';
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

    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${report.tracking_number}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${report.location}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <div class="flex flex-col">
                <span class="font-medium">${report.damage_type || 'Analyzing...'}</span>
                <span class="text-xs text-gray-500">${report.ai_confidence ? (report.ai_confidence * 100).toFixed(1) + '% confidence' : 'Pending'}</span>
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <span class="px-2 py-1 text-xs font-medium rounded-full text-white ${severityColor}">
                ${report.severity_score || 'TBD'}/10
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-medium rounded-full ${statusColor}">
                ${report.status.replace('_', ' ')}
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${new Date(report.created_at).toLocaleDateString()}</td>
        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
            <button onclick="viewReport('${report.tracking_number}')" class="text-green-600 hover:text-green-900">View</button>
            <button onclick="editReport('${report.tracking_number}')" class="text-blue-600 hover:text-blue-900">Edit</button>
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
    // Normalized score assuming score is out of 10
    const normalizedScore = score / 10; 
    if (normalizedScore >= 0.8) return 'bg-red-500'; // High (8-10)
    if (normalizedScore >= 0.6) return 'bg-yellow-500'; // Medium-High (6-7.9)
    if (normalizedScore >= 0.4) return 'bg-orange-500'; // Medium-Low (4-5.9)
    return 'bg-green-500'; // Low (0-3.9)
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

// Edit report
async function editReport(trackingNumber) {
    try {
        const report = allReports.find(r => r.tracking_number === trackingNumber);
        if (!report) {
            showToast('Error', 'Report not found', 'error');
            return;
        }

        showEditReportModal(report);

    } catch (error) {
        console.error('Error in edit mode:', error);
        showToast('Error', 'Failed to open edit mode', 'error');
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
                        ${report.severity_score || 'TBD'}/10
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
                    <p class="text-gray-600">${report.ai_confidence ? (report.ai_confidence * 100).toFixed(1) + '%' : 'N/A'}</p>
                </div>
            </div>
            ` : ''}

            <div>
                <h4 class="font-medium text-gray-900 mb-2">Description</h4>
                <p class="text-gray-600">${report.description}</p>
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
                    onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22%3E%3Crect fill=%22%23e5e7eb%22 width=%22400%22 height=%22300%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-family=%22system-ui%22 font-size=%2216%22 fill=%22%239ca3af%22%3EImage unavailable%3C/text%3E%3C/svg%3E'">
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

            <div class="flex space-x-3">
                <button onclick="updateReportStatus(${report.id}, 'scheduled')" class="flex-1 bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 transition font-medium">
                    <i class="fas fa-calendar-check mr-1"></i>Schedule Repair
                </button>
                <button onclick="updateReportStatus(${report.id}, 'under_review')" class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition font-medium">
                    <i class="fas fa-eye mr-1"></i>Mark Under Review
                </button>
                <button onclick="updateReportStatus(${report.id}, 'completed')" class="flex-1 bg-purple-600 text-white py-2 px-4 rounded-md hover:bg-purple-700 transition font-medium">
                    <i class="fas fa-check mr-1"></i>Mark Completed
                </button>
            </div>
        </div>
    `;

    modal.classList.remove('hidden');
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

    if (window.budgetChart instanceof Chart) {
        window.budgetChart.destroy();
    }

    window.budgetChart = new Chart(ctx, {
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
        const severityColor = getSeverityColor(report.severity_score * 100);

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
                    ${report.severity_score || 'TBD'}/10
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

async function optimizeBudget() {
    try {
        let budgetInput = parseFloat(document.getElementById('budgetInput')?.value) || 5000000;

        if (isNaN(budgetInput) || budgetInput <= 0) {
            showToast('Invalid Budget', 'Please enter a valid budget amount', 'error');
            return;
        }

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

        const remaining = budgetInput - totalCost;

        if (document.getElementById('estimatedRepairCost')) {
            document.getElementById('estimatedRepairCost').textContent = '₦' + totalCost.toLocaleString();
        }
        if (document.getElementById('budgetRemaining')) {
            document.getElementById('budgetRemaining').textContent = '₦' + Math.max(0, remaining).toLocaleString();
        }
        if (document.getElementById('currentBudgetCard')) {
            document.getElementById('currentBudgetCard').textContent = '₦' + budgetInput.toLocaleString();
        }

        loadPriorityQueue(reports, budgetInput);

        const reportsAffordable = reports.filter(r => {
            const cost = r.estimated_cost || 0;
            return cost <= budgetInput;
        }).length;

        showToast('Budget Optimized', `Can repair ${reportsAffordable} reports with ₦${budgetInput.toLocaleString()} budget`, 'success');

    } catch (error) {
        console.error('Error optimizing budget:', error);
        showToast('Optimization Failed', error.message, 'error');
    }
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
    // Load reports and calculate over-time data
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });

        if (!response.ok) throw new Error('Failed to fetch reports');

        const data = await response.json();
        const reports = data.reports || data;

        // Group reports by date (last 30 days)
        const dateMap = {};
        const today = new Date();

        for (let i = 29; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            dateMap[dateStr] = 0;
        }

        reports.forEach(report => {
            const reportDate = new Date(report.created_at);
            const dateStr = reportDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (dateStr in dateMap) {
                dateMap[dateStr]++;
            }
        });

        const labels = Object.keys(dateMap);
        const chartData = Object.values(dateMap);

        // Reports over time chart
        const ctx1 = document.getElementById('reportsChart');
        if (ctx1) {
            const gradient = ctx1.getContext('2d').createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, 'rgba(22, 163, 74, 0.3)');
            gradient.addColorStop(1, 'rgba(22, 163, 74, 0)');

            new Chart(ctx1, {
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
    } catch (error) {
        console.error('Error loading reports chart data:', error);
    }

    // Damage types chart - using real data
    if (reports) {
        const damageTypeMap = {};
        reports.forEach(report => {
            const damageType = report.damage_type || 'Unknown';
            damageTypeMap[damageType] = (damageTypeMap[damageType] || 0) + 1;
        });

        const ctx2 = document.getElementById('damageTypesChart');
        if (ctx2) {
            new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(damageTypeMap),
                    datasets: [{
                        data: Object.values(damageTypeMap),
                        backgroundColor: ['#16a34a', '#15803d', '#10b981', '#86efac', '#6ee7b7', '#a7f3d0']
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
    }
}

// Map functionality
let mapInstance = null;
let markerClusterGroup = null;
let allMapMarkers = [];

function initializeMap() {
    try {
        const initialCoords = [6.5244, 3.3792];

        if (mapInstance) {
            mapInstance.remove();
        }

        mapInstance = L.map('reportMap').setView(initialCoords, 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(mapInstance);

        markerClusterGroup = L.markerClusterGroup({
            chunkedLoading: true
        });
        mapInstance.addLayer(markerClusterGroup);

        refreshMapMarkers();

    } catch (error) {
        console.error('Error initializing map:', error);
    }
}

function getSeverityColor(score) {
    if (!score) return 'gray';
    if (score >= 70) return 'red';
    if (score >= 30) return 'orange';
    if (score > 0) return 'green';
    return 'gray';
}

function getSeverityLabel(score) {
    if (!score) return 'None';
    if (score >= 70) return 'High';
    if (score >= 30) return 'Medium';
    if (score > 0) return 'Low';
    return 'None';
}

function createMarkerIcon(severity, damageType) {
    const color = {
        'red': '#ef4444',
        'orange': '#f59e0b',
        'green': '#22c55e',
        'gray': '#9ca3af'
    }[severity] || '#9ca3af';

    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="background-color: ${color}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border: 3px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">
            <i class="fas fa-map-pin" style="font-size: 14px;"></i>
        </div>`,
        iconSize: [40, 40],
        popupAnchor: [0, -20]
    });
}

async function refreshMapMarkers() {
    try {
        markerClusterGroup.clearLayers();
        allMapMarkers = [];

        const severityFilter = document.getElementById('mapSeverityFilter').value;
        const statusFilter = document.getElementById('mapStatusFilter').value;
        const damageFilter = document.getElementById('mapDamageFilter').value;

        const response = await fetch(`${API_BASE_URL}/api/admin/reports`, {
            headers: getAuthHeader()
        });

        if (!response.ok) throw new Error('Failed to fetch reports');

        const data = await response.json();
        const reports = data.reports || data;

        const filteredReports = reports.filter(report => {
            let pass = true;

            if (severityFilter !== 'all') {
                const reportSeverity = getSeverityLabel(report.severity_score * 100);
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

        filteredReports.forEach(report => {
            let lat, lon;

            if (report.location && report.location.includes(',')) {
                const coords = report.location.split(',');
                lat = parseFloat(coords[0].trim());
                lon = parseFloat(coords[1].trim());
            } else {
                lat = 6.5 + (Math.random() - 0.5) * 0.5;
                lon = 3.3 + (Math.random() - 0.5) * 0.5;
            }

            if (!isNaN(lat) && !isNaN(lon)) {
                const severity = getSeverityColor(report.severity_score * 100);
                const icon = createMarkerIcon(severity, report.damage_type);

                const marker = L.marker([lat, lon], { icon: icon });

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

                marker.bindPopup(popupContent);
                markerClusterGroup.addLayer(marker);
                allMapMarkers.push(marker);
            }
        });

    } catch (error) {
        console.error('Error refreshing map markers:', error);
    }
}