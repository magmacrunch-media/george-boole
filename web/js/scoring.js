// scoring.js - OPTIMIZED - Reduced console logging

let allScores = [];
let isUpdating = false; // Prevent concurrent updates

// Migrate old scores without difficulty field.
// In-memory only: this runs on every load, so the display is always correct.
// It deliberately does not write mc_scores_george-boole — scoreClient owns that
// key, and writing it here would make this a second, competing writer.
// NOTE: entries stored on the backend that predate the difficulty field are not
// repaired by this; that needs a one-off admin fix, not a client-side write.
function migrateOldScores() {
    allScores = allScores.map(score =>
        score.difficulty ? score : { ...score, difficulty: '11' } // classic 2048 mode
    );
}

// Load scores from MAGMA//OPS backend (with localStorage fallback)
async function loadScores() {
    try {
        allScores = await scoreClient.load('george-boole');
        migrateOldScores();
    } catch (error) {
        console.error('Error loading scores:', error);
        allScores = [];
    }
}

// Mode name lookup for the overall board
const MODE_NAMES = {
    '2': '2-BIT',
    '3': '3-BIT',
    '4': '4-BIT',
    '5': '5-BIT',
    '6': '6-BIT',
    '7': '7-BIT',
    '8': '8-BIT',
    'endless': 'GAUNTLET',
    '11': 'CLASSIC'
};

function updateScoreboardOverall(scoreColumns) {
    // Get the single best score per player (by initials) across all modes,
    // then take the top 10 overall. If a player has scores in multiple modes,
    // show their best one with the mode badge.
    if (!Array.isArray(allScores) || allScores.length === 0) {
        const noScoresMsg = document.createElement('div');
        noScoresMsg.style.cssText = 'color:#ffa07a;text-align:center;padding:10px;font-size:10px;';
        noScoresMsg.textContent = 'No scores yet!';
        const leftColumn = document.createElement('div');
        leftColumn.className = 'score-column';
        leftColumn.innerHTML = '<div class="column-title">top 5</div>';
        leftColumn.appendChild(noScoresMsg);
        const rightColumn = document.createElement('div');
        rightColumn.className = 'score-column';
        rightColumn.innerHTML = '<div class="column-title">ranks 6-10</div>';
        scoreColumns.appendChild(leftColumn);
        scoreColumns.appendChild(rightColumn);
        return;
    }

    // Sort all scores globally by score descending, take top 10
    const top10 = [...allScores]
        .sort((a, b) => (b.score || 0) - (a.score || 0))
        .slice(0, 10);

    const leftColumn = document.createElement('div');
    leftColumn.className = 'score-column';
    leftColumn.innerHTML = '<div class="column-title">top 5</div>';

    const rightColumn = document.createElement('div');
    rightColumn.className = 'score-column';
    rightColumn.innerHTML = '<div class="column-title">ranks 6-10</div>';

    top10.forEach((entry, index) => {
        if (!entry || typeof entry !== 'object') return;



        const score = entry.score || 0;
        const modeName = MODE_NAMES[entry.difficulty] || entry.difficulty || '???';

        const div = document.createElement('div');
        div.className = 'score-entry' + (entry.isNew ? ' new-score' : '');
        div.innerHTML = `
            <span class="score-rank" data-rank="${index + 1}">#${index + 1}</span>
            <span class="score-initials">${entry.initials || '???'}</span>
            <span class="score-value">${score} pts</span>
            <span class="score-mode-badge">${modeName}</span>
        `;

        if (index < 5) {
            leftColumn.appendChild(div);
        } else {
            rightColumn.appendChild(div);
        }
    });

    scoreColumns.appendChild(leftColumn);
    scoreColumns.appendChild(rightColumn);
}

function updateScoreboard(difficulty = '11') {
    // Prevent concurrent updates
    if (isUpdating) {
        return;
    }
    
    isUpdating = true;
    
    try {
        const scoreColumns = document.getElementById('scoreColumns');
        if (!scoreColumns) {
            return;
        }
        
        // Clear existing content
        scoreColumns.innerHTML = '';
        
        // Ensure allScores is an array
        if (!Array.isArray(allScores)) {
            allScores = [];
        }

        // Handle overall board separately
        if (difficulty === 'overall') {
            updateScoreboardOverall(scoreColumns);
            return;
        }
        
        // Filter scores for selected difficulty
        const difficultyScores = allScores
            .filter(s => s.difficulty === difficulty)
            .sort((a, b) => {
                // Pure survival mode: Higher score is better
                return (b.score || 0) - (a.score || 0);
            })
            .slice(0, 10);
        
        const leftColumn = document.createElement('div');
        leftColumn.className = 'score-column';
        leftColumn.innerHTML = '<div class="column-title">top 5</div>';
        
        const rightColumn = document.createElement('div');
        rightColumn.className = 'score-column';
        rightColumn.innerHTML = '<div class="column-title">ranks 6-10</div>';
        
        // Only create entries if there are scores
        if (difficultyScores.length > 0) {
            difficultyScores.forEach((entry, index) => {
                if (!entry || typeof entry !== 'object') {
                    return;
                }
                

                
                // Format display: Just show the score (clean and simple)
                const score = entry.score || 0;
                const displayValue = `${score} pts`;
                
                const div = document.createElement('div');
                div.className = 'score-entry' + (entry.isNew ? ' new-score' : '');
                div.innerHTML = `
                    <span class="score-rank" data-rank="${index + 1}">#${index + 1}</span>
                    <span class="score-initials">${entry.initials || '???'}</span>
                    <span class="score-value">${displayValue}</span>
                `;
                
                if (index < 5) {
                    leftColumn.appendChild(div);
                } else {
                    rightColumn.appendChild(div);
                }
            });
        } else {
            // Show "No scores yet" message
            const noScoresMsg = document.createElement('div');
            noScoresMsg.style.color = '#ffa07a';
            noScoresMsg.style.textAlign = 'center';
            noScoresMsg.style.padding = '10px';
            noScoresMsg.style.fontSize = '10px';
            noScoresMsg.textContent = 'No scores yet for this mode!';
            leftColumn.appendChild(noScoresMsg);
        }
        
        scoreColumns.appendChild(leftColumn);
        scoreColumns.appendChild(rightColumn);
    } finally {
        // Always reset the flag, even if there was an error
        isUpdating = false;
    }
}
