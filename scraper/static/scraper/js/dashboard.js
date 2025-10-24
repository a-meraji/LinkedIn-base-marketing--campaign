// ==========================================
// Dashboard JavaScript
// ==========================================

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    loadRecentTasks();
    
    // Refresh stats every 30 seconds
    setInterval(loadDashboardStats, 30000);
});

async function loadDashboardStats() {
    const tasks = TaskStorage.getAllTasks();
    
    const stats = {
        scraping: 0,
        email: 0,
        whatsapp: 0,
        completed: 0
    };
    
    for (const task of tasks) {
        // Fetch latest status for running tasks
        if (task.status === 'running' || task.status === 'queued') {
            try {
                const latestStatus = await API.get(`/taskStatus/${task.task_id}`);
                TaskStorage.updateTask(task.task_id, latestStatus);
                
                if (latestStatus.status === 'running' || latestStatus.status === 'queued') {
                    if (latestStatus.type === 'Scraping') stats.scraping++;
                    else if (latestStatus.type === 'Email Campaign') stats.email++;
                    else if (latestStatus.type === 'WhatsApp Campaign') stats.whatsapp++;
                } else if (latestStatus.status === 'completed') {
                    stats.completed++;
                }
            } catch (error) {
                console.error('Error fetching task status:', error);
            }
        } else if (task.status === 'completed') {
            stats.completed++;
        }
    }
    
    // Update UI
    document.getElementById('activeScraping').textContent = stats.scraping;
    document.getElementById('activeEmail').textContent = stats.email;
    document.getElementById('activeWhatsApp').textContent = stats.whatsapp;
    document.getElementById('completedTasks').textContent = stats.completed;
}

function loadRecentTasks() {
    const tasks = TaskStorage.getAllTasks().slice(0, 5);
    const container = document.getElementById('recentTasksList');
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <span class="empty-icon">📋</span>
                <p>No recent tasks found</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="task-card ${task.status}" onclick="viewTaskDetails('${task.task_id}')">
            <div class="task-header">
                <div class="task-type">${getTaskIcon(task.type)} ${task.type}</div>
                <span class="task-status ${task.status}">${task.status}</span>
            </div>
            <div class="task-progress">${task.progress || 'Waiting to start...'}</div>
            <div class="task-meta">
                <span>Started: ${formatDate(task.started_at)}</span>
                ${task.finished_at ? `<span>Finished: ${formatDate(task.finished_at)}</span>` : ''}
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

function viewTaskDetails(taskId) {
    window.location.href = `/taskTracker?taskId=${taskId}`;
}

