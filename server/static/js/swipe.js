/**
 * Swipe Interface JavaScript - With Animations & Stage Support
 * Handles paper loading, swiping, and smooth transitions across title/abstract stages
 */

let currentPaper = null;
let isProcessing = false;
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

    // Show/hide flag button based on stage
    const flagContainer = document.getElementById('flag-container');
    if (stage === 'title') {
        flagContainer.style.display = 'block';
    } else {
        flagContainer.style.display = 'none';
    }

    // Reset and reload for new stage
    document.getElementById('loading').style.display = 'block';
    document.getElementById('paper-card').style.display = 'none';
    document.getElementById('finished-screen').classList.remove('active');

    loadPaper();
}

/**
 * Load current paper from API
 */
async function loadPaper() {
    try {
        const response = await fetch(`/api/swipe/get-paper?stage=${currentStage}`);
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
    const paperCard = document.getElementById('paper-card');  // ADD THIS

    // Disable buttons
    document.getElementById('keep-btn').disabled = true;
    document.getElementById('reject-btn').disabled = true;

    // Animate content in arc
    contentWrapper.classList.add(decision === 'keep' ? 'swipe-right' : 'swipe-left');

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 500));

    // Hide paper card while loading next one  // ADD THIS
    paperCard.style.display = 'none';           // ADD THIS

    try {
        // ... rest of the function stays the same
        const response = await fetch('/api/swipe/decision', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: currentPaper.id,
                decision: decision,
                stage: currentStage
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update progress
            updateProgress(data.progress);

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
 * Flag paper for systems team review (TITLE STAGE ONLY)
 */
async function flagPaper() {
    if (isProcessing || !currentPaper || currentStage !== 'title') return;

    const confirmed = confirm('Flag this paper for systems team review?\n\nThis will skip to the next paper.');
    if (!confirmed) return;

    isProcessing = true;
    const contentWrapper = document.getElementById('paper-content-wrapper');
    const flagBtn = document.getElementById('flag-btn');

    flagBtn.disabled = true;
    const originalText = flagBtn.innerHTML;
    flagBtn.innerHTML = '<span>⏳</span> Flagging...';

    // Animate up
    contentWrapper.style.transition = 'all 0.4s ease';
    contentWrapper.style.transform = 'translateY(-120%) scale(0.8)';
    contentWrapper.style.opacity = '0';

    // Wait for animation
    await new Promise(resolve => setTimeout(resolve, 400));

    try {
        const response = await fetch('/api/swipe/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paper_id: currentPaper.id,
                stage: currentStage
            })
        });

        const data = await response.json();

        if (data.success) {
            // Reset transform
            contentWrapper.style.transition = 'none';
            contentWrapper.style.transform = '';
            contentWrapper.style.opacity = '1';
            void contentWrapper.offsetWidth;
            contentWrapper.style.transition = '';

            // Load next paper
            await loadPaper();

            flagBtn.disabled = false;
            flagBtn.innerHTML = originalText;
        } else {
            alert('Error: ' + data.error);
            // Reset animation
            contentWrapper.style.transition = 'none';
            contentWrapper.style.transform = '';
            contentWrapper.style.opacity = '1';
            flagBtn.disabled = false;
            flagBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error flagging paper:', error);
        alert('Network error. Please try again.');
        // Reset animation
        contentWrapper.style.transition = 'none';
        contentWrapper.style.transform = '';
        contentWrapper.style.opacity = '1';
        flagBtn.disabled = false;
        flagBtn.innerHTML = originalText;
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

    // Remove old animation classes
    contentWrapper.classList.remove('swipe-left', 'swipe-right', 'fade-in');
    void contentWrapper.offsetWidth;

    // Update basic content
    document.getElementById('paper-title').textContent = paper.title || 'No title';
    document.getElementById('paper-authors').textContent = paper.authors || 'Unknown';
    document.getElementById('paper-year').textContent = paper.year || 'N/A';

    // ONLY show abstract in abstract stage
    const abstractSection = document.getElementById('abstract-section');
    if (currentStage === 'abstract' && paper.abstract) {
        abstractSection.style.display = 'block';
        document.getElementById('paper-abstract').textContent = paper.abstract;
    } else {
        abstractSection.style.display = 'none';
    }

    paperCard.style.display = 'block';

    // Trigger fade-in
    setTimeout(() => {
        contentWrapper.classList.add('fade-in');
    }, 50);
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
    // Hide flag button if starting in abstract stage
    if (currentStage === 'abstract') {
        document.getElementById('flag-container').style.display = 'none';
    }

    loadPaper();
});
