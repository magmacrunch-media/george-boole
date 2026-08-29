# George Boole Has Entered The Chat — terminal version

The third sibling to `web/` (adenosine, browser) and `wii/` (magnolia, C99).
Runs entirely in a shell — no graphics, just characters — in the tradition of
AsciiPatrol, Cataclysm:DDA and the rest of the command-line-only canon.

```
pipx install magmacrunch-george-boole
george-boole
```

`pipx` rather than `pip` because it puts the command on your PATH in
its own virtualenv; plain `pip install` only reaches your PATH inside an
activated venv. It is also a cabinet in the
[magmacrunch](https://pypi.org/project/magmacrunch/) arcade — `pipx install magmacrunch`
gets this and the other two — and plays identically either way.

For working on it:

```
pip install -e ".[dev]"
python -m boole          # or the installed `george-boole` command
```

Published as **`magmacrunch-george-boole`** — prefixed because PyPI has no
scoping like the npm `@magmacrunch/…` packages, and unprefixed names get
taken (`adenosine` and `magnolia` both already belong to someone else there).
The import package stays plain `boole`.

That opens the title screen, where you pick one of the eight modes. Naming a
mode is an instruction to play it, so `--mode` skips straight into a game:

```
python -m boole --mode gauntlet
python -m boole --mode byte --seed 42     # a reproducible run
```

**How to play** is the last row of the mode list, or `H` from anywhere on the
title screen. It carries the browser build's quick rules and a gate table —
the gates are in the HUD during a game, but the HUD is not where you go to
find out what they mean. It scrolls, because the rules are longer than a
standard terminal is tall.

**High scores** are kept on disk, so a record outlives the session. One board
for the whole game with the mode on each row, rather than eight — crumb and
byte are not different games, they are the same game at different widths, and a
single ranked list says which width somebody was brave enough to play at. Filed
under `george-boole`, the same key the browser build posts to. Reach it from the
menu or with `B`.

**On the title screen**

| key | |
|---|---|
| ↑ ↓ / W S | choose a mode |
| Enter | start |
| `2`–`8`, `G` | jump straight to a mode |
| `Q` | quit |

**In a game**

| key | |
|---|---|
| arrows / WASD | move |
| `R` | restart this mode |
| `Esc` | back to the mode menu |
| `Q` | quit |

Best scores are kept per mode for as long as the process runs, and shown on
both screens.

Needs a terminal at least 59x20 for the board, 44x18 for the menu. Below that
it says so rather than drawing a clipped screen. Truecolor is used for the
value ramp but not required.

## Launchable by an arcade

The game declares itself through an entry point, so anything enumerating
`magmacrunch.games` finds it:

```toml
[project.entry-points."magmacrunch.games"]
george-boole = "boole.arcade:GAME"
```

It does not own the terminal. A `texastoast.core.tui_host.TuiHost` does, and
`BooleApp` is handed one — which is what lets the same code run as its own
command and be seated by a launcher without knowing which happened. Esc from
the mode menu ends a standalone session and returns to the arcade menu under a
launcher, and the game does not have to know the difference: it pops a scene
and the host decides what that means.

## How it is built

The engine is [texastoast](../../texastoast) with its terminal backend
(`pip install "texastoast[tui]"`, which this package depends on). The game
draws through texastoast's `Renderer`/`UISurface` protocols and never touches a
terminal library directly, so the planned hand-written ANSI backend will be a
swap rather than a rewrite.

```
boole/
  board.py   the Boolean rules — pure Python, no engine, no terminal
  modes.py   bit modes and their tuning tables
  theme.py   palette and layout, in character cells
  scenes.py  MenuScene and GameScene — the two screens
  app.py     wiring: the game, the renderer, the scene stack
tests/
  test_board.py   the rule set, pinned
  test_app.py     the screens, driven headlessly
```

`board.py` and `modes.py` import nothing outside the standard library. That is
enforced by a test, and it is what lets the rules be checked in under a second.

**Modality is the stack, not a flag.** `MenuScene` sits at the bottom of a
`SceneStack`; choosing a mode pushes a `GameScene` on top, and Esc pops back.
Nothing anywhere holds an `in_menu` boolean — a game that has been popped
stops receiving frames because the stack does not call it, which is the rule
the engine's `scene.py` exists to enforce.

The mode menu is the engine's own `texastoast.ui.Menu`, given layout metrics
in cells instead of its pixel defaults. Navigation, selection and the callbacks
are the widget's; only the numbers and the palette are the game's.

## The rules came from `wii/`, not `web/`

`wii/source/board.c` is the version of these rules already separated from its
renderer, and it was checked against the web game's own assertions when it was
written. `web/js/game.js` has the same rules tangled through ~25 `document.*`
call sites and a constructor that caches DOM nodes, so porting from it would
have meant extracting the logic first.

`tests/test_board.py` is `wii/tests/test_board.c`'s assertion table, ported.
All three builds have to agree on every one of these or the same game plays
differently in three places, and that divergence is invisible until a player
notices.

### The gold personal-best tile, and how it differs from `web/`

The tile holding the best value ever built by merging is plated gold, and it
shimmers — the web sweeps a gradient across it every 2.5s, and a cell that can
only be one colour at a time does the same sweep by changing colour. Only the
bright half of the web's gradient is used: its dark stops are corner shading
that is never the whole tile there, and here they would be, which both makes
the number hard to read and leaves the best tile on the board looking duller
than a lesser one beside it. `tests/test_app.py` pins both as ratios.

Which tile gets it is asked of the **value** — `Board.is_personal_best` — the
way `wii/source/render.c` asks it, rather than tracked as a parallel board of
booleans that slides and merges alongside the values the way `web/js/game.js`
does. So the web golds whichever tile reached the value first, and this golds
every tile holding it. Cosmetic: the height bonus is the same in all three.

Asking about the value cannot accidentally gild a *spawned* tile, which is the
case the web's implementation is careful about. `tests/test_board.py` checks it
exhaustively rather than by argument: every value every spawn table can hand
out, at every width, against that width's height floor.

The **rainbow tile** — the tile that earned a Gauntlet promotion — is in all
three, and takes precedence over the gold when one tile is both.

## Not ported

`board_move()` on the Wii also fills in a `TileMove` list recording where every
tile came from, so the renderer can slide tiles instead of teleporting them. It
is written but never read by the rules, and a terminal redrawing a 4x4 grid
does not animate, so it is omitted. Omitting it cannot change behaviour.
