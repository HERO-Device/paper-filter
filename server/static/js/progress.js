/**
 * Progress Dashboard JavaScript
 * Handles loading and displaying group progress
 */

/**
 * Load progress data from API
 */
async function loadProgress() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';

    try {
        const response = await fetch('/api/progress/all');
        const data = await response.json();

        displayProgress(data);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    } catch (error) {
        console.error('Error loading progress:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading progress. Please try again.</span>';
    }
}

/**
 * Display progress data
 */
function displayProgress(data) {
    const totalPapers = data.total_papers;
    const users = data.users;

    // Calculate summary stats
    let totalProgress = 0;
    let completedCount = 0;

    users.forEach(user => {
        const reviewed = user.total_kept + user.total_rejected;
        const progress = totalPapers > 0 ? (reviewed / totalPapers) * 100 : 0;
        totalProgress += progress;

        if (progress >= 100) {
            completedCount++;
        }
    });

    const avgProgress = users.length > 0 ? (totalProgress / users.length).toFixed(1) : 0;

    // Update summary cards
    document.getElementById('total-papers').textContent = totalPapers.toLocaleString();
    document.getElementById('avg-progress').textContent = avgProgress + '%';
    document.getElementById('completed-count').textContent = completedCount + '/' + users.length;

    // Display user cards
    const userList = document.getElementById('user-list');
    userList.innerHTML = '';

    users.forEach(user => {
        const reviewed = user.total_kept + user.total_rejected;
        const progress = totalPapers > 0 ? (reviewed / totalPapers) * 100 : 0;

        let status = 'not-started';
        let statusText = 'Not Started';

        if (progress >= 100) {
            status = 'complete';
            statusText = 'Complete ✓';
        } else if (progress > 0) {
            status = 'in-progress';
            statusText = 'In Progress';
        }

        const lastActive = user.last_active
            ? formatLastActive(user.last_active)
            : 'Never';

        const userCard = `
            <div class="user-card">
                <div class="user-header">
                    <div class="user-name">${user.display_name}</div>
                    <div class="user-status status-${status}">${statusText}</div>
                </div>
                
                <div class="user-progress-bar">
                    <div class="user-progress-fill" style="width: ${progress}%"></div>
                </div>
                
                <div class="user-stats">
                    <div class="user-stat">
                        <div class="user-stat-value">${reviewed}</div>
                        <div class="user-stat-label">Reviewed</div>
                    </div>
                    <div class="user-stat">
                        <div class="user-stat-value">${user.total_kept}</div>
                        <div class="user-stat-label">Kept</div>
                    </div>
                    <div class="user-stat">
                        <div class="user-stat-value">${user.total_rejected}</div>
                        <div class="user-stat-label">Rejected</div>
                    </div>
                </div>
                
                <div class="last-active">
                    Last active: ${lastActive}
                </div>
            </div>
        `;

        userList.innerHTML += userCard;
    });
}

/**
 * Format last active timestamp
 */
function formatLastActive(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hours ago`;
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString();
}

/**
 * Logout function
 */
function logout() {
    window.location.href = '/logout';
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadProgress();

    // Auto-refresh every 30 seconds
    setInterval(loadProgress, 30000);
});