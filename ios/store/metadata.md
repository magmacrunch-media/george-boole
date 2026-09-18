# App Store Connect: what to paste where

Every field App Store Connect asks for, written out, so the submission is a
copy-and-paste rather than a writing session at the moment you least want one.
Limits are Apple's and are counted, not estimated — `tools/check-metadata.mjs`
fails if any field here is over. Each field is the indented block under its
heading and is pasted exactly as it stands, line breaks included, so the
single-line fields are single lines here however long that makes them.

Nothing in here may promise something the build does not do. Two claims in
particular are load-bearing and are checked by the build itself: the app makes
no network requests, and it has no ads, tracking, accounts or purchases. See
`ios/AGENTS.md` if either ever changes.

---

## Name (30)

    George Boole: Logic Gates

The character's name carries the icon, the splash and the site; "Logic Gates"
is what somebody actually searches for. Alternative if a shorter name is ever
wanted: `George Boole`.

## Subtitle (30)

    Slide tiles, learn logic

## Category

Primary **Games › Puzzle**. Secondary **Games › Board**.

Education is tempting and is the wrong call: it competes with school apps, and
the App Store's Education category expects curriculum. The game teaches by
being a puzzle, which is a puzzle app's job.

## Promotional text (170)

Editable without a new build, so this is the field to change for a sale, an
update or a mention.

    Now with the gate codex: every logic gate you use is recorded with its truth table, the moment you first used it, and the chip that does the same job in real hardware.

## Description (4000)

    Slide the tiles. Every number is binary, and the gates do the rest.

    George Boole is a sliding-tile puzzle about the four logic gates that
    every computer is built from. Push two numbers together across an XOR tile
    and they combine bit by bit. Push them through OR, AND or NOT and you get
    something else. Points come from what the gates compute, so the way to
    score is to understand what they do — and you learn that by playing, not
    by reading a manual.

    THE GATES
    XOR keeps the bits that differ. OR keeps every bit that is set. AND keeps
    only the bits both numbers share. NOT flips all of them at once, and
    flipping the highest number in a mode overflows the tile for the biggest
    payout in the game.

    SHOW THE MATH
    Turn it on and every point is worked out in front of you: the two numbers
    in binary, column by column, and the result. It is the same arithmetic a
    processor does, at a speed you can actually watch.

    THE GATE CODEX
    Each gate you use is recorded with its truth table, the rows you have
    actually played lit up and counted, your first use of it worked out in
    full, and the real 74-series chip that does the same job in hardware.
    Seven discoveries wait for the moments that show a gate's character: XOR a
    number with itself and get nothing back, AND two numbers that share no
    bits, fire two gates in one swipe.

    EIGHT WAYS TO PLAY
    Start at 2-bit, where the ceiling is 3 and a game lasts a minute. Work up
    through nibble, hexad and byte, where the ceiling is 255 and the board
    fills faster than you can clear it. Or take the Gauntlet, which starts
    narrow and promotes you a bit at a time until it stops.

    BUILT TO BE PLAYED ANYWHERE
    No internet connection. No ads. No accounts. No purchases of any kind.
    Nothing is collected about you, and the app makes no network requests at
    all. Your best scores stay on your device; Game Center handles the
    leaderboards and achievements if you want them, and the whole game works
    the same if you never sign in.

    Named for George Boole (1815-1864), who worked out the algebra of true and
    false a century before anyone built a machine that needed it.

## Keywords (100)

Comma-separated, no spaces — a space costs a character and buys nothing.
"2048" is deliberately absent: the credits state the lineage, which is the
opposite of a clone, but bidding on another app's name in the keyword field is
read differently, and Apple applies that distinction.

    logic,gate,binary,boolean,xor,bitwise,puzzle,brain,number,merge,tile,retro,pixel,offline,stem

## What's New (4000)

For 1.0 this field is not shown, so it only matters from the first update. The
1.0 text, if a version of it is wanted:

    First release.

## Support URL

    https://magmacrunch.com/support/george-boole/

## Marketing URL

    https://magmacrunch.com/arcade/george-boole/

The browser version, which is the honest "learn more" page and also shows a
reviewer the game is not a repackaged template.

## Copyright

    2026 magmacrunch media

## Age rating

Everything **None** / **No**, which gives **4+**. Three answers are worth
being deliberate about:

- **Simulated Gambling: None.** A score leaderboard is not gambling, and this
  is the question score games get wrong.
- **User Generated Content: No.** The chat widget the website carries is
  dropped from this bundle, which is what makes the answer clean.
- **Unrestricted Web Access: No.** There is no browser in the app; the credits
  link opens Safari.

Do **not** opt into the Kids Category: Game Center is not permitted there.

## App privacy

**Do you collect data? No.** One question, one answer. Game Center data goes
to Apple under the player's own account, not to us, and `localStorage` never
leaves the device. Privacy Policy URL is
`https://magmacrunch.com/privacy/george-boole/`. Both are per-app: `/privacy/`
and `/support/` are indexes, so a second app gets its own pages rather than
editing these.

## Export compliance

`ITSAppUsesNonExemptEncryption` is already `false` in `Info.plist`, so App
Store Connect stops asking on every upload.

## Review notes

The reviewer's likely objection is guideline 4.2 — a web game in a wrapper —
so this answers it before it is raised, in the reviewer's own terms.

    George Boole is fully playable offline and needs no account, no sign-in
    and no network connection. The app makes no network requests of any kind:
    every asset is in the bundle, and our build fails if any asset references
    an external URL.

    Native integration: Game Center for leaderboards and achievements, the
    Taptic Engine for feedback on every move, merge, overflow and game over,
    and a safe-area layout that fits the notch and the home indicator --
    portrait on iPhone, rotating on iPad.

    Game Center is optional. The game is identical if you decline the sign-in
    prompt — scores are then kept on the device only — so there is no need to
    sign in to review the app.

    To see the whole game quickly: tap TAP TO START, then SELECT MODE, then
    4-BIT. Swipe in any direction to slide the tiles. "GATE CODEX" on the
    rules screen shows the logic gates you have used, and "show the math" in
    Settings works every score out in binary as you play.

    The credits screen states that the game is inspired by Gabriele Cirulli's
    2048 (2014) and reimagined with Boolean logic. The lineage is disclosed
    deliberately; the rules, scoring and subject matter are our own.
