// rules-pages.js
//
// The full rules, one section at a time.
//
// The panel is 3,100px of dense text against a 735px window on a phone: more
// than four screens, in a modal whose scrollbar a touch device never draws.
// It does scroll, and that was the whole problem -- nothing on screen said so,
// and a player who tried and felt nothing concluded it was stuck.
//
// So it pages instead. Each of the six sections the rules already have becomes
// a page with a footer that says which one you are on, and the panel keeps its
// max-height and overflow, which now only matter for the rare page that is
// still taller than a small screen.
//
// The pages are built from the markup rather than written into it: every
// section is an <h4> and its siblings, so a section added to the rules becomes
// a page without touching this file. There is no rule content here, only the
// decision about how much of it to show at once.

(function () {
    'use strict';

    if (typeof document === 'undefined') return;

    const PANEL = '#instructionsModal .instructions-content';

    let pages = [];
    let current = 0;
    let label = null;
    let prev = null;
    let next = null;

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text) node.textContent = text;
        return node;
    }

    function show(index) {
        if (!pages.length) return;
        current = Math.max(0, Math.min(index, pages.length - 1));
        pages.forEach((page, i) => page.classList.toggle('is-current', i === current));
        label.textContent = `${current + 1} / ${pages.length}`;
        prev.disabled = current === 0;
        next.disabled = current === pages.length - 1;

        // A new page starts at its own beginning, not wherever the last one
        // was left.
        const panel = document.querySelector(PANEL);
        if (panel) panel.scrollTop = 0;
    }

    function build() {
        const panel = document.querySelector(PANEL);
        if (!panel || panel.querySelector('.rules-page')) return;

        const heading = panel.querySelector('h3');
        const buttons = panel.querySelector('.modal-btn-row');
        if (!heading || !buttons) return;

        // Everything between the title and the buttons is rules.
        const body = [];
        for (let node = heading.nextElementSibling; node && node !== buttons; node = node.nextElementSibling) {
            body.push(node);
        }
        if (!body.length) return;

        // Split at each <h4>. Whatever precedes the first one is the
        // opening paragraph, and it joins that first section rather than
        // becoming a page of its own: on its own it is 95px of text under a
        // footer saying 1 of 7, which reads as a page that failed to load.
        const groups = [];
        let pageHasHeading = false;
        for (const node of body) {
            // A divider marks the break between sections, and a page break
            // is that already. Removed rather than skipped: skipping leaves
            // it where it was, which is above the pages, so all six stack up
            // as a band of stray lines under the title.
            if (node.classList.contains('section-divider')) {
                node.remove();
                continue;
            }

            if (node.tagName === 'H4') {
                // A heading starts a page, unless the page it would start is
                // the opening paragraph, which belongs with the first one.
                if (groups.length && pageHasHeading) groups.push([]);
                pageHasHeading = true;
            }
            if (!groups.length) groups.push([]);
            groups[groups.length - 1].push(node);
        }

        const filled = groups.filter((group) => group.length);
        if (filled.length < 2) return;   // nothing to page through

        const holder = el('div', 'rules-pages');
        for (const group of filled) {
            const page = el('section', 'rules-page');
            group.forEach((node) => page.appendChild(node));
            holder.appendChild(page);
            pages.push(page);
        }
        panel.insertBefore(holder, buttons);

        const nav = el('div', 'rules-nav');
        prev = el('button', 'rules-nav-btn', '← back');
        prev.type = 'button';
        label = el('span', 'rules-nav-count');
        next = el('button', 'rules-nav-btn', 'next →');
        next.type = 'button';
        prev.addEventListener('click', () => show(current - 1));
        next.addEventListener('click', () => show(current + 1));
        nav.appendChild(prev);
        nav.appendChild(label);
        nav.appendChild(next);
        panel.insertBefore(nav, buttons);

        // Opening the rules starts at the first page, however they were left.
        const modal = document.getElementById('instructionsModal');
        if (modal) {
            new MutationObserver(() => {
                if (modal.classList.contains('active')) show(0);
            }).observe(modal, { attributes: true, attributeFilter: ['class'] });
        }

        show(0);
    }

    // The arrow keys have nothing else to do while this is open: the board
    // behind it ignores them (game.js checks whether anything is covering it),
    // so they page instead.
    document.addEventListener('keydown', (e) => {
        const modal = document.getElementById('instructionsModal');
        if (!modal || !modal.classList.contains('active')) return;
        if (e.key === 'ArrowLeft') {
            show(current - 1);
            e.preventDefault();
        } else if (e.key === 'ArrowRight') {
            show(current + 1);
            e.preventDefault();
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', build);
    } else {
        build();
    }

    window.BooleRules = {
        get page() {
            return current + 1;
        },
        get pages() {
            return pages.length;
        },
        show: (n) => show(n - 1),
    };
})();
