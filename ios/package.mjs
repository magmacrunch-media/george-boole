#!/usr/bin/env node
/**
 * Build the App Store bundle from `web/`.
 *
 * `web/` is the browser version and the source of truth for rules, balance and
 * presentation. It is *not* the app: it is written to be served from the
 * arcade at magmacrunch.com, so it reaches out of its own folder for shared
 * scripts, pulls a font off Google's CDN, and carries a chat widget. All three
 * are correct there and wrong in a bundle. This script is the difference
 * between the two, written down once instead of remembered.
 *
 *     node ios/package.mjs
 *
 * Output is `ios/www/`, which is generated and gitignored — Capacitor's
 * webDir. Never edit it; edit `web/` and rebuild.
 *
 * ## Why a derivation rather than a second copy of the game
 *
 * The repo's rule is that a gameplay change is not done until every version
 * has it. A hand-maintained iOS copy of `web/` would make that four versions
 * to keep in step, and the fourth would drift silently because nothing checks
 * it. Deriving means the app inherits `web/` for free and the rule still reads
 * three.
 *
 * ## The guard is the point
 *
 * Every transform below asserts that it actually changed something, and the
 * final sweep fails on any surviving `../` path or off-device asset. So the
 * failure mode this script exists to prevent — the site gains a widget one day
 * and it quietly ships to the App Store — is a build error, not a discovery
 * made during review. A transform that silently matches nothing is the same
 * bug wearing a different hat, which is why a no-op is also fatal.
 */

import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const IOS = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(IOS, '..');
const WEB = join(REPO, 'web');
const OUT = join(IOS, 'www');

/**
 * Files in `web/` that exist for developing the browser version and have no
 * business in a shipped bundle. Tests especially: they are dead weight, and
 * `performance-test.html` is a second HTML entry point a reviewer could reach.
 */
const EXCLUDE = new Set([
  'tests',
  'performance-test.html',
  'PERFORMANCE_TESTING_GUIDE.md',
  'SOUND_EFFECTS_GUIDE.md',
  'README.md',
  'title-card.html',
  'audio/README.txt',
]);

/**
 * Every `../shared/` file `web/index.html` is allowed to name, and what to do
 * with it. An unlisted one stops the build.
 *
 * This allowlist is the whole safety mechanism. The arcade's shared folder is
 * maintained in the website repo by people who are not thinking about the App
 * Store, and a page that gains a script there gains it here on the next sync.
 * Defaulting to "vendor whatever we find" would carry that into the bundle
 * unread; defaulting to "drop what we don't know" would silently break the
 * game. Refusing to guess is the only option that cannot ship a surprise.
 */
const SHARED = {
  'arcade-base.css': 'vendor',
  'adenosine-score-client.js': 'vendor',
  'adenosine-audio.js': 'vendor',
  'adenosine-puzzle.js': 'vendor',

  // Resolves a WebSocket host for the leaderboard, defaulting to port 8781 on
  // the Raspberry Pi behind magmacrunch.duckdns.org. In a bundle the hostname
  // is Capacitor's own, so `auto()` would dial localhost:8781 and retry
  // forever. Game Center replaces the whole backend; see the bootstrap
  // rewrite below, which drops this and leaves ScoreClient unconnected.
  'score-server.js': 'drop',

  // User-generated content. Shipping it means App Store Review Guideline 1.2:
  // a EULA, content filtering, a report mechanism, a block mechanism and
  // published contact details, plus the age rating that follows. The website
  // keeps all three of these; the app does not.
  'chat-widget.css': 'drop',
  'adenosine-chat.js': 'drop',
  'chat-server.js': 'drop',
};

const FONTS = ['PressStart2P-Regular.woff2', 'PressStart2P-Regular.ttf'];

/**
 * Files from `ios/shim/`, copied to `www/shim/` and loaded in this order
 * immediately after the ScoreClient bootstrap.
 *
 * A shim is the app-only half of something the site has no use for. It goes
 * here rather than in `web/` for the same reason `css/ios.css` does: the
 * browser version should not carry code about a store it will never be in.
 */
const SHIMS = ['gamekit-scores.js'];

function die(msg, detail) {
  console.error(`\npackage.mjs: ${msg}`);
  if (detail) console.error(detail);
  process.exit(1);
}

/**
 * Find a website checkout, the same way everything else here resolves a
 * sibling repo: the documented flat layout first, then the grouped tree, with
 * an env override for anywhere else. Mirrors the Wii Makefile's MAGNOLIA and
 * sync-game.mjs's GAME_SRC.
 */
function findWebsite() {
  const roots = [];
  if (process.env.WEBSITE) roots.push(resolve(process.env.WEBSITE));
  roots.push(resolve(REPO, '..', 'website'));
  roots.push(resolve(REPO, '..', '..', 'web', 'website'));
  const found = roots.find((r) => existsSync(join(r, 'arcade', 'shared', 'adenosine-puzzle.js')));
  if (!found) {
    die(
      'no website checkout found.',
      `The shared arcade scripts and the self-hosted font live there, not in this repo.\nLooked in:\n${roots.map((r) => `  ${r}`).join('\n')}\nSet WEBSITE=<path to the magmacrunch.com checkout> to look elsewhere.`
    );
  }
  return found;
}

/** Apply one named edit, and fail if it changed nothing. */
function edit(state, name, fn) {
  const next = fn(state.html);
  if (next === state.html) {
    die(
      `the "${name}" step matched nothing.`,
      'web/index.html no longer looks the way this script expects. That is not\nnecessarily a problem with the page -- but it means the bundle would be\nbuilt on an assumption that has stopped being true, so it stops here.'
    );
  }
  state.html = next;
  state.applied.push(name);
}

const website = findWebsite();
const shared = join(website, 'arcade', 'shared');
const siteFonts = join(website, 'fonts');

// ── copy web/ ────────────────────────────────────────────────────────────────

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
cpSync(WEB, OUT, {
  recursive: true,
  filter: (src) => {
    const rel = relative(WEB, src).split('\\').join('/');
    return rel === '' || !EXCLUDE.has(rel);
  },
});

const indexPath = join(OUT, 'index.html');
const state = { html: readFileSync(indexPath, 'utf8'), applied: [] };

// ── what the page asks for, checked against the allowlist ────────────────────

const asked = [...state.html.matchAll(/\.\.\/shared\/([A-Za-z0-9._-]+)/g)].map((m) => m[1]);
const unknown = [...new Set(asked)].filter((f) => !(f in SHARED));
if (unknown.length) {
  die(
    `web/index.html names ${unknown.length} shared file(s) this script does not know about:`,
    `${unknown.map((f) => `  ../shared/${f}`).join('\n')}\n\nDecide what each one is and add it to SHARED as 'vendor' or 'drop'.\nRefusing to guess: vendoring an unread script could ship anything the\narcade picked up, and dropping it silently could break the game.`
  );
}

// ── transforms ───────────────────────────────────────────────────────────────

const dropped = Object.keys(SHARED).filter((f) => SHARED[f] === 'drop');

edit(state, 'drop chat and score-server tags', (html) =>
  html
    .split('\n')
    .filter((line) => !dropped.some((f) => line.includes(`../shared/${f}`)))
    .filter((line) => !/<script>[^<]*ChatWidget[^<]*<\/script>/.test(line))
    .join('\n')
);

edit(state, 'unconnect ScoreClient', (html) =>
  html.replace(
    /new AdScore\.ScoreClient\(\)\.auto\(MC_SCORE_OPTS\)/,
    'new AdScore.ScoreClient() /* offline: localStorage only until GameKit lands */'
  )
);

edit(state, 'load the app-only shims', (html) =>
  html.replace(
    /(<script>const scoreClient = new AdScore\.ScoreClient\(\)[^<]*<\/script>)/,
    (_, bootstrap) =>
      `${bootstrap}\n` + SHIMS.map((f) => `<script src="shim/${f}"></script>`).join('\n')
  )
);

edit(state, 'remove the arcade cross-promo', (html) =>
  html.replace(/[ \t]*<p[^>]*>\s*As a warm up, play[\s\S]*?<\/p>\r?\n/, '')
);

edit(state, 'remove the arcade back-link', (html) =>
  html.replace(/[ \t]*<a href="\.\.\/puzzles\/"[^>]*>.*?<\/a>\r?\n/, '')
);

edit(state, 'self-host the font', (html) =>
  html
    .replace(/[ \t]*<link rel="preconnect" href="https:\/\/fonts\.(googleapis|gstatic)\.com"[^>]*>\r?\n/g, '')
    .replace(
      /[ \t]*<link href="https:\/\/fonts\.googleapis\.com\/css2\?family=Press\+Start\+2P[^"]*" rel="stylesheet">/,
      [
        '    <style>',
        "        @font-face {",
        "            font-family: 'Press Start 2P';",
        "            src: url('fonts/PressStart2P-Regular.woff2') format('woff2'),",
        "                 url('fonts/PressStart2P-Regular.ttf') format('truetype');",
        '            font-display: block;',
        '        }',
        '    </style>',
      ].join('\n')
    )
);

edit(state, 'point shared assets at the bundle', (html) => html.replace(/\.\.\/shared\//g, 'shared/'));

edit(state, 'strip cache-buster stamps', (html) => html.replace(/\?v=[0-9a-f]{8}/g, ''));

edit(state, 'let the viewport reach the notch', (html) =>
  html.replace(
    /(<meta name="viewport" content="[^"]*?)(">)/,
    (_, head, tail) => (head.includes('viewport-fit') ? _ : `${head}, viewport-fit=cover${tail}`)
  )
);

edit(state, 'open outbound links in the system browser', (html) =>
  html.replace(/<a href="(https?:\/\/[^"]+)"/g, '<a href="$1" target="_blank" rel="noopener"')
);

edit(state, 'let Safari run it like an app', (html) =>
  html.replace(
    /(<meta name="viewport"[^>]*>)/,
    `$1\n    <meta name="apple-mobile-web-app-capable" content="yes">\n` +
      `    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`
  )
);

edit(state, 'add the iOS stylesheet', (html) =>
  html.replace(/(\r?\n)<\/head>/, '$1    <link rel="stylesheet" href="css/ios.css">$1</head>')
);

writeFileSync(indexPath, state.html);

// ── vendor what the page still needs ─────────────────────────────────────────

mkdirSync(join(OUT, 'shared'), { recursive: true });
const vendored = Object.keys(SHARED).filter((f) => SHARED[f] === 'vendor');
for (const f of vendored) {
  const src = join(shared, f);
  if (!existsSync(src)) die(`shared asset missing from the website checkout: ${src}`);
  cpSync(src, join(OUT, 'shared', f));
}

// The app's icon is the gates, not the site's Boole-in-sunglasses. Overwrites
// the one copied from web/ so that adding the bundle to an iPhone home screen
// -- the only way to test any of this without a Mac -- shows the right picture.
// Generated by tools/make-art.py; regenerate there if the icon changes.
const touchIcon = join(IOS, 'assets', 'apple-touch-icon.png');
if (!existsSync(touchIcon)) die(`apple-touch-icon missing: ${touchIcon}`, 'Run: python ios/tools/make-art.py');
cpSync(touchIcon, join(OUT, 'apple-touch-icon.png'));

mkdirSync(join(OUT, 'shim'), { recursive: true });
for (const f of SHIMS) {
  const src = join(IOS, 'shim', f);
  if (!existsSync(src)) die(`shim missing: ${src}`);
  cpSync(src, join(OUT, 'shim', f));
}

mkdirSync(join(OUT, 'fonts'), { recursive: true });
for (const f of FONTS) {
  const src = join(siteFonts, f);
  if (!existsSync(src)) die(`font missing from the website checkout: ${src}`);
  cpSync(src, join(OUT, 'fonts', f));
}

writeFileSync(
  join(OUT, 'css', 'ios.css'),
  `/* Generated by ios/package.mjs -- edit the script, not this file.
 *
 * Everything the browser version has no reason to carry. Kept out of web/css/
 * so the site is never asked to reason about a home indicator.
 */

:root {
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-right: env(safe-area-inset-right, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
    --safe-left: env(safe-area-inset-left, 0px);
}

body {
    padding:
        var(--safe-top) var(--safe-right)
        var(--safe-bottom) var(--safe-left);
    /* A bundle has nowhere to scroll to, and rubber-banding the whole page
       under a fixed board reads as a bug rather than as elasticity. */
    overscroll-behavior: none;
}

/* The board already sets these; everything else in the app wants them too, or
   a mistimed second tap zooms the page and a long press offers to copy a tile. */
* {
    -webkit-touch-callout: none;
    -webkit-tap-highlight-color: transparent;
}

button,
[role="button"],
.modal,
.overlay {
    -webkit-user-select: none;
    user-select: none;
}
`
);

// ── the sweep ────────────────────────────────────────────────────────────────

const TEXT = /\.(html|css|js|mjs|json|txt|md)$/i;
const offences = [];

function sweep(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) {
      sweep(p);
      continue;
    }
    if (!TEXT.test(name)) continue;
    const rel = relative(OUT, p).split('\\').join('/');
    readFileSync(p, 'utf8')
      .split('\n')
      .forEach((line, i) => {
        if (/(?:src|href)\s*=\s*["']\.\.\//.test(line)) {
          offences.push(`${rel}:${i + 1}  reaches outside the bundle: ${line.trim()}`);
        }
        if (/<(?:script|link|img|source|video|audio)\b[^>]*(?:src|href)\s*=\s*["']https?:/i.test(line)) {
          offences.push(`${rel}:${i + 1}  loads an asset over the network: ${line.trim()}`);
        }
      });
  }
}
sweep(OUT);

if (offences.length) {
  die(
    `the bundle is not self-contained (${offences.length} problem(s)):`,
    `${offences.map((o) => `  ${o}`).join('\n')}\n\nAn App Store build has to run with the network off -- Guideline 4.2 treats a\npage that needs a server to be useful as a web page in a wrapper. Vendor the\nasset in this script, or remove the reference in web/.`
  );
}

// ── report ───────────────────────────────────────────────────────────────────

console.log(`ios/www/ built from web/`);
console.log(`  website checkout   ${website}`);
console.log(`  transforms         ${state.applied.length}`);
for (const t of state.applied) console.log(`      - ${t}`);
console.log(`  vendored           ${vendored.join(', ')}`);
console.log(`  dropped            ${dropped.join(', ')}`);
console.log(`  fonts              ${FONTS.join(', ')}`);
console.log(`  shims              ${SHIMS.join(', ')}`);
console.log(`  self-contained     yes (no ../ paths, no network assets)`);
console.log(`\nLeaderboard is localStorage-only. GameKit is not wired yet -- see ios/AGENTS.md.`);
