// ==========================================
// Task Tracker Page JavaScript
// ==========================================

let allTasks = [];
let filteredTasks = [];
let currentTypeFilter = 'all';
let currentStatusFilter = 'all';
let refreshInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    loadTasks();
    setupFilters();
    setupSearch();
    setupRefresh();
    
    // Check for taskId in URL
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('taskId');
    if (taskId) {
        searchSpecificTask(taskId);
    }
    
    // Auto-refresh every 10 seconds
    refreshInterval = setInterval(loadTasks, 10000);
});

async function loadTasks() {
    try {
        // Get tasks from local storage
        const localTasks = TaskStorage.getAllTasks();
        
        // Fetch latest status for running tasks
        for (const task of localTasks) {
            if (task.status === 'running' || task.status === 'queued') {
                try {
                    const latestStatus = await API.get(`/taskStatus/${task.task_id}`);
                    TaskStorage.updateTask(task.task_id, latestStatus);
                    Object.assign(task, latestStatus);
                } catch (error) {
                    console.error(`Error fetching status for task ${task.task_id}:`, error);
                }
            }
        }
        
        allTasks = TaskStorage.getAllTasks();
        applyFilters();
        
    } catch (error) {
        console.error('Error loading tasks:', error);
        Toast.error('Failed to load tasks');
    }
}

function setupFilters() {
    // Type filters
    document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentTypeFilter = this.dataset.filter;
            applyFilters();
        });
    });
    
    // Status filters
    document.querySelectorAll('.filter-btn[data-status]').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn[data-status]').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentStatusFilter = this.dataset.status;
            applyFilters();
        });
    });
}

function setupSearch() {
    const searchBtn = document.getElementById('searchTaskBtn');
    const searchInput = document.getElementById('taskIdSearch');
    
    searchBtn.addEventListener('click', function() {
        const taskId = searchInput.value.trim();
        if (taskId) {
            searchSpecificTask(taskId);
        }
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const taskId = this.value.trim();
            if (taskId) {
                searchSpecificTask(taskId);
            }
        }
    });
}

async function searchSpecificTask(taskId) {
    try {
        Toast.info('Searching for task...');
        
        const status = await API.get(`/taskStatus/${taskId}`);
        
        // Update local storage
        const existingTask = TaskStorage.getTask(taskId);
        if (existingTask) {
            TaskStorage.updateTask(taskId, status);
        } else {
            TaskStorage.addTask({ task_id: taskId, ...status });
        }
        
        // Show task details in modal
        showTaskModal(status);
        
        // Reload tasks
        await loadTasks();
        
    } catch (error) {
        Toast.error('Task not found or error occurred');
        console.error(error);
    }
}

function setupRefresh() {
    document.getElementById('refreshTasks').addEventListener('click', async function() {
        this.disabled = true;
        this.innerHTML = '<span class="btn-icon"><i class="fas fa-spinner fa-spin"></i></span> Refreshing...';
        
        await loadTasks();
        
        this.disabled = false;
        this.innerHTML = '<span class="btn-icon"><i class="fas fa-sync-alt"></i></span> Refresh';
        Toast.success('Tasks refreshed');
    });
}

function applyFilters() {
    filteredTasks = allTasks.filter(task => {
        const typeMatch = currentTypeFilter === 'all' || task.type === currentTypeFilter;
        const statusMatch = currentStatusFilter === 'all' || task.status === currentStatusFilter;
        return typeMatch && statusMatch;
    });
    
    renderTasks();
}

function renderTasks() {
    const container = document.getElementById('tasksContainer');
    
    if (filteredTasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon"><i class="fas fa-clipboard-list"></i></span>
                <p>No tasks found</p>
                <small>Tasks will appear here once you start scraping or campaigns</small>
            </div>
        `;
        return;
    }
    
    container.innerHTML = filteredTasks.map(task => `
        <div class="task-card ${task.status}" onclick="showTaskModal(${JSON.stringify(task).replace(/"/g, '&quot;')})">
            <div class="task-header">
                <div class="task-type">${getTaskIcon(task.type)} ${task.type}</div>
                <span class="task-status ${task.status}">${task.status}</span>
            </div>
            <div class="task-progress">${task.progress || 'Waiting to start...'}</div>
            <div class="task-meta">
                <span><i class="fas fa-fingerprint"></i> ${task.task_id.substring(0, 8)}...</span>
                <span><i class="far fa-clock"></i> Started: ${formatDate(task.started_at)}</span>
                ${task.finished_at ? `<span><i class="fas fa-check"></i> Finished: ${formatDate(task.finished_at)}</span>` : ''}
                ${!task.finished_at && task.started_at ? `<span><i class="fas fa-hourglass-half"></i> Duration: ${formatDuration(task.started_at, null)}</span>` : ''}
            </div>
        </div>
    `).join('');
}

function getTaskIcon(type) {
    const icons = {
        'Scraping': '<i class="fas fa-search"></i>',
        'Email Campaign': '<i class="fas fa-envelope"></i>',
        'WhatsApp Campaign': '<i class="fab fa-whatsapp"></i>'
    };
    return icons[type] || '<i class="fas fa-clipboard-list"></i>';
}

function showTaskModal(task) {
    const modal = document.getElementById('taskModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = `
        <div class="task-details-full">
            <div class="detail-row">
                <span class="detail-label">Task ID:</span>
                <span class="detail-value">${task.task_id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Type:</span>
                <span class="detail-value">${getTaskIcon(task.type)} ${task.type}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="task-status ${task.status}">${task.status}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Progress:</span>
                <span class="detail-value">${task.progress || 'N/A'}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Started At:</span>
                <span class="detail-value">${formatDate(task.started_at)}</span>
            </div>
            ${task.finished_at ? `
                <div class="detail-row">
                    <span class="detail-label">Finished At:</span>
                    <span class="detail-value">${formatDate(task.finished_at)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Duration:</span>
                    <span class="detail-value">${formatDuration(task.started_at, task.finished_at)}</span>
                </div>
            ` : `
                <div class="detail-row">
                    <span class="detail-label">Running Time:</span>
                    <span class="detail-value">${formatDuration(task.started_at, null)}</span>
                </div>
            `}
            ${task.error ? `
                <div class="detail-row error">
                    <span class="detail-label">Error:</span>
                    <span class="detail-value">${task.error}</span>
                </div>
            ` : ''}
        </div>
        <style>
            .task-details-full { display: flex; flex-direction: column; gap: 1rem; }
            .detail-row { display: flex; justify-content: space-between; padding: 0.75rem; background: var(--bg-secondary); border-radius: 8px; }
            .detail-row.error { background: #ffebee; }
            .detail-label { font-weight: 600; color: var(--text-secondary); }
            .detail-value { color: var(--text-primary); font-family: 'Courier New', monospace; }
        </style>
    `;
    
    modal.classList.add('show');
}

// Close modal
document.getElementById('closeModal').addEventListener('click', function() {
    document.getElementById('taskModal').classList.remove('show');
});

// Close modal when clicking outside
document.getElementById('taskModal').addEventListener('click', function(e) {
    if (e.target === this) {
        this.classList.remove('show');
    }
});

// Cleanup interval on page unload
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

