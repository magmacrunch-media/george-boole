# George Boole Has Entered The Chat — terminal version

The third sibling to `web/` (adenosine, browser) and `wii/` (magnolia, C99).
Runs entirely in a shell — no graphics, just characters — in the tradition of
AsciiPatrol, Cataclysm:DDA and the rest of the command-line-only canon.

```
pip install -e .
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

### One known difference from `web/`

The web build has a **gold "personal best" tile** (`personalBestBoard` in
`game.js`, 14 references). The Wii build does not have it, and neither does
this one — it was not in the source these rules were ported from. That is a
pre-existing divergence between `web/` and `wii/`, not something introduced
here; per the repo's `AGENTS.md` rule that a gameplay change lands in every
version, it is worth resolving in one direction or the other.

The **rainbow tile** — the tile that earned a Gauntlet promotion — is in both
`web/` and `wii/`, and is here too.

## Not ported

`board_move()` on the Wii also fills in a `TileMove` list recording where every
tile came from, so the renderer can slide tiles instead of teleporting them. It
is written but never read by the rules, and a terminal redrawing a 4x4 grid
does not animate, so it is omitted. Omitting it cannot change behaviour.
