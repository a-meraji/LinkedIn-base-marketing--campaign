// ==========================================
// Scraping Page JavaScript
// ==========================================

// Country and Job data
const COUNTRIES = [
    { continent: 'Asia', items: ['China', 'Japan', 'South Korea', 'India', 'Turkey', 'United Arab Emirates', 'Qatar', 'Saudi Arabia', 'Kuwait', 'Bahrain', 'Oman', 'Singapore', 'Malaysia', 'Thailand', 'Indonesia', 'Philippines', 'Vietnam', 'Kazakhstan', 'Azerbaijan'] },
    { continent: 'Europe', items: ['Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Cyprus', 'Czechia', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 'Romania', 'Russia', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom', 'Vatican'] },
    { continent: 'North America', items: ['United States', 'Canada'] },
    { continent: 'Oceania', items: ['Australia', 'New Zealand'] }
];

const DEFAULT_JOBS = [
    'PHP Developer',
    'WordPress Developer',
    'Django Developer',
    'Flutter Developer',
    'Python Developer',
    'React Developer',
    'Node.js Developer',
    'Full Stack Developer',
    'Data Scientist',
    'DevOps Engineer'
];

let selectedCountries = [];
let selectedJobs = [];
let currentTaskId = null;
let statusCheckInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeMultiSelects();
    initializeAdvancedOptions();
    initializeForm();
    updateCombinationsPreview();
});

// ==========================================
// Multi-Select Initialization
// ==========================================
function initializeMultiSelects() {
    // Countries
    const countriesList = document.getElementById('countriesList');
    COUNTRIES.forEach(group => {
        group.items.forEach(country => {
            const option = createOptionElement(country, 'country');
            countriesList.appendChild(option);
        });
    });
    
    // Jobs
    const jobsList = document.getElementById('jobsList');
    DEFAULT_JOBS.forEach(job => {
        const option = createOptionElement(job, 'job');
        jobsList.appendChild(option);
    });
    
    // Trigger handlers
    setupMultiSelectTrigger('countries', 'countriesTrigger', 'countriesDropdown');
    setupMultiSelectTrigger('jobs', 'jobsTrigger', 'jobsDropdown');
    
    // Search handlers
    setupSearch('countrySearch', 'countriesList');
    setupSearch('jobSearch', 'jobsList');
    
    // Select all handlers
    document.getElementById('selectAllCountries').addEventListener('change', function(e) {
        selectAll('country', e.target.checked);
    });
    
    document.getElementById('selectAllJobs').addEventListener('change', function(e) {
        selectAll('job', e.target.checked);
    });
    
    // Add custom job
    document.getElementById('addCustomJob').addEventListener('click', addCustomJob);
}

function createOptionElement(value, type) {
    const div = document.createElement('div');
    div.className = 'option-item';
    div.innerHTML = `
        <input type="checkbox" value="${value}" data-type="${type}" id="${type}-${value.replace(/\s+/g, '-')}">
        <label for="${type}-${value.replace(/\s+/g, '-')}">${value}</label>
    `;
    
    const checkbox = div.querySelector('input');
    checkbox.addEventListener('change', function() {
        handleSelectionChange(value, type, this.checked);
    });
    
    return div;
}

function setupMultiSelectTrigger(type, triggerId, dropdownId) {
    const trigger = document.getElementById(triggerId);
    const dropdown = document.getElementById(dropdownId);
    
    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.classList.toggle('show');
        trigger.classList.toggle('active');
        
        // Close other dropdown
        const otherType = type === 'countries' ? 'jobs' : 'countries';
        document.getElementById(`${otherType}Dropdown`).classList.remove('show');
        document.getElementById(`${otherType}Trigger`).classList.remove('active');
    });
    
    // Close when clicking outside
    document.addEventListener('click', function(e) {
        if (!trigger.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
            trigger.classList.remove('active');
        }
    });
}

function setupSearch(searchId, listId) {
    const searchInput = document.getElementById(searchId);
    const list = document.getElementById(listId);
    
    searchInput.addEventListener('input', debounce(function() {
        const query = this.value.toLowerCase();
        const options = list.querySelectorAll('.option-item');
        
        options.forEach(option => {
            const label = option.querySelector('label').textContent.toLowerCase();
            option.style.display = label.includes(query) ? 'flex' : 'none';
        });
    }, 300));
}

function handleSelectionChange(value, type, isChecked) {
    if (type === 'country') {
        if (isChecked) {
            if (!selectedCountries.includes(value)) {
                selectedCountries.push(value);
            }
        } else {
            selectedCountries = selectedCountries.filter(c => c !== value);
        }
        updateSelectedTags('selectedCountries', selectedCountries, 'country');
        updateTriggerText('countriesTrigger', selectedCountries, 'countries');
    } else if (type === 'job') {
        if (isChecked) {
            if (!selectedJobs.includes(value)) {
                selectedJobs.push(value);
            }
        } else {
            selectedJobs = selectedJobs.filter(j => j !== value);
        }
        updateSelectedTags('selectedJobs', selectedJobs, 'job');
        updateTriggerText('jobsTrigger', selectedJobs, 'job titles');
    }
    
    updateCombinationsPreview();
}

function selectAll(type, checked) {
    if (type === 'country') {
        const allCountries = COUNTRIES.flatMap(g => g.items);
        document.querySelectorAll('[data-type="country"]').forEach(cb => {
            cb.checked = checked;
        });
        selectedCountries = checked ? [...allCountries] : [];
        updateSelectedTags('selectedCountries', selectedCountries, 'country');
        updateTriggerText('countriesTrigger', selectedCountries, 'countries');
    } else if (type === 'job') {
        document.querySelectorAll('[data-type="job"]').forEach(cb => {
            cb.checked = checked;
        });
        selectedJobs = checked ? [...DEFAULT_JOBS] : [];
        updateSelectedTags('selectedJobs', selectedJobs, 'job');
        updateTriggerText('jobsTrigger', selectedJobs, 'job titles');
    }
    
    updateCombinationsPreview();
}

function updateSelectedTags(containerId, items, type) {
    const container = document.getElementById(containerId);
    container.innerHTML = items.map(item => `
        <div class="tag">
            <span>${item}</span>
            <span class="tag-remove" onclick="removeSelection('${item}', '${type}')">&times;</span>
        </div>
    `).join('');
}

function removeSelection(value, type) {
    const checkbox = document.querySelector(`input[value="${value}"][data-type="${type}"]`);
    if (checkbox) {
        checkbox.checked = false;
        handleSelectionChange(value, type, false);
    }
}

function updateTriggerText(triggerId, items, label) {
    const trigger = document.getElementById(triggerId);
    const textSpan = trigger.querySelector('.selected-text');
    
    if (items.length === 0) {
        textSpan.textContent = `Select ${label}...`;
        textSpan.style.color = 'var(--text-secondary)';
    } else if (items.length === 1) {
        textSpan.textContent = items[0];
        textSpan.style.color = 'var(--text-primary)';
    } else {
        textSpan.textContent = `${items.length} ${label} selected`;
        textSpan.style.color = 'var(--text-primary)';
    }
}

function addCustomJob() {
    const searchInput = document.getElementById('jobSearch');
    const customJob = searchInput.value.trim();
    
    if (!customJob) {
        Toast.warning('Please enter a job title');
        return;
    }
    
    if (selectedJobs.includes(customJob)) {
        Toast.info('This job title is already selected');
        return;
    }
    
    // Add to list
    const jobsList = document.getElementById('jobsList');
    const option = createOptionElement(customJob, 'job');
    jobsList.appendChild(option);
    
    // Select it
    option.querySelector('input').checked = true;
    selectedJobs.push(customJob);
    updateSelectedTags('selectedJobs', selectedJobs, 'job');
    updateTriggerText('jobsTrigger', selectedJobs, 'job titles');
    updateCombinationsPreview();
    
    searchInput.value = '';
    Toast.success('Custom job title added');
}

// ==========================================
// Advanced Options
// ==========================================
function initializeAdvancedOptions() {
    const toggleBtn = document.getElementById('toggleAdvanced');
    const content = document.getElementById('advancedContent');
    
    toggleBtn.addEventListener('click', function() {
        content.classList.toggle('show');
        toggleBtn.classList.toggle('active');
    });
}

// ==========================================
// Combinations Preview
// ==========================================
function updateCombinationsPreview() {
    const total = selectedCountries.length * selectedJobs.length;
    document.getElementById('totalCombinations').textContent = total;
}

// ==========================================
// Form Submission
// ==========================================
function initializeForm() {
    const form = document.getElementById('scrapingForm');
    form.addEventListener('submit', handleFormSubmit);
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (selectedCountries.length === 0 || selectedJobs.length === 0) {
        Toast.error('Please select at least one country and one job title');
        return;
    }
    
    const maxResults = parseInt(document.getElementById('maxResults').value);
    const proxyType = document.getElementById('proxyType').value;
    
    const data = {
        country: selectedCountries,
        job: selectedJobs,
        max_results: maxResults,
        proxy_type: proxyType
    };
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon"><i class="fas fa-spinner fa-spin"></i></span> Starting...';
    
    try {
        const response = await API.post('/startScraping', data);
        
        currentTaskId = response.task_id;
        
        // Save to local storage
        TaskStorage.addTask({
            task_id: response.task_id,
            type: 'Scraping',
            status: 'queued',
            progress: 'Waiting to start...',
            started_at: new Date().toISOString()
        });
        
        Toast.success('Scraping task started successfully!');
        
        // Show progress section
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('taskId').textContent = response.task_id;
        
        // Start monitoring
        startStatusMonitoring(response.task_id);
        
    } catch (error) {
        Toast.error(`Failed to start scraping: ${error.message}`);
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon"><i class="fas fa-rocket"></i></span> Start Scraping';
    }
}

// ==========================================
// Status Monitoring
// ==========================================
function startStatusMonitoring(taskId) {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        try {
            const status = await API.get(`/taskStatus/${taskId}`);
            updateProgressUI(status);
            
            // Update local storage
            TaskStorage.updateTask(taskId, status);
            
            if (status.status === 'completed' || status.status === 'failed') {
                clearInterval(statusCheckInterval);
                const submitBtn = document.getElementById('submitBtn');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span class="btn-icon"><i class="fas fa-rocket"></i></span> Start Scraping';
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 3000);
    
    // Setup view task button
    document.getElementById('viewTaskBtn').addEventListener('click', function() {
        window.location.href = `/taskTracker?taskId=${taskId}`;
    });
}

function updateProgressUI(status) {
    document.getElementById('progressStatus').textContent = status.progress || 'Processing...';
    document.getElementById('taskStatus').textContent = status.status;
    document.getElementById('startedAt').textContent = formatDate(status.started_at);
    
    // Update progress bar (estimate based on status)
    const progressBar = document.getElementById('progressBar');
    if (status.status === 'completed') {
        progressBar.style.width = '100%';
    } else if (status.status === 'running') {
        // Animate between 10% and 90%
        const currentWidth = parseInt(progressBar.style.width) || 10;
        progressBar.style.width = Math.min(currentWidth + 5, 90) + '%';
    }
}

