# George Boole — iOS

The App Store version. It is **generated from `web/`**, not written here.

```
node ios/package.mjs
```

That reads `../web/`, applies the transforms below, and writes `ios/www/` —
Capacitor's `webDir`, generated and gitignored. There is no source in this
folder except the script, this file, and the Xcode project once it exists.

## Why a derivation and not a fourth version

The root `AGENTS.md` says a gameplay change is not done until every version has
it. There are three, and each is a real reimplementation: `web/js/`,
`tui/boole/`, `wii/source/`. Nothing cross-checks them, so each one added
multiplies the ways they can quietly disagree.

A hand-maintained iOS copy would be the fourth, and the worst of them — a near
duplicate of `web/`, differing in a handful of lines nobody can list from
memory. Deriving instead means the app inherits `web/` for free, the rule still
reads three, and the differences between the site and the store build are a
file you can read rather than a thing someone knows.

**So `ios/` never edits `web/`, and never holds a copy of it.** A gameplay fix
belongs in `web/js/`; the app picks it up at the next build.

## Where the website comes in

`web/index.html` is written to be served from the arcade, so it names files
that do not exist in this repo — `../shared/*` — and the self-hosted font lives
in the website repo too. `package.mjs` therefore needs a magmacrunch.com
checkout, and finds it the same way everything else here finds a sibling:

| Tried | Layout |
|---|---|
| `$WEBSITE` | anywhere, explicit |
| `../website` | flat clone, beside this repo |
| `../../web/website` | the grouped `dev/magmacrunch/` tree |

It fails with the list if none of them holds `arcade/shared/adenosine-puzzle.js`.
Same shape as the Wii Makefile's `MAGNOLIA=` and the website's `GAME_SRC=`.

## What the build changes, and why

| Transform | Why the site can keep it and the app cannot |
|---|---|
| drop `chat-widget.css`, `adenosine-chat.js`, `chat-server.js` | User-generated content. Shipping it invokes Guideline 1.2 — EULA, filtering, report, block, published contact — and raises the age rating. |
| drop `score-server.js`, and construct `ScoreClient` with no `.auto()` | It dials a WebSocket at port 8781 on the Pi behind `magmacrunch.duckdns.org`. In a bundle the hostname is Capacitor's, so it would retry localhost forever. Unconnected, `ScoreClient` falls back to `localStorage` and works offline. |
| self-host Press Start 2P | `web/index.html` pulls it from `fonts.googleapis.com`. An app that needs the network to render text is not offline-capable, and it is a third-party connection to declare on the privacy label. |
| `../shared/*` → `shared/*`, vendored | Those paths resolve to the arcade, which is not in the bundle. |
| remove the `../puzzles/` back-link | Points at a page that does not exist here. |
| remove the "As a warm up, play 2048 (actually, 2^N)" paragraph | Sends App Store users to a web game. The site keeps it. |
| strip `?v=` stamps | Cache-busters for a CDN. Meaningless in a bundle, and the root `AGENTS.md` already calls them a standing maintenance hazard. |
| `viewport-fit=cover` + `css/ios.css` | Safe-area insets, no rubber-banding, no tap highlight, no long-press callout. The site has no reason to carry any of it. |
| drop every `.ogg`, and pin `AUDIO_EXT` to `.mp3` | Every clip ships twice and iOS has no Vorbis decoder, so 2.7MB of the bundle could never be decoded — `www/` went from 6.2MB to 3.5MB. **Both halves are required.** Dropping the files alone leaves `main.js` still asking for them, from a `canPlayType()` probe that is false on WebKit and true nearly everywhere else: the bundle then works on a phone and 404s in Chrome, where the failed decode takes `AdAudio.init` down and the loading screen never lifts — breaking the one way this bundle can be tested without a Mac, in the direction that looks like the audio work being wrong. Safe only here, and only because the runtime is WebKit by definition; `web/` keeps both, since it is served to Firefox too. |
| outbound `<a href="http…">` gets `target="_blank" rel="noopener"` | So the credits link opens in the system browser instead of navigating the app away from itself. |
| drop `tests/`, `performance-test.html`, the guides, `title-card.html` | Dead weight, and `performance-test.html` is a second entry point a reviewer could reach. |

## The two guards

Both exist because the failure this folder is designed against is *silent*: the
website gains a widget one day, the next sync carries it into `web/`, and it
ships.

**An unknown shared file stops the build.** `SHARED` in `package.mjs` is an
allowlist mapping every `../shared/` file the page may name to `vendor` or
`drop`. Anything unlisted is a hard error asking you to decide. Defaulting to
`vendor` could bundle an unread script; defaulting to `drop` could silently
break the game. Refusing to guess is the only default that cannot ship a
surprise.

**A transform that matches nothing is fatal too.** Every step asserts it
changed the page. A regex that silently stops matching because the markup moved
would leave the app carrying whatever that step was there to remove, and the
build would still say it succeeded — the same bug, one level quieter. `edit()`
does this for `index.html`; `editFile()` does it for any other file in `www/`,
and the `.ogg` step asserts it dropped something for the same reason.

Then a final sweep walks `www/` and fails on any `src`/`href` starting `../` or
on any `<script>`/`<link>`/`<img>` fetching over `http(s)`. That is the actual
claim being made — the bundle runs with the network off — checked rather than
asserted.

## The native project

Capacitor 8, in `App/`. Two commands:

```
npm run build   # web/ -> www/          (package.mjs alone)
npm run sync    # web/ -> www/ -> App/  (package.mjs, then cap sync)
```

`npm run sync` is the one to use. `cap copy` alone would push a stale `www/`
into the project, which looks like the build not taking effect.

| | |
|---|---|
| Bundle id | `com.magmacrunch.georgeboole` |
| Display name | George Boole |
| `webDir` | `www` |
| Platform path | `App` (set in `capacitor.config.json`; the default would have made `ios/ios/`) |

**The bundle id is trivial to change now and permanent after the first
submission** — it is the app's identity on the App Store and in Game Center,
and it cannot be reused or renamed afterwards. Change it before submitting or
not at all.

**`App/` is committed; what is generated inside it is not.** `cap add` wrote
`App/.gitignore`, which already covers the copied `public/`, the derived
`capacitor.config.json`, build output, Pods, DerivedData and xcuserdata. Those
paths are relative to `App/`, so do not restate them in `ios/.gitignore` — a
second copy that drifts would quietly start tracking generated files.

Capacitor 8 uses Swift Package Manager (`App/App/CapApp-SPM/`), not CocoaPods,
so there is no `Podfile` and nothing to `pod install`. `cap sync` rewrites
`CapApp-SPM/Package.swift` from scratch from the npm plugin list on every run —
the file says "DO NOT MODIFY" and means it. Add plugins with `npm install`,
never by hand.

**A plugin written into the App target is not auto-discovered, and the failure
is silent.** Capacitor 8 builds its plugin list from `packageClassList` in the
generated `App/App/App/capacitor.config.json`, which `cap sync` regenerates
wholesale from the npm dependencies — so a class name added there by hand does
not survive a build — and `registerPluginType(_:)` returns immediately while
`autoRegisterPlugins` is true, which it is by default. There is no
Objective-C runtime scan. The one door left open is
`bridge?.registerPluginInstance(_:)` called from
`CAPBridgeViewController.capacitorDidLoad()` in a subclass.

This matters specifically for the GameCenter plugin below, because
`shim/gamekit-scores.js` degrades quietly by design: an unregistered plugin
produces no error anywhere, just a Game Center that never does anything.
`@capacitor/haptics` is unaffected — it came from npm, so it is in
`packageClassList` and registers itself.

`ITSAppUsesNonExemptEncryption` is `false` in `Info.plist`. The bundle makes no
network requests at all, so it is true; without the key App Store Connect asks
the export-compliance question on *every* upload and holds the build until it
is answered.

Two edits to the stock `Info.plist`, both deliberate:

- `UIRequiredDeviceCapabilities` is `arm64`, not the template's `armv7`. 32-bit
  ARM has not been a thing since iOS 11.
- **iPhone is portrait-only.** `web/css/responsive.css` breaks at 600px, so a
  landscape phone — 812 points wide — falls into the *desktop* layout, side
  panels and all, with 375 points of height to draw it in. Offering the
  orientation before there is a landscape design just ships a broken one. iPad
  keeps all four: its narrowest side is 768, so it wants the desktop layout
  either way.

There is no `NSAppTransportSecurity` block and there should never be one. The
bundle makes no network requests at all, so the strict default costs nothing —
and an ATS exception in a fully offline app is a question at review time with
no good answer.

## What the app does that the page cannot

Worth keeping as a list, because it is the answer to the only review guideline
this app is really at risk from. **Guideline 4.2** is where a Capacitor game
dies: a reviewer opens it, sees a web page, and rejects it as a site in a
wrapper. What moves that is native integration, not polish.

| | |
|---|---|
| Haptics | `ios/shim/haptics.js`, via `@capacitor/haptics`. Listens to the `boole:*` events; the site gains no Capacitor dependency because the shim never reaches it. A slide is `LIGHT` and a merge `MEDIUM` — a move fires on most swipes, and anything heavier stops being information within a minute. Overflow is a `SUCCESS` *notification* rather than an impact: it is the biggest single payout in the game and the one moment that should not feel like a merge. A Gauntlet promotion lands ~800ms after the overflow that earned it, so it is three heavy taps rather than a second `SUCCESS` nobody could tell from the first. |
| Genuinely offline | Not a claim, a build failure: the final sweep rejects any asset fetched over `http(s)`, and there is no `NSAppTransportSecurity` block because there is nothing to except. |
| Portrait lock and safe-area layout | `Info.plist` plus the generated `css/ios.css`. |
| Game Center | The strongest item, and the one still missing its native half. |

Note `'HEAVY'` and `'SUCCESS'` in the haptics shim are not matched by name:
`@capacitor/haptics` only string-compares `MEDIUM`/`LIGHT` and `WARNING`/
`ERROR`, and everything else falls through to the initial values, which are
`.heavy` and `.success`. They are the documented API and they do the right
thing, by default rather than by comparison — spelled out so nobody "fixes"
them. The package ships no `PrivacyInfo.xcprivacy`, which is correct:
`UIFeedbackGenerator` is not a required-reason API.

## Not done yet

The build is real and the output runs. These are the open pieces:

- **Game Center: the JavaScript half is done, the native half is not.**
  `shim/gamekit-scores.js` patches `scoreClient.save` to also submit to a
  leaderboard, maps all eight web difficulties to ids taken from
  `tui/boole/modes.py` (whose docstring already promised those keys would stay
  stable), and degrades to exactly today's behaviour when nothing answers.

  What is missing is a Capacitor plugin registered as `GameCenter` providing
  `signIn()`, `submitScore({leaderboardId, score})` and
  `showLeaderboard({leaderboardId})` — Swift, so macOS. Then the eight
  leaderboards have to be created in App Store Connect under exactly those ids.

  Two things the shim decides that are worth knowing. Reading stays local:
  Game Center has no scores-query worth rendering into this game's own
  scoreboard, and it has a full-screen UI instead, which is what
  `showLeaderboard` is for. And the local write happens first and
  unconditionally, so a declined sign-in never costs a player their score.

- **Achievements are not wired**, but the seam they need exists. This bullet
  used to say hooking them meant touching `web/js/game.js` and was therefore a
  decision rather than a detail. It was, and it was taken: `game.js` now
  announces five moments as plain `CustomEvent`s on the document —
  `boole:move`, `boole:overflow`, `boole:height-bonus`, `boole:promotion`,
  `boole:game-over` — each carrying `difficulty` and `bits`. They are named for
  the game rather than for a platform, the site dispatches them into a document
  with no listeners, and `ios/shim/haptics.js` already consumes them.

  `ios/shim/gamekit-achievements.js` is the rest of the JavaScript half: seven
  overflow achievements, one per bit width, plus a Gauntlet clear. It needs one
  method beyond the three `gamekit-scores.js` documents —
  `reportAchievement({ achievementId, percent })`. What is left is that native
  method and the eight achievements in App Store Connect.

  Three decisions in it worth not re-litigating. They are keyed on bit *width*
  rather than mode, so the same achievement is reachable by picking that
  difficulty or by climbing to it in Gauntlet — `bitMode` is what makes an
  overflow hard, not which menu entry you came in through. The Gauntlet clear
  is *overflowing at 8-bit while in Gauntlet*, because every promotion is
  guarded by `if (this.bitMode < 8)` so there is no ninth promotion to observe,
  and "promoted to 8-bit" would be the easier thing wearing the harder one's
  name. And an achievement earned while no plugin answers is **not** recorded
  as reported: the player earned it, and when the native half lands they should
  get it on their next overflow rather than having it written off in advance.

  Seven at 100 plus 300 is 1000 exactly, which is App Store Connect's per-app
  cap — so a ninth achievement means re-pointing all of them. Decide before
  creating any; 80 and 240 would leave 200 spare.

  **Do not replace this with a shim that patches the game from outside.** It
  does not work and it would be wrong twice over. `AdAudio`'s exports are
  installed with `__defProp(target, name, { get, enumerable })` — non-writable,
  non-configurable accessors — and `BooleBoard` is a class declaration, so a
  global *lexical* binding rather than a property of `window`. Both are
  reachable with effort, and both would still be wrong, because of the guard
  below.

- **`_emit` is guarded, and the guard is load-bearing.** `checkGameOver()`
  decides whether the board is dead by running `moveLeft()` for real, four
  times, on a copy. It snapshots and restores score, moves, `highestValueEver`,
  both flag boards and queued timeouts — but not notifications and not sound.
  Every `showOverflowNotification` / `showHeightBonus` /
  `showUpgradeNotification` call site is inside `moveLeft()` or `applyGate()`,
  so all three run during that probe. A dispatched event cannot be restored, so
  filling the board would buzz the phone four times and award achievements
  nobody earned. `this._silent` is set around the probe in `try/finally` —
  `finally` because the loop has an early `return false` that must clear it too.

  The pre-existing version of the same bug is still there and was deliberately
  left alone: the probe also fires the real notifications and sound effects, so
  a board that fills up can flash a phantom overflow popup. That is a visible
  change to the live website and belongs in its own commit.
- **`adenosine_scores__pending` grows forever.** `ScoreClient.save()` queues
  every unsynced score for a later flush that, unconnected, never comes.
  Harmless but unbounded; whatever replaces the backend should drain or ignore
  it.
- **Touch is swipe-only.** `adenosine-puzzle.js` binds `touchstart`/`touchend`
  with no `touchmove`, so tiles do not follow a finger. Playable, but it is the
  thing that will make the app read as a port.
- **Safe-area values are untested on a real device.** `css/ios.css` pads the
  body by the insets, which is the conservative default and not necessarily the
  right design once there is a notch to look at.

  One specific way it was incomplete is fixed: padding the body reaches
  `.container`, which is in normal flow, and reaches **nothing else**.
  `.title-screen`, `.lore-screen`, `.game-over` and the five modals are
  `position: fixed` with inset 0, so they are laid out against the viewport and
  the body's padding is invisible to them — the start button sat under the home
  indicator. They are padded individually now, and padded rather than inset, so
  the gradients and the binary rain still reach the corners. That list is every
  inset-0 overlay in `web/css/` and deliberately not every `position: fixed`
  rule: `body::before` and `body::after` are the CRT scanline and pixel-grid
  layers, which are meant to reach the corners, and `.game-notification` and
  `.initials-prompt` are centred on `top: 50%`.

- **Launch is gated on decoding four minutes of audio.** `web/js/main.js`
  awaits `AdAudio.init()` before hiding the loading screen, and `init()` awaits
  the music load first and alone, ahead of the sfx `Promise.all`. `loadMusic`
  runs the clip through `decodeAudioData` into a resident PCM buffer. Measured
  in a browser against the bundle: `game-loop.mp3` is 2.72MB on disk, 230.5s,
  and decodes to **84.4MB resident**. Nothing renders until that finishes and
  the sfx do not start loading until it does.

  The fix is small and lives in `engines/adenosine`: keep the `loadMusic`
  promise without awaiting it in `init()`, and have `playMusic()` await it
  instead — it already guards on `!musicBuffer`, and music is not wanted until
  `startGame()`, at minimum one tap later.
- **Nothing has been built or run.** `cap add ios` scaffolds the project fine
  on Windows — that is all it did here — but compiling it, running a simulator
  and archiving for submission need macOS and Xcode. Nothing in `App/` has been
  opened by Xcode yet, so treat the project as generated-and-unverified rather
  than known-good.
- **The app icon needs redrawing — but not because it is a placeholder.** This
  bullet claimed until 2026-09-14 that the icon and launch screen were
  Capacitor's stock art. They have not been since `2ef2d8d`: both are generated
  by `tools/make-art.py`, and regenerating means re-running that script.

  Two things are true instead. `make-art.py`'s `build_icon` docstring describes
  the four gates on a 2×2 board and explains why the portrait was rejected —
  but the file on disk *is* the portrait, so the art was replaced again
  afterwards and the docstring no longer describes its own output. And the
  portrait does not survive being small: at 1024 it is fine, at 180
  (`ios/assets/apple-touch-icon.png`, roughly home-screen size) it is a dark
  blob. Dark brown hair and a near-black coat on dark navy is almost no value
  contrast, on a wallpaper that may itself be dark; the sunglasses — the whole
  joke, and what the title screen's `glint` animation exists to show off — are
  black on brown and invisible; the coat runs off the bottom edge in a value
  close to the background, so iOS's superellipse mask will clip the shoulders
  off a silhouette that already reads as cropped. Judge a redraw at 60, 120 and
  180, not at 1024.

  **The launch image is good** and needs nothing: cyan wordmark, magenta
  subtitle, the same gradient and scanlines as the title screen. Apple's HIG
  advises against text on a launch screen; plenty of games ship a wordmark and
  pass review, so treat that as taste rather than a blocker.

- **Two required App Store Connect URLs have nothing to point at.** Both the
  Privacy Policy URL and the Support URL are mandatory for every submission,
  and the magmacrunch.com checkout has **neither page** — no `privacy`, no
  `support`, no `contact` anywhere in it. Nobody discovers this until the
  Submit button is greyed out. The policy is short for an app that collects
  nothing, and unusually easy to write honestly: `package.mjs`'s final sweep
  fails the build on any asset fetched over `http(s)`, so "collects nothing,
  contacts no server" is enforced rather than asserted.
- **Two lines of visible copy still name 2048**, in `web/index.html`: the
  how-to-play ("Just as in *2048*…") and the credits. The credits line —
  "inspired by Gabriele Cirulli's *2048* (2014), reimagined with Boolean
  logic" — should **stay**: guideline 4.3 is about undisclosed clones, and
  stating the lineage is the opposite of that. The cross-promo for the
  arcade's own 2^N is dropped by `package.mjs` since 2026-09-09; the site
  keeps it.

## AI Attribution

**No AI attribution.** Do not append `Co-Authored-By: Claude …`, "Generated
with …", or any similar trailer to commit messages, PR bodies, or release
notes. If your tooling adds such a line by default, remove it before
committing.
