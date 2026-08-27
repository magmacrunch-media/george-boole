"""The two screens, as scenes.

Modality is the stack, not a flag — the engine's own rule. `MenuScene` sits at
the bottom; choosing a mode pushes a `GameScene` on top of it, and Esc pops
back. Nothing needs an ``in_menu`` boolean, and the menu cannot be updated
while a game is on top of it because the stack will not call it.

Both scenes draw through the engine's ``Renderer``/``UISurface`` protocols and
neither knows what Textual is.
"""

from __future__ import annotations

import random
import textwrap
from dataclasses import replace

from texastoast.ui import DEFAULT_THEME, Menu, bigtext

from boole import modes, theme
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

GAME_HELP = (
    ("←↑↓→/WASD", "move"),
    ("R", "restart"),
    ("Esc", "modes"),
    ("Q", "quit"),
)

#: The order the gate table is drawn in: the three that combine two
#: numbers, then the one that sandwiches.
GATE_ORDER = (GATE_XOR, GATE_OR, GATE_AND, GATE_NOT)

MENU_HELP = "↑↓ choose    Enter start    H how to play    Q quit"

#: The label the mode menu carries under the eight modes. It is not a mode, so
#: MenuScene._chose has to tell it apart by index rather than by name.
HOW_TO_PLAY = "how to play"

#: Ported from the "quick rules" panel in web/index.html, which is what a
#: browser player reads. Kept as the same four headings in the same order, so
#: someone who learned the game there recognises this.
RULES = (
    ("MOVES", (
        "Arrow keys or WASD. Every tile slides one direction at once.",
    )),
    ("MERGING", (
        "Same value and same value make the same value again — a number "
        "merges with itself and stays put, which is idempotence.",
        "Two different numbers will not merge on their own. They need a gate "
        "between them, and the gate decides what comes out.",
        "NOT is the exception: it sandwiches, sliding into any single number "
        "and inverting it.",
    )),
    ("SCORING", (
        "An operation scores its result. Land one above the halfway mark and "
        "it scores double.",
        "Overflowing the ceiling scores three times the maximum value.",
    )),
    ("OVERFLOW", (
        "Exceeding the mode's maximum awards the bonus and clears the tile "
        "rather than leaving something impossible on the board.",
        "NOT of the maximum is an overflow too — it comes out as zero.",
    )),
    ("GAUNTLET", (
        "Starts at 2-bit and upgrades the whole board every time you reach "
        "the ceiling, climbing to 8-bit. The tile that earned the promotion "
        "keeps a rainbow.",
    )),
)


def _menu_box_top(renderer) -> int:
    """The row the mode menu's box starts on.

    The engine's ``Menu`` centres itself vertically in the surface, so the room
    a title has is not "the height minus everything else" — it is everything
    above where the box lands, and that moves as the window resizes. Working it
    out rather than reserving a fixed number of rows is what stops a tall
    terminal from drawing a title the menu then paints over.
    """
    # The eight modes plus the how-to-play row beneath them. Counted from
    # the same place the menu is built so the two cannot disagree.
    rows = (len(modes.MODES) + 1) * theme.MENU_ITEM_H + 2 * theme.MENU_PAD
    return (renderer.height - rows) // 2 - theme.MENU_BORDER


def _draw_title(renderer, cx: int) -> int:
    """The name, set as large as the window allows. Returns the row below it.

    Every rung shows the *whole* name — a title that fits by dropping half of
    itself is not the title. What the ladder trades away is how much of it is
    drawn in block letters rather than typed, and the last rung is the plain
    banner, because the mode menu is eight rows of list inside a box and a
    title that pushed it off a short terminal would be one nobody could get
    past. See :mod:`texastoast.ui.bigtext`.
    """
    budget = _menu_box_top(renderer) - 1
    for big, rest in theme.TITLE_LADDER:
        needed = bigtext.height(big) + (1 if rest else 0)
        if bigtext.width(big) > renderer.width - 2 or needed > budget:
            continue
        y = 1
        for line in bigtext.lines(big):
            renderer.ui_text(cx, y, line, fill=theme.TITLE, anchor="n")
            y += 1
        if rest:
            renderer.ui_text(cx, y, rest, fill=theme.MENU_SELECTED, anchor="n")
            y += 1
        return y
    renderer.ui_text(cx, 1, theme.BANNER, fill=theme.TITLE, anchor="n")
    return 2


def _too_small(renderer, cols: int, rows: int) -> bool:
    """Say so rather than drawing a clipped screen."""
    if renderer.width >= cols and renderer.height >= rows:
        return False
    renderer.ui_text(
        1, 1,
        f"terminal too small — need {cols}x{rows}, "
        f"have {renderer.width}x{renderer.height}",
        fill=theme.OVER_FG,
    )
    return True


class MenuScene:
    """Title screen and mode chooser.

    ``render_below`` is deliberately *not* set: a game pushed on top covers
    this completely, so drawing underneath it would be wasted work.
    """

    def __init__(self, app):
        self.app = app
        self.menu = Menu(
            app.renderer,
            theme=_menu_theme(),
            # Cells, not pixels. The engine's defaults (280 wide, 32-cell rows)
            # would put the whole widget off-screen here.
            menu_width=theme.MENU_W,
            item_height=theme.MENU_ITEM_H,
            title_height=theme.MENU_TITLE_H,
            item_padding=theme.MENU_PAD,
            border_pad=theme.MENU_BORDER,
            selected_color=theme.MENU_SELECTED,
            normal_color=theme.PANEL_VALUE,
        )
        self._show()

    def _show(self) -> None:
        self.menu.show(
            [self._label(mode) for mode in modes.MODES] + [HOW_TO_PLAY],
            on_select=self._chose,
            # No heading. It used to read "CHOOSE A MODE", which stopped being
            # true when the list gained a row that is not a mode — and losing
            # it reclaims the two rows the new row cost, so the block title
            # still fits an ordinary 80x24 terminal.
            selected=modes.MODES.index(self.app.mode),
        )

    @staticmethod
    def _label(mode: modes.Mode) -> str:
        """``nibble        4-bit   ceiling 15`` — the name alone is cryptic."""
        if mode.gauntlet:
            return f"{mode.name:<9} climbs 2→8-bit"
        return f"{mode.name:<9} {mode.start_bits}-bit   ceiling " \
               f"{modes.max_value(mode.start_bits)}"

    def _chose(self, index: int, label: str) -> None:  # noqa: ARG002
        # The last row is not a mode. Told apart by index rather than by label,
        # because a mode could in principle be named anything.
        if index >= len(modes.MODES):
            self.app.show_rules()
        else:
            self.app.start_mode(modes.MODES[index])

    def on_resume(self) -> None:
        """Re-arm the menu when a game is popped off the top of it.

        ``Menu.confirm()`` hides the menu as it fires the callback, so without
        this the screen underneath comes back empty.
        """
        self._show()

    def handle_key(self, key: str) -> bool:
        if key in ("up", "w", "k"):
            self.menu.move_up()
        elif key in ("down", "s", "j"):
            self.menu.move_down()
        elif key in ("enter", "space"):
            self.menu.confirm()
        elif key == "q":
            self.app.host.quit()
        elif key == "escape":
            # Leave the game, not the process. Run on its own this is the last
            # scene and the session ends; under a launcher the arcade menu is
            # underneath and this returns to it. Same call either way.
            self.app.leave()
        elif key == "h":
            self.app.show_rules()
        elif key == "g":
            self.app.start_mode(modes.MODES_BY_KEY["gauntlet"])
        elif len(key) == 1 and key in "2345678":
            for mode in modes.MODES:
                if not mode.gauntlet and mode.start_bits == int(key):
                    self.app.start_mode(mode)
                    return True
        else:
            return False
        return True

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        r = self.app.renderer
        r.clear()
        r.draw_rect(0, 0, r.width, r.height, theme.BG)
        if _too_small(r, theme.MENU_MIN_COLS, theme.MENU_MIN_ROWS):
            r.present()
            return

        cx = r.width // 2
        y = _draw_title(r, cx)
        r.ui_text(cx, y, theme.SUBTITLE, fill=theme.DIM, anchor="n")

        self.menu.render()

        best = self.app.best.get(self.app.mode.key, 0)
        if best:
            r.ui_text(cx, r.height - 3, f"best in {self.app.mode.name}: {best}",
                      fill=theme.PANEL_LABEL, anchor="n")
        r.ui_text(cx, r.height - 2, MENU_HELP, fill=theme.DIM, anchor="n")
        r.present()


class RulesScene:
    """How to play. Pushed over whatever is showing.

    The text is the browser's "quick rules" panel, in the same order, so a
    player who learned the game there recognises this one. The gate table is
    added because the browser can afford to keep the four gates permanently
    down the side of the page and a terminal cannot — in play they are in the
    HUD, but the HUD is not where you go to find out what they mean.

    **It scrolls rather than truncating.** Laid out at 80 columns the rules run
    to about 31 rows and a standard terminal has 24, so a screen that simply
    stopped would cut off mid-sentence and lose two of the five headings — the
    two a new player most needs, since overflow and Gauntlet are the parts that
    are not obvious from watching the board.
    """

    def __init__(self, app):
        self.app = app
        self.offset = 0

    def handle_key(self, key: str) -> bool:
        if key in ("up", "w", "k"):
            self.offset = max(0, self.offset - 1)
        elif key in ("down", "s", "j"):
            self.offset = min(self._max_offset(), self.offset + 1)
        else:
            self.app.to_menu()
        return True

    def update(self, dt: float) -> None:
        pass

    # -- Content -----------------------------------------------------

    def _lines(self, width: int) -> list[tuple[int, str, str]]:
        """Every line, as ``(indent, text, colour)``.

        Built fresh per render because the wrap depends on the width and a
        terminal is resized constantly.
        """
        out: list[tuple[int, str, str]] = []
        for heading, paragraphs in RULES:
            out.append((0, heading, theme.MENU_SELECTED))
            for paragraph in paragraphs:
                for line in textwrap.wrap(paragraph, max(10, width - 2)):
                    out.append((2, line, theme.PANEL_VALUE))
            out.append((0, "", theme.DIM))
        out.append((0, "GATES", theme.MENU_SELECTED))
        for gate in GATE_ORDER:
            out.append((2, f"{gate_symbol(gate)}  {GATE_NAMES[gate]}",
                        theme.GATE_FG))
        return out

    def _viewport(self) -> int:
        """Rows of text on screen.

        Content runs from row 3 to two rows off the bottom, so the count is the
        height less the heading block above it and the hint row below — five
        rows in total. Getting this wrong by one writes a line of rules over
        the hint, which is how it was first written.
        """
        return max(1, self.app.renderer.height - 5)

    def _max_offset(self) -> int:
        r = self.app.renderer
        return max(0, len(self._lines(r.width - theme.MARGIN_X * 2))
                   - self._viewport())

    # -- Drawing -----------------------------------------------------

    def render(self) -> None:
        r = self.app.renderer
        r.clear()
        r.draw_rect(0, 0, r.width, r.height, theme.BG)
        if _too_small(r, theme.MENU_MIN_COLS, theme.MENU_MIN_ROWS):
            r.present()
            return

        avail = r.width - theme.MARGIN_X * 2
        lines = self._lines(avail)
        viewport = self._viewport()
        # Clamped here as well as in handle_key: a resize can shrink the
        # content out from under an offset that was legal a frame ago.
        self.offset = min(self.offset, max(0, len(lines) - viewport))

        r.ui_text(theme.MARGIN_X, 1, "HOW TO PLAY", fill=theme.TITLE)

        y = 3
        for indent, text, colour in lines[self.offset:self.offset + viewport]:
            if y >= r.height - 2:
                break
            if text:
                r.ui_text(theme.MARGIN_X + indent, y, text, fill=colour)
            y += 1

        more = len(lines) - (self.offset + viewport)
        hint = "↑↓ scroll    any other key goes back" if (
            more > 0 or self.offset) else "any key goes back"
        r.ui_text(theme.MARGIN_X, r.height - 2, hint, fill=theme.DIM)
        if more > 0:
            tail = f"{more} more ↓"
            r.ui_text(r.width - len(tail) - theme.MARGIN_X, r.height - 2,
                      tail, fill=theme.MENU_SELECTED)
        r.present()


class GameScene:
    """The board."""

    MOVES = {
        "left": Direction.LEFT, "a": Direction.LEFT,
        "right": Direction.RIGHT, "d": Direction.RIGHT,
        "up": Direction.UP, "w": Direction.UP,
        "down": Direction.DOWN, "s": Direction.DOWN,
    }

    def __init__(self, app, mode: modes.Mode):
        self.app = app
        self.mode = mode
        self.rng = random.Random(app.seed)
        self.board = Board(bits=mode.start_bits, gauntlet=mode.gauntlet)
        self.over = False
        self.flash = ""
        self.frame = 0
        self.restart()

    # ── Flow ────────────────────────────────────────────────────────

    def restart(self) -> None:
        self.board = Board(bits=self.mode.start_bits, gauntlet=self.mode.gauntlet)
        self.over = False
        self.flash = ""
        # Two tiles to open with, as every version does.
        self.board.spawn(self.rng.getrandbits(32))
        self.board.spawn(self.rng.getrandbits(32))
        self.board.spawn_at = (-1, -1)

    def do_move(self, direction: Direction) -> None:
        if self.over:
            return
        if not self.board.move(direction):
            # A move that changes nothing is not a move — but if nothing can
            # change in any direction, the run is over and the player is owed
            # the banner.
            if self.board.game_over():
                self._end()
            return

        # In Gauntlet, a merge that reached the ceiling promotes the width; the
        # tile that earned it still holds the *old* ceiling at this point,
        # before the spawn lands. Mark it so the render pass can cycle its hue.
        if self.board.last_upgraded:
            old_max = modes.max_value(self.board.bits - 1)
            for row in range(BOARD_SIZE):
                for col in range(BOARD_SIZE):
                    if self.board.cells[row][col] == old_max:
                        self.board.rainbow_at = (row, col)
                        break
                if self.board.rainbow_at != (-1, -1):
                    break

        self.flash = self._describe(self.board)
        self.board.spawn(self.rng.getrandbits(32))
        self.app.record_best(self.mode, self.board.score)
        if self.board.game_over():
            self._end()

    def _end(self) -> None:
        self.over = True
        self.app.record_best(self.mode, self.board.score)

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

    def handle_key(self, key: str) -> bool:
        if key == "q":
            self.app.host.quit()
        elif key == "escape":
            self.app.to_menu()
        elif key == "r":
            self.restart()
        elif key in self.MOVES:
            self.do_move(self.MOVES[key])
        else:
            return False
        return True

    def update(self, dt: float) -> None:  # noqa: ARG002
        self.frame += 1

    # ── Render ──────────────────────────────────────────────────────

    def render(self) -> None:
        r = self.app.renderer
        r.clear()
        r.draw_rect(0, 0, r.width, r.height, theme.BG)
        if _too_small(r, theme.MIN_COLS, theme.MIN_ROWS):
            r.present()
            return

        r.ui_text(theme.MARGIN_X, 0, theme.BANNER, fill=theme.TITLE)
        self._draw_grid()
        self._draw_panel()
        self._draw_footer()
        r.present()

    def _draw_grid(self) -> None:
        r = self.app.renderer
        board = self.board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                x = theme.MARGIN_X + col * (theme.TILE_W + theme.GAP)
                y = theme.TOP + row * (theme.TILE_H + theme.GAP)
                value = board.cells[row][col]
                bg, fg = theme.tile_colors(value, board.max_value,
                                           gate=is_gate(value))

                if (row, col) == board.rainbow_at:
                    # Earned the Gauntlet promotion: cycle the hue so it reads
                    # as different in kind, not just a bright number.
                    bg = theme.RAINBOW[(self.frame // 3) % len(theme.RAINBOW)]
                    fg = "#1c1917"

                r.ui_rect(x, y, theme.TILE_W, theme.TILE_H, fill=bg)
                if value == TILE_EMPTY:
                    continue

                label = gate_symbol(value) if is_gate(value) else str(value)
                r.ui_text(x + theme.TILE_W // 2, y + theme.TILE_H // 2, label,
                          fill=fg, anchor="center")

    def _draw_panel(self) -> None:
        r = self.app.renderer
        board = self.board
        x = theme.PANEL_X
        y = theme.TOP

        def stat(label: str, value: str) -> None:
            nonlocal y
            r.ui_text(x, y, label, fill=theme.PANEL_LABEL)
            r.ui_text(x + theme.PANEL_W - 2, y, value,
                      fill=theme.PANEL_VALUE, anchor="ne")
            y += 1

        stat("SCORE", f"{board.score}")
        stat("BEST", f"{self.app.best.get(self.mode.key, 0)}")
        y += 1
        stat("MODE", self.mode.name)
        stat("WIDTH", f"{board.bits}-bit")
        stat("CEILING", f"{board.max_value}")
        stat("HIGHEST", f"{board.highest_value()}")
        y += 1

        r.ui_text(x, y, "GATES", fill=theme.PANEL_LABEL)
        y += 1
        for gate in (GATE_XOR, GATE_OR, GATE_AND, GATE_NOT):
            r.ui_text(x, y, f" {gate_symbol(gate)}  {GATE_NAMES[gate]}",
                      fill=theme.GATE_FG)
            y += 1

    def _draw_footer(self) -> None:
        r = self.app.renderer
        y = theme.FOOTER_Y

        if self.over:
            r.ui_text(theme.MARGIN_X, y,
                      f"GAME OVER — {self.board.score} points.  "
                      f"R restart   Esc modes",
                      fill=theme.OVER_FG)
        elif self.flash:
            r.ui_text(theme.MARGIN_X, y, self.flash, fill=theme.TITLE)

        keys = "   ".join(f"{k} {what}" for k, what in GAME_HELP)
        r.ui_text(theme.MARGIN_X, y + 1, keys, fill=theme.DIM)


def _menu_theme():
    """The engine's Theme, recoloured to the game's palette.

    ``dataclasses.replace`` because :class:`~texastoast.ui.theme.Theme` is
    frozen — building variants that way is what its docstring asks for.
    """
    return replace(
        DEFAULT_THEME,
        primary=theme.MENU_SELECTED,
        text=theme.PANEL_VALUE,
        dim_text=theme.DIM,
        box_fill=theme.MENU_BOX,
        box_outline=theme.PANEL_LABEL,
        outline_width=1,
        selection_fill=theme.MENU_SELECTION_BG,
    )
