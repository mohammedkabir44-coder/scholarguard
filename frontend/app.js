/**
 * ScholarGuard Teacher Dashboard - Frontend Application
 * Commercial-Ready SaaS with Authentication & PDF Export
 */

// ========================================
// CONFIGURATION
// ========================================
const API_BASE_URL = 'https://scholarguard.onrender.com';

// ========================================
// DOM ELEMENTS
// ========================================
const authSection = document.getElementById('authSection');
const dashboardSection = document.getElementById('dashboardSection');
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginFormElement = document.getElementById('loginFormElement');
const registerFormElement = document.getElementById('registerFormElement');
const showRegisterLink = document.getElementById('showRegister');
const showLoginLink = document.getElementById('showLogin');
const navMenu = document.getElementById('navMenu');

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const loadingSpinner = document.getElementById('loadingSpinner');
const statusMessage = document.getElementById('statusMessage');
const reportsTableBody = document.getElementById('reportsTableBody');
const reportsCount = document.getElementById('reportsCount');
const emptyState = document.getElementById('emptyState');

// ========================================
// AUTHENTICATION STATE
// ========================================

/**
 * Get JWT token from localStorage
 */
function getToken() {
    return localStorage.getItem('scholarguard_token');
}

/**
 * Get user data from localStorage
 */
function getUser() {
    const userData = localStorage.getItem('scholarguard_user');
    return userData ? JSON.parse(userData) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getToken();
}

/**
 * Save authentication data
 */
function saveAuth(token, user) {
    localStorage.setItem('scholarguard_token', token);
    localStorage.setItem('scholarguard_user', JSON.stringify(user));
}

/**
 * Clear authentication data
 */
function clearAuth() {
    localStorage.removeItem('scholarguard_token');
    localStorage.removeItem('scholarguard_user');
}

/**
 * Get authorization header for API requests
 */
function getAuthHeader() {
    const token = getToken();
    if (!token) {
        throw new Error('No authentication token found');
    }
    return {
        'Authorization': `Bearer ${token}`
    };
}

// ========================================
// UI STATE MANAGEMENT
// ========================================

/**
 * Show login form
 */
function showLoginForm() {
    loginForm.classList.remove('hidden');
    registerForm.classList.add('hidden');
}

/**
 * Show register form
 */
function showRegisterForm() {
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
}

/**
 * Show dashboard
 */
function showDashboard() {
    authSection.classList.add('hidden');
    dashboardSection.classList.remove('hidden');
    updateNavMenu();
}

/**
 * Show authentication section
 */
function showAuthSection() {
    authSection.classList.remove('hidden');
    dashboardSection.classList.add('hidden');
    updateNavMenu();
}

/**
 * Update navigation menu based on auth state
 */
function updateNavMenu() {
    if (isAuthenticated()) {
        const user = getUser();
        navMenu.innerHTML = `
            <li><a href="#dashboard">Dashboard</a></li>
            <li><a href="#reports">Reports</a></li>
            <li><a href="#" id="logoutLink">Logout (${user?.email || 'User'})</a></li>
        `;
        
        // Add logout event listener
        document.getElementById('logoutLink').addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    } else {
        navMenu.innerHTML = `
            <li><a href="#features">Features</a></li>
            <li><a href="#pricing">Pricing</a></li>
            <li><a href="#about">About</a></li>
        `;
    }
}

// ========================================
// AUTHENTICATION FUNCTIONS
// ========================================

/**
 * Register new user
 */
async function registerUser(email, password, fullName) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password,
                full_name: fullName
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            const errorMessage = error.detail || 'Registration failed';
            alert(`Registration Error: ${errorMessage}`);
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        // Save auth data
        saveAuth(data.access_token, data.user);
        
        return data;
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    } finally {
        // Always hide loading spinner and re-enable button
        const submitBtn = registerFormElement?.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Create Account';
            submitBtn.disabled = false;
        }
    }
}

/**
 * Login user
 */
async function loginUser(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            const errorMessage = error.detail || 'Login failed';
            alert(`Login Error: ${errorMessage}`);
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        // Save auth data
        saveAuth(data.access_token, data.user);
        
        return data;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    } finally {
        // Always hide loading spinner and re-enable button
        const submitBtn = loginFormElement?.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Sign In';
            submitBtn.disabled = false;
        }
    }
}

/**
 * Logout user
 */
function logout() {
    clearAuth();
    showAuthSection();
    showLoginForm();
    updateNavMenu();
    console.log('User logged out');
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Get badge class based on score value
 * Green: < 30, Yellow: 30-60, Red: > 60
 */
function getScoreBadgeClass(score) {
    const numScore = parseInt(score, 10);
    if (numScore < 30) return 'badge-green';
    if (numScore <= 60) return 'badge-yellow';
    return 'badge-red';
}

/**
 * Get confidence badge class
 */
function getConfidenceClass(confidence) {
    const lowerConfidence = confidence.toLowerCase();
    if (lowerConfidence === 'high') return 'badge-confidence high';
    if (lowerConfidence === 'medium') return 'badge-confidence medium';
    return 'badge-confidence low';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInMins = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMs / 3600000);
    const diffInDays = Math.floor(diffInMs / 86400000);

    if (diffInMins < 1) return 'Just now';
    if (diffInMins < 60) return `${diffInMins} minute${diffInMins > 1 ? 's' : ''} ago`;
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show status message
 */
function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusMessage.className = 'status-message';
    }, 5000);
}

/**
 * Hide status message
 */
function hideStatus() {
    statusMessage.className = 'status-message';
}

// ========================================
// TABLE MANAGEMENT
// ========================================

/**
 * Create a table row from report data
 */
function createTableRow(report) {
    const row = document.createElement('tr');
    
    const similarityBadgeClass = getScoreBadgeClass(report.similarity_score);
    const aiRiskBadgeClass = getScoreBadgeClass(report.ai_risk_score);
    const confidenceClass = getConfidenceClass(report.ai_confidence);
    
    row.innerHTML = `
        <td><strong>${escapeHtml(report.file_name)}</strong></td>
        <td>${formatDate(report.uploaded_at)}</td>
        <td><span class="badge ${similarityBadgeClass}">${report.similarity_score}%</span></td>
        <td><span class="badge ${aiRiskBadgeClass}">${report.ai_risk_score}%</span></td>
        <td><span class="${confidenceClass}">${escapeHtml(report.ai_confidence)}</span></td>
        <td><span class="badge-recommendation" title="${escapeHtml(report.recommendation)}">${escapeHtml(report.recommendation)}</span></td>
        <td>
            <button class="btn-download-pdf" data-submission-id="${report.id}" title="Download PDF Report">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 2V10M8 10L5 7M8 10L11 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M2 12V14H14V12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                PDF
            </button>
        </td>
    `;
    
    // Add event listener to download button
    const downloadBtn = row.querySelector('.btn-download-pdf');
    downloadBtn.addEventListener('click', () => downloadPDF(report.id));
    
    return row;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Add a report to the table
 */
function addReportToTable(report) {
    // Hide empty state
    emptyState.classList.add('hidden');
    
    // Create and prepend row
    const row = createTableRow(report);
    reportsTableBody.insertBefore(row, reportsTableBody.firstChild);
    
    // Update count
    updateReportsCount();
}

/**
 * Update reports count display
 */
function updateReportsCount() {
    const count = reportsTableBody.querySelectorAll('tr').length;
    reportsCount.textContent = `${count} submission${count !== 1 ? 's' : ''}`;
}

/**
 * Clear the table
 */
function clearTable() {
    reportsTableBody.innerHTML = '';
    emptyState.classList.remove('hidden');
    updateReportsCount();
}

/**
 * Populate table with multiple reports
 */
function populateTable(reports) {
    clearTable();
    
    if (reports && reports.length > 0) {
        emptyState.classList.add('hidden');
        
        // Sort by date (newest first)
        const sortedReports = reports.sort((a, b) => 
            new Date(b.uploaded_at) - new Date(a.uploaded_at)
        );
        
        sortedReports.forEach(report => {
            const row = createTableRow(report);
            reportsTableBody.appendChild(row);
        });
        
        updateReportsCount();
    } else {
        emptyState.classList.remove('hidden');
    }
}

// ========================================
// API FUNCTIONS
// ========================================

/**
 * Upload file to backend
 */
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        // Show loading spinner
        loadingSpinner.classList.add('active');
        hideStatus();
        
        const authHeader = getAuthHeader();
        
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
            method: 'POST',
            headers: authHeader,
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            let errorMessage = 'Unknown error';
            if (errorData.detail) {
                if (Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail[0].msg;
                } else {
                    errorMessage = errorData.detail;
                }
            } else if (errorData.message) {
                errorMessage = errorData.message;
            }
            alert('Upload Error: ' + errorMessage);
            throw new Error('Upload failed');
        }
        
        const data = await response.json();
        
        // Show success message
        showStatus(`File uploaded successfully! Similarity: ${data.similarity_score}%, AI Risk: ${data.ai_risk_score}%`, 'success');
        
        // Add to table
        addReportToTable(data);
        
        // Clear file input
        fileInput.value = '';
        
        return data;
        
    } catch (error) {
        // Show error message
        showStatus(`Error uploading file: ${error.message}`, 'error');
        console.error('Upload error:', error);
        alert(`Upload Error: ${error.message}`);
        
        // Clear file input
        fileInput.value = '';
        
        throw error;
    } finally {
        // Always hide loading spinner
        loadingSpinner.classList.remove('active');
    }
}

/**
 * Fetch all reports from backend
 */
async function fetchReports() {
    try {
        const authHeader = getAuthHeader();
        
        const response = await fetch(`${API_BASE_URL}/api/reports`, {
            headers: authHeader
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Populate table with reports
        if (data.reports && Array.isArray(data.reports)) {
            populateTable(data.reports);
        }
        
        return data;
        
    } catch (error) {
        console.error('Error fetching reports:', error);
        showStatus('Error loading reports. Please refresh the page.', 'error');
        throw error;
    }
}

/**
 * Download PDF report
 */
async function downloadPDF(submissionId) {
    try {
        const authHeader = getAuthHeader();
        
        // Open PDF in new tab/window
        const url = `${API_BASE_URL}/api/reports/${submissionId}/pdf`;
        window.open(url, '_blank');
        
    } catch (error) {
        console.error('Error downloading PDF:', error);
        showStatus('Error downloading PDF. Please try again.', 'error');
    }
}

// ========================================
// EVENT HANDLERS
// ========================================

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    if (!file) return;
    
    // Validate file type
    const allowedTypes = ['.pdf', '.docx', '.doc', '.txt'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExtension)) {
        showStatus('Invalid file type. Please upload PDF, DOCX, or TXT files only.', 'error');
        return;
    }
    
    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showStatus('File too large. Maximum size is 10MB.', 'error');
        return;
    }
    
    // Upload file
    uploadFile(file).catch(error => {
        console.error('Upload failed:', error);
    });
}

/**
 * Handle drag over event
 */
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add('dragover');
}

/**
 * Handle drag leave event
 */
function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('dragover');
}

/**
 * Handle drop event
 */
function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

/**
 * Handle click event on dropzone
 */
function handleClick(e) {
    // Prevent triggering when clicking on actual file input
    if (e.target === fileInput) {
        return;
    }
    fileInput.click();
}

/**
 * Handle file input change
 */
function handleFileInputChange(e) {
    const files = e.target.files;
    
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

/**
 * Handle login form submission
 */
async function handleLoginSubmit(e) {
    e.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const submitBtn = loginFormElement.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Signing in...';
        submitBtn.disabled = true;
        
        await loginUser(email, password);
        
        showStatus('Login successful! Welcome back.', 'success');
        showDashboard();
        
        // Fetch reports
        await fetchReports();
        
        // Reset form
        loginFormElement.reset();
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        
    } catch (error) {
        showStatus(error.message || 'Login failed. Please try again.', 'error');
        const submitBtn = loginFormElement.querySelector('button[type="submit"]');
        submitBtn.textContent = 'Sign In';
        submitBtn.disabled = false;
    }
}

/**
 * Handle register form submission
 */
async function handleRegisterSubmit(e) {
    e.preventDefault();
    
    const fullName = document.getElementById('registerName').value;
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    
    try {
        const submitBtn = registerFormElement.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Creating account...';
        submitBtn.disabled = true;
        
        await registerUser(email, password, fullName);
        
        showStatus('Account created successfully! Welcome to ScholarGuard.', 'success');
        showDashboard();
        
        // Fetch reports
        await fetchReports();
        
        // Reset form
        registerFormElement.reset();
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        
    } catch (error) {
        showStatus(error.message || 'Registration failed. Please try again.', 'error');
        const submitBtn = registerFormElement.querySelector('button[type="submit"]');
        submitBtn.textContent = 'Create Account';
        submitBtn.disabled = false;
    }
}

// ========================================
// EVENT LISTENERS
// ========================================

// Auth form toggles
if (showRegisterLink) {
    showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        showRegisterForm();
    });
}

if (showLoginLink) {
    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        showLoginForm();
    });
}

// Login form submission
if (loginFormElement) {
    loginFormElement.addEventListener('submit', handleLoginSubmit);
}

// Register form submission
if (registerFormElement) {
    registerFormElement.addEventListener('submit', handleRegisterSubmit);
}

// Dropzone events
if (dropzone) {
    dropzone.addEventListener('dragover', handleDragOver);
    dropzone.addEventListener('dragleave', handleDragLeave);
    dropzone.addEventListener('drop', handleDrop);
    dropzone.addEventListener('click', handleClick);
}

// File input events
if (fileInput) {
    fileInput.addEventListener('change', handleFileInputChange);
}

// ========================================
// INITIALIZATION
// ========================================

/**
 * Initialize application
 */
async function init() {
    console.log('ScholarGuard Teacher Dashboard initialized');
    
    // Check authentication state
    if (isAuthenticated()) {
        showDashboard();
        try {
            await fetchReports();
        } catch (error) {
            console.error('Initialization error:', error);
            showAuthSection();
            showLoginForm();
        }
    } else {
        showAuthSection();
        showLoginForm();
    }
}

// Run initialization when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM already loaded
    init();
}

// ========================================
// EXPORT FOR TESTING
// ========================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        uploadFile,
        fetchReports,
        downloadPDF,
        createTableRow,
        populateTable,
        clearTable,
        loginUser,
        registerUser,
        logout,
        getScoreBadgeClass,
        getConfidenceClass,
        formatDate,
        escapeHtml,
        isAuthenticated,
        getToken,
        getUser
    };
}
