/**
 * test-game.js — Smoke tests for George Boole Game2048 class.
 * Tests the full game with minimal DOM mocking.
 * 
 * Run: node test-game.js
 */

// ── Minimal DOM shim ─────────────────────────────────────────────────────────
// Provide just enough DOM to let Game2048 constructor run without errors.

function createMockEl() {
    const el = {
        style: {},
        classList: { add(){}, remove(){}, contains(){ return false; } },
        textContent: '',
        innerHTML: '',
        appendChild(){},
        remove(){},
        querySelector(){ return createMockEl(); },
        querySelectorAll(){ return []; },
        addEventListener(){},
        removeEventListener(){},
        getAttribute(){ return ''; },
        setAttribute(){},
        removeAttribute(){},
        dataset: {},
        offsetWidth: 600,
        offsetHeight: 600,
        children: [],
        parentNode: { insertBefore(){}, removeChild(){} },
    };
    return el;
}

const mockElement = createMockEl();

global.document = {
    getElementById(id) { return createMockEl(); },
    querySelector(){ return createMockEl(); },
    querySelectorAll(){ return []; },
    createElement(){ return createMockEl(); },
    addEventListener(){},
    removeEventListener(){},
    documentElement: { style: { setProperty(){}, getPropertyValue(){ return ''; } } },
    body: { appendChild(){}, classList: { add(){}, remove(){}, contains(){ return false; } } },
};

global.window = {
    location: { search: '', hostname: 'localhost' },
    addEventListener(){},
    innerWidth: 1200,
    innerHeight: 800,
    matchMedia(){ return { matches: false, addEventListener(){} }; },
};

global.localStorage = {
    getItem(){ return null; },
    setItem(){},
    removeItem(){},
};

global.setTimeout = function(fn, delay) { 
    // Don't actually execute — just record
    return 1; 
};
global.clearTimeout = function(){};
global.currentGame = null;

// Mock AdPuzzle (adenosine puzzle input library)
global.AdPuzzle = {
    createInput() { return {}; },
};

// Mock AdAudio (adenosine audio library)
global.AdAudio = {
    playSfx() {},
    playMusic() { return Promise.resolve(); },
    init() { return Promise.resolve(); },
};

// Mock scoreClient (adenosine score-client instance)
global.scoreClient = {
    save() { return Promise.resolve(); },
    load() { return Promise.resolve([]); },
};

// ── Load Game2048 ────────────────────────────────────────────────────────────
const fs = require('fs');
const vm = require('vm');
const gameCode = fs.readFileSync(__dirname + '/../js/game.js', 'utf8');

// Run in this context so class is accessible
vm.runInThisContext(gameCode, { filename: 'game.js' });

// ── Tests ────────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function assert(condition, message) {
    if (condition) {
        passed++;
    } else {
        failed++;
        console.error(`  FAIL: ${message}`);
    }
}

function assertEqual(actual, expected, message) {
    const a = JSON.stringify(actual);
    const e = JSON.stringify(expected);
    if (a === e) {
        passed++;
    } else {
        failed++;
        console.error(`  FAIL: ${message} — got ${a}, expected ${e}`);
    }
}

console.log('=== George Boole Game2048 Smoke Tests ===\n');

// ── Constructor ──────────────────────────────────────────────────────────────

console.log('Constructor:');
try {
    const game = new Game2048('2', 'test');
    assert(game.size === 4, 'Board size is 4');
    assert(game.board.length === 4, 'Board has 4 rows');
    assert(game.score === 0, 'Initial score is 0');
    assert(game.moves === 0, 'Initial moves is 0');
    assert(game.maxValue === 3, '2-bit mode maxValue is 3');
    assert(game.gateSpawnChance === 0.45, '2-bit gate spawn rate is 0.45');
} catch(e) {
    console.error(`  FAIL: Constructor threw ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Gate spawn rate ──────────────────────────────────────────────────────────

console.log('updateGateSpawnRate:');
try {
    const game = new Game2048('2', 'test');
    
    game.bitMode = 2;
    game.updateGateSpawnRate();
    assertEqual(game.gateSpawnChance, 0.45, '2-bit rate');
    
    game.bitMode = 3;
    game.updateGateSpawnRate();
    assertEqual(game.gateSpawnChance, 0.32, '3-bit rate');
    
    game.bitMode = 4;
    game.updateGateSpawnRate();
    assertEqual(game.gateSpawnChance, 0.24, '4-bit rate');
    
    game.bitMode = 5;
    game.updateGateSpawnRate();
    assertEqual(game.gateSpawnChance, 0.20, '5-bit rate');
    
    game.bitMode = 7;
    game.updateGateSpawnRate();
    assertEqual(game.gateSpawnChance, 0.18, '7-bit rate');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Move left basic ──────────────────────────────────────────────────────────

console.log('moveLeft:');
try {
    const game = new Game2048('2', 'test');
    
    // Test 1: No merge possible
    game.board = [
        [1, 2, 1, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ];
    game.score = 0;
    
    const moved1 = game.moveLeft();
    assert(moved1 === false, 'No merge = no change');
    assertEqual(game.score, 0, 'Score unchanged');
    
    // Test 2: Same values merge
    game.board = [
        [1, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ];
    game.score = 0;
    
    const moved2 = game.moveLeft();
    assert(moved2 === true, 'Merge occurred');
    assertEqual(game.board[0], [1, 0, 0, 0], '1+1=1');
    assertEqual(game.score, 1, 'Score = value');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
}
console.log(`  ${passed} passed\n`);

// ── Idempotent merge ─────────────────────────────────────────────────────────

console.log('Idempotent merge:');
try {
    const game = new Game2048('2', 'test');
    game.board = [
        [1, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ];
    game.score = 0;
    
    game.moveLeft();
    assertEqual(game.board[0], [1, 0, 0, 0], '1+1=1');
    assertEqual(game.score, 1, 'Score = value consolidated');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Gate operation ───────────────────────────────────────────────────────────

console.log('Gate operation:');
try {
    const game = new Game2048('2', 'test');
    game.board = [
        [1, -1, 2, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ];
    game.score = 0;
    
    game.moveLeft();
    assertEqual(game.board[0], [3, 0, 0, 0], '1 XOR 2 = 3');
    assertEqual(game.score, 3, 'Score = result value');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Game over detection ──────────────────────────────────────────────────────

console.log('Game over detection:');
try {
    const game = new Game2048('2', 'test');
    
    // Fill board with no valid moves
    game.board = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ];
    
    const isOver = game.checkGameOver();
    assert(isOver === true, 'Full board with no moves = game over');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}

try {
    const game = new Game2048('2', 'test');
    
    // Board with a valid move available
    game.board = [
        [1, 2, 1, 0],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ];
    
    const isOver = game.checkGameOver();
    assert(isOver === false, 'Board with empty cell = not game over');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Game over preserves state ────────────────────────────────────────────────

console.log('Game over preserves state:');
try {
    const game = new Game2048('2', 'test');
    game.score = 100;
    game.moves = 50;
    game.highestValueEver = 3;
    
    // Fill board with no valid moves
    game.board = [
        [1, 2, 1, 2],
        [2, 1, 2, 1],
        [1, 2, 1, 2],
        [2, 1, 2, 1],
    ];
    
    game.checkGameOver();
    
    assertEqual(game.score, 100, 'Score preserved');
    assertEqual(game.moves, 50, 'Moves preserved');
    assertEqual(game.highestValueEver, 3, 'Highest value preserved');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

// ── Zero results and NOT chains ──────────────────────────────────────

console.log('Zero results and NOT chains:');
try {
    // A gate result of 0 clears the tile. It must leave nothing behind: the row
    // is built with zeros stripped, so a literal 0 would be re-scanned as an
    // operand and eat the tiles to its right.
    const only = (cells) => [cells, [0,0,0,0], [0,0,0,0], [0,0,0,0]];

    // 3-bit: NOT 7 = 0, the overflow move (+21). The gate and the 4 both survive.
    let game = new Game2048('3', 'test');
    game.board = only([7, -4, -2, 4]);
    game.score = 0;
    game.moveLeft();
    assertEqual(game.board[0], [-2, 4, 0, 0], 'overflow leaves the OR gate and the 4');
    assertEqual(game.score, 21, 'overflow scores 21, not 25');

    game = new Game2048('3', 'test');
    game.board = only([7, -4, -3, 4]);
    game.score = 0;
    game.moveLeft();
    assertEqual(game.board[0], [-3, 4, 0, 0], 'overflow does not destroy the 4 via AND');
    assertEqual(game.score, 21, 'overflow scores 21');

    // Same shape without an overflow: a real two-step resolution, unchanged.
    game = new Game2048('3', 'test');
    game.board = only([6, -4, -2, 4]);
    game.score = 0;
    game.moveLeft();
    assertEqual(game.board[0], [5, 0, 0, 0], 'NOT 6 = 1, then 1 OR 4 = 5');
    assertEqual(game.score, 6, 'two-step resolution scores 1 + 5');

    // A binary gate cancelling to zero also leaves nothing.
    game = new Game2048('3', 'test');
    game.board = only([1, -3, 2, 0]);
    game.score = 0;
    game.moveLeft();
    assertEqual(game.board[0], [0, 0, 0, 0], '1 AND 2 = 0 clears the row');

    // A NOT chain resolves once, and is billed once.
    game = new Game2048('7', 'test');
    game.board = only([114, -4, -4, -4]);
    game.score = 0;
    game.moveLeft();
    assertEqual(game.board[0], [13, 0, 0, 0], 'triple NOT of 114 is 13');
    assertEqual(game.score, 13, 'the chain scores the one operation it performed');
    assertEqual(game.highestValueEver, 13, 'no intermediate 114 in highestValueEver');

    // The documented cancellation fires with a number to the left of the pair.
    game = new Game2048('3', 'test');
    game.board = only([3, -4, -4, 0]);
    game.score = 0;
    const cancelled = game.moveLeft();
    assert(cancelled === true, 'NOT NOT cancellation counts as a merge');
    assertEqual(game.board[0], [3, 0, 0, 0], 'the pair cancels and leaves the 3');
    assertEqual(game.score, 0, 'an identity operation scores nothing');
} catch(e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed
`);

// ── Summary ──────────────────────────────────────────────────────────────────

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);
