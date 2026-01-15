/**
 * Moderator JavaScript - With Stage Support
 * Handles loading and reviewing disputed papers (1 yes, 1 no) across stages
 */

let disputedPapers = [];
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
    loadDisputedPapers();
}

/**
 * Load disputed papers from API
 */
async function loadDisputedPapers() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('paper-card').style.display = 'none';
    document.getElementById('finished-screen').classList.remove('active');

    try {
        const response = await fetch(`/api/moderator/disputed-papers?stage=${currentStage}`);
        const data = await response.json();

        disputedPapers = data.papers;
        updateStats(data.stats);

        if (disputedPapers.length === 0) {
            showFinishedScreen();
        } else {
            displayCurrentPaper();
        }

        document.getElementById('loading').style.display = 'none';
    } catch (error) {
        console.error('Error loading disputed papers:', error);
        document.getElementById('loading').innerHTML =
            '<span style="color: #dc3545;">Error loading papers. Please refresh.</span>';
    }
}

/**
 * Update statistics
 */
function updateStats(stats) {
    document.getElementById('pending-count').textContent = stats.pending || 0;
    document.getElementById('completed-count').textContent = stats.completed || 0;
}

/**
 * Display current paper
 */
function displayCurrentPaper() {
    if (currentIndex >= disputedPapers.length) {
        showFinishedScreen();
        return;
    }

    currentPaper = disputedPapers[currentIndex];

    const paperCard = document.getElementById('paper-card');
    const contentWrapper = document.getElementById('paper-content-wrapper');

    // Remove animation classes
    contentWrapper.classList.remove('swipe-left', 'swipe-right', 'fade-in');

    // Update content
    document.getElementById('paper-title').textContent = currentPaper.title || 'No title';
    document.getElementById('paper-authors').textContent = currentPaper.authors || 'Unknown';
    document.getElementById('paper-year').textContent = currentPaper.year || 'N/A';
    document.getElementById('paper-votes').textContent =
        `${currentPaper.keep_votes} Keep, ${currentPaper.reject_votes} Reject`;

    // Show/hide abstract based on stage
    const abstractSection = document.getElementById('abstract-section');
    if (currentStage === 'abstract' && currentPaper.abstract) {
        abstractSection.style.display = 'block';
        document.getElementById('paper-abstract').textContent = currentPaper.abstract;
    } else {
        abstractSection.style.display = 'none';
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
    const paperCard = document.getElementById('paper-card');  // ADD THIS LINE

    // Disable buttons
    document.getElementById('keep-btn').disabled = true;
    document.getElementById('reject-btn').disabled = true;

    // Animate card (left or right)
    contentWrapper.classList.add(decision === 'keep' ? 'swipe-right' : 'swipe-left');

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 500));

    try {
        const response = await fetch('/api/moderator/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
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

            // Hide paper card while loading
            paperCard.style.display = 'none';

            // Reload everything (updates stats AND loads next paper)
            currentIndex = 0; // Reset index
            await loadDisputedPapers();
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
    loadDisputedPapers();
});
