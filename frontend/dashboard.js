/**
 * Sawa Digital Tech Solutions - Teacher Dashboard
 * Academic Integrity Platform - Frontend Application
 */

// Console log to indicate dashboard has started
console.log("Sawa Digital Tech Solutions dashboard started");

// Configuration
const API_BASE_URL = 'https://sawadigitaltech.onrender.com';
const UPLOAD_URL = `${API_BASE_URL}/api/upload`;
const REPORTS_URL = `${API_BASE_URL}/api/reports`;

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const reportsTableBody = document.getElementById('reportsTableBody');
const totalReportsEl = document.getElementById('totalReports');
const avgSimilarityEl = document.getElementById('avgSimilarity');
const avgAIRiskEl = document.getElementById('avgAIRisk');
const reportModal = document.getElementById('reportModal');
const modalBody = document.getElementById('modalBody');

// ========================================
// Utility Functions
// ========================================

/**
 * Get score color class based on value
 * @param {number} score - Score value (0-100)
 * @returns {string} CSS class name
 */
function getScoreClass(score) {
    if (score < 20) return 'score-low';
    if (score < 50) return 'score-medium';
    return 'score-high';
}

/**
 * Get risk level class
 * @param {string} riskLevel - Risk level string
 * @returns {string} CSS class name
 */
function getRiskClass(riskLevel) {
    const riskMap = {
        'low': 'risk-low',
        'medium': 'risk-medium',
        'high': 'risk-high',
        'very_high': 'risk-very-high',
        'critical': 'risk-critical'
    };
    return riskMap[riskLevel] || 'risk-low';
}

/**
 * Format date for display
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - 'success' | 'error' | 'info'
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Style the toast
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        z-index: 9999;
        font-weight: 500;
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
    `;
    
    // Add animation keyframes if not exists
    if (!document.getElementById('toast-styles')) {
        const style = document.createElement('style');
        style.id = 'toast-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========================================
// File Upload Functions
// ========================================

/**
 * Upload file to backend
 * @param {File} file - File object to upload
 */
async function uploadFile(file) {
    // Validate file
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        showToast(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`, 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showToast('File too large. Maximum size: 10MB', 'error');
        return;
    }
    
    // Show progress
    uploadProgress.style.display = 'block';
    uploadZone.style.pointerEvents = 'none';
    uploadZone.style.opacity = '0.6';
    
    try {
        // Prepare form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Get token for authentication
        const token = localStorage.getItem('sawa_token');
        
        // Upload file
        const response = await fetch(`${UPLOAD_URL}?token=${token}`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }
        
        const result = await response.json();
        
        // Show success message
        showToast('File uploaded and analyzed successfully!', 'success');
        
        // Refresh reports table
        await refreshReports();
        
        // Reset upload zone
        uploadZone.style.pointerEvents = 'auto';
        uploadZone.style.opacity = '1';
        
    } catch (error) {
        console.error('Upload error:', error);
        showToast(`Error: ${error.message}`, 'error');
        uploadZone.style.pointerEvents = 'auto';
        uploadZone.style.opacity = '1';
    } finally {
        uploadProgress.style.display = 'none';
        fileInput.value = ''; // Reset file input
    }
}

// ========================================
// Reports Functions
// ========================================

/**
 * Fetch all reports from API
 * @param {number} skip - Number of records to skip
 * @param {number} limit - Maximum number of records
 * @returns {Promise<Array>} Array of reports
 */
async function fetchReports(skip = 0, limit = 100) {
    try {
const token = localStorage.getItem('sawa_token');
        const response = await fetch(`${REPORTS_URL}?token=${token}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch reports');
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching reports:', error);
        showToast('Failed to load reports', 'error');
        return { total_reports: 0, reports: [] };
    }
}

/**
 * Refresh reports table
 */
async function refreshReports() {
    const data = await fetchReports(0, 100);
    displayReports(data.reports);
    updateStats(data.reports);
}

/**
 * Display reports in table
 * @param {Array} reports - Array of report objects
 */
function displayReports(reports) {
    if (!reports || reports.length === 0) {
        reportsTableBody.innerHTML = `
            <tr class="empty-state">
                <td colspan="7">
                    <div class="empty-content">
                        <svg width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M24 4L6 12V24C6 36 15 44 24 44C33 44 42 36 42 24V12L24 4Z" stroke="#94a3b8" stroke-width="2" fill="none"/>
                            <path d="M16 24L22 30L32 18" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <p>No reports yet. Upload a file to get started.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    reportsTableBody.innerHTML = reports.map(report => `
        <tr>
            <td>${report.id}</td>
            <td>${report.file_name}</td>
            <td>
                <span class="score-badge ${getScoreClass(report.similarity_score || 0)}">
                    ${(report.similarity_score || 0).toFixed(1)}%
                </span>
            </td>
            <td>
                <span class="score-badge ${getScoreClass(report.ai_risk_score || 0)}">
                    ${(report.ai_risk_score || 0).toFixed(1)}%
                </span>
            </td>
            <td>
                <span class="risk-badge ${getRiskClass('low')}">
                    Low
                </span>
            </td>
            <td>${formatDate(report.uploaded_at)}</td>
            <td>
                <div class="action-buttons">
                    <button class="btn-icon" onclick="viewReport(${report.id})" title="View Details">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M8 5C5.23858 5 3 7.23858 3 10C3 12.7614 5.23858 15 8 15C10.7614 15 13 12.7614 13 10C13 7.23858 10.7614 5 8 5Z" stroke="currentColor" stroke-width="1.5"/>
                            <circle cx="8" cy="10" r="2" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Update statistics cards
 * @param {Array} reports - Array of report objects
 */
function updateStats(reports) {
    // Total reports
    totalReportsEl.textContent = reports.length;
    
    // Average similarity
    if (reports.length > 0) {
        const avgSimilarity = reports.reduce((sum, r) => sum + r.similarity_score, 0) / reports.length;
        avgSimilarityEl.textContent = `${avgSimilarity.toFixed(1)}%`;
        
        // Average AI risk
        const avgAIRisk = reports.reduce((sum, r) => sum + r.ai_risk_score, 0) / reports.length;
        avgAIRiskEl.textContent = `${avgAIRisk.toFixed(1)}%`;
    } else {
        avgSimilarityEl.textContent = '0%';
        avgAIRiskEl.textContent = '0%';
    }
}

/**
 * View report details
 * @param {number} reportId - Report ID to view
 */
async function viewReport(reportId) {
    try {
const token = localStorage.getItem('sawa_token');
        const response = await fetch(`${REPORTS_URL}/${reportId}?token=${token}`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch report details');
        }
        
        const data = await response.json();
        const report = data;
        
        // Display report in modal
        modalBody.innerHTML = `
            <div class="report-details">
                <div class="report-section">
                    <h3>Submission Information</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Report ID:</label>
                            <span>${report.id}</span>
                        </div>
                        <div class="info-item">
                            <label>File Name:</label>
                            <span>${report.file_name}</span>
                        </div>
                        <div class="info-item">
                            <label>Uploaded:</label>
                            <span>${formatDate(report.uploaded_at)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h3>Analysis Results</h3>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>Similarity Score:</label>
                            <span class="score-badge ${getScoreClass(report.similarity_score || 0)}">${(report.similarity_score || 0).toFixed(1)}%</span>
                        </div>
                        <div class="info-item">
                            <label>AI Risk Score:</label>
                            <span class="score-badge ${getScoreClass(report.ai_risk_score || 0)}">${(report.ai_risk_score || 0).toFixed(1)}%</span>
                        </div>
                        <div class="info-item">
                            <label>AI Confidence:</label>
                            <span class="risk-badge ${getRiskClass('low')}">${report.ai_confidence || 'N/A'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h3>Recommendation</h3>
                    <p>${report.recommendation || 'No recommendation available'}</p>
                </div>
            </div>
        `;
        
        // Show modal
        reportModal.style.display = 'flex';
        
    } catch (error) {
        console.error('Error fetching report:', error);
        showToast('Failed to load report details', 'error');
    }
}

/**
 * Close modal
 */
function closeModal() {
    reportModal.style.display = 'none';
}

// ========================================
// Event Listeners
// ========================================

// Drag and drop events
if (uploadZone) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop zone
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.add('drag-over');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, () => {
            uploadZone.classList.remove('drag-over');
        }, false);
    });
    
    // Handle dropped files
    uploadZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    }, false);
    
    // Handle click to upload
    uploadZone.addEventListener('click', (e) => {
        if (e.target !== fileInput && !e.target.closest('button')) {
            fileInput.click();
        }
    });
}

// File input change
if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        const files = e.target.files;
        if (files.length > 0) {
            uploadFile(files[0]);
        }
    });
}

// Close modal on background click
if (reportModal) {
    reportModal.addEventListener('click', (e) => {
        if (e.target === reportModal) {
            closeModal();
        }
    });
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && reportModal.style.display === 'flex') {
        closeModal();
    }
});

// Refresh button
window.refreshReports = refreshReports;

// View report function (global)
window.viewReport = viewReport;

// Close modal function (global)
window.closeModal = closeModal;

// ========================================
// Initialization
// ========================================

// Load reports on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Sawa Digital Tech Solutions dashboard initialized');
    refreshReports();
});

// ========================================
// Export for testing
// ========================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        uploadFile,
        fetchReports,
        refreshReports,
        displayReports,
        getScoreClass,
        getRiskClass,
        formatDate,
        showToast
    };
}
