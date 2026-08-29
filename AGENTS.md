# George Boole — agent brief

One game, three versions, one repo:

- `web/` — browser version (adenosine engine, plain JS). Source of truth for
  rules and balance. Deployed by the website repo: run
  `make sync-george-boole` there to copy `web/` into `arcade/george-boole/`.
  Never edit the website repo's copy directly — it gets overwritten.
- `wii/` — Wii port (magnolia engine, C99). Has its own `AGENTS.md` with build
  and porting detail. Expects magnolia checked out beside this repo.
- `tui/` — terminal version (the `magmacrunch.engine` TUI engine, Python).
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

## The gold "personal best" tile — how the three builds differ

All three plate the tile holding the best value ever built by merging, and all
three pay the same height bonus for reaching it (`mode_height_bonus`,
`modes.height_bonus`, the `heightBonus` in `moveLeft`). What differs is only
*which tile* gets the plate when more than one holds that value:

| | how the tile is identified |
|---|---|
| `web/` | a parallel 4x4 boolean board (`personalBestBoard`, 14 references) that slides, merges and rotates alongside the values, so exactly one *instance* is gold |
| `wii/` | `value == b->highest_earned`, asked at draw time (`render.c`) |
| `tui/` | `Board.is_personal_best(value)`, the same predicate as one method instead of three copies |

So the web golds whichever tile got there first; the other two gold every tile
holding that value. The difference is visible only when a value is built twice,
and it is cosmetic — nothing about scoring depends on it.

**Asking about the value cannot gild a spawn**, which is the thing the web's
comments are careful about. `tui/tests/test_board.py` checks it exhaustively:
every value every spawn table can hand out, at every width, against that
width's height floor. Nothing spawns within reach of a floor.

This section used to say the Wii did not have the tile at all and that the TUI
had inherited the gap. That was wrong about the Wii — `render.c` has drawn it
since the repo was restructured — and is now wrong about the TUI too.

The **rainbow tile** (the tile that earned a Gauntlet promotion) is in all
three, and wins over the gold in all three when one tile is both. Note it only
appears when a *merge* lands on the ceiling — NOT-of-ceiling also promotes, but
clears the tile, so there is nothing left to mark.

## `tui/LICENSE` and `tui/NOTICE` are copies

The originals are at the repo root, where they cover `web/` and `wii/` too.
The copies exist because the wheel is built from `tui/` and PolyForm requires
the notice to travel with the distribution — a wheel built from a subdirectory
cannot reach a file above it, and `force-include` does not help because
`python -m build` builds the wheel from an unpacked sdist that has no parent.

**Relicensing means changing all three copies**, here and in
`texas-holdem-lava-dome/tui/`. Nothing checks this automatically.
