// Roadmap Dashboard JavaScript Module
const API_BASE = '/api/v1/roadmap';

// ????????????? ??? ???????? ????????
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

// ???????? ?????? dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE}/dashboard`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        // ?????????? ?????????? ? header
        updateHeaderStats(data);
        
        // ??????????? ??????
        renderBlocks(data.blocks);
        
        // ???????? ????????? ?????
        loadRecentTasks();
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('blocksContainer', 'Failed to load dashboard data');
    }
}

// ?????????? ?????????? ? header
function updateHeaderStats(data) {
    document.getElementById('totalBlocks').textContent = data.total_blocks || 0;
    document.getElementById('totalTasks').textContent = data.total_tasks || 0;
    document.getElementById('totalDone').textContent = data.total_done || 0;
    document.getElementById('overallCompletion').textContent = 
        `${data.overall_completion || 0}%`;
}

// ????????? ??????
function renderBlocks(blocks) {
    const container = document.getElementById('blocksContainer');
    
    if (!blocks || blocks.length === 0) {
        container.innerHTML = '<div class="loading">No blocks found</div>';
        return;
    }
    
    container.innerHTML = blocks.map(block => `
        <div class="block-card">
            <div class="block-code">${escapeHtml(block.block_code || 'N/A')}</div>
            <div class="block-title">${escapeHtml(block.block_title || 'Untitled')}</div>
            <span class="block-status status-${block.block_status || 'planned'}">
                ${escapeHtml(block.block_status || 'planned')}
            </span>
            <div class="block-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${block.completion_percentage || 0}%"></div>
                </div>
                <div class="progress-text">
                    ${block.tasks_done || 0} / ${block.tasks_total || 0} tasks 
                    (${block.completion_percentage || 0}%)
                </div>
            </div>
        </div>
    `).join('');
}

// ???????? ????????? ?????
async function loadRecentTasks() {
    try {
        const response = await fetch(`${API_BASE}/tasks?limit=10`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const tasks = await response.json();
        renderTasks(tasks);
        
    } catch (error) {
        console.error('Error loading tasks:', error);
        showError('tasksContainer', 'Failed to load tasks');
    }
}

// ????????? ?????
function renderTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    
    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<div class="loading">No tasks found</div>';
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="task-card">
            <div class="task-code">${escapeHtml(task.code || 'N/A')}</div>
            <div class="task-title">${escapeHtml(task.title || 'Untitled')}</div>
        </div>
    `).join('');
}

// ??????????? ??????
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="error">${escapeHtml(message)}</div>`;
}

// ????????????? HTML ??? ????????????
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
