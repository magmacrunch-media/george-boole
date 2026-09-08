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
| strip `?v=` stamps | Cache-busters for a CDN. Meaningless in a bundle, and the root `AGENTS.md` already calls them a standing maintenance hazard. |
| `viewport-fit=cover` + `css/ios.css` | Safe-area insets, no rubber-banding, no tap highlight, no long-press callout. The site has no reason to carry any of it. |
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
build would still say it succeeded — the same bug, one level quieter.

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
so there is no `Podfile` and nothing to `pod install`.

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

## Not done yet

The build is real and the output runs. These are the open pieces:

- **Game Center.** The leaderboard is `localStorage` only. `tui/boole/modes.py`
  already defines eight modes with stable keys, and says in its own docstring
  that the key *is* the leaderboard id — so the eight GameKit leaderboards are
  a data-entry job, not a design one. The seam is `scoreClient`, whose whole
  surface is `load(game)` and `save(game, initials, score, extra)`.
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
- **Nothing has been built or run.** `cap add ios` scaffolds the project fine
  on Windows — that is all it did here — but compiling it, running a simulator
  and archiving for submission need macOS and Xcode. Nothing in `App/` has been
  opened by Xcode yet, so treat the project as generated-and-unverified rather
  than known-good.
- **App icon and launch screen are Capacitor's placeholders.**
  `Assets.xcassets/AppIcon.appiconset` holds the stock 1024px square, and
  `Splash.imageset` three stock splashes. The game already has real art to draw
  from — `web/apple-touch-icon.png` and `web/title-card.html`.
- **Three lines of visible copy still name 2048**, in `web/index.html`: the
  how-to-play ("Just as in *2048*…"), a cross-promo for the arcade's own 2^N,
  and the credits. The credits line — "inspired by Gabriele Cirulli's *2048*
  (2014), reimagined with Boolean logic" — should **stay**: guideline 4.3 is
  about undisclosed clones, and stating the lineage is the opposite of that.
  The other two are worth a look, the cross-promo especially, since it points
  App Store users at a web game. Not touched, because they are the site's copy
  as much as the app's.

## AI Attribution

**No AI attribution.** Do not append `Co-Authored-By: Claude …`, "Generated
with …", or any similar trailer to commit messages, PR bodies, or release
notes. If your tooling adds such a line by default, remove it before
committing.
