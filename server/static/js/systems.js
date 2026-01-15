/**
 * Systems Team JavaScript - With Stage Support
 * Handles loading and reviewing flagged papers across stages
 */

let flaggedPapers = [];
let currentIndex = 0;
let currentPaper = null;
let isProcessing = false;
let keptCount = 0;
let rejectedCount = 0;
let currentStage = 'title'; // Default to title stage

/**
 * Switch between title and abstract stages
 */
function switchStage(stage) {
    if (isProcessing) return;

    currentStage = stage;

    // Update tab UI
    document.querySelectorAll('.stage-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.stage === stage) {
            tab.classList.add('active');
        }
    });

    // Reset state
    currentIndex = 0;
    keptCount = 0;
    rejectedCount = 0;

    // Reload papers for new stage
    loadFlaggedPapers();
}

/**
 * Load flagged papers from API
 */
async function loadFlaggedPapers() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('paper-card').style.display = 'none';
    document.getElementById('finished-screen').classList.remove('active');

    try {
        const response = await fetch(`/api/systems/flagged-papers?stage=${currentStage}`);
        const data = await response.json();

        flaggedPapers = data.papers;
        updateStats(data.stats);

        if (flaggedPapers.length === 0) {
            showFinishedScreen();
        } else {
            displayCurrentPaper();
        }

        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('Error loading flagged papers:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading papers. Please refresh.</span>';
    }
}

/**
 * Update statistics
 */
function updateStats(stats) {
    document.getElementById('total-flagged').textContent = stats.total_flagged || 0;
    document.getElementById('pending-review').textContent = stats.pending || 0;
    document.getElementById('reviewed-count').textContent = stats.reviewed || 0;
}

/**
 * Display current paper
 */
function displayCurrentPaper() {
    if (currentIndex >= flaggedPapers.length) {
        showFinishedScreen();
        return;
    }

    currentPaper = flaggedPapers[currentIndex];

    const paperCard = document.getElementById('paper-card');
    const contentWrapper = document.getElementById('paper-content-wrapper');

    // Remove animation classes
    contentWrapper.classList.remove('swipe-left', 'swipe-right', 'fade-in');

    // Update content
    document.getElementById('paper-title').textContent = currentPaper.title || 'No title';
    document.getElementById('paper-authors').textContent = currentPaper.authors || 'Unknown';
    document.getElementById('paper-year').textContent = currentPaper.year || 'N/A';
    document.getElementById('flagged-by').textContent = currentPaper.flagged_by_name || 'Unknown';  // Changed from 'flagged-by-name' to 'flagged-by'

    // Show/hide abstract based on stage
    const abstractSection = document.getElementById('abstract-section');
    if (currentStage === 'abstract' && currentPaper.abstract) {
        if (abstractSection) {
            abstractSection.style.display = 'block';
            document.getElementById('paper-abstract').textContent = currentPaper.abstract;
        }
    } else {
        if (abstractSection) {
            abstractSection.style.display = 'none';
        }
    }

    // Show flag reason if it exists
    const flagReasonDiv = document.getElementById('flag-reason');
    if (currentPaper.reason && currentPaper.reason.trim()) {
        flagReasonDiv.style.display = 'block';
        document.getElementById('reason-text').textContent = currentPaper.reason;
    } else {
        flagReasonDiv.style.display = 'none';
    }

    paperCard.style.display = 'block';

    // Trigger fade-in animation
    setTimeout(() => {
        contentWrapper.classList.add('fade-in');
    }, 50);
}

/**
 * Submit decision (swipe)
 */
async function swipe(decision) {
    if (isProcessing || !currentPaper) return;

    isProcessing = true;
    const contentWrapper = document.getElementById('paper-content-wrapper');

    // Disable buttons
    document.getElementById('keep-btn').disabled = true;
    document.getElementById('reject-btn').disabled = true;

    // Animate card (left or right)
    contentWrapper.classList.add(decision === 'keep' ? 'swipe-right' : 'swipe-left');

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
        const response = await fetch('/api/systems/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                flag_id: currentPaper.flag_id,
                paper_id: currentPaper.paper_id,
                decision: decision,
                stage: currentStage
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update counts
            if (decision === 'keep') {
                keptCount++;
            } else {
                rejectedCount++;
            }

            // Remove animation class
            contentWrapper.classList.remove('swipe-left', 'swipe-right');

            // Reload everything (this updates stats AND loads next paper)
            currentIndex = 0; // Reset index
            await loadFlaggedPapers();
        } else {
            alert('Error saving decision: ' + data.error);
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
 * Show finished screen
 */
function showFinishedScreen() {
    document.getElementById('paper-card').style.display = 'none';
    document.getElementById('final-kept').textContent = keptCount;
    document.getElementById('final-rejected').textContent = rejectedCount;
    document.getElementById('finished-screen').classList.add('active');
}

/**
 * Logout
 */
function logout() {
    window.location.href = '/logout';
}

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', (e) => {
    if (isProcessing || !currentPaper) return;

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
    loadFlaggedPapers();
});