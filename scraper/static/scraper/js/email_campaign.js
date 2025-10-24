// ==========================================
// Email Campaign Page JavaScript
// ==========================================

let currentTaskId = null;
let statusCheckInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeForm();
    loadPendingContacts();
    
    // Enable submit button when checkbox is checked
    document.getElementById('confirmEmail').addEventListener('change', function(e) {
        document.getElementById('submitBtn').disabled = !e.target.checked;
    });
    
    // Check pending button
    document.getElementById('checkPendingBtn').addEventListener('click', loadPendingContacts);
    
    // Open sheets button (will be set up after task starts)
    setupOpenSheetsButton();
});

function initializeForm() {
    const form = document.getElementById('emailCampaignForm');
    form.addEventListener('submit', handleFormSubmit);
}

async function loadPendingContacts() {
    const btn = document.getElementById('checkPendingBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="btn-icon"><i class="fas fa-spinner fa-spin"></i></span> Checking...';
    
    try {
        // Since we don't have a direct endpoint to check pending contacts,
        // we'll show estimated values. In production, you'd add an API endpoint for this.
        
        // Simulate loading
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // For now, show placeholder values
        document.getElementById('pendingEmailCount').textContent = '-';
        document.getElementById('activeSenders').textContent = '-';
        
        Toast.info('Check your Google Sheets for exact pending contact count');
        
    } catch (error) {
        Toast.error('Failed to load pending contacts');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span class="btn-icon"><i class="fas fa-sync-alt"></i></span> Check Pending Contacts';
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!document.getElementById('confirmEmail').checked) {
        Toast.warning('Please confirm that you want to start the campaign');
        return;
    }
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon"><i class="fas fa-spinner fa-spin"></i></span> Starting Campaign...';
    
    try {
        const response = await API.post('/startEmailCampaign', {});
        
        currentTaskId = response.task_id;
        
        // Save to local storage
        TaskStorage.addTask({
            task_id: response.task_id,
            type: 'Email Campaign',
            status: 'queued',
            progress: 'Waiting to start...',
            started_at: new Date().toISOString()
        });
        
        Toast.success('Email campaign started successfully!');
        
        // Show progress section
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('taskId').textContent = response.task_id;
        
        // Hide form
        document.getElementById('emailCampaignForm').style.display = 'none';
        
        // Start monitoring
        startStatusMonitoring(response.task_id);
        
    } catch (error) {
        Toast.error(`Failed to start email campaign: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon"><i class="fas fa-rocket"></i></span> Start Email Campaign';
    }
}

function startStatusMonitoring(taskId) {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    // Initial check
    checkTaskStatus(taskId);
    
    // Check every 5 seconds
    statusCheckInterval = setInterval(async () => {
        await checkTaskStatus(taskId);
    }, 5000);
    
    // Setup view task button
    document.getElementById('viewTaskBtn').addEventListener('click', function() {
        window.location.href = `/taskTracker?taskId=${taskId}`;
    });
}

async function checkTaskStatus(taskId) {
    try {
        const status = await API.get(`/taskStatus/${taskId}`);
        updateProgressUI(status);
        
        // Update local storage
        TaskStorage.updateTask(taskId, status);
        
        if (status.status === 'completed') {
            clearInterval(statusCheckInterval);
            Toast.success('Email campaign completed successfully!');
            
            // Show success message
            document.getElementById('progressStatus').innerHTML = '<i class="fas fa-check-circle"></i> Campaign completed! Check Google Sheets for results.';
            document.getElementById('progressBar').style.width = '100%';
            
        } else if (status.status === 'failed') {
            clearInterval(statusCheckInterval);
            Toast.error('Email campaign failed: ' + (status.error || 'Unknown error'));
            
            // Show error message
            document.getElementById('progressStatus').innerHTML = '<i class="fas fa-times-circle"></i> Campaign failed. Check logs for details.';
        }
    } catch (error) {
        console.error('Error checking task status:', error);
    }
}

function updateProgressUI(status) {
    document.getElementById('progressStatus').textContent = status.progress || 'Processing...';
    document.getElementById('taskStatus').textContent = status.status;
    document.getElementById('campaignProgress').textContent = status.progress || 'In progress...';
    
    // Update progress bar
    const progressBar = document.getElementById('progressBar');
    if (status.status === 'completed') {
        progressBar.style.width = '100%';
        progressBar.style.background = 'var(--success-gradient)';
    } else if (status.status === 'failed') {
        progressBar.style.width = '100%';
        progressBar.style.background = 'var(--secondary-gradient)';
    } else if (status.status === 'running') {
        // Animate progress
        const currentWidth = parseInt(progressBar.style.width) || 10;
        progressBar.style.width = Math.min(currentWidth + 3, 95) + '%';
    }
}

function setupOpenSheetsButton() {
    const openSheetsBtn = document.getElementById('openSheetsBtn');
    if (openSheetsBtn) {
        openSheetsBtn.addEventListener('click', function() {
            // Get sheet ID from settings or environment
            // For now, show a message
            Toast.info('Open your configured Google Sheet to view campaign results');
        });
    }
}

