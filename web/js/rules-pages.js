// rules-pages.js
//
// The full rules, a screenful at a time.
//
// The panel is 3,100px of dense text against a 735px window on a phone: more
// than four screens, in a modal whose scrollbar a touch device never draws.
// It did scroll, and that was the whole problem -- nothing on screen said so,
// and a player who tried and felt nothing concluded it was stuck.
//
// So it pages. The first version split at each <h4> and left it there, which
// fixed five sections and not the sixth: Gauntlet is 650px of text, still
// taller than the window, still cut off at the bottom with nothing to say so.
//
// This one measures. A section starts a page, and a section too tall for one
// runs on to the next, so no page is ever longer than the space it has. The
// measuring happens the first time the rules are opened, because a hidden
// element has no height, and again when the viewport changes, because a
// rotated iPad is a different question from a phone.
//
// The pages are built from the markup rather than written into it: every
// section is an <h4> and its siblings, so a section added to the rules is
// paginated with the rest and needs nothing here. There is no rule content in
// this file, only the decision about how much of it to show at once.

(function () {
    'use strict';

    if (typeof document === 'undefined') return;

    const PANEL = '#instructionsModal .instructions-content';

    // What a page cannot use: the sticky bar above, the title, the footer and
    // the buttons below it. Measured rather than assumed, then a little more
    // for the margins between them.
    const CHROME_SLACK = 48;

    let blocks = [];        // the rules, in order, outside the DOM until placed
    let pages = [];
    let current = 0;
    let holder = null;
    let nav = null;
    let label = null;
    let prev = null;
    let next = null;
    let laidOutFor = 0;     // the panel height the current pagination was built for

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text) node.textContent = text;
        return node;
    }

    function panelEl() {
        return document.querySelector(PANEL);
    }

    function show(index) {
        if (!pages.length) return;
        current = Math.max(0, Math.min(index, pages.length - 1));
        pages.forEach((page, i) => page.classList.toggle('is-current', i === current));
        label.textContent = `${current + 1} / ${pages.length}`;
        prev.disabled = current === 0;
        next.disabled = current === pages.length - 1;

        const panel = panelEl();
        if (panel) panel.scrollTop = 0;
    }

    /** Height including the margins, which is what stacking actually costs. */
    function outerHeight(node) {
        const style = getComputedStyle(node);
        return node.offsetHeight
            + parseFloat(style.marginTop || 0)
            + parseFloat(style.marginBottom || 0);
    }

    /**
     * Collect the rules once: every child between the title and the buttons,
     * with its height, measured while they are all still in the panel and
     * therefore visible. Dividers go: a page break is that already.
     */
    function collect(panel, heading, buttons) {
        const found = [];
        let node = heading.nextElementSibling;
        while (node && node !== buttons) {
            const nextNode = node.nextElementSibling;
            if (node.classList.contains('section-divider')) {
                node.remove();
            } else if (node === holder || node === nav) {
                // This runs after the pages holder and the footer are in the
                // panel, and they sit between the title and the buttons like
                // everything else. Collected, the holder would be paginated
                // into a page inside itself: "the new child element contains
                // the parent", from appendChild, which is the whole story.
                node = nextNode;
                continue;
            } else {
                found.push({ node, height: outerHeight(node), heading: node.tagName === 'H4' });
            }
            node = nextNode;
        }
        return found;
    }

    /**
     * A block taller than a whole page, split into parts of itself.
     *
     * Two of the rule boxes are: the maximum values box is 529px against a
     * page of about 390, and the Gauntlet box 634. Nothing above can help,
     * because a page cannot be shorter than the one thing on it -- so the box
     * is rebuilt as several boxes, each a shallow copy carrying the same
     * background, border and padding, with as many of its children as fit.
     *
     * Splitting here rather than in the markup keeps the rules one piece of
     * prose: an editor writes a box, and how many screens it takes is this
     * file's problem.
     */
    function splitTall(node, available) {
        if (outerHeight(node) <= available || node.childElementCount < 2) return [node];

        const parent = node.parentNode;
        const parts = [];
        let part = null;

        const startPart = () => {
            part = node.cloneNode(false);      // same box, no contents
            parent.insertBefore(part, node);
            parts.push(part);
        };

        startPart();
        while (node.firstElementChild) {
            const child = node.firstElementChild;
            part.appendChild(child);
            if (outerHeight(part) > available && part.childElementCount > 1) {
                startPart();
                part.appendChild(child);       // the one that did not fit
            }
        }

        node.remove();
        return parts;
    }

    function paginate(available) {
        pages = [];
        holder.textContent = '';

        let page = null;
        let used = 0;
        let heading = null;
        let pageHasHeading = false;

        const startPage = (continued) => {
            page = el('section', 'rules-page');
            holder.appendChild(page);
            pages.push(page);
            used = 0;
            pageHasHeading = false;
            // A section that runs on says so, rather than starting a page with
            // a paragraph that appears to belong to nothing.
            if (continued && heading) {
                const echo = heading.cloneNode(true);
                echo.classList.add('rules-page-continued');
                echo.textContent = `${heading.textContent} (cont.)`;
                page.appendChild(echo);
                used += outerHeight(echo);
                pageHasHeading = true;
            }
        };

        for (const block of blocks) {
            if (block.heading) heading = block.node;

            const needsPage = !page
                || (block.heading && pageHasHeading)
                || (used > 0 && used + block.height > available);

            if (needsPage) startPage(!block.heading);
            page.appendChild(block.node);
            used += block.height;
            if (block.heading) pageHasHeading = true;
        }
    }

    function layout() {
        const panel = panelEl();
        if (!panel || !panel.clientHeight) return;

        const heading = panel.querySelector('h3');
        const buttons = panel.querySelector('.modal-btn-row');
        const topbar = panel.querySelector('.instructions-topbar');
        if (!heading || !buttons) return;

        // Everything below needs real heights, and a page that is not the
        // current one is display:none. This shows them all for the duration.
        if (holder) holder.classList.add('is-measuring');

        const chrome = (topbar ? outerHeight(topbar) : 0)
            + outerHeight(heading)
            + (nav ? outerHeight(nav) : 0)
            + outerHeight(buttons)
            + CHROME_SLACK;

        // From the panel's max-height, not its current height. The panel is
        // as tall as the page inside it, so measuring it here would measure
        // the result of the last pagination and shrink a little more every
        // time this ran.
        const ceiling = parseFloat(getComputedStyle(panel).maxHeight)
            || panel.clientHeight
            || window.innerHeight;
        const available = Math.max(160, ceiling - chrome);

        if (!blocks.length) {
            blocks = collect(panel, heading, buttons);
        } else {
            for (const block of blocks) block.height = outerHeight(block.node);
        }

        // A block that cannot fit a page becomes several that can, which has
        // to happen before the pages are filled.
        const expanded = [];
        for (const block of blocks) {
            for (const node of splitTall(block.node, available)) {
                expanded.push({ node, height: outerHeight(node), heading: node.tagName === 'H4' });
            }
        }
        blocks = expanded;

        paginate(available);
        if (holder) holder.classList.remove('is-measuring');
        laidOutFor = window.innerHeight;
        show(0);
    }

    function build() {
        const panel = panelEl();
        if (!panel || holder) return false;

        const heading = panel.querySelector('h3');
        const buttons = panel.querySelector('.modal-btn-row');
        if (!heading || !buttons) return false;

        holder = el('div', 'rules-pages');
        panel.insertBefore(holder, buttons);

        nav = el('div', 'rules-nav');
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

        layout();
        return true;
    }

    // Everything here needs real heights, and a hidden panel has none, so the
    // work happens the first time the rules are opened rather than at load.
    const modal = document.getElementById('instructionsModal');
    if (modal) {
        new MutationObserver(() => {
            if (!modal.classList.contains('active')) return;
            const panel = panelEl();
            if (!holder) {
                build();
            } else if (window.innerHeight !== laidOutFor) {
                layout();          // rotated, or a resized window
            } else {
                show(0);
            }
        }).observe(modal, { attributes: true, attributeFilter: ['class'] });
    }

    let resizeTimer = 0;
    window.addEventListener('resize', () => {
        if (!holder || !modal || !modal.classList.contains('active')) return;
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(layout, 200);
    });

    // The arrow keys have nothing else to do while this is open: the board
    // behind it ignores them (game.js checks whether anything is covering it),
    // so they page instead.
    document.addEventListener('keydown', (e) => {
        if (!modal || !modal.classList.contains('active')) return;
        if (e.key === 'ArrowLeft') {
            show(current - 1);
            e.preventDefault();
        } else if (e.key === 'ArrowRight') {
            show(current + 1);
            e.preventDefault();
        }
    });

    window.BooleRules = {
        get page() {
            return current + 1;
        },
        get pages() {
            return pages.length;
        },
        show: (n) => show(n - 1),
        relayout: layout,
    };
})();
