"""The terminal front end — everything that knows about drawing or keys.

Written against texastoast's ``Renderer``/``UISurface`` protocols, not against
Textual. Nothing here reaches for a terminal library, which is what makes the
planned hand-written ANSI backend a swap rather than a rewrite.

The rules live in :mod:`boole.board`; this module never reimplements one.
"""

from __future__ import annotations

import random

from texastoast.core.tui_game import TuiGame, TuiInput

from boole import modes
from boole.board import (
    BOARD_SIZE,
    GATE_AND,
    GATE_NAMES,
    GATE_NOT,
    GATE_OR,
    GATE_XOR,
    TILE_EMPTY,
    Board,
    Direction,
    gate_symbol,
    is_gate,
)

FPS = 20

# One tile is 7x3 cells with a one-cell gutter: 31x15 for the grid. Values run
# to 255 in byte mode, so 7 wide is the narrowest that keeps three digits from
# touching the edges.
TILE_W = 7
TILE_H = 3
GAP = 1
GRID_W = BOARD_SIZE * TILE_W + (BOARD_SIZE - 1) * GAP
GRID_H = BOARD_SIZE * TILE_H + (BOARD_SIZE - 1) * GAP

PANEL_W = 22
MARGIN_X = 3
TOP = 2
#: Where the stats panel starts. Derived, so the minimum size below cannot
#: drift away from where the panel is actually drawn.
PANEL_X = MARGIN_X + GRID_W + 3
FOOTER_Y = TOP + GRID_H + 1

#: Smallest terminal the layout fits in. Below this the board is not drawn at
#: all — a half-clipped grid is worse than being told to resize.
MIN_COLS = PANEL_X + PANEL_W
MIN_ROWS = FOOTER_Y + 2

BG = "#12101f"
PANEL_LABEL = "#6b6b8f"
PANEL_VALUE = "#e8e8f4"
TITLE = "#f59e0b"
DIM = "#4a4a6a"
EMPTY_TILE = "#221c33"
GATE_BG = "#0e4f5c"
GATE_FG = "#67e8f9"
OVER_FG = "#ff6b6b"

# The lava ramp, coolest to hottest. A value is placed on it by its position
# within the current bit width, so every mode uses the whole ramp rather than
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

# Cycled through for the Gauntlet tile that earned a promotion.
RAINBOW = ("#ff5f5f", "#ffaf5f", "#ffff5f", "#5fff87", "#5fd7ff", "#af87ff")

HELP = (
    ("←↑↓→ / WASD", "move"),
    ("R", "restart"),
    ("M", "next mode"),
    ("2-8, G", "pick mode"),
    ("Q", "quit"),
)


def tile_colors(value: int, max_value: int) -> tuple[str, str]:
    """Background and foreground for a tile, by where it sits in the width."""
    if value == TILE_EMPTY:
        return EMPTY_TILE, EMPTY_TILE
    if is_gate(value):
        return GATE_BG, GATE_FG
    span = max(1, max_value)
    idx = min(len(RAMP) - 1, (value - 1) * len(RAMP) // span)
    return RAMP[idx]


class BooleApp:
    """Board, mode selection, and the render pass."""

    def __init__(self, mode_key: str = "nibble", seed: int | None = None):
        self.rng = random.Random(seed)
        self.mode = modes.MODES_BY_KEY.get(mode_key, modes.MODES_BY_KEY["nibble"])
        self.board = Board(bits=self.mode.start_bits, gauntlet=self.mode.gauntlet)
        self.best = 0
        self.over = False
        self.frame = 0
        self.flash = ""

        # hold_ms=0 gives edge semantics — one keystroke, one move. A decay
        # timer here would turn a single arrow press into a slide across the
        # board, because a terminal reports repeats but never releases.
        self.game = TuiGame(title="George Boole Has Entered The Chat",
                            fps=FPS, input_source=TuiInput(hold_ms=0))
        self.r = self.game.renderer
        self.game.set_update(self.update)
        self.game.set_render(self.render)

        self.restart()

    # ── Game flow ───────────────────────────────────────────────────

    def restart(self) -> None:
        self.board = Board(bits=self.mode.start_bits, gauntlet=self.mode.gauntlet)
        self.over = False
        self.flash = ""
        # Two tiles to open with, as every version does.
        self.board.spawn(self.rng.getrandbits(32))
        self.board.spawn(self.rng.getrandbits(32))
        self.board.spawn_at = (-1, -1)

    def set_mode(self, mode: modes.Mode) -> None:
        self.mode = mode
        self.best = 0
        self.restart()

    def next_mode(self) -> None:
        idx = modes.MODES.index(self.mode)
        self.set_mode(modes.MODES[(idx + 1) % len(modes.MODES)])

    def do_move(self, direction: Direction) -> None:
        if self.over:
            return
        if not self.board.move(direction):
            # A move that changes nothing is not a move — but if nothing can
            # change in any direction, the run is over and the player is owed
            # the banner. Normally caught below, after the spawn; this covers a
            # board that arrived here already dead.
            if self.board.game_over():
                self.over = True
            return

        # In Gauntlet, a merge that reached the ceiling promotes the width; the
        # tile that earned it still holds the *old* ceiling at this point,
        # before the spawn lands. Mark it so the render pass can cycle its hue.
        if self.board.last_upgraded:
            old_max = modes.max_value(self.board.bits - 1)
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if self.board.cells[r][c] == old_max:
                        self.board.rainbow_at = (r, c)
                        break
                if self.board.rainbow_at != (-1, -1):
                    break

        self.flash = self._describe(self.board)
        self.board.spawn(self.rng.getrandbits(32))
        self.best = max(self.best, self.board.score)
        if self.board.game_over():
            self.over = True

    @staticmethod
    def _describe(board: Board) -> str:
        """One line about what the last move was worth."""
        if not board.last_gained and not board.last_upgraded:
            return ""
        parts = [f"+{board.last_gained}"]
        if board.last_overflow_bonus:
            parts.append(f"OVERFLOW +{board.last_overflow_bonus}")
        if board.last_height_bonus:
            parts.append(f"NEW HIGH +{board.last_height_bonus}")
        if board.last_upgraded:
            parts.append(f"PROMOTED TO {board.bits}-BIT")
        return "   ".join(parts)

    # ── Input ───────────────────────────────────────────────────────

    MOVES = {
        "left": Direction.LEFT, "a": Direction.LEFT,
        "right": Direction.RIGHT, "d": Direction.RIGHT,
        "up": Direction.UP, "w": Direction.UP,
        "down": Direction.DOWN, "s": Direction.DOWN,
    }

    def update(self, dt: float) -> None:  # noqa: ARG002
        self.frame += 1
        for key in self.game.input.drain():
            if key in ("q", "escape"):
                self.game.quit()
                return
            if key == "r":
                self.restart()
            elif key == "m":
                self.next_mode()
            elif key == "g":
                self.set_mode(modes.MODES_BY_KEY["gauntlet"])
            elif key in "2345678" and len(key) == 1:
                for mode in modes.MODES:
                    if not mode.gauntlet and mode.start_bits == int(key):
                        self.set_mode(mode)
                        break
            elif key in self.MOVES:
                self.do_move(self.MOVES[key])

    # ── Render ──────────────────────────────────────────────────────

    def render(self) -> None:
        r = self.r
        r.clear()
        r.draw_rect(0, 0, r.width, r.height, BG)

        if r.width < MIN_COLS or r.height < MIN_ROWS:
            r.ui_text(1, 1,
                      f"terminal too small — need {MIN_COLS}x{MIN_ROWS}, "
                      f"have {r.width}x{r.height}",
                      fill=OVER_FG)
            r.present()
            return

        self._draw_title()
        self._draw_grid()
        self._draw_panel()
        self._draw_footer()
        r.present()

    def _draw_title(self) -> None:
        self.r.ui_text(MARGIN_X, 0, "GEORGE BOOLE HAS ENTERED THE CHAT", fill=TITLE)

    def _draw_grid(self) -> None:
        r = self.r
        board = self.board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = MARGIN_X + col * (TILE_W + GAP)
                y = TOP + row * (TILE_H + GAP)
                value = board.cells[row][col]
                bg, fg = tile_colors(value, board.max_value)

                if (row, col) == board.rainbow_at:
                    # Earned the Gauntlet promotion: cycle the hue so it reads
                    # as different in kind, not just a bright number.
                    bg = RAINBOW[(self.frame // 3) % len(RAINBOW)]
                    fg = "#1c1917"

                r.ui_rect(x, y, TILE_W, TILE_H, fill=bg)
                if value == TILE_EMPTY:
                    continue

                label = gate_symbol(value) if is_gate(value) else str(value)
                r.ui_text(x + TILE_W // 2, y + TILE_H // 2, label,
                          fill=fg, anchor="center")

    def _draw_panel(self) -> None:
        r = self.r
        board = self.board
        x = PANEL_X
        y = TOP

        def stat(label: str, value: str) -> None:
            nonlocal y
            r.ui_text(x, y, label, fill=PANEL_LABEL)
            r.ui_text(x + PANEL_W - 2, y, value, fill=PANEL_VALUE, anchor="ne")
            y += 1

        stat("SCORE", f"{board.score}")
        stat("BEST", f"{self.best}")
        y += 1
        stat("MODE", self.mode.name)
        stat("WIDTH", f"{board.bits}-bit")
        stat("CEILING", f"{board.max_value}")
        stat("HIGHEST", f"{board.highest_value()}")
        y += 1

        r.ui_text(x, y, "GATES", fill=PANEL_LABEL)
        y += 1
        for gate in (GATE_XOR, GATE_OR, GATE_AND, GATE_NOT):
            r.ui_text(x, y, f" {gate_symbol(gate)}  {GATE_NAMES[gate]}", fill=GATE_FG)
            y += 1

    def _draw_footer(self) -> None:
        r = self.r
        y = FOOTER_Y

        if self.over:
            r.ui_text(MARGIN_X, y,
                      f"GAME OVER — {self.board.score} points.  R to restart.",
                      fill=OVER_FG)
        elif self.flash:
            r.ui_text(MARGIN_X, y, self.flash, fill=TITLE)

        keys = "   ".join(f"{k} {what}" for k, what in HELP)
        r.ui_text(MARGIN_X, y + 1, keys, fill=DIM)


def run(mode_key: str = "nibble", seed: int | None = None) -> None:
    BooleApp(mode_key, seed).game.start()
