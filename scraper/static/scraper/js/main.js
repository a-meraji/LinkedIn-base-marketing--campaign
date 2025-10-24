// ==========================================
// Main JavaScript - Global Utilities
// ==========================================

// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle) {
        navToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('show');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
                navMenu.classList.remove('show');
            }
        });
    }
});

// ==========================================
// Toast Notification System
// ==========================================
const Toast = {
    show: function(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toastContainer');
        
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-times-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <div class="toast-content">
                <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        container.appendChild(toast);
        
        // Close button
        toast.querySelector('.toast-close').addEventListener('click', function() {
            toast.remove();
        });
        
        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                toast.style.opacity = '0';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    },
    
    success: function(message, duration) {
        this.show(message, 'success', duration);
    },
    
    error: function(message, duration) {
        this.show(message, 'error', duration);
    },
    
    warning: function(message, duration) {
        this.show(message, 'warning', duration);
    },
    
    info: function(message, duration) {
        this.show(message, 'info', duration);
    }
};

// Make Toast globally available
window.Toast = Toast;

// ==========================================
// API Helper Functions
// ==========================================
const API = {
    baseUrl: window.location.origin,
    
    async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);
            
            if (!response.ok) {
                const errorData = await response.text();
                throw new Error(errorData || `HTTP Error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    },
    
    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },
    
    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

// Make API globally available
window.API = API;

// ==========================================
// Task Storage (LocalStorage)
// ==========================================
const TaskStorage = {
    KEY: 'linkedin_tasks',
    
    getAllTasks() {
        const tasks = localStorage.getItem(this.KEY);
        return tasks ? JSON.parse(tasks) : [];
    },
    
    addTask(task) {
        const tasks = this.getAllTasks();
        tasks.unshift(task);
        localStorage.setItem(this.KEY, JSON.stringify(tasks));
    },
    
    updateTask(taskId, updates) {
        const tasks = this.getAllTasks();
        const index = tasks.findIndex(t => t.task_id === taskId);
        if (index !== -1) {
            tasks[index] = { ...tasks[index], ...updates };
            localStorage.setItem(this.KEY, JSON.stringify(tasks));
        }
    },
    
    getTask(taskId) {
        const tasks = this.getAllTasks();
        return tasks.find(t => t.task_id === taskId);
    },
    
    clearOldTasks(daysOld = 7) {
        const tasks = this.getAllTasks();
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysOld);
        
        const filtered = tasks.filter(task => {
            const taskDate = new Date(task.started_at);
            return taskDate > cutoffDate;
        });
        
        localStorage.setItem(this.KEY, JSON.stringify(filtered));
    }
};

// Make TaskStorage globally available
window.TaskStorage = TaskStorage;

// ==========================================
// Utility Functions
// ==========================================
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDuration(startDate, endDate) {
    if (!startDate) return '-';
    
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diff = Math.floor((end - start) / 1000); // seconds
    
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
    return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Make utilities globally available
window.formatDate = formatDate;
window.formatDuration = formatDuration;
window.debounce = debounce;

// ==========================================
// Initialize on page load
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    // Clear old tasks periodically
    TaskStorage.clearOldTasks(7);
    
    console.log('LinkedIn Lead Generation System Loaded');
});

