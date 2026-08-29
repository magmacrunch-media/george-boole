"""Palette and layout, in character cells.

Split out so :mod:`boole.scenes` and :mod:`boole.app` can share it without
importing each other. Nothing here imports the engine.

Every measurement is **cells**, not pixels. The engine's widgets take their
layout metrics as constructor arguments for exactly this reason — the numbers
below are what a terminal wants, where the defaults are what a canvas wants.
"""

from __future__ import annotations

BOARD_SIZE = 4

# One tile is 7x3 cells with a one-cell gutter. Values run to 255 in byte mode,
# so 7 wide is the narrowest that keeps three digits off the edges.
TILE_W = 7
TILE_H = 3
GAP = 1
GRID_W = BOARD_SIZE * TILE_W + (BOARD_SIZE - 1) * GAP
GRID_H = BOARD_SIZE * TILE_H + (BOARD_SIZE - 1) * GAP

PANEL_W = 22
MARGIN_X = 3
TOP = 2
#: Derived, so the minimum size cannot drift from where things are drawn.
PANEL_X = MARGIN_X + GRID_W + 3
FOOTER_Y = TOP + GRID_H + 1

#: Smallest terminal the board fits in. Below this it is not drawn at all — a
#: half-clipped grid is worse than being told to resize.
MIN_COLS = PANEL_X + PANEL_W
MIN_ROWS = FOOTER_Y + 2

#: The menu is the smaller screen, so it sets its own floor.
MENU_MIN_COLS = 44
MENU_MIN_ROWS = 18

# Menu geometry, in cells. Passed to the engine's Menu widget in place of its
# pixel defaults (280 wide, 32-cell rows), which would sit entirely off-screen.
MENU_W = 36
MENU_ITEM_H = 1
MENU_TITLE_H = 2
MENU_PAD = 1
MENU_BORDER = 1

BG = "#12101f"
PANEL_LABEL = "#6b6b8f"
PANEL_VALUE = "#e8e8f4"
TITLE = "#f59e0b"
DIM = "#4a4a6a"
EMPTY_TILE = "#221c33"
GATE_BG = "#0e4f5c"
GATE_FG = "#67e8f9"
OVER_FG = "#ff6b6b"
MENU_BOX = "#1b1730"
MENU_SELECTED = "#f59e0b"
MENU_SELECTION_BG = "#33234d"

# The lava ramp, coolest to hottest. A value is placed on it by its position
# within the *current* bit width, so every mode uses the whole ramp rather than
# byte mode living permanently at the cool end.
RAMP = (
    ("#3b1d5e", "#c4b5fd"),
    ("#5b21a6", "#ddd6fe"),
    ("#7e22ce", "#f3e8ff"),
    ("#a21caf", "#fce7f3"),
    ("#be123c", "#ffe4e6"),
    ("#dc2626", "#fee2e2"),
    ("#ea580c", "#fff7ed"),
    ("#f59e0b", "#1c1917"),
    ("#fbbf24", "#1c1917"),
    ("#fde047", "#1c1917"),
)

#: Cycled for the Gauntlet tile that earned a promotion.
RAINBOW = ("#ff5f5f", "#ffaf5f", "#ffff5f", "#5fff87", "#5fd7ff", "#af87ff")

# The personal-best tile: the one holding the best value ever built by merging.
#
# The web plates it with a 135° gradient that sweeps across itself every 2.5s;
# the Wii, which has no shimmer, settles for a flat #ffd700. A terminal can
# move, so it takes the web's treatment rather than the Wii's — a sweeping
# background-position, seen from one tile, is the tile changing colour.
#
# Only the gradient's *bright* half is used, and that is deliberate. The web's
# dark stops (#8b6914) are shading at the corners of a gradient and are never
# the whole tile; a cell has one colour, so here a dark stop would be the whole
# tile for a quarter of every cycle. Two things break when it is:
#
#   - #3a2000 on #8b6914 is 3.0:1, and the number stops being readable;
#   - #8b6914 is dimmer than most of RAMP, so the best tile on the board spends
#     part of each second looking duller than a lesser one beside it. Same
#     mistake as a starfield louder than the ship it is behind.
#
# So the sweep runs #ffd700 -> #ffe87c and back, both the web's own stops, with
# one interpolated step to keep it from reading as a blink. Every stop clears
# 10:1 against the text and outshines every tile colour except RAMP's very top
# step, which in practice this tile is the one wearing.
GOLD = ("#ffd700", "#ffdd3f", "#ffe87c", "#ffdd3f")
GOLD_FG = "#3a2000"
#: Frames per shimmer step. Four steps at 20fps is 2.4s, the web's 2.5s as
#: near as a whole number of frames gets.
GOLD_PERIOD = 12

#: The plain title, and the last fallback when no block face will fit.
BANNER = "GEORGE BOOLE HAS ENTERED THE CHAT"
SUBTITLE = "a command-line-only Boolean puzzle"

#: How the name is set, best first: the block text, and whatever is left of
#: the name in plain text beneath it. The whole name is on screen in every
#: rung - what changes is how much of it is drawn rather than typed.
#:
#: Both come from magmacrunch.com. The puzzles card breaks the name over three
#: lines (``GEORGE BOOLE<br>HAS ENTERED<br>THE CHAT``); the game's own title
#: card sets ``GEORGE BOOLE`` large with ``HAS ENTERED THE CHAT`` under it.
TITLE_LADDER = (
    ("GEORGE BOOLE\nHAS ENTERED\nTHE CHAT", ""),
    ("GEORGE BOOLE", "HAS ENTERED THE CHAT"),
)


def tile_colors(value: int, max_value: int, *,
                empty: int = 0, gate: bool = False) -> tuple[str, str]:
    """Background and foreground for a tile, by where it sits in the width."""
    if value == empty:
        return EMPTY_TILE, EMPTY_TILE
    if gate:
        return GATE_BG, GATE_FG
    span = max(1, max_value)
    idx = min(len(RAMP) - 1, (value - 1) * len(RAMP) // span)
    return RAMP[idx]
