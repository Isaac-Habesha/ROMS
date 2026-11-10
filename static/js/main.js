/* ============================================
   ROMS - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initSidebarToggle();
    initCurrentTime();
    initAutoHideAlerts();
});

/**
 * Sidebar toggle for mobile
 */
function initSidebarToggle() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (toggle && sidebar) {
        toggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && 
                sidebar.classList.contains('show') && 
                !sidebar.contains(e.target) && 
                e.target !== toggle &&
                !toggle.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}

/**
 * Live clock in top navigation
 */
function initCurrentTime() {
    const timeEl = document.getElementById('currentTime');
    if (!timeEl) return;
    
    function updateTime() {
        const now = new Date();
        timeEl.textContent = now.toLocaleDateString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    }
    
    updateTime();
    setInterval(updateTime, 1000);
}

/**
 * Auto-hide alert messages after 5 seconds
 */
function initAutoHideAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * CSRF token helper for AJAX requests
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='));
    
    if (cookieValue) {
        return cookieValue.split('=')[1];
    }
    
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

/**
 * Fetch helper with CSRF token
 */
async function fetchJSON(url, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest',
        },
    };
    
    const config = {
        ...defaults,
        ...options,
        headers: { ...defaults.headers, ...options.headers },
    };
    
    const response = await fetch(url, config);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
}

/**
 * Show a Bootstrap toast notification
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer') || createNotificationContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 4000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1090';
    document.body.appendChild(container);
    return container;
}

/**
 * Format currency
 */
function formatCurrency(amount, symbol = '$') {
    return symbol + parseFloat(amount).toFixed(2);
}

/**
 * Format relative time
 */
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hr ago';
    return Math.floor(seconds / 86400) + ' days ago';
}
