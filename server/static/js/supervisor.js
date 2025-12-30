/**
 * Supervisor JavaScript
 * Displays final consensus papers and progress tracking
 */

let consensusPapers = [];

/**
 * Load consensus papers and progress
 */
async function loadData() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';

    try {
        const response = await fetch('/api/supervisor/consensus-papers');
        const data = await response.json();

        consensusPapers = data.papers;
        updateProgress(data.progress);
        displayPapers(consensusPapers);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading data. Please refresh.</span>';
    }
}

/**
 * Update progress statistics
 */
function updateProgress(progress) {
    const completed = progress.completed || 0;
    const pending = progress.pending || 0;
    const total = progress.total || 0;

    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

    document.getElementById('completed-count').textContent = completed;
    document.getElementById('pending-count').textContent = pending;
    document.getElementById('total-count').textContent = total;
    document.getElementById('progress-bar').style.width = percentage + '%';
    document.getElementById('progress-text').textContent = percentage + '%';
}

/**
 * Display papers in the list
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
    // Determine decision type badge
    let badge = '';
    if (paper.decision_type === 'auto') {
        badge = '<span class="decision-badge badge-auto">✓ Reviewer Consensus (2/2)</span>';
    } else if (paper.decision_type === 'moderator') {
        badge = '<span class="decision-badge badge-moderator">⚖️ Moderator Decision</span>';
    }

    return `
        <div class="paper-card">
            <div class="paper-title">${paper.title || 'Untitled'}</div>
            
            <div class="paper-meta">
                <div><strong>Authors:</strong> ${paper.authors || 'Unknown'}</div>
                <div><strong>Year:</strong> ${paper.year || 'N/A'}</div>
            </div>

            ${badge}
        </div>
    `;
}

/**
 * Export papers to CSV
 */
function exportToCSV() {
    if (consensusPapers.length === 0) {
        alert('No papers to export!');
        return;
    }

    // Create CSV content
    const headers = ['Title', 'Authors', 'Year', 'DOI', 'Source', 'Decision Type'];
    const rows = consensusPapers.map(paper => [
        paper.title || '',
        paper.authors || '',
        paper.year || '',
        paper.doi || '',
        paper.source || '',
        paper.decision_type === 'auto' ? 'Reviewer Consensus' : 'Moderator Decision'
    ]);

    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        const escapedRow = row.map(field => {
            // Escape quotes and wrap in quotes if contains comma or quote
            const escaped = String(field).replace(/"/g, '""');
            return escaped.includes(',') || escaped.includes('"') ? `"${escaped}"` : escaped;
        });
        csvContent += escapedRow.join(',') + '\n';
    });

    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `consensus_papers_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
    loadData();

    // Auto-refresh every 30 seconds
    setInterval(loadData, 30000);
});