/**
 * Supervisor JavaScript - Dual Stage Dashboard
 * Displays overview of both title and abstract stages with detail views
 */

let currentViewStage = null; // null = overview, 'title' or 'abstract' = detail view

/**
 * Load stage status overview
 */
async function loadStageOverview() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('overview').style.display = 'none';

    try {
        const response = await fetch('/api/supervisor/stage-status');
        const data = await response.json();

        updateStageCards(data);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('overview').style.display = 'block';
    } catch (error) {
        console.error('Error loading stage status:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading data. Please refresh.</span>';
    }
}

/**
 * Update stage overview cards
 */
function updateStageCards(data) {
    // Title Stage
    const titleComplete = data.title_stage.complete;
    const titlePercent = data.title_stage.completion_percentage.toFixed(1);

    document.getElementById('title-status').textContent =
        titleComplete ? '✅ Complete' : '🔄 In Progress';
    document.getElementById('title-progress-fill').style.width = titlePercent + '%';
    document.getElementById('title-stats').textContent =
        `${data.title_stage.reviewed_papers}/${data.title_stage.total_papers} papers reviewed (${titlePercent}%)`;

    // Abstract Stage
    const abstractInitialized = data.abstract_stage.initialized;
    const abstractPercent = abstractInitialized && data.abstract_stage.total_papers > 0
        ? ((data.abstract_stage.total_papers - data.abstract_stage.reviewer_pool) / data.abstract_stage.total_papers * 100).toFixed(1)
        : 0;

    if (abstractInitialized) {
        document.getElementById('abstract-status').textContent = '🔄 In Progress';
        document.getElementById('abstract-progress-fill').style.width = abstractPercent + '%';
        document.getElementById('abstract-stats').textContent =
            `${data.abstract_stage.total_papers} papers in pool (${data.abstract_stage.reviewer_pool} for reviewers, ${data.abstract_stage.systems_pool} for systems)`;
        document.getElementById('init-abstract-btn').style.display = 'none';
    } else {
        document.getElementById('abstract-status').textContent = '⏸️ Not Started';
        document.getElementById('abstract-progress-fill').style.width = '0%';
        document.getElementById('abstract-stats').textContent = 'Ready to initialize';

        // Show initialize button if title stage is complete
        if (titleComplete) {
            document.getElementById('init-abstract-btn').style.display = 'block';
        }
    }
}

/**
 * Initialize abstract stage
 */
async function initializeAbstractStage() {
    const confirmed = confirm('Initialize the Abstract Review Stage?\n\nThis will populate the abstract pool with papers that passed the title stage.');
    if (!confirmed) return;

    const btn = document.getElementById('init-abstract-btn');
    btn.disabled = true;
    btn.textContent = 'Initializing...';

    try {
        const response = await fetch('/api/supervisor/initialize-abstract-stage', {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            alert(`Abstract stage initialized!\n${data.papers_added} papers added to the pool.`);
            loadStageOverview(); // Reload
        } else {
            alert('Error initializing abstract stage');
            btn.disabled = false;
            btn.textContent = 'Initialize Abstract Stage';
        }
    } catch (error) {
        console.error('Error initializing abstract stage:', error);
        alert('Network error. Please try again.');
        btn.disabled = false;
        btn.textContent = 'Initialize Abstract Stage';
    }
}

/**
 * View details for a specific stage
 */
async function viewStage(stage) {
    currentViewStage = stage;

    document.getElementById('overview').style.display = 'none';
    document.getElementById('detail-view').style.display = 'block';
    document.getElementById('detail-title').textContent =
        stage === 'title' ? '📋 Title Review - Consensus Papers' : '📝 Abstract Review - Consensus Papers';

    await loadStageDetail(stage);
}

/**
 * Load detail view for a stage
 */
async function loadStageDetail(stage) {
    try {
        const response = await fetch(`/api/supervisor/consensus-papers?stage=${stage}`);
        const data = await response.json();

        updateDetailProgress(data.stats);
        displayPapers(data.papers);
    } catch (error) {
        console.error('Error loading stage detail:', error);
        alert('Error loading papers. Please try again.');
    }
}

/**
 * Update detail view progress
 */
function updateDetailProgress(stats) {
    const percentage = stats.total_papers > 0
        ? Math.round((stats.consensus_count / stats.total_papers) * 100)
        : 0;

    // Update with correct IDs from HTML
    document.getElementById('completed-count').textContent = stats.consensus_count;
    document.getElementById('pending-count').textContent = stats.pending;
    document.getElementById('total-count').textContent = stats.total_papers;
    document.getElementById('progress-bar').style.width = percentage + '%';
    document.getElementById('progress-text').textContent = percentage + '%';
}

/**
 * Display papers in detail view
 */
function displayPapers(papers) {
    const papersList = document.getElementById('papers-list');
    const noPapers = document.getElementById('no-papers');
    const approvedCount = document.getElementById('approved-count');

    if (papers.length === 0) {
        papersList.style.display = 'none';
        noPapers.style.display = 'block';
        approvedCount.textContent = '0 papers';
        return;
    }

    papersList.style.display = 'grid';
    noPapers.style.display = 'none';
    approvedCount.textContent = `${papers.length} paper${papers.length !== 1 ? 's' : ''}`;

    papersList.innerHTML = '';

    papers.forEach(paper => {
        const paperCard = createPaperCard(paper);
        papersList.innerHTML += paperCard;
    });
}

/**
 * Create HTML for a paper card
 */
function createPaperCard(paper) {
    let badgeClass = 'badge-auto';
    let badgeText = paper.decision_type;

    if (paper.decision_type.includes('Moderator')) {
        badgeClass = 'badge-moderator';
    } else if (paper.decision_type.includes('Systems')) {
        badgeClass = 'badge-systems';
    }

    return `
        <div class="paper-card">
            <div class="paper-title">${paper.title || 'Untitled'}</div>
            
            <div class="paper-meta">
                <div><strong>Authors:</strong> ${paper.authors || 'Unknown'}</div>
                <div><strong>Year:</strong> ${paper.year || 'N/A'}</div>
                ${paper.doi ? `<div><strong>DOI:</strong> ${paper.doi}</div>` : ''}
            </div>

            <span class="decision-badge ${badgeClass}">${badgeText}</span>
        </div>
    `;
}

/**
 * Back to overview
 */
function backToOverview() {
    currentViewStage = null;
    document.getElementById('detail-view').style.display = 'none';
    document.getElementById('overview').style.display = 'block';
    loadStageOverview();
}

/**
 * Export current stage to CSV
 */
async function exportToCSV() {
    if (!currentViewStage) {
        alert('Please select a stage to export');
        return;
    }

    try {
        const response = await fetch(`/api/supervisor/export-csv?stage=${currentViewStage}`);
        const blob = await response.blob();

        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);

        link.setAttribute('href', url);
        link.setAttribute('download', `consensus_papers_${currentViewStage}_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (error) {
        console.error('Error exporting CSV:', error);
        alert('Error exporting. Please try again.');
    }
}

/**
 * Logout
 */
function logout() {
    window.location.href = '/logout';
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadStageOverview();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        if (currentViewStage) {
            loadStageDetail(currentViewStage);
        } else {
            loadStageOverview();
        }
    }, 30000);
});