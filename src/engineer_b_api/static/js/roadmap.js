// Roadmap Dashboard JavaScript - Fixed Version
console.log('[Roadmap] Loading dashboard...');

const API_BASE = '/api';

// Load dashboard on page ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Roadmap] DOM ready, loading dashboard...');
    loadDashboard();
});

// Main dashboard loader
async function loadDashboard() {
    try {
        console.log('[Roadmap] Fetching from', API_BASE + '/roadmap');
        const response = await fetch(API_BASE + '/roadmap');
        
        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ': ' + response.statusText);
        }

        const data = await response.json();
        console.log('[Roadmap] Data received:', data);

        // Update statistics
        updateStats(data);
        
        // Render tasks
        renderTasks(data.tasks || []);
        
        // Hide error message
        hideError();
        
        console.log('[Roadmap] Dashboard loaded successfully');
    } catch (error) {
        console.error('[Roadmap] Error loading dashboard:', error);
        showError('Failed to load dashboard: ' + error.message);
    }
}

// Update header statistics
function updateStats(data) {
    const totalTasks = data.total_tasks || 0;
    const tasks = data.tasks || [];
    
    const doneTasks = tasks.filter(t => t.status === 'done').length;
    const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length;
    const plannedTasks = tasks.filter(t => t.status === 'planned').length;
    const completionPercent = totalTasks > 0 ? Math.round((doneTasks / totalTasks) * 100) : 0;
    
    // Update DOM elements (safe)
    setTextContent('blocks-count', '1'); // E1 stage
    setTextContent('tasks-count', totalTasks);
    setTextContent('done-count', doneTasks);
    setTextContent('in-progress-count', inProgressTasks);
    setTextContent('planned-count', plannedTasks);
    setTextContent('progress-percentage', completionPercent + '%');
    
    console.log('[Roadmap] Stats updated:', {totalTasks, doneTasks, inProgressTasks, plannedTasks, completionPercent});
}

// Render tasks list
function renderTasks(tasks) {
    const container = document.getElementById('recent-tasks');
    if (!container) {
        console.warn('[Roadmap] Element #recent-tasks not found');
        return;
    }
    
    if (tasks.length === 0) {
        container.innerHTML = '<div class=\"alert alert-info\">No tasks found</div>';
        return;
    }
    
    const html = tasks.map(task => {
        const statusBadge = getStatusBadge(task.status);
        const title = escapeHtml(task.title || 'Untitled');
        const code = escapeHtml(task.code || '');
        
        return '<div class=\"card mb-2\">' +
               '<div class=\"card-body\">' +
               '<span class=\"badge ' + statusBadge + ' me-2\">' + task.status + '</span>' +
               '<strong>' + code + '</strong>: ' + title +
               '</div>' +
               '</div>';
    }).join('');
    
    container.innerHTML = html;
    console.log('[Roadmap] Rendered ' + tasks.length + ' tasks');
}

// Get Bootstrap badge class for status
function getStatusBadge(status) {
    switch(status) {
        case 'done': return 'bg-success';
        case 'in_progress': return 'bg-warning';
        case 'planned': return 'bg-secondary';
        default: return 'bg-light';
    }
}

// Show error message
function showError(message) {
    const errorEl = document.getElementById('dashboard-error');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    }
    console.error('[Roadmap] Error shown:', message);
}

// Hide error message
function hideError() {
    const errorEl = document.getElementById('dashboard-error');
    if (errorEl) {
        errorEl.style.display = 'none';
    }
}

// Safe set text content
function setTextContent(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
    } else {
        console.warn('[Roadmap] Element #' + id + ' not found');
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

console.log('[Roadmap] Script loaded');
