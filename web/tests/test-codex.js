// test-codex.js — the gate codex and discoveries (js/codex.js).
//
// detect() decides what a move unlocks, from game.js's operation log. It runs
// here with no DOM: codex.js skips everything page-related when there is no
// document. Operations are written the way BooleBoard.lastOperations records
// them, so the fixtures below are what a real move produces.

const fs = require('fs');
const vm = require('vm');

vm.runInThisContext(fs.readFileSync(__dirname + '/../js/codex.js', 'utf8'), { filename: 'codex.js' });
const { detect, emptyState, GATES, GATE_ORDER, DISCOVERIES } = globalThis.BooleCodex;

let passed = 0;
let failed = 0;

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

const gate = (name, a, b, result) => ({ kind: 'gate', gate: name, a, b, result, points: result, row: 0, col: 0 });
const overflow = (a, points) => ({ kind: 'overflow', gate: 'NOT', a, b: null, result: 0, points, row: 0, col: 0 });
const same = (v) => ({ kind: 'same', a: v, b: v, result: v, points: v, row: 0, col: 0 });

console.log('=== George Boole gate codex ===\n');

console.log('Truth tables:');
try {
    const table = (name) => {
        const g = GATES[name];
        return g.unary ? [g.out(0), g.out(1)] : [g.out(0, 0), g.out(0, 1), g.out(1, 0), g.out(1, 1)];
    };
    assertEqual(table('XOR'), [0, 1, 1, 0], 'XOR is 1 where the inputs differ');
    assertEqual(table('OR'), [0, 1, 1, 1], 'OR is 1 where either input is');
    assertEqual(table('AND'), [0, 0, 0, 1], 'AND is 1 only where both are');
    assertEqual(table('NOT'), [1, 0], 'NOT flips');
    assertEqual(DISCOVERIES.length, 7, 'seven discoveries');
    assertEqual(new Set(DISCOVERIES.map((d) => d.id)).size, 7, 'discovery ids are unique');
} catch (e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

console.log('Unlocking a gate:');
try {
    const state = emptyState();
    let found = detect(state, [gate('XOR', 5, 3, 6)], 4, 1000);
    assertEqual(found.gates, ['XOR'], 'the first XOR unlocks XOR');
    assertEqual(state.gates.XOR.first, { a: 5, b: 3, result: 6, bits: 4 }, 'and remembers the operation that did it');
    // 0101 XOR 0011, column by column: (0,0) (1,0) (0,1) (1,1).
    assertEqual(state.gates.XOR.rows, { '00': 1, '10': 1, '01': 1, '11': 1 },
        'each column counts as one row of the one-bit truth table');

    found = detect(state, [gate('XOR', 1, 2, 3)], 4, 2000);
    assertEqual(found.gates, [], 'a second XOR unlocks nothing new');
    assertEqual(state.gates.XOR.first.a, 5, 'and does not replace the first');
    // 0001 XOR 0010: (0,0) (0,0) (0,1) (1,0).
    assertEqual(state.gates.XOR.rows, { '00': 3, '10': 2, '01': 2, '11': 1 }, 'but its columns are counted');

    detect(state, [gate('NOT', 1, null, 2)], 2, 3000);
    assertEqual(state.gates.NOT.rows, { '0': 1, '1': 1 }, 'NOT rows are one input wide, at the move\'s bit width');
    assertEqual(state.gates.NOT.first.b, null, 'NOT has no second operand');

    const s2 = emptyState();
    assertEqual(detect(s2, [same(5)], 4).gates, [], 'same + same is not a gate and unlocks nothing');
} catch (e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

console.log('Discoveries:');
try {
    const found = (ops, bits) => detect(emptyState(), ops, bits).discoveries;

    assertEqual(found([gate('XOR', 5, 5, 0)], 4), ['self_inverse'], 'XOR of equal numbers is self-inverse');
    assertEqual(found([gate('XOR', 5, 3, 6)], 4), [], 'an ordinary XOR is not');

    assertEqual(found([gate('AND', 4, 3, 0)], 4), ['nothing_in_common'], 'AND with no shared bits is nothing in common');
    assertEqual(found([gate('AND', 6, 3, 2)], 4), [], 'AND that keeps a bit is not');

    assertEqual(found([gate('OR', 12, 3, 15)], 4), ['all_lit'], 'OR filling every column is all lit');
    assertEqual(found([gate('OR', 15, 3, 15)], 4), [], 'but not when an input was already all ones');
    assertEqual(found([gate('OR', 5, 2, 7)], 4), [], 'OR short of the ceiling is not');
    assertEqual(found([gate('OR', 5, 2, 7)], 3), ['all_lit'], 'the ceiling is the move\'s own width: 7 is all lit at 3-bit');

    assertEqual(found([gate('XOR', 10, 5, 15)], 4), ['opposites'], 'XOR of complements lights every bit');
    assertEqual(found([gate('XOR', 12, 1, 13)], 4), [], 'XOR short of the ceiling is not opposites');

    assertEqual(found([overflow(15, 45)], 4), ['wraparound'], 'an overflow is wraparound');

    assertEqual(found([gate('OR', 1, 2, 3), gate('XOR', 3, 1, 2)], 4), ['chain_reaction'],
        'two gates in one move is a chain reaction');
    assertEqual(found([gate('OR', 1, 2, 3), same(3)], 4), [], 'a gate and a consolidation is not');

    const state = emptyState();
    detect(state, [gate('XOR', 5, 3, 6)], 4);
    detect(state, [gate('OR', 5, 2, 7)], 4);
    detect(state, [gate('AND', 6, 3, 2)], 4);
    assertEqual(state.discoveries.full_set, undefined, 'three gates is not the full set');
    const last = detect(state, [gate('NOT', 5, null, 10)], 4);
    assertEqual(last.gates, ['NOT'], 'the fourth gate unlocks');
    assertEqual(last.discoveries, ['full_set'], 'and completes the full set in the same move');

    const again = detect(state, [gate('XOR', 5, 5, 0)], 4);
    detect(state, [gate('XOR', 6, 6, 0)], 4);
    assertEqual(again.discoveries, ['self_inverse'], 'a discovery is reported the first time');
    assertEqual(detect(state, [gate('XOR', 7, 7, 0)], 4).discoveries, [], 'and never again');
    assertEqual(GATE_ORDER.every((g) => state.gates[g]), true, 'all four gates recorded');
} catch (e) {
    console.error(`  FAIL: ${e.message}`);
    failed++;
}
console.log(`  ${passed} passed\n`);

console.log(`\n=== Results: ${passed} passed, ${failed} failed ===`);
process.exit(failed > 0 ? 1 : 0);
