/**
 * Swipe Interface JavaScript - With Animations
 * Handles paper loading, swiping, and smooth transitions
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
 * Submit swipe decision with arc animation
 */
async function swipe(decision) {
    if (isProcessing || !currentPaper) return;

    isProcessing = true;
    const contentWrapper = document.getElementById('paper-content-wrapper');

    // Disable buttons
    document.getElementById('keep-btn').disabled = true;
    document.getElementById('reject-btn').disabled = true;

    // Animate content in arc (left or right)
    contentWrapper.classList.add(decision === 'keep' ? 'swipe-right' : 'swipe-left');

    // Wait for arc animation (500ms)
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
        const response = await fetch('/api/swipe/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: currentPaper.id,
                decision: decision
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update progress
            updateProgress(data.new_progress);

            // Load next paper (displayPaper will handle cleanup)
            await loadPaper();
        } else {
            alert('Error saving decision. Please try again.');
            contentWrapper.classList.remove('swipe-left', 'swipe-right');
        }
    } catch (error) {
        console.error('Error submitting decision:', error);
        alert('Network error. Please try again.');
        contentWrapper.classList.remove('swipe-left', 'swipe-right');
    } finally {
        isProcessing = false;
        document.getElementById('keep-btn').disabled = false;
        document.getElementById('reject-btn').disabled = false;
    }
}

/**
 * Flag paper for systems team review
 */
async function flagPaper() {
    if (isProcessing || !currentPaper) return;

    // Confirm with user
    const confirmed = confirm('Flag this paper for systems team review?\n\nYou will still need to Keep or Reject it yourself.');
    if (!confirmed) return;

    isProcessing = true;
    const contentWrapper = document.getElementById('paper-content-wrapper');
    const flagBtn = document.getElementById('flag-btn');

    // Disable flag button
    flagBtn.disabled = true;
    flagBtn.textContent = '🚩 Flagging...';

    try {
        const response = await fetch('/api/swipe/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: currentPaper.id,
                reason: null  // Optional: could add a prompt for reason
            })
        });

        const data = await response.json();

        if (data.success) {
            // Animate card moving up
            contentWrapper.classList.add('flag-up');

            // Show success message
            alert('✓ Paper flagged for systems team!\n\nNow choose Keep or Reject for yourself.');

            // Wait for animation, then reset
            await new Promise(resolve => setTimeout(resolve, 500));
            contentWrapper.classList.remove('flag-up');

            // Re-enable flag button
            flagBtn.disabled = false;
            flagBtn.textContent = '🚩 Flag for Systems Team';
        } else {
            alert('Error flagging paper: ' + data.error);
            flagBtn.disabled = false;
            flagBtn.textContent = '🚩 Flag for Systems Team';
        }
    } catch (error) {
        console.error('Error flagging paper:', error);
        alert('Network error. Please try again.');
        flagBtn.disabled = false;
        flagBtn.textContent = '🚩 Flag for Systems Team';
    } finally {
        isProcessing = false;
    }
}

/**
 * Display paper information with fade-in
 */
function displayPaper(paper) {
    currentPaper = paper;

    const paperCard = document.getElementById('paper-card');
    const contentWrapper = document.getElementById('paper-content-wrapper');

    // Remove old animation classes immediately (before setting new content)
    contentWrapper.classList.remove('swipe-left', 'swipe-right', 'fade-in');

    // Force reflow to reset animations
    void contentWrapper.offsetWidth;

    // Update content
    document.getElementById('paper-title').textContent = paper.title || 'No title';
    document.getElementById('paper-authors').textContent = paper.authors || 'Unknown';
    document.getElementById('paper-year').textContent = paper.year || 'N/A';
    document.getElementById('paper-abstract').textContent = paper.abstract || 'No abstract available';

    paperCard.style.display = 'block';

    // Trigger fade-in animation
    setTimeout(() => {
        contentWrapper.classList.add('fade-in');
    }, 50);
}

/**
 * Show decision overlay (big ✓ or ✗)
 */
function showDecisionOverlay(decision) {
    // Create overlay if it doesn't exist
    let overlay = document.getElementById('decision-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'decision-overlay';
        overlay.className = 'decision-overlay';
        document.querySelector('.swipe-container').appendChild(overlay);
    }

    // Set icon and color
    overlay.textContent = decision === 'keep' ? '✓' : '✗';
    overlay.className = `decision-overlay ${decision} show`;
}

/**
 * Hide decision overlay
 */
function hideDecisionOverlay() {
    const overlay = document.getElementById('decision-overlay');
    if (overlay) {
        overlay.classList.remove('show');
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