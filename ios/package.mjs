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

import { cpSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const IOS = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(IOS, '..');

// The shared half of this script lives in engines/hypnopompia, resolved by path
// the way the Wii Makefiles resolve magnolia: $HYPNOPOMPIA, then ../hypnopompia,
// then ../../engines/hypnopompia. There is no npm package and no junction for
// games/, so this is the lookup, and it fails by name rather than by a module
// error three frames deep.
const SHELL = [
  process.env.HYPNOPOMPIA && resolve(process.env.HYPNOPOMPIA),
  resolve(REPO, '..', 'hypnopompia'),
  resolve(REPO, '..', '..', 'engines', 'hypnopompia'),
].filter(Boolean).find((r) => existsSync(join(r, 'pipeline', 'index.mjs')));

if (!SHELL) {
  console.error('\npackage.mjs: no hypnopompia checkout found.');
  console.error(
    'The shared bundle pipeline lives there. Looked for pipeline/index.mjs under\n'
    + '  $HYPNOPOMPIA, ../hypnopompia, ../../engines/hypnopompia\n'
    + 'Set HYPNOPOMPIA=<path to the hypnopompia checkout> to look elsewhere.'
  );
  process.exit(1);
}

const { createBuild, transforms } = await import(
  pathToFileURL(join(SHELL, 'pipeline', 'index.mjs')).href
);

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
const SHIMS = ['gamekit-scores.js', 'gamekit-achievements.js', 'haptics.js', 'personal-bests.js'];

// `adenosine-puzzle.js` is this game's engine, and probing for it rather than
// for any shared file is what stops a website checkout that cannot build this
// game from being accepted as one that can.
const build = createBuild({ ios: IOS, probe: 'adenosine-puzzle.js' });
const { OUT, die, edit, editFile } = build;
const website = build.website;

// ── copy web/ ────────────────────────────────────────────────────────────────

const oggDropped = build.copyWeb({ exclude: EXCLUDE, drop: (rel) => rel.endsWith('.ogg') });

// Same reasoning as the no-op transforms below: if this stops matching, the
// bundle silently regains a couple of megabytes of undecodable audio and the
// build still says it succeeded.
if (!oggDropped) {
  die(
    'no .ogg files were dropped from the bundle.',
    'web/audio/ is supposed to carry both .ogg and .mp3 for every clip, and the\niOS bundle only ever plays the .mp3. Finding none means the audio layout\nchanged -- check that the .mp3 files are still there before assuming this\nstep is simply obsolete.'
  );
}

// Removing the files is only half of it: main.js still ASKS for them, from a
// canPlayType() test that is false on WebKit and true almost everywhere else.
// So the bundle worked on a phone and 404'd in any other browser, where the
// failed decode takes AdAudio.init down and the loading screen never lifts.
// That breaks the one way this bundle can be tested without a Mac, and it
// breaks it in the direction that looks like the audio work being wrong.
//
// Pinning the extension rather than keeping the probe: a bundle that ships no
// .ogg has no business testing for an .ogg decoder.
editFile('js/main.js', 'pin the audio extension to mp3', (js) =>
  js.replace(
    /const AUDIO_EXT = document\.createElement\('audio'\)\r?\n?\s*\.canPlayType\([^)]*\) \? '\.ogg' : '\.mp3';/,
    "const AUDIO_EXT = '.mp3'; // ios/package.mjs: this bundle ships no .ogg"
  )
);

const state = build.openPage();

// ── what the page asks for, checked against the allowlist ────────────────

build.checkAllowlist(state, SHARED);

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
    'new AdScore.ScoreClient() /* never connected: bests are local, the rest is Game Center */'
  )
);

transforms.loadShims(build, state, SHIMS);

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

transforms.pointSharedAssets(build, state);

transforms.stripStamps(build, state);

transforms.viewportNotch(build, state);

// The credits, in the app only. The site's line is "last updated: <date>",
// which answers nothing useful about an installed app; store/metadata.md
// points support at magmacrunch.com/support/george-boole/, and the first thing
// anybody is asked for there is the version they are running. The two URLs are
// the ones on file with App Store Connect -- one page per app, since a second
// app's policy is its own -- so a reviewer looking for the privacy policy
// inside the app finds it rather than taking our word for it.
//
// This step runs BEFORE the outbound-links one below, so these two links get
// target="_blank" from that rule rather than carrying their own copy of it.
//
// The version is read from project.pbxproj rather than retyped: a version in
// two places is a version that disagrees with itself the first time somebody
// bumps one. Both build configurations must agree, or the number shown would
// depend on which one was built.
function appVersion() {
  const pbx = join(IOS, 'App', 'App', 'App.xcodeproj', 'project.pbxproj');
  if (!existsSync(pbx)) die(`the Xcode project is missing: ${pbx}`);
  const text = readFileSync(pbx, 'utf8');
  const read = (key) => {
    const found = [...text.matchAll(new RegExp(`${key} = ([^;]+);`, 'g'))].map((m) => m[1].trim());
    if (found.length === 0) die(`${key} is not set in project.pbxproj`);
    if (new Set(found).size > 1) {
      die(
        `${key} differs between build configurations: ${[...new Set(found)].join(', ')}`,
        'The credits would then show whichever configuration happened to be built.'
      );
    }
    return found[0];
  };
  return { marketing: read('MARKETING_VERSION'), build: read('CURRENT_PROJECT_VERSION') };
}

const version = appVersion();

edit(state, 'credits: the app version and the store URLs', (html) =>
  html.replace(
    /<p><strong>last updated:<\/strong><br>[^<]*<\/p>/,
    [
      `<p><strong>version:</strong><br>${version.marketing} (build ${version.build})</p>`,
      '',
      // One line rather than two bullets: this panel fits a phone screen
      // exactly, and it is the last thing on it.
      '            <p><strong>privacy &amp; support:</strong><br>',
      '            <a href="https://magmacrunch.com/privacy/george-boole/">privacy policy</a>'
        + ' · <a href="https://magmacrunch.com/support/george-boole/">support</a></p>',
    ].join('\n')
  )
);

// The title screen's mark links to magmacrunch.com on the website, and must
// not in the app. An outbound link on the first screen is a front door
// pointing somewhere else, which is the reading of guideline 4.2 this bundle
// spends the rest of its transforms arguing against; the credits carry the
// links, where somebody has gone looking for them.
edit(state, 'unlink the title screen publisher mark', (html) =>
  html.replace(
    /<a class="title-publisher-link"[^>]*>([\s\S]*?)<\/a>/,
    (_, inner) => inner.trim()
  )
);

transforms.outboundLinks(build, state);

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

build.writePage(state);

// ── vendor what the page still needs ─────────────────────────────────────────

const vendored = build.vendorShared(SHARED);
build.copyShims(SHIMS);
build.copyFonts(FONTS);

// Generated by tools/make-boole-pixel.py; regenerate there if the icon changes.
const touchIcon = join(IOS, 'assets', 'apple-touch-icon.png');
if (!existsSync(touchIcon)) die(`apple-touch-icon missing: ${touchIcon}`, 'Run: python ios/tools/make-boole-pixel.py');
cpSync(touchIcon, join(OUT, 'apple-touch-icon.png'));

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

/* Padding the body reaches .container, which is in normal flow. It does not
   reach any of these: they are position:fixed with inset 0, so they are laid
   out against the viewport and the body's padding is invisible to them. On a
   notched phone that puts the title screen's start button under the home
   indicator and the top of every modal under the Dynamic Island.

   Padding rather than insetting the box, so the gradients and the binary rain
   still run edge to edge behind the notch -- the point of viewport-fit=cover
   is that the background reaches the corners and the content does not.

   This is every inset-0 overlay in web/css/, and deliberately not every
   position:fixed rule: body::before and body::after are the CRT scanline and
   pixel-grid layers, which are meant to reach the corners, and
   .game-notification and .initials-prompt are centred on top:50% rather than
   pinned to the edges. */
.title-screen,
.lore-screen,
.difficulty-modal,
.scoreboard-modal,
.settings-modal,
.instructions-modal,
.credits-modal,
.game-over,
.codex-modal,
.loading-screen {
    padding:
        var(--safe-top) var(--safe-right)
        var(--safe-bottom) var(--safe-left);
    box-sizing: border-box;
}

/* "Your bests", which shim/personal-bests.js puts in place of the arcade
   scoreboard. Same palette as that board's rows in modal-scoreboard.css: cyan
   for the mode, violet for its name, white for the number. */
.bests-list {
    text-align: left;
}

.best-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 9px 6px;
    border-bottom: 1px solid rgba(138, 43, 226, 0.2);
    font-family: 'Press Start 2P', monospace;
}

.best-row:last-child {
    border-bottom: none;
}

.best-row.is-last-played {
    background: rgba(0, 255, 255, 0.08);
    box-shadow: inset 3px 0 0 #00ffff;
}

.best-mode {
    color: #00ffff;
    font-size: 10px;
    min-width: 76px;
    text-shadow: 1px 1px 0 #006666;
}

.best-name {
    color: #b48cff;
    font-size: 8px;
    flex: 1;
}

.best-score {
    color: #ffffff;
    font-size: 10px;
    text-align: right;
    text-shadow: 1px 1px 0 #333333;
}

.bests-note {
    color: rgba(255, 255, 255, 0.45);
    font-size: 7px;
    margin: 14px 0 0;
    letter-spacing: 1px;
}

.game-over-best {
    color: #b48cff;
    font-size: 10px;
    margin: 6px 0 14px;
}

.game-over-best.is-new {
    color: #ffff00;
    text-shadow: 2px 2px 0 #999900, 0 0 10px rgba(255, 255, 0, 0.6);
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

build.sweepSelfContained();

// ── report ───────────────────────────────────────────────────────────────────

console.log(`ios/www/ built from web/`);
console.log(`  website checkout   ${website}`);
console.log(`  transforms         ${state.applied.length}`);
for (const t of state.applied) console.log(`      - ${t}`);
console.log(`  vendored           ${vendored.join(', ')}`);
console.log(`  dropped            ${dropped.join(', ')}`);
console.log(`  fonts              ${FONTS.join(', ')}`);
console.log(`  shims              ${SHIMS.join(', ')}`);
console.log(`  ogg left out       ${oggDropped} file(s) -- iOS decodes the mp3`);
console.log(`  self-contained     yes (no ../ paths, no network assets)`);
console.log(
  `\nScores: personal bests on the device, and Game Center for the rest.`
    + `\nGameCenterPlugin.swift is in the app target; what is left is the App`
    + `\nStore Connect entries and the capability. See ios/AGENTS.md.`
);
