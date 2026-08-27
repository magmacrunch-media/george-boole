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

#: The plain title, and the fallback when the block face will not fit.
BANNER = "GEORGE BOOLE HAS ENTERED THE CHAT"
SUBTITLE = "a command-line-only Boolean puzzle"

#: Drawn in :mod:`texastoast.ui.bigtext` when there is room. The full banner
#: is 33 characters and would be 164 columns in block letters, so the block
#: face carries the name alone and the strapline stays beneath it in text.
BIG_TITLE = "GEORGE BOOLE"
#: The block title costs two rows more than the plain one, and the mode menu
#: is eight rows of list plus its box. Below this the plain banner is drawn
#: instead, which is what keeps the screen usable at MENU_MIN_ROWS.
BIG_TITLE_MIN_ROWS = MENU_MIN_ROWS + 3


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
