/**
 * Swipe Interface JavaScript
 * Handles paper loading, swiping, and progress tracking
 */

let currentPaper = null;
let isProcessing = false;

/**
 * Load current paper from API
 */
async function loadPaper() {
    try {
        const response = await fetch('/api/swipe/get-paper');
        const data = await response.json();

        if (data.finished) {
            showFinishedScreen(data.stats);
        } else {
            displayPaper(data.paper);
            updateProgress(data.progress);
        }

        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('Error loading paper:', error);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
    }
}

/**
 * Display paper information on the card
 */
function displayPaper(paper) {
    currentPaper = paper;

    document.getElementById('paper-title').textContent = paper.title || 'No title';
    document.getElementById('paper-authors').textContent = paper.authors || 'Unknown';
    document.getElementById('paper-year').textContent = paper.year || 'N/A';
    document.getElementById('paper-abstract').textContent = paper.abstract || 'No abstract available';

    document.getElementById('paper-card').style.display = 'block';
}

/**
 * Update progress bar and counters
 */
function updateProgress(progress) {
    const percent = (progress.current / progress.total * 100).toFixed(1);

    document.getElementById('progress-text').textContent =
        `Paper ${progress.current} of ${progress.total}`;
    document.getElementById('progress-percent').textContent = `${percent}%`;
    document.getElementById('progress-fill').style.width = `${percent}%`;

    document.getElementById('kept-count').textContent = progress.kept;
    document.getElementById('rejected-count').textContent = progress.rejected;
}

/**
 * Submit swipe decision (keep or reject)
 */
async function swipe(decision) {
    if (isProcessing || !currentPaper) return;

    isProcessing = true;
    document.getElementById('keep-btn').disabled = true;
    document.getElementById('reject-btn').disabled = true;

    try {
        const response = await fetch('/api/swipe/decision', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                paper_id: currentPaper.id,
                decision: decision
            })
        });

        const data = await response.json();

        if (data.success) {
            updateProgress(data.new_progress);

            // Load next paper
            await loadPaper();
        } else {
            alert('Error saving decision. Please try again.');
        }
    } catch (error) {
        console.error('Error submitting decision:', error);
        alert('Network error. Please try again.');
    } finally {
        isProcessing = false;
        document.getElementById('keep-btn').disabled = false;
        document.getElementById('reject-btn').disabled = false;
    }
}

/**
 * Show finished screen when all papers reviewed
 */
function showFinishedScreen(stats) {
    document.getElementById('paper-card').style.display = 'none';
    document.getElementById('final-kept').textContent = stats.total_kept;
    document.getElementById('final-rejected').textContent = stats.total_rejected;
    document.getElementById('finished-screen').classList.add('active');
}

/**
 * Logout function
 */
function logout() {
    window.location.href = '/logout';
}

/**
 * Keyboard shortcuts handler
 */
document.addEventListener('keydown', (e) => {
    if (isProcessing) return;

    if (e.key.toLowerCase() === 'y') {
        swipe('keep');
    } else if (e.key.toLowerCase() === 'n') {
        swipe('reject');
    }
});

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    loadPaper();
});