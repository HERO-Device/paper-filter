/**
 * Admin Dashboard JavaScript
 * Handles loading and displaying all papers with analytics
 */

let allPapers = [];
let currentFilter = 'all';

/**
 * Load all papers from API
 */
async function loadPapers() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';

    try {
        const response = await fetch('/api/admin/all-papers');
        const data = await response.json();

        allPapers = data.papers;
        updateStats(allPapers);
        displayPapers(allPapers);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    } catch (error) {
        console.error('Error loading papers:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading data. Please try again.</span>';
    }
}

/**
 * Update summary statistics
 */
function updateStats(papers) {
    const totalPapers = papers.length;
    const consensusPapers = papers.filter(p => p.keep_votes >= 5).length;
    const fullyReviewed = papers.filter(p => p.total_votes >= 8).length;
    const avgVotes = totalPapers > 0
        ? (papers.reduce((sum, p) => sum + p.total_votes, 0) / totalPapers).toFixed(1)
        : 0;

    document.getElementById('total-papers').textContent = totalPapers;
    document.getElementById('consensus-papers').textContent = consensusPapers;
    document.getElementById('fully-reviewed').textContent = fullyReviewed;
    document.getElementById('avg-votes').textContent = avgVotes;
}

/**
 * Display papers in table
 */
function displayPapers(papers) {
    const tbody = document.getElementById('papers-tbody');
    const noResults = document.getElementById('no-results');

    if (papers.length === 0) {
        tbody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }

    noResults.style.display = 'none';
    tbody.innerHTML = '';

    papers.forEach((paper, index) => {
        const row = createPaperRow(paper, index + 1);
        tbody.innerHTML += row;
    });
}

/**
 * Create HTML for a single table row
 */
function createPaperRow(paper, index) {
    const hasConsensus = paper.keep_votes >= 5;
    const consensusBadge = hasConsensus
        ? '<span class="consensus-indicator consensus-yes">✓ YES</span>'
        : '<span class="consensus-indicator consensus-no">NO</span>';

    return `
        <tr>
            <td>${index}</td>
            <td class="paper-title-cell">${paper.title || 'Untitled'}</td>
            <td>${paper.authors || 'Unknown'}</td>
            <td>${paper.year || 'N/A'}</td>
            <td><span class="vote-badge vote-keep">${paper.keep_votes}</span></td>
            <td><span class="vote-badge vote-reject">${paper.reject_votes}</span></td>
            <td><span class="vote-badge vote-neutral">${paper.total_votes}/8</span></td>
            <td>${consensusBadge}</td>
        </tr>
    `;
}

/**
 * Set filter category
 */
function setFilter(filter) {
    currentFilter = filter;

    // Update button states
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    filterPapers();
}

/**
 * Filter papers based on search and category
 */
function filterPapers() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();

    let filtered = allPapers;

    // Apply category filter
    if (currentFilter === 'consensus') {
        filtered = filtered.filter(p => p.keep_votes >= 5);
    } else if (currentFilter === 'no-consensus') {
        filtered = filtered.filter(p => p.keep_votes < 5 && p.total_votes > 0);
    } else if (currentFilter === 'not-reviewed') {
        filtered = filtered.filter(p => p.total_votes === 0);
    }

    // Apply search filter
    if (searchTerm !== '') {
        filtered = filtered.filter(paper => {
            const title = (paper.title || '').toLowerCase();
            const authors = (paper.authors || '').toLowerCase();

            return title.includes(searchTerm) || authors.includes(searchTerm);
        });
    }

    displayPapers(filtered);
}

/**
 * Export all papers to CSV
 */
function exportToCSV() {
    exportPapersToCSV(allPapers, 'all_papers');
}

/**
 * Export consensus papers only to CSV
 */
function exportConsensusToCSV() {
    const consensusPapers = allPapers.filter(p => p.keep_votes >= 5);
    if (consensusPapers.length === 0) {
        alert('No consensus papers to export');
        return;
    }
    exportPapersToCSV(consensusPapers, 'consensus_papers');
}

/**
 * Generic CSV export function
 */
function exportPapersToCSV(papers, filename) {
    if (papers.length === 0) {
        alert('No papers to export');
        return;
    }

    const headers = ['ID', 'Title', 'Authors', 'Year', 'Keep Votes', 'Reject Votes', 'Total Votes', 'Consensus', 'DOI', 'Source'];
    const rows = papers.map(paper => [
        paper.id || '',
        paper.title || '',
        paper.authors || '',
        paper.year || '',
        paper.keep_votes || 0,
        paper.reject_votes || 0,
        paper.total_votes || 0,
        paper.keep_votes >= 5 ? 'Yes' : 'No',
        paper.doi || '',
        paper.source || ''
    ]);

    let csvContent = headers.join(',') + '\n';
    rows.forEach(row => {
        const escapedRow = row.map(field => {
            const str = String(field).replace(/"/g, '""');
            return str.includes(',') ? `"${str}"` : str;
        });
        csvContent += escapedRow.join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
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