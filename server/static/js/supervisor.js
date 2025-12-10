/**
 * Supervisor View JavaScript
 * Handles loading and displaying consensus papers
 */

let allPapers = [];

/**
 * Load consensus papers from API
 */
async function loadPapers() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';

    try {
        const response = await fetch('/api/supervisor/consensus-papers');
        const data = await response.json();

        allPapers = data.papers;
        displayPapers(allPapers);

        document.getElementById('consensus-count').textContent = data.total_papers;
        document.getElementById('threshold-display').textContent = data.threshold + '/8';

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    } catch (error) {
        console.error('Error loading papers:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading papers. Please try again.</span>';
    }
}

/**
 * Display papers in the list
 */
function displayPapers(papers) {
    const papersList = document.getElementById('papers-list');
    const noPapers = document.getElementById('no-papers');

    if (papers.length === 0) {
        papersList.style.display = 'none';
        noPapers.style.display = 'block';
        return;
    }

    papersList.style.display = 'grid';
    noPapers.style.display = 'none';
    papersList.innerHTML = '';

    papers.forEach(paper => {
        const paperCard = createPaperCard(paper);
        papersList.innerHTML += paperCard;
    });
}

/**
 * Create HTML for a single paper card
 */
function createPaperCard(paper) {
    const totalVotes = paper.keep_votes + paper.reject_votes;
    const doiLink = paper.doi
        ? `<a href="https://doi.org/${paper.doi}" target="_blank" class="paper-doi">DOI: ${paper.doi}</a>`
        : '<span class="paper-doi">No DOI available</span>';

    return `
        <div class="paper-card">
            <div class="paper-header">
                <div class="paper-title">${paper.title || 'Untitled'}</div>
                <div class="vote-badge">✅ ${paper.keep_votes} Keeps</div>
            </div>

            <div class="paper-meta">
                <div class="meta-item">
                    <strong>Authors:</strong> ${paper.authors || 'Unknown'}
                </div>
                <div class="meta-item">
                    <strong>Year:</strong> ${paper.year || 'N/A'}
                </div>
                ${paper.source ? `<div class="meta-item"><strong>Source:</strong> ${paper.source}</div>` : ''}
            </div>

            <div class="paper-abstract">
                ${paper.abstract || 'No abstract available'}
            </div>

            <div class="paper-footer">
                <div class="vote-stats">
                    <div class="vote-stat">
                        <strong>${paper.keep_votes}</strong> Keep
                    </div>
                    <div class="vote-stat">
                        <strong>${paper.reject_votes}</strong> Reject
                    </div>
                    <div class="vote-stat">
                        <strong>${totalVotes}</strong> Total Votes
                    </div>
                </div>
                ${doiLink}
            </div>
        </div>
    `;
}

/**
 * Filter papers based on search input
 */
function filterPapers() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();

    if (searchTerm === '') {
        displayPapers(allPapers);
        return;
    }

    const filtered = allPapers.filter(paper => {
        const title = (paper.title || '').toLowerCase();
        const authors = (paper.authors || '').toLowerCase();
        const abstract = (paper.abstract || '').toLowerCase();

        return title.includes(searchTerm) ||
               authors.includes(searchTerm) ||
               abstract.includes(searchTerm);
    });

    displayPapers(filtered);
}

/**
 * Export papers to CSV
 */
function exportToCSV() {
    if (allPapers.length === 0) {
        alert('No papers to export');
        return;
    }

    // Create CSV content
    const headers = ['Title', 'Authors', 'Year', 'Keep Votes', 'Reject Votes', 'Total Votes', 'DOI', 'Source'];
    const rows = allPapers.map(paper => [
        paper.title || '',
        paper.authors || '',
        paper.year || '',
        paper.keep_votes || 0,
        paper.reject_votes || 0,
        (paper.keep_votes || 0) + (paper.reject_votes || 0),
        paper.doi || '',
        paper.source || ''
    ]);

    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        // Escape commas and quotes in CSV
        const escapedRow = row.map(field => {
            const str = String(field).replace(/"/g, '""');
            return str.includes(',') ? `"${str}"` : str;
        });
        csvContent += escapedRow.join(',') + '\n';
    });

    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consensus_papers_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
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
    loadPapers();

    // Auto-refresh every 60 seconds
    setInterval(loadPapers, 60000);
});