# George Boole — agent brief

One game, three versions, one repo:

- `web/` — browser version (adenosine engine, plain JS). Source of truth for
  rules and balance. Deployed by the website repo: run
  `make sync-george-boole` there to copy `web/` into `arcade/george-boole/`.
  Never edit the website repo's copy directly — it gets overwritten.
- `wii/` — Wii port (magnolia engine, C99). Has its own `AGENTS.md` with build
  and porting detail. Expects magnolia checked out beside this repo.
- `tui/` — terminal version (texastoast engine, Python + its `[tui]` backend).
  `python -m boole`. Has its own `README.md`.

A gameplay change is not done until all three versions have it (or the commit
says why one is skipped). `web/js/` is the reference the Wii port was checked
against.

## Where the rules live in each version

| | rules | rendering |
|---|---|---|
| `web/` | `js/game.js` — tangled with ~25 `document.*` call sites | same file |
| `wii/` | `source/board.c`, `source/modes.c` | `source/render.c`, `screens.c` |
| `tui/` | `boole/board.py`, `boole/modes.py` — pure, no engine import | `boole/app.py` |

**`wii/source/board.c` is the best reference to port from**, not `web/js/game.js`
— it is the same rules already separated from a renderer, and it was checked
against the web game's own assertions when it was written. The TUI version was
ported from it for that reason.

The assertion table exists three times and must agree everywhere:
`web/tests/test-game-logic.js` → `wii/tests/test_board.c` → `tui/tests/test_board.py`.
Adding a rule means adding it to all three.

## Known divergence — the gold "personal best" tile

`web/js/game.js` has a `personalBestBoard` marking the tile that first reached a
new personal-best value (14 references). **`wii/` does not have it, and neither
does `tui/`.** This predates the TUI port — it was already missing from the Wii
version, so the TUI inherited the gap by porting from `board.c`.

Per the rule above this should be resolved in one direction: either port it to
`wii/` and `tui/`, or drop it from `web/`. It is flagged here so it is not
rediscovered a fourth time.

The **rainbow tile** (the tile that earned a Gauntlet promotion) *is* in all
three. Note it only appears when a *merge* lands on the ceiling — NOT-of-ceiling
also promotes, but clears the tile, so there is nothing left to mark.

## `tui/LICENSE` and `tui/NOTICE` are copies

The originals are at the repo root, where they cover `web/` and `wii/` too.
The copies exist because the wheel is built from `tui/` and PolyForm requires
the notice to travel with the distribution — a wheel built from a subdirectory
cannot reach a file above it, and `force-include` does not help because
`python -m build` builds the wheel from an unpacked sdist that has no parent.

**Relicensing means changing all three copies**, here and in
`texas-holdem-lava-dome/tui/`. Nothing checks this automatically.
