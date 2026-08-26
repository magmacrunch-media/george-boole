/**
 * test-game-logic.js — Pure logic tests for George Boole game.
 * Tests Boolean operations, merge logic, overflow, and gate patterns.
 * 
 * Run: node test-game-logic.js
 */

// ── Extracted Pure Functions ──────────────────────────────────────────────────
// These are the core logic functions extracted from Game2048 for testing.

function isGate(val) {
    return val === -1 || val === -2 || val === -3 || val === -4;
}

function applyGate(gate, value1, value2, maxValue) {
    let result;
    switch (gate) {
        case -1: // XOR
            result = value1 ^ value2;
            break;
        case -2: // OR
            result = value1 | value2;
            break;
        case -3: // AND
            result = value1 & value2;
            break;
        case -4: // NOT (unary)
            result = (~value1) & maxValue;
            break;
        default:
            result = value1;
    }
    return result;
}

// A zero result means the tile is gone. Drop the cells rather than writing a
// literal 0 back, which the zero-stripped row would treat as a number operand.
function writeResult(cells, i, count, result) {
    if (result === 0) {
        cells.splice(i, count);
    } else {
        cells.splice(i, count, result);
    }
}

// Mirrors Game2048.moveLeft() row processing: one mutable array, re-scanned
// from the same index after every operation, so a result can feed the next one.
function advanceRow(row, maxValue) {
    // Returns { mergedRow, mergeOccurred }
    const size = row.length;

    // Strip zeros — 0 is the empty sentinel, never a tile
    const cells = row.filter(v => v !== 0);

    let mergeOccurred = false;
    let i = 0;

    while (i < cells.length) {
        // NOT + NOT = cancellation
        if (cells[i] === -4 && cells[i + 1] === -4) {
            cells.splice(i, 2);
            mergeOccurred = true;
            continue;
        }

        // NOT + NOT cancels behind a number too, so a chain resolves in one step
        if (!isGate(cells[i]) && cells[i + 1] === -4 && cells[i + 2] === -4) {
            cells.splice(i + 1, 2);
            mergeOccurred = true;
            continue;
        }

        // NOT + number (unary NOT)
        if (cells[i] === -4 && i + 1 < cells.length && !isGate(cells[i + 1])) {
            writeResult(cells, i, 2, applyGate(-4, cells[i + 1], null, maxValue));
            mergeOccurred = true;
            continue;
        }

        // number + NOT (reversed NOT)
        if (!isGate(cells[i]) && cells[i + 1] === -4) {
            writeResult(cells, i, 2, applyGate(-4, cells[i], null, maxValue));
            mergeOccurred = true;
            continue;
        }

        // number + gate + number (binary gate sandwich)
        if (!isGate(cells[i]) && i + 2 < cells.length &&
            isGate(cells[i + 1]) && cells[i + 1] !== -4 && !isGate(cells[i + 2])) {
            writeResult(cells, i, 3, applyGate(cells[i + 1], cells[i], cells[i + 2], maxValue));
            mergeOccurred = true;
            continue;
        }

        // Same values merge (idempotent: A+A=A)
        if (i + 1 < cells.length && !isGate(cells[i]) && cells[i] === cells[i + 1]) {
            cells.splice(i + 1, 1);
            mergeOccurred = true;
            i++;
            continue;
        }

        // No merge
        i++;
    }

    // Pad to original size
    while (cells.length < size) {
        cells.push(0);
    }

    return { mergedRow: cells.slice(0, size), mergeOccurred };
}

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

console.log('=== George Boole Game Logic Tests ===\n');

// ── isGate ───────────────────────────────────────────────────────────────────

console.log('isGate:');
assert(isGate(-1) === true, 'XOR is gate');
assert(isGate(-2) === true, 'OR is gate');
assert(isGate(-3) === true, 'AND is gate');
assert(isGate(-4) === true, 'NOT is gate');
assert(isGate(0) === false, '0 is not gate');
assert(isGate(1) === false, '1 is not gate');
assert(isGate(7) === false, '7 is not gate');
console.log(`  ${passed} passed\n`);

// ── applyGate: XOR ───────────────────────────────────────────────────────────

console.log('applyGate XOR:');
assertEqual(applyGate(-1, 1, 2, 3), 3, '1 XOR 2 = 3');
assertEqual(applyGate(-1, 3, 3, 3), 0, '3 XOR 3 = 0');
assertEqual(applyGate(-1, 1, 1, 3), 0, '1 XOR 1 = 0');
assertEqual(applyGate(-1, 2, 2, 3), 0, '2 XOR 2 = 0');
assertEqual(applyGate(-1, 0, 5, 7), 5, '0 XOR 5 = 5');
assertEqual(applyGate(-1, 5, 0, 7), 5, '5 XOR 0 = 5');
console.log(`  ${passed} passed\n`);

// ── applyGate: OR ────────────────────────────────────────────────────────────

console.log('applyGate OR:');
assertEqual(applyGate(-2, 1, 2, 3), 3, '1 OR 2 = 3');
assertEqual(applyGate(-2, 3, 3, 3), 3, '3 OR 3 = 3');
assertEqual(applyGate(-2, 1, 1, 3), 1, '1 OR 1 = 1');
assertEqual(applyGate(-2, 0, 5, 7), 5, '0 OR 5 = 5');
assertEqual(applyGate(-2, 5, 3, 7), 7, '5 OR 3 = 7');
console.log(`  ${passed} passed\n`);

// ── applyGate: AND ───────────────────────────────────────────────────────────

console.log('applyGate AND:');
assertEqual(applyGate(-3, 1, 2, 3), 0, '1 AND 2 = 0');
assertEqual(applyGate(-3, 3, 3, 3), 3, '3 AND 3 = 3');
assertEqual(applyGate(-3, 1, 3, 3), 1, '1 AND 3 = 1');
assertEqual(applyGate(-3, 5, 3, 7), 1, '5 AND 3 = 1');
assertEqual(applyGate(-3, 6, 3, 7), 2, '6 AND 3 = 2');
console.log(`  ${passed} passed\n`);

// ── applyGate: NOT ───────────────────────────────────────────────────────────

console.log('applyGate NOT:');
assertEqual(applyGate(-4, 0, 0, 3), 3, 'NOT 0 = 3 (2-bit)');
assertEqual(applyGate(-4, 1, 0, 3), 2, 'NOT 1 = 2 (2-bit)');
assertEqual(applyGate(-4, 2, 0, 3), 1, 'NOT 2 = 1 (2-bit)');
assertEqual(applyGate(-4, 3, 0, 3), 0, 'NOT 3 = 0 (2-bit)');
assertEqual(applyGate(-4, 0, 0, 7), 7, 'NOT 0 = 7 (3-bit)');
assertEqual(applyGate(-4, 7, 0, 7), 0, 'NOT 7 = 0 (3-bit)');
assertEqual(applyGate(-4, 5, 0, 15), 10, 'NOT 5 = 10 (4-bit)');
console.log(`  ${passed} passed\n`);

// ── advanceRow: Basic merges ─────────────────────────────────────────────────

console.log('advanceRow basic:');
assertEqual(advanceRow([1, 2, 3, 0], 3).mergedRow, [1, 2, 3, 0], 'No merge');
assertEqual(advanceRow([1, 1, 0, 0], 3).mergedRow, [1, 0, 0, 0], 'Same merge');
assertEqual(advanceRow([2, 2, 0, 0], 3).mergedRow, [2, 0, 0, 0], 'Same merge 2');
assertEqual(advanceRow([3, 3, 0, 0], 3).mergedRow, [3, 0, 0, 0], 'Same merge 3');
assertEqual(advanceRow([1, 2, 1, 2], 3).mergedRow, [1, 2, 1, 2], 'No merge different');
console.log(`  ${passed} passed\n`);

// ── advanceRow: Idempotent merge ─────────────────────────────────────────────

console.log('advanceRow idempotent:');
assertEqual(advanceRow([1, 1, 0, 0], 3).mergedRow, [1, 0, 0, 0], '1+1=1');
assertEqual(advanceRow([2, 2, 0, 0], 3).mergedRow, [2, 0, 0, 0], '2+2=2');
assertEqual(advanceRow([3, 3, 0, 0], 3).mergedRow, [3, 0, 0, 0], '3+3=3');
assertEqual(advanceRow([5, 5, 0, 0], 7).mergedRow, [5, 0, 0, 0], '5+5=5 (3-bit)');
assertEqual(advanceRow([7, 7, 0, 0], 7).mergedRow, [7, 0, 0, 0], '7+7=7 (3-bit)');
console.log(`  ${passed} passed\n`);

// ── advanceRow: Gate patterns ────────────────────────────────────────────────

console.log('advanceRow gate patterns:');
// XOR sandwich
assertEqual(advanceRow([1, -1, 2, 0], 3).mergedRow, [3, 0, 0, 0], '1 XOR 2 = 3');
assertEqual(advanceRow([3, -1, 3, 0], 3).mergedRow, [0, 0, 0, 0], '3 XOR 3 = 0');
// OR sandwich
assertEqual(advanceRow([1, -2, 2, 0], 3).mergedRow, [3, 0, 0, 0], '1 OR 2 = 3');
// AND sandwich
assertEqual(advanceRow([3, -3, 3, 0], 3).mergedRow, [3, 0, 0, 0], '3 AND 3 = 3');
assertEqual(advanceRow([1, -3, 2, 0], 3).mergedRow, [0, 0, 0, 0], '1 AND 2 = 0');
console.log(`  ${passed} passed\n`);

// ── advanceRow: NOT patterns ─────────────────────────────────────────────────

console.log('advanceRow NOT patterns:');
// NOT + number
assertEqual(advanceRow([-4, 1, 0, 0], 3).mergedRow, [2, 0, 0, 0], 'NOT 1 = 2');
// number + NOT
assertEqual(advanceRow([1, -4, 0, 0], 3).mergedRow, [2, 0, 0, 0], '1 NOT = 2');
// NOT + NOT = cancellation
assertEqual(advanceRow([-4, -4, 0, 0], 3).mergedRow, [0, 0, 0, 0], 'NOT NOT cancels');
assertEqual(advanceRow([-4, -4, 1, 0], 3).mergedRow, [1, 0, 0, 0], 'NOT NOT then 1');
console.log(`  ${passed} passed\n`);

// ── advanceRow: Zero results clear the tile ──────────────────────────────

console.log('advanceRow zero results:');
// A 0 left in the row would be re-scanned as an operand by the next gate
assertEqual(advanceRow([7, -4, -2, 4], 7).mergedRow, [-2, 4, 0, 0], 'NOT 7 clears, OR and 4 survive');
assertEqual(advanceRow([7, -4, -3, 4], 7).mergedRow, [-3, 4, 0, 0], 'NOT 7 clears, AND and 4 survive');
assertEqual(advanceRow([6, -4, -2, 4], 7).mergedRow, [5, 0, 0, 0], 'no overflow: NOT 6 = 1, 1 OR 4 = 5');
console.log(`  ${passed} passed
`);

// ── advanceRow: NOT chains ────────────────────────────────────────────

console.log('advanceRow NOT chains:');
assertEqual(advanceRow([3, -4, -4, 0], 3).mergedRow, [3, 0, 0, 0], 'NOT NOT cancels behind a number');
assertEqual(advanceRow([114, -4, -4, -4], 127).mergedRow, [13, 0, 0, 0], 'triple NOT resolves once');
console.log(`  ${passed} passed
`);

// ── advanceRow: Edge cases ───────────────────────────────────────────────────

console.log('advanceRow edge cases:');
assertEqual(advanceRow([0, 0, 0, 0], 3).mergedRow, [0, 0, 0, 0], 'All zeros');
assertEqual(advanceRow([1, 2, 3, 4], 7).mergedRow, [1, 2, 3, 4], 'Full row no merge');
assertEqual(advanceRow([-4, 0, 0, 0], 3).mergedRow, [-4, 0, 0, 0], 'NOT at edge stays (gate waiting for number)');
console.log(`  ${passed} passed\n`);

// ── Summary ──────────────────────────────────────────────────────────────────

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);
