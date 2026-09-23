# George Boole — iOS

The App Store version. It is **generated from `web/`**, not written here.

```
node ios/package.mjs
```

That reads `../web/`, applies the transforms below, and writes `ios/www/` —
Capacitor's `webDir`, generated and gitignored. No copy of the *game* lives
here: what this folder holds beside the script and the Xcode project is
`shim/` (the four files bundled into `www/shim/`), `tools/` (the icon, launch
image and screenshot scripts), `store/metadata.md`, and
`assets/apple-touch-icon.png`, which the build refuses to run without.

## Part of this folder now has an upstream

Since 2026-09-18 the shared half of an iOS build lives in
`engines/hypnopompia`, the iOS shell, and this game is its first consumer.
Read its AGENTS.md before changing any of the following.

| Here | Upstream |
|---|---|
| `App/App/App/GameCenterPlugin.swift` | **vendored** from `hypnopompia/native/`. Do not edit it here. |
| `App/App/App/GameViewController.swift` | the same |
| the metadata checker | **moved.** Run `node ../../../engines/hypnopompia/tools/check-metadata.mjs .` from this folder, or give it this folder's path from there. `tools/check-metadata.mjs` is gone. |

**`ios build` now checks that the plugin survived into the app**, which it did
not before 2026-09-23: it compiled the app and stopped, so its green said the
project builds and said nothing about whether `GameCenterPlugin` was in it.
That gap mattered most for exactly the file above, vendored from another repo
where a change arrives without anyone here looking at it.

The check reads `App.debug.dylib` as well as `App`, and that is not belt and
braces. **Since Xcode 16 a Debug build is split in two**: this project's code
compiles into `App.debug.dylib` while `App` is a ~70KB launcher stub carrying
none of these classes, `AppDelegate` and `SceneDelegate` included. makemecookies
has the same step and checked only `App`, and spent four days calling a
correctly wired project broken. To look yourself, on the Mac:

```
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer   # Xcode is
                                    # installed but xcode-select points at CLT
nm -a <derived>/Build/Products/Debug-iphonesimulator/App.app/App.debug.dylib \
  | grep '_OBJC_CLASS_\$_GameCenterPlugin'
```

**Editing a vendored Swift file here is the drift this arrangement is designed
to catch, and it is caught from the other end.** `node tools/sync.mjs --check`
in hypnopompia hash-compares both files against every consumer in its
`consumers.json`, which lists this repo. A change belongs upstream, followed by
`node tools/sync.mjs ../../games/george-boole` to bring it back down. Nothing in
this repo notices on its own yet; wiring that check into this game's CI is
listed as outstanding in hypnopompia's AGENTS.md.

`store/metadata.md` gained a `<!-- forbid-keywords: 2048 -->` line, which is how
the moved checker learns a fact it used to hardcode. The prose above it explains
why "2048" must not be a keyword; that line is what enforces it.

Everything else here is still this game's own, and the pipeline, the four shims
and the safe-area CSS deliberately have **not** moved. They wait for a second
iOS game, because with one example there is no way to tell which of
`package.mjs`'s fourteen transforms are arcade-wide and which are george-boole's.

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
| drop `tests/`, `performance-test.html`, the guides, `title-card.html`, `README.md`, `audio/README.txt` | Dead weight, and `performance-test.html` is a second entry point a reviewer could reach. |

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

**To look at the bundle without a Mac, serve `www/` and open it:**

```
npx serve ios/www
```

That is the whole recipe, and it is deliberately not a script in this repo. There
was one, an untracked `ios/serve.js`, and it was deleted on 2026-09-18: it
hardcoded an absolute path to this checkout, sent no `Content-Type` on anything,
and joined the request path onto the root without a traversal check. `npx serve`
does the job with correct MIME types and nothing to keep working. `9ffff21` had
already generalised the reference in `shim/haptics.js` from that file to "any
static server pointed at `ios/www`", so this only finishes that thought.

Open `/`, not `/index.html`: `serve` does clean URLs, so the full filename 301s to
`/index`, which reads like a misconfiguration and is not one. Verified 2026-09-18
that it types everything this bundle loads correctly, `text/html` on `/` through
to `font/woff2` on the Press Start face.

Pick a port nobody else is on, and note that a browser is where the shims are
*supposed* to do nothing: Capacitor injects `window.Capacitor.Plugins.*` from the
native side, so haptics and Game Center are no-ops here by design. What this
does catch is everything else, which is most of it.

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

Because it is both tracked and rewritten, `cap sync` leaves `git status` showing
` M CapApp-SPM/Package.swift` even when the plugin list has not changed. That is
a stale stat cache, not drift: the bytes match the index exactly, `git diff` is
empty, and a commit of it would be a no-op. Confirmed 2026-09-18 by comparing the
file against `git show :<path>`, which is the check to run rather than assuming
either way.

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
| Game Center | The strongest item. Native since 2026-09-17: `App/App/App/GameCenterPlugin.swift`, registered by `App/App/App/GameViewController.swift`. What is left is not code — the leaderboards and achievements in App Store Connect, and the capability, which needs the paid account. |

Note `'HEAVY'` and `'SUCCESS'` in the haptics shim are not matched by name:
`@capacitor/haptics` only string-compares `MEDIUM`/`LIGHT` and `WARNING`/
`ERROR`, and everything else falls through to the initial values, which are
`.heavy` and `.success`. They are the documented API and they do the right
thing, by default rather than by comparison — spelled out so nobody "fixes"
them. The package ships no `PrivacyInfo.xcprivacy`, which is correct:
`UIFeedbackGenerator` is not a required-reason API. The app has its own, at
`App/App/App/PrivacyInfo.xcprivacy`, and what Apple checks is the aggregate of
the two -- Product > Archive > Generate Privacy Report is how to see it.

## Not done yet

The build is real and the output runs. These are the open pieces:

- **The app has no arcade scoreboard, on purpose.** On the website the
  scoreboard is a cabinet — type initials, compete for the top ten — and it
  works because `ScoreClient` is connected to a shared backend. The bundle
  drops that connection, so the same board would only ever list one person's
  games on one phone under initials they typed to compete with themselves.

  `shim/personal-bests.js` replaces it. It sets `GameBoole.scoreboard` to
  `'personal'`, which is the whole switch: `handleGameOver()` in
  `web/js/game.js` checks it and goes straight to the game-over screen instead
  of the initials prompt. The website never sets it, so its board is
  unchanged. From `boole:game-over` the shim records each mode's best score,
  best tile and games played in `localStorage['gb_bests']`, adds a "NEW BEST!" /
  "your best: N" line to the game-over screen, and plays the high-score sound on
  a new best. It rebuilds `#scoreboardModal`'s contents as a "your bests" card —
  keeping the modal id and `#closeScoreboard`, so main.js's open and close
  wiring applies unchanged — with a Game Center leaderboards button shown only
  when signed in. main.js's `updateScoreboard()` and dropdown code both guard
  against the elements the card removes; no patching needed.

  A consequence worth knowing: the app never calls `scoreClient.save()` now,
  so the unbounded `adenosine_scores__pending` queue this list used to warn
  about cannot grow in the app.

- **Game Center: both halves are written; what is left needs an Apple account.**
  `shim/gamekit-scores.js` submits to a leaderboard on `boole:game-over`, maps
  all eight web difficulties to ids taken from `tui/boole/modes.py` (whose
  docstring already promised those keys would stay stable), and does nothing
  when no plugin answers.

  **It submits every finished game, which it did not before.** It used to wrap
  `scoreClient.save`, and that is called only from `submitInitials()` — only
  when a score made the local top ten *and* the player typed initials. A
  leaderboard fed that way would have missed nearly every game. Game Center
  keeps each player's best per leaderboard itself, so submitting a lower score
  is harmless; a zero is skipped. Verified with a stand-in plugin injected ahead
  of the page: sign-in at launch, 120 then 30 both submitted to `hexad`, 0
  skipped, and the card's button opening the last-played mode's leaderboard.

  `App/App/App/GameCenterPlugin.swift` is the native side: `signIn`, `submitScore`,
  `showLeaderboard` and `reportAchievement`, registered by
  `GameViewController.capacitorDidLoad()` for the reason given further up.
  Verified in the simulator: the plugin registers, the shim sees it, and
  `signIn` answers. What is left is the capability and the App Store Connect
  entries — eight leaderboards and fifteen achievements under exactly the ids
  the shims name — both of which need the paid account.

  **The art for those entries is drawn and waiting**, by
  `tools/make-boards.py`, into `store/game-center/`: one image per
  leaderboard and per achievement, named for the id it belongs to. They are
  **1024 x 1024**, which is what App Store Connect asks for on both; 512 is
  the number everybody remembers and it is wrong. An achievement image is
  required, a leaderboard image optional.

  The script reads the modes from `tui/boole/modes.py`, the discoveries from
  `web/js/codex.js` and the ids from the achievements shim, and refuses to
  draw if the codex and the shim disagree about what the seven discoveries
  are. An image is not compiled and nothing else would ever notice it had
  gone stale.

  **Two GameKit traps are handled, and both look like nothing is wrong.**
  `authenticateHandler` is not a completion handler: GameKit keeps it, calls
  it again on every later state change, and reports an outcome once. A
  `signIn` arriving *after* that outcome must be answered from
  `GKLocalPlayer.local.isAuthenticated` rather than queued on the handler —
  queued, it hangs forever, and the app still looks healthy because the shim's
  one call at page load is the one that worked. That was a real bug, found by
  probing the running app rather than by reading it. And a
  `GKGameCenterViewController` with no delegate does not dismiss itself: the
  Done button does nothing and the player is stuck on Apple's screen.

  `App/App/App/App.entitlements` carries `com.apple.developer.game-center` and is
  wired through `CODE_SIGN_ENTITLEMENTS`. A simulator build signs ad hoc and
  ignores it; a device build or archive fails on it, naming that entitlement,
  until Game Center is enabled for the bundle id on the account. That failure
  is expected until then, not a mistake in the project.

  Reading stays local: Game Center has no scores-query worth rendering into
  this game's own card, and it has a full-screen UI instead, which is what
  `showLeaderboard` is for.

- **Achievements: the same state as the leaderboards above** — both halves
  written, nothing created in App Store Connect. This bullet
  used to say hooking them meant touching `web/js/game.js` and was therefore a
  decision rather than a detail. It was, and it was taken: `game.js` now
  announces five moments as plain `CustomEvent`s on the document —
  `boole:move`, `boole:overflow`, `boole:height-bonus`, `boole:promotion`,
  `boole:game-over` — each carrying `difficulty` and `bits`. They are named for
  the game rather than for a platform, the site dispatches them into a document
  with no listeners, and `ios/shim/haptics.js` already consumes them.

  `ios/shim/gamekit-achievements.js` is the rest of the JavaScript half:
  fifteen achievements. Seven overflows, one per bit width, and a Gauntlet
  clear; and seven `learn.<id>` achievements, one per discovery in
  `web/js/codex.js` (`self_inverse`, `nothing_in_common`, `all_lit`,
  `opposites`, `wraparound`, `chain_reaction`, `full_set`), awarded on its
  `boole:discovery` event so the codex and Game Center agree about what was
  found. Those ids are permanent once created in App Store Connect, so the
  codex's ids must not be renamed after that. It needs one method beyond the
  three `gamekit-scores.js` documents —
  `reportAchievement({ achievementId, percent })` — and
  `GameCenterPlugin.swift` provides it. What is left is the fifteen
  achievements in App Store Connect.

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

  Points: App Store Connect allows at most **100 per achievement** and 1000
  per app. An earlier version of this bullet planned the Gauntlet clear at 300,
  which the form refuses. The budget is overflows 7 × 50, Gauntlet clear 100,
  discoveries 7 × 50 — 800, leaving 200 for later.

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
- **Touch-drag is wired here and waiting on an npm release.** The engine half
  already exists: adenosine's `createInput` gained opt-in `onDrag` /
  `onDragEnd` in `@magmacrunch/adenosine-puzzle` **0.4.0** (PR #18, merged
  2026-09-12). `web/js/game.js` now passes both, so occupied tiles lean after
  the finger along the drag's axis, capped at 0.22 of the measured cell pitch
  with a `tanh` soft stop, and glide home on lift.

  **It does nothing yet, and correctly so.** 0.4.0 was merged and never
  published — npm stops at 0.3.0 — and the chain from engine to app is
  adenosine → npm → the website's `node_modules` → `sync-adenosine.mjs` →
  `arcade/shared/` → `package.mjs`. A 0.3.0 bundle reads only `onMove` and
  `isActive`, so the new callbacks are ignored and swiping behaves exactly as
  before. Verified both ways against the bundle: with a locally built 0.4.0 the
  tiles follow and cap, empty cells stay put, a tap is not hijacked,
  `touchcancel` settles without moving, and one swipe emits one `boole:move`;
  with the shipping 0.3.0, nothing leans and every swipe still moves. What turns
  it on is a GitHub Release on adenosine (which is what `publish.yml` fires on),
  then `npm update` and `sync-adenosine.mjs` in the website.

  It is a rubber band, not a preview of the move. Tiles are sixteen fixed cells
  whose contents change in place, so sliding each tile to where it will land
  means knowing the move's result first — by copying the merge rules into the
  renderer, a fourth implementation in all but name, or by simulating the move,
  which plays real sounds and shows real popups. Every occupied tile leans the
  same way instead.

  The engine does not listen for `touchcancel`, which iOS fires when a system
  gesture takes the touch; `game.js` settles on it itself.
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

- **Launch no longer waits for the music, but the music still costs 84MB.**
  `game-loop.mp3` is 2.72MB on disk, 230.5s, and `decodeAudioData` turns it
  into **84.4MB of resident PCM**. `AdAudio.init()` awaits every track in its
  manifest, and the music used to be in it, so the loading screen waited for
  that whole decode and the sound effects did not start loading until it was
  done.

  Fixed in `web/js/main.js`, not in the engine: `init()` now gets only the sound
  effects, and `AdAudio.loadMusic()` — already exported on its own — runs in the
  background with its promise kept; `startGame()` plays the music once it
  settles. The engine needed no release for this, which an `init()` change
  would have. Measured against the bundle in a desktop browser, median of five
  cold loads: the title went from **274ms to 35ms**, now shown before the music
  has finished downloading. A phone's decode is several times slower, so the
  saving there is larger in absolute terms.

  Audio loading also has its own `try` now. It used to share one with all of
  the title-screen wiring, so a single clip failing to decode threw past it and
  left the loading screen up permanently. Verified with a fetch stub: music
  failing, or a sound effect failing, still reaches the title and the
  how-to-play screen, with one console error each; tapping start before the
  music has decoded starts it the moment the decode finishes.

  What is not fixed is the 84MB. The track still decodes fully, only not in the
  player's way. Streaming it through an `<audio>` element would avoid the
  buffer, but that is the engine's decision to make, and it is why the loop is
  a decoded buffer in the first place (see the root `AGENTS.md` on mp3 loop
  seams).

- **Built and run in the Simulator; not yet on a device, signed, or archived.**
  First built 2026-09-16 on the MacBook Pro '26 (`jakes-macbook-pro--26`,
  macOS 26.5.2, Xcode 26.6, iOS 26.5 Simulator runtime, iPhone 17 Pro). It
  compiled at the first attempt with no source changes, and the Swift packages
  resolve (`capacitor-swift-pm` 8.5.1 plus the local `CapacitorHaptics`). The
  one warning is Xcode noting the app has no App Intents, which is harmless.

  The Mac's checkout is flat, `~/Documents/magmacrunch/george-boole` beside
  `~/Documents/magmacrunch/website`, which is `package.mjs`'s first candidate,
  so it needs no `WEBSITE=`. Note `~/Documents/magmacrunch/games/george-boole`
  on that Mac is an older loose copy and not a git repository. Build and run
  without Xcode's window, and without signing, since the Simulator needs none:

  ```
  export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
  cd ios && npm run sync && cd App/App
  xcodebuild -project App.xcodeproj -scheme App -configuration Debug \
    -destination "platform=iOS Simulator,name=iPhone 17 Pro" \
    -derivedDataPath ~/Library/Developer/gb-derived CODE_SIGNING_ALLOWED=NO build
  xcrun simctl install booted ~/Library/Developer/gb-derived/Build/Products/Debug-iphonesimulator/App.app
  xcrun simctl launch booted com.magmacrunch.georgeboole
  ```

  `DEVELOPER_DIR` because that Mac's `xcode-select` still points at the
  Command Line Tools; `sudo xcode-select -s` fixes it for good and needs a
  password. The shared scheme landed on 2026-09-17, so `-scheme App` now
  resolves from a fresh clone. `Package.resolved` is committed as of
  2026-09-17, pinning capacitor-swift-pm, so a fresh clone resolves to the
  same version this was built against. Still outstanding: a development team
  in the project, and anything that needs the paid developer account.
- **Screenshots are captured by a script, not by hand.**
  `tools/screenshots/capture.sh <udid> <name>` boots a simulator, injects
  `tools/screenshots/shots.js` into a *copy* of the built app, freezes the
  status bar at 9:41 and takes five: title, the rules as tiles, a board with
  the point labels and the math card, the gate codex, and your bests. The
  staging script taps the real buttons and plays real moves, so what is
  captured is the app.

  Two things it has to work around, both of which produced a bad take first.
  `main.js` declares `let currentGame` at the top level of a classic script,
  which is a global lexical binding and **not** a property of `window` --
  `window.currentGame` is undefined, and reaching for it staged nothing while
  appearing to work. And every codex unlock shows a toast for 2.4 seconds, so
  the gates are unlocked in one early burst and the shots that follow wait the
  whole queue out; a toast across the top of a frame means the timeline and
  the offsets in `capture.sh` have drifted apart.

  The images themselves are **not** committed -- 24MB of PNG that this script
  reproduces. They land in `~/gb-shots/<name>/` on the Mac.
- **The app icon was redrawn on 2026-09-17, and one script owns it.**
  `tools/make-boole-pixel.py` draws it; `tools/make-art.py` draws only the
  launch image. Both used to write `AppIcon-512@2x.png` — `make-art.py` the
  four gates on a 2×2 board, the pixel script (added 2026-09-13) the portrait —
  so the icon on disk was whichever had run last, and `make-art.py`'s
  docstring described a picture that was no longer there.

  The first portrait icon was the title-screen sprite scaled up, and at
  home-screen size it was a dark blob: dark hair and a near-black coat on dark
  navy, and the sunglasses — the whole joke — black on brown. The icon is now
  its own sprite (`ICON`, beside the title screen's `PORTRAIT`): a magenta
  ground, a one-cell dark outline, cyan lenses with a white glint and a cyan
  bow tie, and a head-and-shoulders crop with the coat running off the bottom.

  There are two icons. `AppIcon-512@2x.png` is the one above;
  `AppIcon-512@2x-dark.png` is a deeper version of the same sprite, paired
  with it by an `appearances` entry in the appiconset's `Contents.json`,
  because from iOS 18 the system dims a light icon on a dark home screen and
  took the magenta nearly to black. The tinted variant is derived by the
  system, so there is no third file.

  Two things to keep. **Judge them at 60, 120 and 180px**, not 1024:
  `--sheet <png>` writes both at those sizes, masked -- the light icon on a
  light wallpaper and the dark one on a dark wallpaper, which is where each is
  actually shown.
  And the script **refuses an outline that iOS's rounded corners would cut**.
  Solid coat running into a corner is fine, since the rounding only trims
  colour; the first redraw had narrower shoulders whose outline crossed the
  bottom corners, which would have bitten a notch out of the silhouette on a
  home screen while the asset catalog previewed the full square intact.

  A plain run leaves `web/` alone. `--web` also rewrites the site's
  `apple-touch-icon.png` and the title screen's `img/boole-pixel.png` from
  `PORTRAIT`, which is a decision about the website rather than the app.

  **The launch image is good** and needs nothing: cyan wordmark, magenta
  subtitle, the same gradient and scanlines as the title screen. Apple's HIG
  advises against text on a launch screen; plenty of games ship a wordmark and
  pass review, so treat that as taste rather than a blocker.

- **The two required App Store Connect URLs exist as of 2026-09-17**:
  Privacy Policy `https://magmacrunch.com/privacy/george-boole/` and Support
  `https://magmacrunch.com/support/george-boole/`, both in the website repo
  (`privacy/george-boole/`, `support/george-boole/`, with `/privacy/` and
  `/support/` as indexes -- one page per app, since App Store Connect takes
  one of each per app and a second app's answers are its own). Both are scoped to this app,
  not the website, which has chat and score servers the app does not.

  The policy makes factual claims about the bundle, so **a change that
  breaks one of them means updating the page before shipping**. They are: no
  network connections of the app's own (true because `package.mjs` swaps
  `ScoreClient().auto(...)` for an unconnected client and its sweep refuses
  remote assets); the four kinds of thing kept in `localStorage` — bests,
  codex progress, settings, and the reported-achievements set; and Game
  Center as the only thing that leaves the device. A new storage key is
  usually fine. Analytics, crash reporting, an ad, or reconnecting the score
  client is not, and also changes the App Store privacy label.
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
