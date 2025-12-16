/**
 * Systems Team JavaScript
 * Handles loading and reviewing flagged papers
 */

let flaggedPapers = [];
let myDecisions = {};

/**
 * Load flagged papers from API
 */
async function loadFlaggedPapers() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('content').style.display = 'none';

    try {
        const response = await fetch('/api/systems/flagged-papers');
        const data = await response.json();

        flaggedPapers = data.papers;
        myDecisions = data.my_decisions || {};

        updateStats(data);
        displayPapers(flaggedPapers);

        document.getElementById('loading').style.display = 'none';
        document.getElementById('content').style.display = 'block';
    } catch (error) {
        console.error('Error loading flagged papers:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading flagged papers. Please try again.</span>';
    }
}

/**
 * Update statistics
 */
function updateStats(data) {
    document.getElementById('total-flagged').textContent = data.total_flagged || 0;
    document.getElementById('pending-review').textContent = data.pending_review || 0;
    document.getElementById('my-reviewed').textContent = data.my_reviewed || 0;
}

/**
 * Display flagged papers
 */
function displayPapers(papers) {
    const papersGrid = document.getElementById('papers-grid');
    const noPapers = document.getElementById('no-papers');

    if (papers.length === 0) {
        papersGrid.style.display = 'none';
        noPapers.style.display = 'block';
        return;
    }

    papersGrid.style.display = 'grid';
    noPapers.style.display = 'none';
    papersGrid.innerHTML = '';

    papers.forEach(paper => {
        const paperCard = createPaperCard(paper);
        papersGrid.innerHTML += paperCard;
    });
}

/**
 * Create HTML for a paper card
 */
function createPaperCard(paper) {
    const myDecision = myDecisions[paper.flag_id];
    const hasDecided = !!myDecision;

    const decisionSection = hasDecided
        ? `<div class="my-decision">
             ✓ You voted: <strong>${myDecision.toUpperCase()}</strong>
           </div>`
        : `<div class="decision-buttons">
             <button class="decision-btn reject" onclick="submitDecision(${paper.flag_id}, 'reject')">
                 ✗ Reject
             </button>
             <button class="decision-btn keep" onclick="submitDecision(${paper.flag_id}, 'keep')">
                 ✓ Keep
             </button>
           </div>`;

    const flaggedDate = new Date(paper.flagged_at).toLocaleDateString();

    return `
        <div class="paper-card" id="paper-${paper.flag_id}">
            <div class="paper-header">
                <div class="paper-title">${paper.title || 'Untitled'}</div>
                <div class="flag-badge">🚩 Flagged</div>
            </div>

            <div class="paper-meta">
                <div><strong>Authors:</strong> ${paper.authors || 'Unknown'}</div>
                <div><strong>Year:</strong> ${paper.year || 'N/A'}</div>
                <div><strong>Flagged by:</strong> ${paper.flagged_by_name}</div>
                <div><strong>Date:</strong> ${flaggedDate}</div>
            </div>

            <div class="paper-abstract">
                ${paper.abstract || 'No abstract available'}
            </div>

            ${paper.reason ? `<div style="background: #fff3cd; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
                <strong>Flag Reason:</strong> ${paper.reason}
            </div>` : ''}

            <div class="paper-footer">
                <div class="vote-stats">
                    <div class="vote-stat">
                        <strong>${paper.keep_votes || 0}</strong> Keep
                    </div>
                    <div class="vote-stat">
                        <strong>${paper.reject_votes || 0}</strong> Reject
                    </div>
                    <div class="vote-stat">
                        <strong>${paper.systems_reviews || 0}</strong> Total Reviews
                    </div>
                </div>
                ${decisionSection}
            </div>
        </div>
    `;
}

/**
 * Submit decision on a flagged paper
 */
async function submitDecision(flaggedPaperId, decision) {
    const paperCard = document.getElementById(`paper-${flaggedPaperId}`);
    const buttons = paperCard.querySelectorAll('.decision-btn');

    // Disable buttons
    buttons.forEach(btn => btn.disabled = true);

    try {
        const response = await fetch('/api/systems/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                flagged_paper_id: flaggedPaperId,
                decision: decision
            })
        });

        const data = await response.json();

        if (data.success) {
            // Record decision locally
            myDecisions[flaggedPaperId] = decision;

            // Reload to update UI
            await loadFlaggedPapers();
        } else {
            alert('Error saving decision: ' + data.error);
            buttons.forEach(btn => btn.disabled = false);
        }
    } catch (error) {
        console.error('Error submitting decision:', error);
        alert('Network error. Please try again.');
        buttons.forEach(btn => btn.disabled = false);
    }
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
    loadFlaggedPapers();

    // Auto-refresh every 60 seconds
    setInterval(loadFlaggedPapers, 60000);
});