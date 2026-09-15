// main.js

let currentGame = null;
let currentDifficulty = '6';

function getScoreboardDefault() {
    return localStorage.getItem('lastPlayedDifficulty') || 'overall';
}

// Track if we opened instructions/credits from settings
let returnToSettings = false;

// Track if we opened instructions from difficulty modal
let returnToLoreScreen = false;

// Binary display mode - enabled by default
let binaryDisplayMode = true;

// iOS has no Ogg Vorbis decoder, and every browser on iOS is WebKit, so Chrome
// and Firefox there fail identically - the audio was simply silent on every
// iPhone and iPad. Each clip now ships as .ogg and .mp3; pick whichever this
// browser can actually decode. Ogg stays preferred where it works, since the
// mp3 is a transcode of it.
const AUDIO_EXT = document.createElement('audio')
    .canPlayType('audio/ogg; codecs="vorbis"') ? '.ogg' : '.mp3';
const audioSrc = (path) => path.replace(/\.ogg$/, AUDIO_EXT);

// How many glyphs trail behind each falling head.
const RAIN_TRAIL = 14;

/**
 * Binary rain behind the title screen.
 *
 * Returns { start, stop }. Nothing runs until start() is called, and stop()
 * is real -- the first version of this left a requestAnimationFrame loop
 * running behind the board for the whole session, which on a phone is a
 * background render loop nobody asked for.
 *
 * Three things here are deliberate, because the first attempt got each of
 * them wrong and the result was invisible rather than obviously broken:
 *
 *  - The canvas is cleared each frame, not veiled with a translucent fill.
 *    The veil is the classic trail technique and it only works when the
 *    canvas IS the background; composited over the title screen's gradient
 *    it converges towards opaque and flattens the glow underneath, so the
 *    effect fights itself at every opacity.
 *  - Column width is measured from the font, once, rather than assumed equal
 *    to the font size in three separate places.
 *  - The glyphs stay put and the trail moves across them. Re-rolling every
 *    character every frame reads as television static.
 */
function createBinaryRain(canvas) {
    if (!canvas || !canvas.getContext) return { start() {}, stop() {} };

    const ctx = canvas.getContext('2d');
    const reduce = window.matchMedia
        ? window.matchMedia('(prefers-reduced-motion: reduce)')
        : null;

    let cols = [];
    let cellW = 18;
    let cellH = 24;
    let rows = 0;
    let cssW = 0;
    let cssH = 0;
    let raf = 0;
    let running = false;

    const glyph = () => (Math.random() < 0.5 ? '0' : '1');

    function newColumn(scatter) {
        const chars = [];
        for (let i = 0; i < RAIN_TRAIL; i++) chars.push(glyph());
        return {
            // On the first fill, heads are scattered across the whole height
            // so the field is already running when the title screen appears.
            // A recycled column re-enters from above the top edge.
            head: scatter
                ? Math.random() * (rows + RAIN_TRAIL) - RAIN_TRAIL
                : -RAIN_TRAIL - Math.random() * rows * 0.5,
            speed: 0.4 + Math.random() * 0.8,
            chars,
        };
    }

    function measure() {
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return false;

        cssW = rect.width;
        cssH = rect.height;

        // Without this the buffer is in CSS pixels and the browser upscales
        // it, which on a 3x iPhone is visibly soft.
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.round(cssW * dpr);
        canvas.height = Math.round(cssH * dpr);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        const size = parseFloat(
            getComputedStyle(canvas).getPropertyValue('--rain-size')
        ) || 18;
        ctx.font = size + 'px "Press Start 2P", monospace';
        ctx.textBaseline = 'top';

        cellW = Math.max(1, Math.ceil(ctx.measureText('0').width)) + 2;
        cellH = Math.max(1, Math.round(size * 1.35));
        rows = Math.ceil(cssH / cellH);

        const count = Math.ceil(cssW / cellW);
        cols = [];
        for (let i = 0; i < count; i++) cols.push(newColumn(true));
        return true;
    }

    function draw() {
        ctx.clearRect(0, 0, cssW, cssH);

        for (let i = 0; i < cols.length; i++) {
            const col = cols[i];
            const before = Math.floor(col.head);
            col.head += col.speed;
            const row = Math.floor(col.head);

            for (let n = before; n < row; n++) {
                col.chars.pop();
                col.chars.unshift(glyph());
            }

            const x = i * cellW;
            for (let t = 0; t < RAIN_TRAIL; t++) {
                const y = (row - t) * cellH;
                if (y < -cellH || y > cssH) continue;
                ctx.fillStyle = t === 0
                    ? 'rgba(224, 255, 255, 0.95)'
                    : 'rgba(0, 255, 255, ' + ((1 - t / RAIN_TRAIL) * 0.55).toFixed(3) + ')';
                ctx.fillText(col.chars[t], x, y);
            }

            // Recycle the moment the tail clears the bottom. The first version
            // waited on a 0.5%-per-frame coin flip, so columns died off and
            // the field thinned out the longer you looked at it.
            if ((row - RAIN_TRAIL) * cellH > cssH) {
                cols[i] = newColumn(false);
            }
        }

        raf = requestAnimationFrame(draw);
    }

    function stop() {
        running = false;
        if (raf) {
            cancelAnimationFrame(raf);
            raf = 0;
        }
        if (cssW && cssH) ctx.clearRect(0, 0, cssW, cssH);
    }

    function start() {
        if (running) return;
        // Someone who has asked their device for less motion gets none of
        // this. It carries no information, so there is nothing to replace it
        // with -- the stylesheet stills the other six animations.
        if (reduce && reduce.matches) return;
        if (!measure()) return;
        running = true;
        raf = requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => {
        if (running) measure();
    });

    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            if (raf) {
                cancelAnimationFrame(raf);
                raf = 0;
            }
        } else if (running && !raf) {
            raf = requestAnimationFrame(draw);
        }
    });

    if (reduce && reduce.addEventListener) {
        reduce.addEventListener('change', () => {
            if (reduce.matches) stop();
        });
    }

    return { start, stop };
}

/** The gate glyphs drifting up behind the title. Pure CSS once placed. */
function createFloatingGates(container) {
    if (!container || container.childElementCount) return;
    const gates = [
        { symbol: '⊕', gate: 'xor' },
        { symbol: '∨', gate: 'or' },
        { symbol: '∧', gate: 'and' },
        { symbol: '¬', gate: 'not' },
    ];
    for (let i = 0; i < 8; i++) {
        const g = gates[i % gates.length];
        const el = document.createElement('span');
        el.className = 'floating-gate';
        el.setAttribute('data-gate', g.gate);
        el.textContent = g.symbol;
        el.style.left = (10 + Math.random() * 80) + '%';
        el.style.animationDuration = (12 + Math.random() * 18) + 's';
        el.style.animationDelay = (Math.random() * 20) + 's';
        el.style.fontSize = (12 + Math.random() * 10) + 'px';
        container.appendChild(el);
    }
}

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Initialize adenosine-audio
        await AdAudio.init({
            music: { url: audioSrc('audio/game-loop.ogg'), volume: 0.3, fadeIn: 2.0 },
            sfx: {
                spawn:    { url: audioSrc('audio/sfx/spawn.ogg'),     volume: 0.3, pool: 3 },
                merge:    { url: audioSrc('audio/sfx/merge.ogg'),     volume: 0.3, pool: 3 },
                victory:  { url: audioSrc('audio/sfx/victory.ogg'),   volume: 0.3, pool: 3 },
                gameOver: { url: audioSrc('audio/sfx/gameover.ogg'),  volume: 0.3, pool: 3 },
                move:     { url: audioSrc('audio/sfx/move.ogg'),      volume: 0.3, pool: 3 },
                highScore:{ url: audioSrc('audio/sfx/highscore.ogg'), volume: 0.3, pool: 3 },
            },
        });
        AdAudio.handleVisibility({ pauseMusic: true });
        
        // Start loading scores
        await loadScores();

        // Hide loading screen
        const loadingScreen = document.getElementById('loadingScreen');
        loadingScreen.classList.add('hidden');
        setTimeout(() => {
            loadingScreen.style.display = 'none';
        }, 500);

        // ---- Title screen background ----
        const rain = createBinaryRain(document.getElementById('binaryRain'));
        createFloatingGates(document.getElementById('floatingGates'));

        // Wait for Press Start 2P before measuring: the column width comes
        // from the font's own advance, and the fallback's is different, so
        // starting early would lay out the field twice. Not awaited -- the
        // title screen is interactive without it.
        const fontsReady = document.fonts && document.fonts.ready
            ? document.fonts.ready
            : Promise.resolve();
        fontsReady.then(() => rain.start());

        // Title screen navigation
        const titleScreen = document.getElementById('titleScreen');
        const loreScreen = document.getElementById('loreScreen');
        const difficultyModal = document.getElementById('difficultyModal');
        
        // Function to show the lore/rules screen
        const startGame = () => {
            titleScreen.classList.remove('active');
            loreScreen.classList.add('active');

            // The title screen is gone for the rest of the session, so the
            // canvas loop has nothing left to draw. Leaving it running is a
            // render loop behind the board, which matters on a phone.
            rain.stop();

            // Start music with fade-in
            AdAudio.playMusic();
        };
        
        // Function to advance from lore screen to difficulty selector
        const showDifficulty = () => {
            loreScreen.classList.remove('active');
            difficultyModal.classList.add('active');
            
            // Sync quick toggle states with current settings
            const quickMusicToggle = document.getElementById('quickMusicToggle');
            const quickSfxToggle = document.getElementById('quickSfxToggle');
            
            if (quickMusicToggle) {
                const musicMuted = AdAudio.isMusicMuted();
                quickMusicToggle.classList.toggle('active', !musicMuted);
                quickMusicToggle.querySelector('.toggle-state').textContent = musicMuted ? 'OFF' : 'ON';
            }
            
            if (quickSfxToggle) {
                const sfxMuted = AdAudio.isSfxMuted();
                quickSfxToggle.classList.toggle('active', !sfxMuted);
                quickSfxToggle.querySelector('.toggle-state').textContent = sfxMuted ? 'OFF' : 'ON';
            }
        };
        
        // Click handler for start button (title → lore)
        document.getElementById('startButton').addEventListener('click', startGame);
        
        // Click handler for continue button (lore → difficulty)
        document.getElementById('loreContinue').addEventListener('click', showDifficulty);
        
        // Spacebar handler: title screen OR lore screen
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                if (titleScreen.classList.contains('active')) {
                    e.preventDefault();
                    startGame();
                } else if (loreScreen.classList.contains('active')) {
                    e.preventDefault();
                    showDifficulty();
                }
            }
        });
        
        // Quick action button handlers
        const quickHighScores = document.getElementById('quickHighScores');
        const quickSettings = document.getElementById('quickSettings');
        
        // High Scores button - opens scoreboard from difficulty modal
        if (quickHighScores) {
            quickHighScores.addEventListener('click', () => {
                loreScreen.classList.remove('active');
                returnToLoreScreen = true;
                const scoreDefault = getScoreboardDefault();
                updateCustomDropdownValue(scoreDefault);
                updateScoreboard(scoreDefault);
                document.getElementById('scoreboardModal').classList.add('active');
                document.getElementById('scoreboardModal').classList.add('menu-mode');
            });
        }
        
        // Settings button - opens settings from difficulty modal
        if (quickSettings) {
            quickSettings.addEventListener('click', () => {
                loreScreen.classList.remove('active');
                returnToLoreScreen = true;
                document.getElementById('settingsModal').classList.add('active');
                document.getElementById('settingsModal').classList.add('menu-mode');
            });
        }

        // Setup difficulty selection
        const difficultyButtons = document.querySelectorAll('.difficulty-btn');
        
        difficultyButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const difficulty = btn.dataset.difficulty;
                const target = parseInt(btn.dataset.target);
                const theme = btn.dataset.theme || 'snes';
                currentDifficulty = difficulty;
                localStorage.setItem('lastPlayedDifficulty', difficulty);
                
                // Clean up old game instance to prevent memory leaks
                if (currentGame) {
                    currentGame.destroy();
                }
                
                // Apply theme to body
                document.body.setAttribute('data-theme', theme);
                
                // Add game-active class to enable animations
                document.body.classList.add('game-active');
                
                // Mark gauntlet mode for side panel highlighting
                if (difficulty === 'endless') {
                    document.body.classList.add('game-active-gauntlet');
                } else {
                    document.body.classList.remove('game-active-gauntlet');
                }
                
                // Hide difficulty modal
                difficultyModal.classList.remove('active');
                
                // Start game with selected difficulty
                currentGame = new BooleBoard(difficulty, target);
            });
        });

        // Back button: difficulty modal -> lore screen
        const difficultyBack = document.getElementById('difficultyBack');
        if (difficultyBack) {
            difficultyBack.addEventListener('click', () => {
                difficultyModal.classList.remove('active');
                loreScreen.classList.add('active');
            });
        }
        
        // How to play link in mobile rules strip
        const howToPlayLink = document.getElementById('howToPlayLink');
        if (howToPlayLink) {
            howToPlayLink.addEventListener('click', () => {
                const instructionsModal = document.getElementById('instructionsModal');
                instructionsModal.classList.add('active');
                const instructionsContent = instructionsModal.querySelector('.instructions-content');
                if (instructionsContent) {
                    instructionsContent.scrollTop = 0;
                }
            });
        }

        let scoreboardOpen = false;

        // Scoreboard modal controls
        document.getElementById('toggleScoreboard').addEventListener('click', () => {
            if (scoreboardOpen) return;
            scoreboardOpen = true;
            
            setTimeout(() => {
                // Show overall if no game played yet, otherwise last-played mode
                const scoreDefault = getScoreboardDefault();
                updateCustomDropdownValue(scoreDefault);
                updateScoreboard(scoreDefault);
                document.getElementById('scoreboardModal').classList.add('active');
            }, 10);
        });

        document.getElementById('closeScoreboard').addEventListener('click', () => {
            document.getElementById('scoreboardModal').classList.remove('active');
            document.getElementById('scoreboardModal').classList.remove('menu-mode');
            
            // If we came from lore screen, go back to it
            if (returnToLoreScreen) {
                loreScreen.classList.add('active');
                returnToLoreScreen = false;
            }
            
            setTimeout(() => {
                scoreboardOpen = false;
            }, 300);
        });

        // Close modal when clicking outside the content
        document.getElementById('scoreboardModal').addEventListener('click', (e) => {
            if (e.target.id === 'scoreboardModal') {
                document.getElementById('scoreboardModal').classList.remove('active');
                document.getElementById('scoreboardModal').classList.remove('menu-mode');
                
                // If we came from lore screen, go back to it
                if (returnToLoreScreen) {
                    loreScreen.classList.add('active');
                    returnToLoreScreen = false;
                }
                
                setTimeout(() => {
                    scoreboardOpen = false;
                }, 300);
            }
        });

        // Custom dropdown functionality
        const customDropdown = document.getElementById('customDropdown');
        const dropdownSelected = document.getElementById('dropdownSelected');
        const dropdownOptions = document.getElementById('dropdownOptions');
        
        // Toggle dropdown open/closed
        if (dropdownSelected) {
            dropdownSelected.addEventListener('click', (e) => {
                e.stopPropagation();
                customDropdown.classList.toggle('open');
            });
        }
        
        // Handle option selection
        if (dropdownOptions) {
            dropdownOptions.addEventListener('click', (e) => {
                if (e.target.classList.contains('dropdown-option')) {
                    const value = e.target.dataset.value;
                    const text = e.target.textContent;
                    
                    // Update selected display
                    document.querySelector('.selected-text').textContent = text;
                    
                    // Update active state
                    document.querySelectorAll('.dropdown-option').forEach(opt => {
                        opt.classList.remove('active');
                    });
                    e.target.classList.add('active');
                    
                    // Close dropdown
                    customDropdown.classList.remove('open');
                    
                    // Update scoreboard
                    updateScoreboard(value);
                }
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (customDropdown && !customDropdown.contains(e.target)) {
                customDropdown.classList.remove('open');
            }
        });
        
        // Helper function to update dropdown value
        function updateCustomDropdownValue(difficulty) {
            const options = document.querySelectorAll('.dropdown-option');
            options.forEach(opt => {
                if (opt.dataset.value === difficulty) {
                    document.querySelector('.selected-text').textContent = opt.textContent;
                    opt.classList.add('active');
                } else {
                    opt.classList.remove('active');
                }
            });
        }

        // Instructions modal controls
        document.getElementById('closeInstructions').addEventListener('click', () => {
            document.getElementById('instructionsModal').classList.remove('active');
            returnToSettings = false;
        });

        document.getElementById('instructionsToSettings').addEventListener('click', () => {
            document.getElementById('instructionsModal').classList.remove('active');
            document.getElementById('settingsModal').classList.add('active');
            returnToSettings = false;
        });

        document.getElementById('instructionsModal').addEventListener('click', (e) => {
            if (e.target.id === 'instructionsModal') {
                document.getElementById('instructionsModal').classList.remove('active');
                returnToSettings = false;
            }
        });

        // Settings modal controls
        document.getElementById('toggleSettings').addEventListener('click', () => {
            document.getElementById('settingsModal').classList.add('active');
        });

        document.getElementById('closeSettings').addEventListener('click', () => {
            document.getElementById('settingsModal').classList.remove('active');
            document.getElementById('settingsModal').classList.remove('menu-mode');
            
            // If we came from lore screen, go back to it
            if (returnToLoreScreen) {
                loreScreen.classList.add('active');
                returnToLoreScreen = false;
            }
        });

        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target.id === 'settingsModal') {
                document.getElementById('settingsModal').classList.remove('active');
                document.getElementById('settingsModal').classList.remove('menu-mode');
                
                // If we came from lore screen, go back to it
                if (returnToLoreScreen) {
                    loreScreen.classList.add('active');
                    returnToLoreScreen = false;
                }
            }
        });

        // Settings links to other modals
        document.getElementById('settingsHowToPlay').addEventListener('click', () => {
            returnToSettings = true; // Remember we came from settings
            document.getElementById('settingsModal').classList.remove('active');
            const instructionsModal = document.getElementById('instructionsModal');
            instructionsModal.classList.add('active');
            
            // Reset scroll position to top
            const instructionsContent = instructionsModal.querySelector('.instructions-content');
            if (instructionsContent) {
                instructionsContent.scrollTop = 0;
            }
        });

        document.getElementById('settingsCredits').addEventListener('click', () => {
            returnToSettings = true; // Remember we came from settings
            document.getElementById('settingsModal').classList.remove('active');
            document.getElementById('creditsModal').classList.add('active');
        });

        // Side panel "full rules" link opens instructions modal
        const sidePanelHowToPlay = document.getElementById('sidePanelHowToPlay');
        if (sidePanelHowToPlay) {
            sidePanelHowToPlay.addEventListener('click', () => {
                const instructionsModal = document.getElementById('instructionsModal');
                instructionsModal.classList.add('active');
                const instructionsContent = instructionsModal.querySelector('.instructions-content');
                if (instructionsContent) {
                    instructionsContent.scrollTop = 0;
                }
            });
        }

        // Music toggle
        document.getElementById('musicToggle').addEventListener('click', function() {
            const muted = AdAudio.toggleMusicMute();
            this.classList.toggle('active', !muted);
            this.querySelector('.toggle-status').textContent = muted ? 'OFF' : 'ON';
            
            if (!muted) {
                AdAudio.setMusicMuted(false, 0);
            } else {
                AdAudio.setMusicMuted(true, 1);
            }
        });

        // SFX toggle
        document.getElementById('sfxToggle').addEventListener('click', function() {
            const muted = AdAudio.toggleSfxMute();
            this.classList.toggle('active', !muted);
            this.querySelector('.toggle-status').textContent = muted ? 'OFF' : 'ON';
            
            // Play a test sound when enabling
            if (!muted) {
                AdAudio.playSfx('spawn');
            }
        });

        // Binary display toggle
        const binaryToggle = document.getElementById('binaryToggle');
        if (binaryToggle) {
            binaryToggle.addEventListener('click', function() {
                binaryDisplayMode = !binaryDisplayMode;
                this.classList.toggle('active');
                this.querySelector('.toggle-status').textContent = binaryDisplayMode ? 'ON' : 'OFF';
                
                // Re-render the game board if game is active
                if (currentGame) {
                    currentGame.render();
                }
            });
        }

        // Performance mode toggle
        const performanceToggle = document.getElementById('performanceToggle');
        if (performanceToggle) {
            performanceToggle.addEventListener('click', function() {
                const performanceModeEnabled = document.body.classList.toggle('performance-mode');
                this.classList.toggle('active');
                this.querySelector('.toggle-status').textContent = performanceModeEnabled ? 'ON' : 'OFF';
            });
        }

        // Credits modal controls
        document.getElementById('closeCredits').addEventListener('click', () => {
            document.getElementById('creditsModal').classList.remove('active');
            returnToSettings = false;
        });

        document.getElementById('creditsToSettings').addEventListener('click', () => {
            document.getElementById('creditsModal').classList.remove('active');
            document.getElementById('settingsModal').classList.add('active');
            returnToSettings = false;
        });

        document.getElementById('creditsModal').addEventListener('click', (e) => {
            if (e.target.id === 'creditsModal') {
                document.getElementById('creditsModal').classList.remove('active');
                returnToSettings = false;
            }
        });
    } catch (error) {
        console.error('Error initializing game:', error);
        document.getElementById('loadingScreen').classList.add('hidden');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    AdAudio.destroy();
});
