// math-overlay.js
//
// Shows the player what each move actually did.
//
// The score on its own reads as arbitrary: every gate pays the decimal value
// of its result, so a player learns "OR scores well, AND scores badly" without
// ever seeing why. The logic is in the bits, and the bits used to change in a
// single frame. This draws two things over the board after every move:
//
//  - a point label on each tile that scored: "+6 XOR", "+5 SAME",
//    "+45 OVERFLOW", "+12 NEW HIGH", or "AND = 0" for a gate that cleared its
//    tiles. Always on: it only explains the score.
//  - "show the math": the bit columns of the move's most interesting gate,
//    drawn above the tile it produced, result bits lighting left to right.
//
//      0101
//    ⊕ 0011
//    ──────
//      0110
//
// It reads game.js's boole:operations event and nothing else, so it cannot
// change what a move does. Positions arrive in board coordinates; the tile for
// row r, column c is the gameBoard's child r * 4 + c.

(function () {
    'use strict';

    const STORAGE_KEY = 'gb_show_math';
    const SIZE = 4;

    const GATE_SYMBOL = { XOR: '⊕', OR: '∨', AND: '∧', NOT: '¬' };

    let showMath = true;
    try {
        showMath = localStorage.getItem(STORAGE_KEY) !== 'off';
    } catch (e) {
        // Storage unavailable: keep the default.
    }

    let layer = null;
    let currentCard = null;
    let cardTimer = 0;

    function getLayer() {
        if (!layer) {
            layer = document.createElement('div');
            layer.className = 'math-layer';
            layer.setAttribute('aria-hidden', 'true');
            document.body.appendChild(layer);
        }
        return layer;
    }

    function tileRect(row, col) {
        const board = document.getElementById('gameBoard');
        const tile = board && board.children[row * SIZE + col];
        return tile ? tile.getBoundingClientRect() : null;
    }

    function bits(value, width) {
        return (value >>> 0).toString(2).padStart(width, '0').slice(-width);
    }

    // ── point labels ────────────────────────────────────────────────────────

    function labelText(op) {
        switch (op.kind) {
            case 'gate':
                return op.result === 0 ? `${op.gate} = 0` : `+${op.points} ${op.gate}`;
            case 'same':
                return `+${op.points} SAME`;
            case 'overflow':
                return `+${op.points} OVERFLOW`;
            case 'height':
                return `+${op.points} NEW HIGH`;
            default:
                return `+${op.points}`;
        }
    }

    function showLabels(operations) {
        const stack = new Map(); // tiles with more than one label stack upward
        for (const op of operations) {
            const rect = tileRect(op.row, op.col);
            if (!rect) continue;

            const key = op.row * SIZE + op.col;
            const index = stack.get(key) || 0;
            stack.set(key, index + 1);

            const el = document.createElement('div');
            el.className = 'point-label';
            el.dataset.kind = op.kind;
            if (op.gate) el.dataset.gate = op.gate.toLowerCase();
            if (op.kind === 'gate' && op.result === 0) el.dataset.cleared = 'true';
            el.textContent = labelText(op);
            el.style.left = `${rect.left + rect.width / 2}px`;
            el.style.top = `${rect.top + rect.height * 0.35 - index * 16}px`;
            el.addEventListener('animationend', () => el.remove());
            getLayer().appendChild(el);

            // animationend never fires when animations are off (reduced
            // motion, performance mode), so the label must remove itself.
            setTimeout(() => el.remove(), 1400);
        }
    }

    // ── the math card ───────────────────────────────────────────────────────

    // One card per move, or the board disappears under them in a chain. An
    // overflow is the rarest and most worth understanding; after that the gate
    // that paid most; a gate that cleared its tiles still teaches something.
    function pickOperation(operations) {
        const overflow = operations.find((op) => op.kind === 'overflow');
        if (overflow) return overflow;
        const gates = operations.filter((op) => op.kind === 'gate');
        if (!gates.length) return null;
        return gates.reduce((best, op) => (op.points > best.points ? op : best), gates[0]);
    }

    function bitRow(symbol, value, width, role) {
        const row = document.createElement('div');
        row.className = `math-row math-row-${role}`;

        const sym = document.createElement('span');
        sym.className = 'math-symbol';
        sym.textContent = symbol;
        row.appendChild(sym);

        const text = bits(value, width);
        for (let k = 0; k < text.length; k++) {
            const bit = document.createElement('span');
            bit.className = 'math-bit';
            bit.dataset.on = text[k];
            // Result bits light left to right, like a carry chain settling.
            if (role === 'result') bit.style.animationDelay = `${120 + k * 55}ms`;
            bit.textContent = text[k];
            row.appendChild(bit);
        }
        return row;
    }

    // The overflow / new-high / level-up banner, if it is showing. game.js
    // shows it synchronously inside the move, so it is already up by the time
    // boole:operations arrives.
    function visibleBanner() {
        const el = document.getElementById('overflowNotification');
        if (!el) return null;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return null;
        const r = el.getBoundingClientRect();
        return r.width && r.height ? r : null;
    }

    function clearCard() {
        clearTimeout(cardTimer);
        if (currentCard) currentCard.remove();
        currentCard = null;
    }

    function showCard(op, width) {
        clearCard();
        const rect = tileRect(op.row, op.col);
        if (!rect) return;

        const card = document.createElement('div');
        card.className = 'math-card';
        card.dataset.gate = op.gate.toLowerCase();
        if (op.kind === 'overflow') card.dataset.overflow = 'true';

        const unary = op.b === null || op.b === undefined;
        if (unary) {
            card.appendChild(bitRow(GATE_SYMBOL[op.gate] || op.gate, op.a, width, 'operand'));
        } else {
            card.appendChild(bitRow('', op.a, width, 'operand'));
            card.appendChild(bitRow(GATE_SYMBOL[op.gate] || op.gate, op.b, width, 'operand'));
        }

        const rule = document.createElement('div');
        rule.className = 'math-rule';
        card.appendChild(rule);

        card.appendChild(bitRow('', op.result, width, 'result'));

        const caption = document.createElement('div');
        caption.className = 'math-caption';
        if (op.kind === 'overflow') {
            caption.textContent = 'overflow: every bit flips to 0';
        } else if (unary) {
            caption.textContent = `${op.gate} ${op.a} = ${op.result}`;
        } else {
            caption.textContent = `${op.a} ${op.gate} ${op.b} = ${op.result}`;
        }
        card.appendChild(caption);

        getLayer().appendChild(card);

        // Placed after insertion, since its size depends on the bit count.
        //
        // Beside the tile it produced, but never over the game's own banner.
        // A new high or an overflow also puts a banner in the middle of the
        // screen, in the same move, and the first version sat the card right
        // under it whenever the merge was in the middle rows -- hiding exactly
        // the moves most worth explaining. Tried in order: above the tile,
        // below it, then above or below the banner; the first spot that fits
        // on screen and clears the banner wins.
        const cw = card.offsetWidth;
        const ch = card.offsetHeight;
        const margin = 6;
        const gap = 8;
        let left = rect.left + rect.width / 2 - cw / 2;
        left = Math.max(margin, Math.min(left, window.innerWidth - cw - margin));

        const banner = visibleBanner();
        const candidates = [rect.top - ch - gap, rect.bottom + gap];
        if (banner) candidates.push(banner.top - ch - gap, banner.bottom + gap);

        const fits = (top) => top >= margin && top + ch <= window.innerHeight - margin;
        const clearsBanner = (top) => !banner ||
            left + cw <= banner.left || left >= banner.right ||
            top + ch <= banner.top || top >= banner.bottom;

        let top = candidates.find((t) => fits(t) && clearsBanner(t));
        if (top === undefined) top = candidates.find(fits);
        if (top === undefined) top = Math.max(margin, candidates[0]);

        card.style.left = `${left}px`;
        card.style.top = `${top}px`;

        currentCard = card;
        cardTimer = setTimeout(() => {
            card.classList.add('is-leaving');
            setTimeout(() => {
                if (currentCard === card) clearCard();
                else card.remove();
            }, 220);
        }, 1300);
    }

    // ── wiring ──────────────────────────────────────────────────────────────

    document.addEventListener('boole:operations', (e) => {
        const detail = e.detail || {};
        const operations = detail.operations || [];
        if (!operations.length) return;

        showLabels(operations);

        if (showMath) {
            const op = pickOperation(operations);
            if (op) showCard(op, detail.bits || 4);
        }
    });

    // A new game, or leaving the board, should not leave a card floating over
    // whatever comes next.
    document.addEventListener('boole:game-over', clearCard);

    function syncToggle(button) {
        button.classList.toggle('active', showMath);
        const status = button.querySelector('.toggle-status');
        if (status) status.textContent = showMath ? 'ON' : 'OFF';
    }

    document.addEventListener('DOMContentLoaded', () => {
        const toggle = document.getElementById('mathToggle');
        if (!toggle) return;
        syncToggle(toggle);
        toggle.addEventListener('click', () => {
            showMath = !showMath;
            try {
                localStorage.setItem(STORAGE_KEY, showMath ? 'on' : 'off');
            } catch (e) {}
            if (!showMath) clearCard();
            syncToggle(toggle);
        });
    });
})();
