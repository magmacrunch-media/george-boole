// codex.js
//
// The gate codex, and the discoveries.
//
// "Show the math" explains one move. The codex is what a player keeps: a card
// per gate that unlocks the first time that gate fires on their board, with
// its one-bit truth table, the rows of it they have actually used, and the
// operation that unlocked it written out in columns. Every multi-bit move is
// several one-bit truth-table rows side by side -- 0101 XOR 0011 is the rows
// 0,0 / 1,0 / 0,1 / 1,1 at once -- and the codex is where that connection is
// made visible.
//
// Discoveries are the defining property of each gate, found by playing rather
// than read: XOR a number with itself, AND two numbers with nothing in common,
// and so on. A locked one shows the challenge; an unlocked one, the lesson.
//
// It reads boole:operations from game.js and nothing else, so it cannot change
// a move. It announces boole:codex and boole:discovery for anything that
// wants them -- the App Store build reports discoveries to Game Center.
//
// detect() is pure apart from the state object it is handed, and is exported
// as BooleCodex for web/tests/test-codex.js. Everything touching the page is
// skipped when there is no document.

(function (root) {
    'use strict';

    const STORAGE_KEY = 'gb_codex';

    // Chip numbers are the 74HC series parts that do exactly one of these, four
    // to a package -- the gates a first electronics kit comes with.
    const GATES = {
        XOR: {
            symbol: '⊕',
            name: 'exclusive or',
            meaning: 'a bit is 1 when the two inputs differ',
            chip: '74HC86',
            unary: false,
            out: (a, b) => a ^ b,
        },
        OR: {
            symbol: '∨',
            name: 'or',
            meaning: 'a bit is 1 when either input is 1',
            chip: '74HC32',
            unary: false,
            out: (a, b) => a | b,
        },
        AND: {
            symbol: '∧',
            name: 'and',
            meaning: 'a bit is 1 only when both inputs are 1',
            chip: '74HC08',
            unary: false,
            out: (a, b) => a & b,
        },
        NOT: {
            symbol: '¬',
            name: 'not',
            meaning: 'every bit flips',
            chip: '74HC04',
            unary: true,
            out: (a) => 1 - a,
        },
    };

    const GATE_ORDER = ['XOR', 'OR', 'AND', 'NOT'];

    // Order is display order. `challenge` is shown while locked, `formula` and
    // `lesson` once found.
    const DISCOVERIES = [
        {
            id: 'self_inverse',
            title: 'self-inverse',
            challenge: 'XOR a number with itself',
            formula: 'a ⊕ a = 0',
            lesson: 'Every bit agrees with itself, so every bit cancels. Processors clear a register this way, and it is why XOR undoes itself.',
        },
        {
            id: 'nothing_in_common',
            title: 'nothing in common',
            challenge: 'AND two numbers that share no bits',
            formula: 'a ∧ b = 0',
            lesson: 'AND keeps only the bits both inputs have. Nothing shared, nothing kept -- which is how a mask switches bits off.',
        },
        {
            id: 'all_lit',
            title: 'all lit',
            challenge: 'OR your way to the ceiling',
            formula: 'a ∨ b = 11…1',
            lesson: 'OR can only switch bits on, never off. Cover every column between the two inputs and every bit is lit.',
        },
        {
            id: 'opposites',
            title: 'opposites',
            challenge: 'XOR a number with its opposite',
            formula: 'a ⊕ ¬a = 11…1',
            lesson: 'Two numbers that differ in every column are each other\'s NOT. They disagree everywhere, so XOR lights every bit.',
        },
        {
            id: 'wraparound',
            title: 'wraparound',
            challenge: 'overflow a tile',
            formula: '¬ 11…1 = 00…0',
            lesson: 'Every bit flips at once and nothing is left. A counter that runs out of bits wraps to zero the same way.',
        },
        {
            id: 'chain_reaction',
            title: 'chain reaction',
            challenge: 'fire two gates in one swipe',
            formula: 'out → in',
            lesson: 'A result can feed the next gate in the same move: one gate\'s output wired to another\'s input. That is all a circuit is.',
        },
        {
            id: 'full_set',
            title: 'full set',
            challenge: 'use all four gates',
            formula: '⊕ ∨ ∧ ¬',
            lesson: 'Any digital circuit, a whole processor included, can be built from AND, OR and NOT alone. You have used all of them.',
        },
    ];

    function emptyState() {
        return { gates: {}, discoveries: {} };
    }

    function maxFor(bits) {
        return Math.pow(2, bits) - 1;
    }

    // Bit `k` counting from the most significant of `width`, so columns read
    // left to right the way the tiles print them.
    function bitAt(value, k, width) {
        return (value >> (width - 1 - k)) & 1;
    }

    /**
     * Fold one move's operations into `state`. Returns what is new:
     * { gates: [names first used this move], discoveries: [ids found] }.
     *
     * `operations` are game.js's lastOperations; `bits` the mode's width at
     * the time of the move.
     */
    function detect(state, operations, bits, now) {
        const found = { gates: [], discoveries: [] };
        if (!state.gates) state.gates = {};
        if (!state.discoveries) state.discoveries = {};
        const when = now || Date.now();
        const width = Math.max(1, bits || 4);
        const max = maxFor(width);

        const discover = (id) => {
            if (state.discoveries[id]) return;
            state.discoveries[id] = when;
            found.discoveries.push(id);
        };

        const fired = (operations || []).filter(
            (op) => op && GATES[op.gate] && (op.kind === 'gate' || op.kind === 'overflow')
        );

        for (const op of fired) {
            const gate = GATES[op.gate];
            let entry = state.gates[op.gate];
            if (!entry) {
                entry = state.gates[op.gate] = {
                    at: when,
                    first: { a: op.a, b: gate.unary ? null : op.b, result: op.result, bits: width },
                    rows: {},
                };
                found.gates.push(op.gate);
            }

            // Each column of a multi-bit operation is one row of the one-bit
            // truth table.
            for (let k = 0; k < width; k++) {
                const a = bitAt(op.a, k, width);
                const key = gate.unary ? `${a}` : `${a}${bitAt(op.b, k, width)}`;
                entry.rows[key] = (entry.rows[key] || 0) + 1;
            }

            if (op.kind === 'overflow') discover('wraparound');
            if (op.kind !== 'gate') continue;

            if (op.gate === 'XOR' && op.a === op.b) discover('self_inverse');
            if (op.gate === 'AND' && op.result === 0 && op.a !== op.b) discover('nothing_in_common');
            // Not when an input was already all ones: 15 OR 3 is 15 without
            // combining anything, and the lesson is that OR fills the columns.
            if (op.gate === 'OR' && op.result === max && op.a !== max && op.b !== max) discover('all_lit');
            if (op.gate === 'XOR' && op.result === max && op.a !== 0 && op.b !== 0) discover('opposites');
        }

        if (fired.length >= 2) discover('chain_reaction');
        if (GATE_ORDER.every((g) => state.gates[g])) discover('full_set');

        return found;
    }

    root.BooleCodex = { GATES, GATE_ORDER, DISCOVERIES, detect, emptyState, maxFor };

    if (typeof document === 'undefined' || typeof document.createElement !== 'function') return;

    // ── page ────────────────────────────────────────────────────────────────

    let state = emptyState();
    try {
        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
        if (saved && typeof saved === 'object') state = Object.assign(emptyState(), saved);
    } catch (e) {
        // Unreadable or unavailable: start empty.
    }

    function save() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
            // Storage full or disabled; the codex just will not outlive the page.
        }
    }

    const el = (tag, className, text) => {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    };

    // ── toasts ──────────────────────────────────────────────────────────────

    const toastQueue = [];
    let toastBusy = false;

    function toast(kicker, title, gate) {
        toastQueue.push({ kicker, title, gate });
        if (!toastBusy) nextToast();
    }

    function nextToast() {
        const item = toastQueue.shift();
        if (!item) {
            toastBusy = false;
            return;
        }
        toastBusy = true;
        const node = el('div', 'codex-toast');
        if (item.gate) node.dataset.gate = item.gate.toLowerCase();
        node.setAttribute('role', 'status');
        node.appendChild(el('span', 'codex-toast-kicker', item.kicker));
        node.appendChild(el('span', 'codex-toast-title', item.title));
        document.body.appendChild(node);
        setTimeout(() => {
            node.classList.add('is-leaving');
            setTimeout(() => {
                node.remove();
                nextToast();
            }, 250);
        }, 2400);
    }

    // ── the modal ───────────────────────────────────────────────────────────

    let modal = null;
    let body = null;

    function bitsRow(symbol, value, width, role) {
        const row = el('div', `codex-bits-row codex-bits-${role}`);
        row.appendChild(el('span', 'codex-bits-symbol', symbol));
        const text = (value >>> 0).toString(2).padStart(width, '0').slice(-width);
        for (const ch of text) {
            const bit = el('span', 'codex-bit', ch);
            bit.dataset.on = ch;
            row.appendChild(bit);
        }
        return row;
    }

    function gateCard(name) {
        const gate = GATES[name];
        const entry = state.gates[name];
        const card = el('section', 'codex-card');
        card.dataset.gate = name.toLowerCase();
        card.id = `codex-${name.toLowerCase()}`;

        const head = el('div', 'codex-card-head');
        head.appendChild(el('span', 'codex-symbol', gate.symbol));
        const titles = el('div', 'codex-card-titles');
        titles.appendChild(el('h4', 'codex-card-name', name));
        titles.appendChild(el('span', 'codex-card-sub', entry ? `${gate.name} · ${gate.chip}` : 'locked'));
        head.appendChild(titles);
        card.appendChild(head);

        if (!entry) {
            card.classList.add('is-locked');
            card.appendChild(el('p', 'codex-hint', gate.unary
                ? 'slide a ¬ into a tile to unlock'
                : `fire ${name} between two numbers to unlock`));
            return card;
        }

        card.appendChild(el('p', 'codex-meaning', gate.meaning));

        // The one-bit truth table, with the rows this player has used lit and
        // counted.
        const table = el('div', 'codex-table');
        const header = el('div', 'codex-table-row codex-table-head');
        (gate.unary ? ['A', 'OUT'] : ['A', 'B', 'OUT']).forEach((h) => header.appendChild(el('span', '', h)));
        table.appendChild(header);
        const inputs = gate.unary ? [[0], [1]] : [[0, 0], [0, 1], [1, 0], [1, 1]];
        for (const ins of inputs) {
            const count = entry.rows[ins.join('')] || 0;
            const row = el('div', 'codex-table-row');
            if (count) row.classList.add('is-seen');
            ins.forEach((v) => row.appendChild(el('span', '', String(v))));
            row.appendChild(el('span', 'codex-out', String(gate.out(ins[0], ins[1]))));
            row.appendChild(el('span', 'codex-count', count ? `×${count}` : ''));
            table.appendChild(row);
        }
        card.appendChild(table);

        // The move that unlocked it, in columns.
        const first = entry.first;
        const width = first.bits || 4;
        const worked = el('div', 'codex-first');
        worked.appendChild(el('span', 'codex-first-label', `your first ${name}`));
        if (gate.unary) {
            worked.appendChild(bitsRow(gate.symbol, first.a, width, 'operand'));
        } else {
            worked.appendChild(bitsRow('', first.a, width, 'operand'));
            worked.appendChild(bitsRow(gate.symbol, first.b, width, 'operand'));
        }
        worked.appendChild(el('div', 'codex-bits-rule'));
        worked.appendChild(bitsRow('', first.result, width, 'result'));
        worked.appendChild(el('span', 'codex-first-caption', gate.unary
            ? `${name} ${first.a} = ${first.result}`
            : `${first.a} ${name} ${first.b} = ${first.result}`));
        card.appendChild(worked);

        return card;
    }

    function discoveryItem(d) {
        const found = state.discoveries[d.id];
        const item = el('li', 'codex-discovery');
        if (!found) item.classList.add('is-locked');
        const head = el('div', 'codex-discovery-head');
        head.appendChild(el('span', 'codex-discovery-mark', found ? '✓' : '?'));
        head.appendChild(el('span', 'codex-discovery-title', d.title));
        if (found) head.appendChild(el('span', 'codex-discovery-formula', d.formula));
        item.appendChild(head);
        item.appendChild(el('p', 'codex-discovery-text', found ? d.lesson : d.challenge));
        return item;
    }

    function render() {
        if (!body) return;
        body.textContent = '';
        const gatesFound = GATE_ORDER.filter((g) => state.gates[g]).length;
        const discFound = DISCOVERIES.filter((d) => state.discoveries[d.id]).length;
        body.appendChild(el('p', 'codex-progress',
            `${gatesFound} of 4 gates · ${discFound} of ${DISCOVERIES.length} discoveries`));

        const cards = el('div', 'codex-cards');
        GATE_ORDER.forEach((g) => cards.appendChild(gateCard(g)));
        body.appendChild(cards);

        body.appendChild(el('h4', 'codex-section-title', 'discoveries'));
        const list = el('ul', 'codex-discoveries');
        DISCOVERIES.forEach((d) => list.appendChild(discoveryItem(d)));
        body.appendChild(list);
    }

    function build() {
        modal = el('div', 'codex-modal');
        modal.id = 'codexModal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-label', 'gate codex');

        const panel = el('div', 'codex-content');
        const bar = el('div', 'codex-topbar');
        const back = el('button', 'codex-back', '← back');
        back.type = 'button';
        back.id = 'codexBack';
        back.addEventListener('click', close);
        bar.appendChild(back);
        bar.appendChild(el('h3', 'codex-title', 'gate codex'));
        panel.appendChild(bar);

        body = el('div', 'codex-body');
        panel.appendChild(body);
        modal.appendChild(panel);

        modal.addEventListener('click', (e) => {
            if (e.target === modal) close();
        });
        document.body.appendChild(modal);
    }

    function open(gateName) {
        if (!modal) build();
        render();
        modal.classList.add('active');
        const panel = modal.querySelector('.codex-content');
        panel.scrollTop = 0;
        if (gateName) {
            const card = document.getElementById(`codex-${String(gateName).toLowerCase()}`);
            if (card) panel.scrollTop = card.offsetTop - 60;
        }
    }

    // Every way out goes through here -- the back button, the backdrop and
    // Escape -- so whoever opened the codex is told once, however it closed.
    // main.js uses it to put the settings modal back, since opening settings
    // from the rules screen hides that screen: without this, closing the codex
    // left an empty board behind it.
    function close() {
        if (!modal || !modal.classList.contains('active')) return;
        modal.classList.remove('active');
        document.dispatchEvent(new CustomEvent('boole:codex-closed'));
    }

    function isOpen() {
        return !!(modal && modal.classList.contains('active'));
    }

    // ── wiring ──────────────────────────────────────────────────────────────

    document.addEventListener('boole:operations', (e) => {
        const detail = e.detail || {};
        const found = detect(state, detail.operations, detail.bits);
        if (!(detail.operations || []).some((op) => op && GATES[op.gate])) return;
        save();

        for (const name of found.gates) {
            toast('added to codex', `${GATES[name].symbol} ${name}`, name);
            document.dispatchEvent(new CustomEvent('boole:codex', { detail: { gate: name } }));
        }
        for (const id of found.discoveries) {
            const d = DISCOVERIES.find((x) => x.id === id);
            toast('discovery', d.title);
            document.dispatchEvent(new CustomEvent('boole:discovery', { detail: { id } }));
        }
        if (isOpen()) render();
    });

    // While the codex is open, keys belong to it: an arrow would otherwise move
    // the board hidden behind it, and space would advance the screen below.
    document.addEventListener('keydown', (e) => {
        if (!isOpen()) return;
        if (e.key === 'Escape') {
            close();
            e.preventDefault();
        }
        if (e.key === ' ' || e.key.startsWith('Arrow')) {
            e.stopImmediatePropagation();
            if (e.key === ' ') e.preventDefault();
        }
    }, true);

    document.addEventListener('DOMContentLoaded', () => {
        const openFrom = (node, gate) => {
            if (!node) return;
            node.classList.add('codex-opener');
            node.setAttribute('role', 'button');
            node.setAttribute('tabindex', '0');
            node.addEventListener('click', () => open(gate));
            node.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') open(gate);
            });
        };

        openFrom(document.getElementById('loreCodex'));
        openFrom(document.getElementById('sidePanelCodex'));
        // The strip under the board, which is the only one of these a phone
        // shows: the gate symbols there open the codex too, but a tap target
        // whose only affordance is a hover tint announces nothing on touch.
        openFrom(document.getElementById('stripCodexLink'));
        document.querySelectorAll('.gate-tag[data-gate], .gate-ref[data-gate]').forEach((node) => {
            openFrom(node, node.dataset.gate.toUpperCase());
        });
    });

    root.BooleCodex.open = open;
    root.BooleCodex.close = close;
    root.BooleCodex.state = () => state;
})(typeof window !== 'undefined' ? window : globalThis);
