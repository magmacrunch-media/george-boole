// game.js - BOOLEAN LOGIC VERSION - Pure bitwise operations

class Game2048 {
    constructor(difficulty = '11', target = 2048) {
        this.size = 4;
        this.board = [];
        this.score = 0;
        this.moves = 0; // Track number of moves
        this.highestValueEver = 0; // Track highest value ever reached (for scoring)
        this.won = false; // Track if player reached max value
        this.gameOver = false;
        this.waitingForInitials = false;
        this.difficulty = difficulty;
        
        // Progressive bit mode for endless
        // Simple: Just reach the max value once to upgrade!
        this.hasReachedMaxInCurrentMode = false;
        
        // Gauntlet mode: parallel 4×4 boolean board.
        // earnedBoard[i][j] === true means that specific tile instance is the
        // earned rainbow tile. It moves and merges in sync with this.board.
        // Any merge result is always false (fresh tile, not earned).
        this.earnedBoard = Array(this.size).fill().map(() => Array(this.size).fill(false));
        // Temporary flag: set by applyGate when it triggers a Gauntlet upgrade,
        // read immediately by moveLeft to mark earnedRow[j] = true.
        this._pendingEarnedUpgrade = false;
        
        // Personal best: parallel 4×4 boolean board (all modes).
        // personalBestBoard[i][j] === true means this specific tile is the ONE
        // gold-plated "session high" tile. Set when a new highestValueEver is
        // reached; cleared when that tile is consumed. Slides/merges in sync.
        this.personalBestBoard = Array(this.size).fill().map(() => Array(this.size).fill(false));
        // Same pending-flag pattern as earnedBoard for applyGate paths.
        this._pendingPersonalBest = false;
        
        // Calculate maximum value from bit mode
        if (difficulty === 'endless') {
            this.bitMode = 2; // Start at 2-bit
            this.maxValue = Math.pow(2, this.bitMode) - 1; // Start at max=3
        } else {
            this.bitMode = parseInt(difficulty);
            this.maxValue = Math.pow(2, this.bitMode) - 1; // 2^n - 1
        }
        
        // Legacy target for compatibility
        this.target = this.maxValue;
        this.wasVictory = false;
        
        // Logic gates feature - spawn rate varies by difficulty
        this.gatesEnabled = true;
        
        // Set gate spawn chance based on bit mode
        this.updateGateSpawnRate();
        
        // Cache DOM elements for better performance
        this.gameBoardElement = document.getElementById('gameBoard');
        this.scoreElement = document.getElementById('score');
        this.tiles = [];
        
        // Track previous board state for dirty checking (major performance boost)
        this.previousBoard = [];
        
        // Store event listeners for cleanup (prevent memory leaks)
        this.eventListeners = [];
        
        // Track pending timeouts for cleanup (prevent stale callbacks)
        this._pendingTimeouts = [];
        
        this.init();
        this.setupEventListeners();
        
        // Initialize puzzle input (keyboard + touch)
        this.input = AdPuzzle.createInput({
            onMove: (dir) => {
                if (this.gameOver || this.waitingForInitials) return;
                const moved = this.move(dir);
                if (moved) {
                    this.moves++;
                    this.addRandomTile();
                    this.render();
                    if (this.checkGameOver()) {
                        this.handleGameOver();
                    }
                }
            },
            isActive: () => !this.gameOver && !this.waitingForInitials,
        }, document.getElementById('gameBoard'));
    }
    
    // Clean up event listeners and timeouts to prevent memory leaks
    destroy() {
        this.eventListeners.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.eventListeners = [];
        this._pendingTimeouts.forEach(id => clearTimeout(id));
        this._pendingTimeouts = [];
    }
    
    // Helper to register event listeners for later cleanup
    addListener(element, event, handler, options) {
        element.addEventListener(event, handler, options);
        this.eventListeners.push({ element, event, handler });
    }
    
    // Helper to register timeouts that auto-cancel on destroy
    _setTimeout(fn, delay) {
        const id = setTimeout(() => {
            this._pendingTimeouts = this._pendingTimeouts.filter(t => t !== id);
            fn();
        }, delay);
        this._pendingTimeouts.push(id);
        return id;
    }
    
    init() {
        this.board = Array(this.size).fill().map(() => Array(this.size).fill(0));
        this.previousBoard = Array(this.size).fill().map(() => Array(this.size).fill(0));
        this.score = 0;
        this.moves = 0;
        this.highestValueEver = 0; // Reset highest value tracker
        this.won = false;
        this.gameOver = false;
        this.waitingForInitials = false;
        this.wasVictory = false;
        this.personalBestBoard = Array(this.size).fill().map(() => Array(this.size).fill(false));
        
        // Reset progressive mode tracking for endless
        if (this.difficulty === 'endless') {
            this.hasReachedMaxInCurrentMode = false;
            this.bitMode = 2;
            this.maxValue = 3;
            this.earnedBoard = Array(this.size).fill().map(() => Array(this.size).fill(false));
        }
        
        this.addRandomTile();
        this.addRandomTile();
        
        // Update mode display
        this.updateModeDisplay();
        
        // Clear "new" flags (only if allScores exists)
        if (typeof allScores !== 'undefined' && Array.isArray(allScores)) {
            allScores.forEach(s => s.isNew = false);
        }
        
        // Initialize tile elements once
        this.initializeTileElements();
        this.render();
    }
    
    // Create tile elements once and reuse them
    initializeTileElements() {
        this.gameBoardElement.innerHTML = '';
        this.tiles = [];
        
        for (let i = 0; i < this.size * this.size; i++) {
            const tile = document.createElement('div');
            tile.className = 'tile';
            this.gameBoardElement.appendChild(tile);
            this.tiles.push(tile);
        }
    }
    
    setupEventListeners() {
        // New game button
        const newGameHandler = () => {
            document.getElementById('difficultyModal').classList.add('active');
        };
        this.addListener(document.getElementById('newGame'), 'click', newGameHandler);
        
        // Restart button
        const restartHandler = () => {
            document.getElementById('gameOver').classList.remove('active');
            document.getElementById('difficultyModal').classList.add('active');
        };
        this.addListener(document.getElementById('restartGame'), 'click', restartHandler);
        
        // Initials input handling
        const initialsInput = document.getElementById('initialsInput');
        
        const inputHandler = (e) => {
            e.target.value = e.target.value.toUpperCase().replace(/[^A-Z]/g, '');
        };
        this.addListener(initialsInput, 'input', inputHandler);
        
        const keypressHandler = (e) => {
            if (e.key === 'Enter') {
                this.submitInitials();
            }
        };
        this.addListener(initialsInput, 'keypress', keypressHandler);
        
        const submitHandler = () => {
            this.submitInitials();
        };
        this.addListener(document.getElementById('submitInitials'), 'click', submitHandler);
    }
    
    // Helper to count gates on board
    countGates() {
        let count = 0;
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                if (this.isGate(this.board[i][j])) {
                    count++;
                }
            }
        }
        return count;
    }
    
    addRandomTile() {
        const emptyCells = [];
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                if (this.board[i][j] === 0) {
                    emptyCells.push({row: i, col: j});
                }
            }
        }
        
        if (emptyCells.length > 0) {
            const {row, col} = emptyCells[Math.floor(Math.random() * emptyCells.length)];
            
            // Use the gate spawn chance set in constructor (no caps!)
            const effectiveGateSpawnChance = this.gateSpawnChance;
            
            // Decide: spawn logic gate or normal tile?
            if (this.gatesEnabled && Math.random() < effectiveGateSpawnChance) {
                // Spawn a logic gate
                // Gates are represented as negative numbers: -1=XOR, -2=OR, -3=AND, -4=NOT
                const gates = [-1, -2, -3, -4];
                this.board[row][col] = gates[Math.floor(Math.random() * gates.length)];
            } else {
                // PROGRESSIVE SPAWN SYSTEM - tiles scale with player progress!
                const maxTileOnBoard = this.getHighestValue();
                let spawnValue;
                
                // SPECIAL: 2-BIT MODE - Only spawn 1s and 2s; 3 (the max) must be earned
                if (this.bitMode === 2) {
                    spawnValue = Math.random() < 0.5 ? 1 : 2;
                }
                // SPECIAL: 3-BIT MODE - Also more aggressive
                else if (this.bitMode === 3 && maxTileOnBoard >= 3) {
                    // Spawn up to 5s
                    const rand = Math.random();
                    if (rand < 0.2) spawnValue = 1;
                    else if (rand < 0.4) spawnValue = 2;
                    else if (rand < 0.6) spawnValue = 3;
                    else if (rand < 0.8) spawnValue = 4;
                    else spawnValue = 5;
                }
                // NORMAL PROGRESSION for other modes
                else if (maxTileOnBoard <= 1) {
                    // Very early: 1s and 2s (even at start)
                    spawnValue = Math.random() < 0.6 ? 1 : 2;
                } else if (maxTileOnBoard <= 3) {
                    // Early game: 1s and 2s (50/50 split) - faster progression
                    spawnValue = Math.random() < 0.5 ? 1 : 2;
                } else if (maxTileOnBoard <= 7) {
                    // Mid-early: 1, 2, 3 (40/35/25 split) - more variety
                    const rand = Math.random();
                    spawnValue = rand < 0.4 ? 1 : (rand < 0.75 ? 2 : 3);
                } else if (maxTileOnBoard <= 15) {
                    // Mid game: 1-4 with weighted distribution
                    const rand = Math.random();
                    if (rand < 0.4) spawnValue = 1;
                    else if (rand < 0.7) spawnValue = 2;
                    else if (rand < 0.9) spawnValue = 3;
                    else spawnValue = 4;
                } else if (maxTileOnBoard <= 31) {
                    // Late-mid: 1-6
                    const rand = Math.random();
                    if (rand < 0.3) spawnValue = 1;
                    else if (rand < 0.5) spawnValue = 2;
                    else if (rand < 0.7) spawnValue = 3;
                    else if (rand < 0.85) spawnValue = 4;
                    else if (rand < 0.95) spawnValue = 5;
                    else spawnValue = 6;
                } else if (maxTileOnBoard <= 63) {
                    // Late game: 1-8
                    const rand = Math.random();
                    if (rand < 0.25) spawnValue = 1;
                    else if (rand < 0.4) spawnValue = 2;
                    else if (rand < 0.55) spawnValue = 3;
                    else if (rand < 0.7) spawnValue = 4;
                    else if (rand < 0.8) spawnValue = 5;
                    else if (rand < 0.9) spawnValue = 6;
                    else if (rand < 0.96) spawnValue = 7;
                    else spawnValue = 8;
                } else {
                    // Very late game (127+): 1-12
                    const rand = Math.random();
                    if (rand < 0.2) spawnValue = 1;
                    else if (rand < 0.35) spawnValue = 2;
                    else if (rand < 0.5) spawnValue = 4;
                    else if (rand < 0.65) spawnValue = 6;
                    else if (rand < 0.78) spawnValue = 8;
                    else if (rand < 0.88) spawnValue = 10;
                    else spawnValue = 12;
                }
                
                this.board[row][col] = spawnValue;
                // Note: spawned tiles intentionally do NOT update highestValueEver.
                // Only merges/gate-results earn the personal best marker.
                // Advancing the tracker on spawn would silently raise the bar,
                // causing legitimately-earned tiles to miss the gold treatment.
            }
            
            // Play spawn sound
            AdAudio.playSfx('spawn');
        }
    }
    
    // Helper to get gate name
    getGateName(value) {
        const gates = {
            '-1': 'XOR',
            '-2': 'OR',
            '-3': 'AND',
            '-4': 'NOT'
        };
        return gates[value.toString()] || 'UNKNOWN';
    }
    
    // Helper to get gate symbol
    getGateSymbol(value) {
        const symbols = {
            '-1': '⊕',
            '-2': '∨',
            '-3': '∧',
            '-4': '¬'
        };
        return symbols[value.toString()] || '?';
    }
    
    // Gauntlet: rotate earnedBoard 90° clockwise (mirrors rotateBoard exactly).
    rotateEarnedBoard(times) {
        for (let t = 0; t < times; t++) {
            const nb = Array(this.size).fill().map(() => Array(this.size).fill(false));
            for (let i = 0; i < this.size; i++)
                for (let j = 0; j < this.size; j++)
                    nb[j][this.size - 1 - i] = this.earnedBoard[i][j];
            this.earnedBoard = nb;
        }
    }

    // Rotate personalBestBoard 90° clockwise (mirrors rotateBoard exactly).
    rotatePersonalBestBoard(times) {
        for (let t = 0; t < times; t++) {
            const nb = Array(this.size).fill().map(() => Array(this.size).fill(false));
            for (let i = 0; i < this.size; i++)
                for (let j = 0; j < this.size; j++)
                    nb[j][this.size - 1 - i] = this.personalBestBoard[i][j];
            this.personalBestBoard = nb;
        }
    }

    // Check if value is a gate
    isGate(value) {
        return value < 0;
    }
    
    // Note: In Boolean logic mode, ALL numbers from 0 to maxValue are valid!
    // No "impossible numbers" - values like 1, 3, 5, 7, etc. come from gate operations
    
    move(direction) {
        const originalBoard = JSON.stringify(this.board);
        let mergeOccurred = false;
        
        // Store merge state
        this.lastMoveHadMerge = false;
        
        if (direction === 'left') {
            mergeOccurred = this.moveLeft();
        } else if (direction === 'right') {
            this.rotateBoard(2);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(2);
            this.rotatePersonalBestBoard(2);
            mergeOccurred = this.moveLeft();
            this.rotateBoard(2);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(2);
            this.rotatePersonalBestBoard(2);
        } else if (direction === 'up') {
            this.rotateBoard(3);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(3);
            this.rotatePersonalBestBoard(3);
            mergeOccurred = this.moveLeft();
            this.rotateBoard(1);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(1);
            this.rotatePersonalBestBoard(1);
        } else if (direction === 'down') {
            this.rotateBoard(1);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(1);
            this.rotatePersonalBestBoard(1);
            mergeOccurred = this.moveLeft();
            this.rotateBoard(3);
            if (this.difficulty === 'endless') this.rotateEarnedBoard(3);
            this.rotatePersonalBestBoard(3);
        }
        
        const boardChanged = originalBoard !== JSON.stringify(this.board);
        
        // 🔊 SOUND: Play merge sound if tiles merged, otherwise move sound
        if (boardChanged) {
            if (mergeOccurred) {
                AdAudio.playSfx('merge');
            } else {
                AdAudio.playSfx('move');
            }
        }
        
        return boardChanged;
    }
    
    moveLeft() {
        let mergeOccurred = false;
        
        for (let i = 0; i < this.size; i++) {
            // Build parallel arrays: values, earned flags, and personal-best flags
            const srcRow = this.board[i];
            const srcEarned = (this.difficulty === 'endless') ? this.earnedBoard[i] : null;
            const srcPB = this.personalBestBoard[i];
            
            let row = [];
            let earnedRow = [];
            let pbRow = [];
            for (let k = 0; k < this.size; k++) {
                if (srcRow[k] !== 0) {
                    row.push(srcRow[k]);
                    earnedRow.push(srcEarned ? srcEarned[k] : false);
                    pbRow.push(srcPB[k]);
                }
            }
            
            // Process merges and gate operations
            let j = 0;
            while (j < row.length) {
                // Check for NOT + NOT cancellation (¬¬A = A, identity operation)
                if (j < row.length - 1 && 
                    row[j] === -4 && 
                    row[j + 1] === -4) {
                    row.splice(j, 2);
                    earnedRow.splice(j, 2);
                    pbRow.splice(j, 2);
                    mergeOccurred = true;
                    continue;
                }
                
                // Check for NOT gate with single number (unary operation)
                // Pattern: [NOT gate] [number]
                if (j < row.length - 1 && 
                    row[j] === -4 && 
                    !this.isGate(row[j + 1])) {
                    const num = row[j + 1];
                    this._pendingEarnedUpgrade = false;
                    this._pendingPersonalBest = false;
                    const result = this.applyGate(-4, num, null);
                    const wasEarned = this._pendingEarnedUpgrade;
                    const wasPB = this._pendingPersonalBest;
                    this._writeGateResult(row, earnedRow, pbRow, j, 2, result, wasEarned, wasPB);
                    mergeOccurred = true;
                    continue;
                }
                
                // A ¬¬ pair cancels even with a number to its left. Without this,
                // [number][¬] below matches first and the chain resolves one step
                // at a time — scoring every intermediate and leaving
                // highestValueEver on a value that never rested on the board.
                if (!this.isGate(row[j]) &&
                    row[j + 1] === -4 &&
                    row[j + 2] === -4) {
                    row.splice(j + 1, 2);
                    earnedRow.splice(j + 1, 2);
                    pbRow.splice(j + 1, 2);
                    mergeOccurred = true;
                    continue;
                }
                
                // Also check for [number] [NOT gate] pattern
                if (j < row.length - 1 && 
                    !this.isGate(row[j]) && 
                    row[j + 1] === -4) {
                    const num = row[j];
                    this._pendingEarnedUpgrade = false;
                    this._pendingPersonalBest = false;
                    const result = this.applyGate(-4, num, null);
                    const wasEarned = this._pendingEarnedUpgrade;
                    const wasPB = this._pendingPersonalBest;
                    this._writeGateResult(row, earnedRow, pbRow, j, 2, result, wasEarned, wasPB);
                    mergeOccurred = true;
                    continue;
                }
                
                // Look for pattern: [number] [gate] [number] (for binary gates: XOR, OR, AND)
                if (j < row.length - 2 && 
                    !this.isGate(row[j]) && 
                    this.isGate(row[j + 1]) && 
                    row[j + 1] !== -4 &&
                    !this.isGate(row[j + 2])) {
                    const leftNum = row[j];
                    const gate = row[j + 1];
                    const rightNum = row[j + 2];
                    this._pendingEarnedUpgrade = false;
                    this._pendingPersonalBest = false;
                    const result = this.applyGate(gate, leftNum, rightNum);
                    const wasEarned = this._pendingEarnedUpgrade;
                    const wasPB = this._pendingPersonalBest;
                    this._writeGateResult(row, earnedRow, pbRow, j, 3, result, wasEarned, wasPB);
                    mergeOccurred = true;
                    
                } else if (j < row.length - 1 && 
                           !this.isGate(row[j]) && 
                           !this.isGate(row[j + 1])) {
                    
                    const current = row[j];
                    const next = row[j + 1];
                    
                    // BOOLEAN LOGIC: Same values merge to same (idempotence: A∨A=A, A∧A=A)
                    if (current === next) {
                        row.splice(j + 1, 1);
                        earnedRow.splice(j + 1, 1);
                        pbRow.splice(j + 1, 1);
                        earnedRow[j] = false; // merge result is never gauntlet-earned
                        pbRow[j] = false;     // will be set true below if new personal best
                        
                        // Award points based on value consolidated
                        this.score += current;
                        
                        // ENDLESS MODE: Track when max value is reached!
                        if (this.difficulty === 'endless' && current === this.maxValue && !this.hasReachedMaxInCurrentMode) {
                            this.hasReachedMaxInCurrentMode = true;
                            
                            // Mark THIS specific tile as the earned rainbow tile.
                            // We're right here in the row — set earnedRow[j] directly.
                            // (markGauntletEarnedTile scans this.board which isn't written
                            // back yet, so we bypass it here.)
                            earnedRow[j] = true;
                            
                            if (this.bitMode < 8) {
                                this._setTimeout(() => {
                                    if (currentGame !== this) return;
                                    this.bitMode++;
                                    this.maxValue = Math.pow(2, this.bitMode) - 1;
                                    this.hasReachedMaxInCurrentMode = false;
                                    this.updateGateSpawnRate();
                                    
                                    this.updateModeDisplay();
                                    this.showUpgradeNotification(this.bitMode);
                                    this.render();
                                }, 800);
                            }
                            
                            this.updateModeDisplay();
                        }
                        
                        // HEIGHT BONUS: Reward reaching new personal best!
                        const minBonusThreshold = this.getMinimumBonusThreshold();
                        
                        if (current > this.highestValueEver && current >= minBonusThreshold) {
                            const heightBonus = current * 2;
                            this.score += heightBonus;
                            this.highestValueEver = current;
                            // Mark this cell first, THEN clear other rows.
                            // Clearing first would stomp pbRow[j] on the current row
                            // before the write-back at the end of the outer loop.
                            pbRow[j] = true;
                            for (let ii = 0; ii < this.size; ii++) {
                                if (ii !== i) this.personalBestBoard[ii].fill(false);
                            }
                            this.showHeightBonus(current, heightBonus);
                            AdAudio.playSfx('victory');
                        } else if (current > this.highestValueEver) {
                            // New high but below the spawnable threshold — track it
                            // for future comparisons but don't award the gold tile.
                            this.highestValueEver = current;
                        }
                        
                        mergeOccurred = true;
                        j++;
                    } else {
                        j++;
                    }
                    
                } else {
                    j++;
                }
            }
            
            // Pad to board size
            while (row.length < this.size) {
                row.push(0);
                earnedRow.push(false);
                pbRow.push(false);
            }
            
            this.board[i] = row;
            if (this.difficulty === 'endless') this.earnedBoard[i] = earnedRow;
            this.personalBestBoard[i] = pbRow;
        }
        
        return mergeOccurred;
    }
    
    // Show overflow notification
    showOverflowNotification(bonus) {
        const notification = document.getElementById('overflowNotification');
        if (!notification) return;
        
        notification.textContent = `*** OVERFLOW +${bonus} ***`;
        notification.style.display = 'block';
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, -50%) scale(1)';
        notification.style.background = 'rgba(255, 100, 100, 0.95)';
        
        // Animate in
        notification.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            // Fade out and scale up
            notification.style.opacity = '0';
            notification.style.transform = 'translate(-50%, -50%) scale(1.5)';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 300);
        }, 1000);
    }
    
    // Show height bonus notification (new personal best!)
    showHeightBonus(value, bonus) {
        const notification = document.getElementById('overflowNotification');
        if (!notification) return;
        
        notification.textContent = `>>> NEW HIGH ${value} (+${bonus})`;
        notification.style.display = 'block';
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, -50%) scale(1)';
        notification.style.background = 'rgba(100, 200, 100, 0.95)'; // Green for height bonus
        
        // Animate in
        notification.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            // Fade out and scale up
            notification.style.opacity = '0';
            notification.style.transform = 'translate(-50%, -50%) scale(1.5)';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 300);
        }, 1000);
    }
    
    // Show upgrade notification for endless mode progression!
    showUpgradeNotification(newBitMode) {
        const notification = document.getElementById('overflowNotification');
        if (!notification) return;
        
        notification.textContent = `>> LEVEL UP: ${newBitMode}-BIT MODE <<`;
        notification.style.display = 'block';
        notification.style.opacity = '1';
        notification.style.transform = 'translate(-50%, -50%) scale(1)';
        notification.style.background = 'rgba(255, 215, 0, 0.95)'; // Gold for upgrade!
        
        // Animate in
        notification.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            // Fade out and scale up
            notification.style.opacity = '0';
            notification.style.transform = 'translate(-50%, -50%) scale(1.5)';
            
            setTimeout(() => {
                notification.style.display = 'none';
            }, 300);
        }, 1500); // Longer display for upgrades
    }
    
    // Apply logic gate operation
    applyGate(gate, value1, value2) {
        // For single-operand gates (NOT), value2 is ignored
        // For two-operand gates (XOR, OR, AND), we need two values
        
        let result;
        
        switch(gate) {
            case -1: // XOR
                result = value1 ^ value2; // Bitwise XOR
                break;
            case -2: // OR
                result = value1 | value2; // Bitwise OR
                break;
            case -3: // AND
                result = value1 & value2; // Bitwise AND
                break;
            case -4: // NOT
                // NOT operation: flip all bits within the bit mode
                // Bit-limited mode: flip all bits within bit limit
                // e.g., 2-bit: NOT 1 (01) = 2 (10), NOT 2 (10) = 1 (01)
                result = (~value1) & this.maxValue;
                // Special case: NOT maxValue produces 0, which can't exist as a tile.
                // Treat this as an overflow — award the overflow bonus and clear the tile.
                if (result === 0) {
                    const overflowBonus = this.maxValue * 3;
                    this.score += overflowBonus;
                    this.showOverflowNotification(overflowBonus);
                    
                    // Check for Gauntlet upgrade (NOT maxValue counts as reaching max)
                    if (this.difficulty === 'endless' && !this.hasReachedMaxInCurrentMode) {
                        this.hasReachedMaxInCurrentMode = true;
                        this._triggerGauntletEarned();
                        if (this.bitMode < 8) {
                            this._setTimeout(() => {
                                if (currentGame !== this) return;
                                this.bitMode++;
                                this.maxValue = Math.pow(2, this.bitMode) - 1;
                                this.hasReachedMaxInCurrentMode = false;
                                this.updateGateSpawnRate();
                                this.updateModeDisplay();
                                this.showUpgradeNotification(this.bitMode);
                                this.render();
                            }, 800);
                        }
                        this.updateModeDisplay();
                    }
                    
                    return 0;
                }
                break;
            default:
                result = value1; // Unknown gate, return value unchanged
        }
        
        // ROLLOVER LOGIC: If result exceeds max, award BONUS and clear tile!
        if (this.maxValue !== Infinity && result > this.maxValue) {
            // OVERFLOW BONUS! Award max value × 3 as bonus points
            const overflowBonus = this.maxValue * 3;
            this.score += overflowBonus;
            
            // ENDLESS MODE: Count this as reaching max (overflow counts too!)
            if (this.difficulty === 'endless' && !this.hasReachedMaxInCurrentMode) {
                this.hasReachedMaxInCurrentMode = true;
                
                // Signal to moveLeft to mark the result cell as earned
                this._triggerGauntletEarned();
                if (this.bitMode < 8) {
                    this._setTimeout(() => {
                        if (currentGame !== this) return;
                        this.bitMode++;
                        this.maxValue = Math.pow(2, this.bitMode) - 1;
                        this.hasReachedMaxInCurrentMode = false;
                        this.updateGateSpawnRate();
                        this.updateModeDisplay();
                        this.showUpgradeNotification(this.bitMode);
                        this.render();
                    }, 800);
                }
                
                // Update display immediately to show checkmark
                this.updateModeDisplay();
            }
            
            // Play special overflow sound
            AdAudio.playSfx('highScore');
            
            // Show overflow notification popup
            this.showOverflowNotification(overflowBonus);
            
            result = 0; // Rollover to 0 means tile disappears!
        } else {
            // Normal operation - award points based on result
            this.score += result;
            
            // ENDLESS MODE: Track when max value is reached (not exceeded)!
            if (this.difficulty === 'endless' && result === this.maxValue && !this.hasReachedMaxInCurrentMode) {
                this.hasReachedMaxInCurrentMode = true;
                
                // Signal to moveLeft to mark the result cell as earned
                this._triggerGauntletEarned();
                
                // Upgrade to next bit mode (if not at max)
                if (this.bitMode < 8) {
                    this._setTimeout(() => {
                        if (currentGame !== this) return;
                        this.bitMode++;
                        this.maxValue = Math.pow(2, this.bitMode) - 1;
                        this.hasReachedMaxInCurrentMode = false;
                        this.updateGateSpawnRate();
                        this.updateModeDisplay();
                        this.showUpgradeNotification(this.bitMode);
                        this.render();
                    }, 800);
                }
                
                // Play special overflow sound
                AdAudio.playSfx('highScore');
                
                // Re-render to update any tiles that might be affected
                this.render();
                
                // Update display immediately to show checkmark
                this.updateModeDisplay();
            }
            
            // HEIGHT BONUS: Award extra points for reaching new personal best!
            // BUT: Only for values that are "achievements" (not just spawned)
            const minBonusThreshold = this.getMinimumBonusThreshold();
            
            if (result > 0 && result > this.highestValueEver && result >= minBonusThreshold) {
                const heightBonus = result * 2; // Double the value as bonus!
                this.score += heightBonus;
                this.highestValueEver = result;
                // Signal moveLeft to mark the result cell, THEN clear other rows.
                // Setting the pending flag first ensures the current row's write-back
                // won't be stomped by the board-wide clear.
                this._pendingPersonalBest = true;
                for (let ii = 0; ii < this.size; ii++) this.personalBestBoard[ii].fill(false);
                
                // Show height bonus notification
                this.showHeightBonus(result, heightBonus);
                
                // Play victory sound for milestone
                AdAudio.playSfx('victory');
            } else if (result > this.highestValueEver) {
                // New high but below the spawnable threshold — track it
                // for future comparisons but don't award the gold tile.
                this.highestValueEver = result;
            }
        }
        
        return result;
    }
    
    rotateBoard(times) {
        for (let t = 0; t < times; t++) {
            const newBoard = Array(this.size).fill().map(() => Array(this.size).fill(0));
            for (let i = 0; i < this.size; i++) {
                for (let j = 0; j < this.size; j++) {
                    newBoard[j][this.size - 1 - i] = this.board[i][j];
                }
            }
            this.board = newBoard;
        }
    }
    
    updateGateSpawnRate() {
        if (this.bitMode === 2) {
            this.gateSpawnChance = 0.45;
        } else if (this.bitMode === 3) {
            this.gateSpawnChance = 0.32;
        } else if (this.bitMode === 4) {
            this.gateSpawnChance = 0.24;
        } else if (this.bitMode <= 6) {
            this.gateSpawnChance = 0.20;
        } else {
            this.gateSpawnChance = 0.18;
        }
    }
    
    checkGameOver() {
        // NO MORE WIN CONDITION - All modes are survival!
        // Game only ends when board is full and no moves possible
        
        // Check for empty cells
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                if (this.board[i][j] === 0) return false;
            }
        }
        
        // Check for possible moves by simulating each direction
        // This is more accurate than just checking adjacency
        const testBoard = JSON.parse(JSON.stringify(this.board));

        // Snapshot all side-effecting state so simulated moveLeft calls
        // cannot corrupt real personal-best tracking or highestValueEver.
        const savedHighest = this.highestValueEver;
        const savedPBBoard = this.personalBestBoard.map(r => r.slice());
        const savedEarnedBoard = (this.difficulty === 'endless') ? this.earnedBoard.map(r => r.slice()) : null;
        const savedPendingPB = this._pendingPersonalBest;
        const savedPendingEarned = this._pendingEarnedUpgrade;
        const savedScore = this.score;
        const savedMoves = this.moves;
        const savedHasReached = this.hasReachedMaxInCurrentMode;
        const savedTimeouts = this._pendingTimeouts.slice();

        // Try each direction
        for (const direction of ['left', 'right', 'up', 'down']) {
            // Temporarily set board for testing
            this.board = JSON.parse(JSON.stringify(testBoard));
            
            // Try the move
            let moved = false;
            if (direction === 'left') {
                moved = this.moveLeft();
            } else if (direction === 'right') {
                this.rotateBoard(2);
                moved = this.moveLeft();
                this.rotateBoard(2);
            } else if (direction === 'up') {
                this.rotateBoard(3);
                moved = this.moveLeft();
                this.rotateBoard(1);
            } else if (direction === 'down') {
                this.rotateBoard(1);
                moved = this.moveLeft();
                this.rotateBoard(3);
            }
            
            // If this direction moved something, game is not over
            if (moved) {
                this.board = testBoard;
                this.highestValueEver = savedHighest;
                this.personalBestBoard = savedPBBoard;
                if (this.difficulty === 'endless') this.earnedBoard = savedEarnedBoard;
                this._pendingPersonalBest = savedPendingPB;
                this._pendingEarnedUpgrade = savedPendingEarned;
                this.score = savedScore;
                this.moves = savedMoves;
                this.hasReachedMaxInCurrentMode = savedHasReached;
                // Clear any timeouts queued during simulation
                this._pendingTimeouts.forEach(id => clearTimeout(id));
                this._pendingTimeouts = savedTimeouts;
                return false;
            }
        }
        
        // Restore original board and all simulation side-effects
        this.board = testBoard;
        this.highestValueEver = savedHighest;
        this.personalBestBoard = savedPBBoard;
        if (this.difficulty === 'endless') this.earnedBoard = savedEarnedBoard;
        this._pendingPersonalBest = savedPendingPB;
        this._pendingEarnedUpgrade = savedPendingEarned;
        this.score = savedScore;
        this.moves = savedMoves;
        this.hasReachedMaxInCurrentMode = savedHasReached;
        this._pendingTimeouts.forEach(id => clearTimeout(id));
        this._pendingTimeouts = savedTimeouts;
        
        // No moves possible in any direction
        this.gameOver = true;
        return true;
    }
    
    // Helper to get highest value on board (for non-winners)
    getHighestValue() {
        let max = 0;
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                const val = this.board[i][j];
                if (val > 0 && !this.isGate(val)) {
                    max = Math.max(max, val);
                }
            }
        }
        return max;
    }
    
    // Gauntlet mode: called by applyGate when a gate operation produces the max value
    // or causes an overflow. Sets a pending flag that moveLeft picks up immediately
    // to mark earnedRow[j] = true — we can't set earnedBoard directly here because
    // this.board[i] hasn't been written back yet during row processing.
    _triggerGauntletEarned() {
        this._pendingEarnedUpgrade = true;
    }

    // Write a gate result back over `count` cells of the row and its two parallel
    // flag arrays. A zero result means the tile is gone — an overflow, NOT maxValue,
    // or an AND/XOR that cancelled. Drop the cells rather than leaving a literal 0:
    // the row is built with zeros stripped, so a 0 left in place is re-scanned as
    // a number operand by the next [number][gate][number] match.
    _writeGateResult(row, earnedRow, pbRow, j, count, result, wasEarned, wasPB) {
        if (result === 0) {
            row.splice(j, count);
            earnedRow.splice(j, count);
            pbRow.splice(j, count);
        } else {
            row.splice(j, count, result);
            earnedRow.splice(j, count, wasEarned);
            pbRow.splice(j, count, wasPB);
        }
    }
    
    // Get minimum value worth celebrating with height bonus
    getMinimumBonusThreshold() {
        // Don't celebrate values that commonly spawn
        // Only celebrate true achievements!
        if (this.bitMode === 2) {
            // In 2-bit: don't celebrate 1, 2, or 3 (all can spawn)
            // No bonuses in 2-bit mode (max is 3, everything spawns)
            return Infinity; // Never give bonus in 2-bit
        } else if (this.bitMode === 3) {
            // In 3-bit: don't celebrate 1-5 (all can spawn)
            return 6; // Only celebrate 6 and 7
        } else if (this.bitMode === 4) {
            // In 4-bit: 1-4 spawn, celebrate 5+
            return 5;
        } else if (this.bitMode <= 6) {
            // 5-6 bit: celebrate values > max spawn / 2
            return Math.floor(this.maxValue / 2);
        } else {
            // Higher modes: celebrate anything > 1/3 of max
            return Math.floor(this.maxValue / 3);
        }
    }
    
    handleGameOver() {
        // Play game over sound (only if not victory)
        if (!this.wasVictory) {
            AdAudio.playSfx('gameOver');
        }
        
        if (!Array.isArray(allScores)) {
            allScores = [];
        }
        
        const difficultyScores = allScores
            .filter(s => s.difficulty === this.difficulty)
            .sort((a, b) => b.score - a.score);
        const lowestTopScore = difficultyScores.length >= 10 ? difficultyScores[9].score : -1;
        
        if (difficultyScores.length < 10 || this.score > lowestTopScore) {
            let rank = 1;
            for (let i = 0; i < difficultyScores.length; i++) {
                if (this.score > difficultyScores[i].score) {
                    break;
                }
                rank++;
            }
            
            // Play high score sound
            AdAudio.playSfx('highScore');
            
            this.waitingForInitials = true;
            
            const promptTitle = document.querySelector('#initialsPrompt h3');
            const promptSubtitle = document.querySelector('#initialsPrompt p');
            
            // Determine rank text for the prompt
            let rankText = '';
            if (rank === 1) rankText = '1ST PLACE';
            else if (rank === 2) rankText = '2ND PLACE';
            else if (rank === 3) rankText = '3RD PLACE';
            else rankText = `#${rank}`;
            
            // Update the prompt with rank and moves
            promptTitle.textContent = '*** NEW HIGH SCORE! ***';
            const moveText = `${this.moves} move${this.moves === 1 ? '' : 's'}`;
            promptSubtitle.innerHTML = `<strong>${rankText}</strong> • ${moveText}<br>enter your initials:`;
            
            document.getElementById('initialsPrompt').classList.add('active');
            setTimeout(() => document.getElementById('initialsInput').focus(), 100);
        } else {
            this.showGameOver();
        }
    }
    
    submitInitials() {
        const input = document.getElementById('initialsInput');
        let initials = input.value.trim();
        
        // Require at least one character - if empty, don't submit yet
        if (initials.length === 0) {
            // Flash the input to indicate it needs content
            input.style.borderColor = '#ff6b6b';
            setTimeout(() => {
                input.style.borderColor = '';
            }, 500);
            input.focus();
            return;
        }
        
        // Pad with underscores if less than 3 characters
        while (initials.length < 3) {
            initials += '_';
        }
        
        if (!Array.isArray(allScores)) {
            allScores = [];
        }
        
        allScores.push({ 
            initials: initials, 
            score: this.score, // New scoring system: points from operations
            moves: this.moves, // Still track moves separately
            won: false, // No more wins in survival mode
            valueReached: this.highestValueEver, // Highest value ever reached
            difficulty: this.difficulty,
            timestamp: Date.now(),
            isNew: true 
        });
        
        const difficulties = ['2', '3', '4', '5', '6', '7', '8', 'endless'];
        let cleanedScores = [];
        
        difficulties.forEach(diff => {
            const diffScores = allScores
                .filter(s => s.difficulty === diff)
                .sort((a, b) => {
                    // Pure survival mode: Higher score is better
                    return (b.score || 0) - (a.score || 0);
                })
                .slice(0, 10);
            cleanedScores = cleanedScores.concat(diffScores);
        });
        
        allScores = cleanedScores;
        
        scoreClient.save('george-boole', initials, this.score, {
            difficulty: this.difficulty,
            moves: this.moves,
            valueReached: this.highestValueEver
        });
        updateScoreboard(this.difficulty);
        
        document.getElementById('initialsPrompt').classList.remove('active');
        document.getElementById('initialsInput').value = '';
        this.waitingForInitials = false;
        
        // Don't show game over screen after high score - just return to difficulty selector
        document.getElementById('difficultyModal').classList.add('active');
    }
    
    showGameOver() {
        const finalScoreElement = document.getElementById('finalScore');
        // New survival format: Show score and highest value reached
        finalScoreElement.textContent = `${this.score} points - Max Value: ${this.highestValueEver}`;
        document.getElementById('gameOver').classList.add('active');
    }
    
    // Update score label based on difficulty
    updateScoreLabel() {
        const scoreLabel = document.querySelector('.score-label');
        if (scoreLabel) {
            // All modes now use "points" (new scoring system)
            const newLabel = 'points';
            if (scoreLabel.textContent !== newLabel) {
                scoreLabel.textContent = newLabel;
            }
        }
    }
    
    // Update mode display to show current bit mode
    updateModeDisplay() {
        const modeDisplay = document.getElementById('modeDisplay');
        if (modeDisplay) {
            if (this.difficulty === 'endless') {
                // Show current bit mode and merge goal
                const goalDisplay = this.hasReachedMaxInCurrentMode ? '✓' : `REACH ${this.maxValue}`;
                modeDisplay.textContent = `GAUNTLET: ${goalDisplay}`;
            } else {
                modeDisplay.textContent = `${this.bitMode}-BIT MODE`;
            }
        }
    }
    
    // HIGHLY OPTIMIZED RENDER - Only updates tiles that changed (dirty checking)
    render() {
        let tileIndex = 0;
        let boardChanged = false;
        
        // Update score label based on difficulty
        this.updateScoreLabel();
        
        // Update mode display (especially for endless mode progress)
        this.updateModeDisplay();
        
        for (let i = 0; i < this.size; i++) {
            for (let j = 0; j < this.size; j++) {
                const tile = this.tiles[tileIndex];
                const value = this.board[i][j];
                const prevValue = this.previousBoard[i][j];
                
                // Determine correct class — earnedBoard[i][j] is ground truth
                const isRainbow = this.difficulty === 'endless' &&
                                  value > 0 && !this.isGate(value) &&
                                  this.earnedBoard[i][j];
                const wantedClass = isRainbow ? 'tile gauntlet-max-earned' : 'tile';
                
                // Compute wanted attributes for non-gate tiles
                // intensity: how close this value is to maxValue, bucketed 1–5
                // Only applied to non-power-of-2, non-max values (the "rule 3" tiles)
                let wantedIntensity = null;
                let wantedPersonalBest = false;
                if (value > 0 && !this.isGate(value)) {
                    const isPow2 = (value & (value - 1)) === 0;
                    const isMax  = value === this.maxValue;
                    if (!isPow2 && !isMax) {
                        const ratio = this.maxValue > 1 ? value / this.maxValue : 0;
                        if      (ratio < 0.2)  wantedIntensity = '1';
                        else if (ratio < 0.4)  wantedIntensity = '2';
                        else if (ratio < 0.6)  wantedIntensity = '3';
                        else if (ratio < 0.8)  wantedIntensity = '4';
                        else                   wantedIntensity = '5';
                    }
                    // Personal best: only the ONE specific tile instance that earned it
                    wantedPersonalBest = this.personalBestBoard[i][j];
                }
                
                // DIRTY CHECKING — only touch DOM if value or class changed
                const classChanged = !this.isGate(value) && tile.className !== wantedClass;
                const intensityChanged = tile.getAttribute('data-intensity') !== wantedIntensity;
                const pbChanged = (tile.getAttribute('data-personal-best') === 'true') !== wantedPersonalBest;
                
                if (value !== prevValue || classChanged || intensityChanged || pbChanged) {
                    boardChanged = boardChanged || (value !== prevValue);
                    
                    if (value !== 0) {
                        if (this.isGate(value)) {
                            if (value !== prevValue) {
                                tile.textContent = this.getGateSymbol(value);
                                tile.setAttribute('data-value', 'gate');
                                tile.className = 'tile gate-tile';
                                tile.setAttribute('data-gate', this.getGateName(value).toLowerCase());
                                tile.removeAttribute('data-intensity');
                                tile.removeAttribute('data-personal-best');
                            }
                        } else {
                            if (value !== prevValue) {
                                if (typeof binaryDisplayMode !== 'undefined' && binaryDisplayMode) {
                                    let binary = value.toString(2);
                                    if (this.bitMode !== Infinity) {
                                        binary = binary.padStart(this.bitMode, '0');
                                    }
                                    tile.innerHTML = `<div class="tile-decimal">${value}</div><div class="tile-binary">${binary}</div>`;
                                } else {
                                    tile.textContent = value;
                                }
                                tile.setAttribute('data-value', value);
                            }
                            if (classChanged) tile.className = wantedClass;
                            // Intensity attribute
                            if (intensityChanged) {
                                if (wantedIntensity !== null) {
                                    tile.setAttribute('data-intensity', wantedIntensity);
                                } else {
                                    tile.removeAttribute('data-intensity');
                                }
                            }
                            // Personal best attribute
                            if (pbChanged) {
                                if (wantedPersonalBest) {
                                    tile.setAttribute('data-personal-best', 'true');
                                } else {
                                    tile.removeAttribute('data-personal-best');
                                }
                            }
                        }
                    } else {
                        if (value !== prevValue) {
                            tile.textContent = '';
                            tile.removeAttribute('data-value');
                            tile.removeAttribute('data-intensity');
                            tile.removeAttribute('data-personal-best');
                            tile.className = 'tile';
                        }
                    }
                    
                    this.previousBoard[i][j] = value;
                }
                
                tileIndex++;
            }
        }
        
        // Update score display (only update DOM if needed)
        const currentScoreText = this.scoreElement.textContent;
        const newScoreText = this.score.toString();
        if (currentScoreText !== newScoreText) {
            this.scoreElement.textContent = newScoreText;
        }
    }
}
