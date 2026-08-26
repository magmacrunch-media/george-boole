# George Boole has entered the chat 🎮

A **Boolean logic puzzle game** where you combine numbers using bitwise operations and survive as long as possible! Think survival mode meets computer science - use logic gates (XOR, OR, AND, NOT) to manage your board before it fills up!

---

## 🎯 How to Play

### Goal
**Survive as long as possible** and earn the highest score by strategically using logic gates and managing your board space!

### The Twist: Boolean Logic!
Unlike 2048 where tiles double (2+2=4), this game uses **Boolean operations**:

#### Same Numbers Consolidate
```
1 + 1 = 1  (idempotence: A∨A = A)
2 + 2 = 2  (same values merge to same)
3 + 3 = 3  (no doubling!)
```

#### Different Numbers Need Gates
You **cannot** merge different numbers directly! You must use logic gates:
```
Can't do: 1 + 2
Must use: 1 [OR] 2 = 3
       or 1 [XOR] 2 = 3
```

#### Logic Gate Operations
- **XOR (⊕)**: `1 XOR 2 = 3`, `2 XOR 3 = 1`
- **OR (∨)**: `1 OR 2 = 3`, `4 OR 3 = 7`
- **AND (∧)**: `3 AND 2 = 2`, `7 AND 4 = 4`
- **NOT (¬)**: `NOT 1 = 2` (in 2-bit), `NOT 8 = 7` (in 4-bit)
  - **Special:** NOT is unary - just slide it into any number! No sandwich needed.

---

## 🔄 Rollover Mechanic

Each bit mode has a **maximum value** (2ⁿ - 1):

| Mode | Max Value | What Happens |
|------|-----------|--------------|
| 2-BIT | 3 | Operations exceeding 3 → **OVERFLOW! +9 bonus pts** |
| 3-BIT | 7 | Operations exceeding 7 → **OVERFLOW! +21 bonus pts** |
| 4-BIT | 15 | Operations exceeding 15 → **OVERFLOW! +45 bonus pts** |
| 5-BIT | 31 | Operations exceeding 31 → **OVERFLOW! +93 bonus pts** |
| 6-BIT | 63 | Operations exceeding 63 → **OVERFLOW! +189 bonus pts** |
| 7-BIT | 127 | Operations exceeding 127 → **OVERFLOW! +381 bonus pts** |
| 8-BIT | 255 | Operations exceeding 255 → **OVERFLOW! +765 bonus pts** |
| GAUNTLET | ∞ | Progressive — survive all modes! |

**Strategic choice:** Overflow clears the tile (frees space) AND awards big bonus points!

---

## 🎮 Game Modes

Modes are named after real bit-culture terminology:

| Mode | Name | Max Value | Theme |
|------|------|-----------|-------|
| 2-BIT | crumb | 3 | Game Boy green |
| 3-BIT | trit | 7 | NES red/orange |
| 4-BIT | nibble | 15 | SNES blue/purple |
| 5-BIT | pentad | 31 | Genesis blue/cyan |
| 6-BIT | hexad | 63 | Arcade red/gold |
| 7-BIT | ascii | 127 | Neo Geo pink/cyan |
| 8-BIT | byte | 255 | PS1 silver (gold accents) |
| GAUNTLET | progressive | — | Matrix green |

### 🔄 Gauntlet Mode: Progressive Difficulty
Gauntlet mode is the **ultimate survival challenge** with escalating difficulty:

- **Start at 2-BIT** (max value: 3)
- **Reach the max value** → Automatic upgrade!
- **Progress through all modes**: 2-BIT → 3-BIT → 4-BIT → 5-BIT → 6-BIT → 7-BIT → 8-BIT
- **Each upgrade** increases max value and difficulty
- **Watch the display**: Shows current mode and goal (e.g., "REACH → 3")
- **Final challenge**: Survive 8-BIT mode as long as you can!

**Example:** Start with max value 3, reach it, upgrade to max value 7, reach it, upgrade to max value 15, and so on...

---

## 📊 Scoring System

### How Points are Earned:

1. **Operations**: Points = result value
   - `1 + 1 = 1` → +1 point
   - `4 OR 3 = 7` → +7 points

2. **Height Bonuses**: First time reaching certain values (must be earned through merges, not spawned)
   - 3-bit: Bonuses for 6, 7 (double value!)
   - 4-bit: Bonuses for 5+
   - Higher modes: Upper-tier values only

3. **Overflow Bonuses**: Max value × 3
   - 2-bit overflow: +9 points
   - 8-bit overflow: +765 points!

**Strategy:** Balance survival (consolidate) vs. scoring (reach new heights, cause overflows)

### 🏅 Special Tile Treatments

- **Rainbow tile**: The exact max-value tile in each mode gets a rainbow gradient. In Gauntlet, the specific tile instance that *earned* the mode upgrade is marked — it travels with you as you play.
- **Gold-plated tile**: The single tile representing your current session high gets a shimmering gold treatment. Only awarded for values you *earned through merges* (not randomly spawned ones), and only for meaningful achievements above each mode's threshold.

---

## ✨ Features

- 🔧 **Logic Gates**: XOR, OR, AND, NOT
- 🎯 **Boolean Idempotence**: Same+same=same
- 💥 **Overflow Bonuses**: Risk = reward!
- 📈 **Height Bonuses**: Milestone rewards
- 🌈 **Rainbow Max Tile**: Visual celebration for hitting the mode ceiling
- ✨ **Gold-Plated Personal Best**: Your session high tile shimmers gold
- 🎨 **8 Retro Themes**: Unique per mode, with collision-free gate colors
- 🔢 **Binary Display Mode**: See the bitwise magic (improved readability: larger binary text, better contrast per theme)
- ☁️ **Global Leaderboards**: Compete worldwide, with OVERALL cross-mode board
- 🔊 **Sound Effects & Music**: Retro vibes
- 📱 **Touch Controls**: Mobile-friendly
- ⚙️ **Settings**: Customize audio and display
- ⚡ **Performance Mode**: Reduce CPU usage & heat
- ⌨️ **Keyboard Support**: Arrow keys + spacebar

---

## 🚀 Quick Start

1. Open `index.html` in browser
2. Press [SPACE] or click to start
3. Select a bit mode (try 3-BIT first!)
4. Use arrow keys or swipe to move tiles
5. Survive and score!

---

## 🎓 Educational Value

Teaches:
- **Boolean algebra** (A∨A = A, idempotence)
- **Bitwise operations** (XOR, OR, AND, NOT)
- **Binary representation** (see the bits!)
- **Overflow arithmetic** (modulo behavior)
- **Strategic thinking** (risk management)

Perfect for CS students, programmers, or anyone curious about how computers work!

---

## 🎯 Strategy Tips

### Beginners:
- Learn what each gate does (check instructions!)
- NOT gates are easy - just slide them into any number!
- Consolidate same numbers to free space
- Don't be afraid of overflow - it gives bonus points!

### Intermediate:
- Plan gate usage 2-3 moves ahead
- Balance scoring (new highs) vs. survival (consolidation)
- Use overflow strategically to clear space

### Advanced:
- Maximize height bonuses in mid-game
- Time overflows for maximum points
- Manage board space like Tetris

---

## ⚡ Performance Optimizations

### Automatic Optimizations:
- Background animations only run during active gameplay
- Loading spinner stops when hidden
- Audio fades use fewer steps (still smooth!)
- Reduced GPU memory usage

### Performance Mode:
Toggle in Settings → Display Options to:
- Disable CRT scanline effects
- Disable background glow animations
- Reduce CPU usage by 70-85%
- Keep gameplay completely intact

**Perfect for:** Laptops, extended sessions, battery saving, or if your device runs hot!

---

## 🗺️ Planned Features

### 16-BIT Mode (word)
The next planned mode after 8-BIT would be **16-BIT**, named "word" — the actual technical term used in assembly and low-level programming (alongside dword for 32-bit and qword for 64-bit).

Key design considerations for 16-BIT:
- **Max value**: 65,535 — far too large to read comfortably in decimal
- **Hexadecimal display**: tiles would show values in hex notation (e.g. `0xFF`, `0x3F`) instead of decimal, since hex maps naturally onto bit boundaries and is how programmers actually think about 16-bit values
- **Gameplay tuning**: the much larger value range would require rethinking spawn rates and overflow bonuses to keep sessions feeling meaningful
- Future modes beyond 16-bit (32-bit "dword", 64-bit "qword") would follow the same hex convention

This would also be a natural point to introduce a **hex display toggle** in Settings alongside the existing binary display toggle.

---

## 🗝️ Current Status

### ✅ Completed Features:
- Boolean logic core (idempotence)
- Rollover/overflow mechanics with bonuses
- Progressive tile spawning (scales with progress)
- Height bonus system (rewards milestones)
- Points-based scoring
- 8 difficulty modes with proper balance
- Gauntlet mode with progressive bit upgrades
- Binary display with proper padding
- Mode display in UI (shows "REACH → N" in Gauntlet)
- Clean leaderboards (just points)
- All gate operations working
- **NOT gate as unary operation** (no sandwich required!)
- **2-bit Gauntlet fix**: max value (3) never spawns — must be earned
- Custom dropdown selector with retro styling
- Bit-culture mode names (crumb, tribt, nibble, pentad, hexad, ascii, byte)
- Unique theme per mode (including new arcade red/gold for 6-bit)
- Improved "How to Play" window with better readability
- Unified navigation (High Scores & Settings buttons)
- Touch controls for mobile devices
- Mobile layout fixes (scrollable mode select, contained game-over modal)
- Spacebar support on title screen
- Audio system with pool-based SFX management
- **Performance optimizations** for reduced CPU usage & heat
- **Rainbow max-value tile**: per-mode and per-instance in Gauntlet
- **Gold-plated personal best tile**: tracks session high, earned merges only
- **Gate color overhaul**: each gate (XOR/OR/AND/NOT) has a distinct color per theme with no collisions against number tile ramps

### 🎮 Gameplay Balance:
- Gate spawn rates tuned by mode (45% in 2-bit, 18% in 8-bit)
- No gate caps (natural accumulation)
- Progressive spawn system (higher tiles as you progress)
- Smart height bonuses (only for earned merges above mode threshold, not spawned values)
- Gold tile only awarded for values above each mode's spawnable range

### 🎵 Audio System:
Ready for custom sound effects! Replace placeholder files in `audio/sfx/`:
- `merge.ogg` - When tiles combine
- `spawn.ogg` - New tile appears
- `victory.ogg` - High score milestones
- `gameover.ogg` - Game ends
- `move.ogg` - Valid tile movements
- `highscore.ogg` - New personal best

System features audio pooling (3 instances per sound) for smooth overlapping playback.

### 🔧 Ready to Deploy:
All core systems working and balanced! Fully optimized for performance.

---

## 📂 File Structure

```
.
├── index.html          # Main page (difficulty selector, modals)
├── js/
│   ├── game.js        # Core game logic (Boolean ops, rollover, scoring)
│   ├── scoring.js     # Leaderboard system
│   ├── main.js        # UI management, sound, settings
│   └── config.js      # API keys, configuration
├── css/
│   ├── base.css            # Base styles & CRT effects (optimized!)
│   ├── themes.css          # Retro themes (one per mode)
│   ├── game.css            # Tile styling (graduated color ramps, special tiles)
│   ├── gates.css           # Gate tile styling (collision-free per theme)
│   ├── container.css       # Main container
│   ├── responsive.css      # Mobile support
│   ├── modal-title.css     # Title screen
│   ├── modal-difficulty.css # Difficulty selector & per-theme button styles
│   ├── modal-scoreboard.css # Dropdown, scoreboard, initials prompt
│   ├── modal-settings.css  # Settings (toggle buttons hardened against theme bleed)
│   └── modal-misc.css      # Instructions, credits, game over
└── audio/
    ├── game-loop.ogg  # Background music
    └── sfx/           # Sound effects (ready for custom recordings)
```

---

## 🎨 Themes

Each bit mode has its own distinct retro theme, with gate tiles using colors that never clash with the number tile ramp:

| Mode | Theme | Gate color philosophy |
|------|-------|-----------------------|
| 2-bit | Game Boy green | Gates use teal, ochre, slate blue, near-black |
| 3-bit | NES red/orange | Gates use teal, amber, deep magenta, near-black |
| 4-bit | SNES blue/purple | Gates use electric teal, burnt amber, dark indigo, near-black |
| 5-bit | Genesis blue/cyan | Gates use spring green, rose-pink, dark teal, near-black |
| 6-bit | Arcade red/gold | Gates use cyan, violet, forest green, near-black |
| 7-bit | Neo Geo pink/cyan | Gates use vivid orange, coral-red, dark olive, near-black |
| 8-bit | PS1 silver (gold accents) | Gates use emerald green, lime-yellow, deep teal, near-black |
| Gauntlet | Matrix green | Gates use magenta, electric blue, amber, near-white (off-palette) |

---

## 🏆 Leaderboard

- **Global scores** saved to MAGMA//OPS backend via ScoreClient
- **Top 10** per difficulty mode
- **OVERALL board**: top 10 scores across all modes with mode badge
- **Sorted by points** (highest wins)
- Shows: Rank (gold/silver/bronze color for top 3), initials, score
- Custom dropdown selector with retro styling
- **Default view**: OVERALL on first visit; last-played mode thereafter

Format: `#1  ABC  247 pts  [8-BIT]` (on overall board)

---

## 📖 Credits

- **Based on**: 2048 by Gabriele Cirulli
- **Mechanics by**: Boolean algebra & bitwise operations
- **Developed by**: Jake McCoy
- **Published by**: magmacrunch media
- **Music**: "George Boole has entered the chat" by Juanito Thompson
- **SFX**: Custom analog synthesizer recordings (coming soon!)
- **Font**: Press Start 2P by CodeMan38
- **Themes**: Custom retro designs
- **Inspiration**: George Boole (1815-1864), mathematician & logician

---

## 📝 Version History

### Latest (February 2026)
- **CSS refactor**: split `modals.css` into 5 focused files (`modal-title`, `modal-difficulty`, `modal-scoreboard`, `modal-settings`, `modal-misc`) for easier maintenance
- **Settings modal fix**: toggle buttons and HOW TO PLAY/CREDITS links now correctly use default styling regardless of active game theme (same `!important` pattern already used by the scoreboard modal)
- Added **OVERALL high scores** board: top 10 across all modes with mode badge on each entry
- **Smart scoreboard default**: shows OVERALL on first visit; remembers last-played mode across sessions
- **5-BIT theme redesign**: Genesis blue/cyan replaces blue/gold — eliminates clash with gold personal-best tile
- **8-BIT contrast fix**: tile text now uses gold on dark grey tiles, dark text on light grey tiles
- **Score entry layout**: switched to CSS grid — mode badge no longer wraps or gets squeezed
- **Top-3 rank colors**: gold/silver/bronze on #1/#2/#3 rank numbers (no redundant label text)
- **Binary display improvements**: larger text (10px→13px), higher opacity (0.7→0.85), safe smaller decimal to prevent overflow; per-theme color fixes for low-contrast tiles
- **Mode button subtitles**: larger (7px→9px), higher opacity, per-theme color overrides for legibility
- **Retro UI**: replaced all in-game emoji (medals, notifications) with ASCII alternatives (*** OVERFLOW ***, >>> NEW HIGH, etc.)
- **Score box ring fix**: cyan box-shadow no longer bleeds through on PS1, Matrix, and Genesis themes

### Previous (February 2026)
- 🌈 Rainbow max-value tile treatment (per mode; per tile-instance in Gauntlet)
- ✨ Gold-plated personal best tile (session high, earned merges only, above spawnable threshold)
- 🎨 Gate color overhaul: XOR/OR/AND/NOT each have distinct, collision-free colors per theme
- 🐛 Fixed: gold tile no longer appears on randomly-spawnable values
- 🐛 Fixed: gold tile state no longer corrupted by game-over move simulation
- 🐛 Fixed: gold tile mark-before-clear race condition in multi-row moves
- 🗺️ Planned 16-BIT "word" mode with hexadecimal tile display
- 🎨 New arcade red/gold theme for 6-bit mode (replacing duplicate SNES Classic)
- 🏷️ Bit-culture mode names: crumb, tribit, nibble, pentad, hexad, ascii, byte
- 🎮 Gauntlet mode display now shows "REACH → N" instead of "MERGE → N"
- 🐛 Fixed: 2-bit Gauntlet no longer spawns 3 (max value must be earned)
- 📱 Mobile fixes: scrollable mode select, constrained game-over modal, tile overflow prevention
- ⚡ Major performance optimizations (50-85% CPU reduction)
- ⚡ Added Performance Mode toggle
- 🎮 NOT gate now works as unary operation (intuitive!)
- 🔧 Optimized animations (only run during gameplay)
- 🔧 Reduced audio fade overhead
- 🔧 Removed unnecessary GPU allocations

---

**Have fun, and may George Boole be with you!** 🎮✨
