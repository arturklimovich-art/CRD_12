// Truth Matrix Dashboard JavaScript
console.log('[Truth Matrix] Initializing...');

// API URLs
const API_BASE = '/api/v1/truth';
const MATRIX_URL = `${API_BASE}/matrix`;
const DASHBOARD_URL = `${API_BASE}/dashboard`;

// State
let matrixData = null;
let dashboardData = null;
let filteredRows = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[Truth Matrix] DOM loaded, fetching data...');
    await loadDashboard();
    await loadMatrix();
    setupFilters();
});

// Load dashboard metrics
async function loadDashboard() {
    try {
        const response = await fetch(DASHBOARD_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        dashboardData = await response.json();
        console.log('[Truth Matrix] Dashboard data loaded:', dashboardData);
        
        updateDashboardStats(dashboardData);
        updateRevisionInfo(dashboardData.active_revision);
    } catch (error) {
        console.error('[Truth Matrix] Error loading dashboard:', error);
        showError('Failed to load dashboard metrics');
    }
}

// Load truth matrix
async function loadMatrix() {
    try {
        const response = await fetch(MATRIX_URL);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        matrixData = await response.json();
        console.log('[Truth Matrix] Matrix data loaded:', matrixData);
        
        filteredRows = matrixData.rows;
        updateMatrixTable(filteredRows);
    } catch (error) {
        console.error('[Truth Matrix] Error loading matrix:', error);
        showError('Failed to load truth matrix');
    }
}

// Update dashboard stats
function updateDashboardStats(data) {
    document.getElementById('totalTasks').textContent = data.total_tasks || 0;
    document.getElementById('verifiedTasks').textContent = data.total_verdicts || 0;
    document.getElementById('withEvidence').textContent = data.verdicts_with_evidence || 0;
    
    // Coverage calculation
    const coverage = data.verification_coverage || 0;
    document.getElementById('coveragePercent').textContent = `${coverage.toFixed(1)}%`;
}

// Update revision info
function updateRevisionInfo(revision) {
    const container = document.querySelector('.revision-card');
    
    if (!revision) {
        container.innerHTML = '<p>⚠️ No active revision found</p>';
        return;
    }
    
    const date = new Date(revision.committed_at).toLocaleString();
    const shortSha = revision.sha256.substring(0, 16);
    
    container.innerHTML = `
        <p><strong>File:</strong> ${revision.file_path}</p>
        <p><strong>SHA256:</strong> ${shortSha}...</p>
        <p><strong>Commit:</strong> ${revision.commit_sha || 'N/A'}</p>
        <p><strong>Date:</strong> ${date}</p>
        <p><strong>Actor:</strong> ${revision.actor || 'system'}</p>
    `;
}

// Update matrix table
function updateMatrixTable(rows) {
    const tbody = document.getElementById('matrixTableBody');
    
    if (!rows || rows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No tasks found</td></tr>';
        return;
    }
    
    // Update mismatch count
    const mismatches = rows.filter(r => 
        r.navigator_status && r.verified_status && 
        r.navigator_status !== r.verified_status
    ).length;
    document.getElementById('mismatchCount').textContent = mismatches;
    
    tbody.innerHTML = rows.map(row => {
        const isMatch = row.navigator_status && row.verified_status && 
                       row.navigator_status === row.verified_status;
        const isMismatch = row.navigator_status && row.verified_status && 
                          row.navigator_status !== row.verified_status;
        const isUnverified = !row.verified_status;
        
        let rowClass = '';
        let matchBadge = '';
        
        if (isMatch) {
            rowClass = 'row-match';
            matchBadge = '<span class="badge badge-match">✅ Match</span>';
        } else if (isMismatch) {
            rowClass = 'row-mismatch';
            matchBadge = '<span class="badge badge-mismatch">⚠️ Mismatch</span>';
        } else if (isUnverified) {
            rowClass = 'row-unverified';
            matchBadge = '<span class="badge badge-unverified">❌ Unverified</span>';
        }
        
        const navStatus = row.navigator_status 
            ? `<span class="status-badge status-${row.navigator_status}">${row.navigator_status}</span>`
            : '-';
        
        const verStatus = row.verified_status
            ? `<span class="status-badge status-${row.verified_status}">${row.verified_status}</span>`
            : '-';
        
        const evidence = row.has_evidence
            ? '<span class="badge badge-evidence">📋 Has Evidence</span>'
            : '<span class="badge badge-no-evidence">🔍 No Evidence</span>';
        
        const verdictDate = row.verdict_ts 
            ? new Date(row.verdict_ts).toLocaleDateString()
            : '-';
        
        return `
            <tr class="${rowClass}">
                <td><strong>${escapeHtml(row.title)}</strong></td>
                <td>${navStatus}</td>
                <td>${verStatus}</td>
                <td>${evidence}</td>
                <td>${verdictDate}</td>
                <td>${matchBadge}</td>
            </tr>
        `;
    }).join('');
}

// Setup filters
function setupFilters() {
    const statusFilter = document.getElementById('filterStatus');
    const searchInput = document.getElementById('searchTask');
    
    statusFilter.addEventListener('change', applyFilters);
    searchInput.addEventListener('input', applyFilters);
}

// Apply filters
function applyFilters() {
    if (!matrixData) return;
    
    const statusFilter = document.getElementById('filterStatus').value;
    const searchText = document.getElementById('searchTask').value.toLowerCase();
    
    filteredRows = matrixData.rows.filter(row => {
        // Status filter
        let statusMatch = true;
        if (statusFilter === 'mismatch') {
            statusMatch = row.navigator_status && row.verified_status && 
                         row.navigator_status !== row.verified_status;
        } else if (statusFilter === 'verified') {
            statusMatch = !!row.verified_status;
        } else if (statusFilter === 'unverified') {
            statusMatch = !row.verified_status;
        } else if (statusFilter === 'with_evidence') {
            statusMatch = row.has_evidence;
        } else if (statusFilter === 'no_evidence') {
            statusMatch = !row.has_evidence;
        }
        
        // Search filter
        const searchMatch = !searchText || 
                          row.title.toLowerCase().includes(searchText);
        
        return statusMatch && searchMatch;
    });
    
    updateMatrixTable(filteredRows);
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    console.error('[Truth Matrix] Error:', message);
    alert(`Error: ${message}`);
}
