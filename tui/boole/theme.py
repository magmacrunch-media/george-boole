"""Palette and layout, in character cells.

Split out so :mod:`boole.scenes` and :mod:`boole.app` can share it without
importing each other. Nothing here imports the engine.

Every measurement is **cells**, not pixels. The engine's widgets take their
layout metrics as constructor arguments for exactly this reason — the numbers
below are what a terminal wants, where the defaults are what a canvas wants.

**Colour is per mode.** Each bit mode wears a console era: 2-bit is a Game Boy,
4-bit is a SNES, 8-bit is a PS1, Gauntlet is the Matrix. That is the joke, it is
what a player who knows the browser version recognises, and until now the TUI
was the one port without it — ``web/`` and ``wii/`` have had it all along.

The values are transcribed from ``wii/source/palette.c``, which is itself
``web/css/themes.css`` flattened into a table indexed by mode. Porting that
table is the third transcription of one set of numbers; re-deriving them from
the stylesheet would be a fourth opinion about what they are. See the repo
AGENTS.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

BOARD_SIZE = 4

# One tile is 7x3 cells with a one-cell gutter. Values run to 255 in byte mode,
# so 7 wide is the narrowest that keeps three digits off the edges.
TILE_W = 7
TILE_H = 3
GAP = 1
GRID_W = BOARD_SIZE * TILE_W + (BOARD_SIZE - 1) * GAP
GRID_H = BOARD_SIZE * TILE_H + (BOARD_SIZE - 1) * GAP

PANEL_W = 22
#: Between the right edge of the grid and the left edge of the panel.
PANEL_GAP = 3
#: The smallest gap kept at the left edge when the board cannot be centred.
MARGIN_X = 3
#: Rows above the grid: the banner, then a blank.
TOP = 2

#: The board and its panel, as one block. Everything below is derived from
#: these so the minimum size cannot drift from where things are drawn.
CONTENT_W = GRID_W + PANEL_GAP + PANEL_W
#: Banner, blank, grid, blank, then the two footer rows.
CONTENT_H = TOP + GRID_H + 1 + 2

#: Smallest terminal the board fits in. Below this it is not drawn at all — a
#: half-clipped grid is worse than being told to resize.
#:
#: One margin, not two. Symmetric margins would read better but would cost
#: three columns of minimum size, and a cabinet that seats in fewer terminals
#: is a worse trade than a board sitting slightly left of centre in the
#: smallest window it runs in at all. Everything roomier is centred properly.
MIN_COLS = CONTENT_W + MARGIN_X
MIN_ROWS = CONTENT_H

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


@dataclass(frozen=True)
class Layout:
    """Where the board's parts land, for one terminal size.

    Built by :func:`layout` rather than kept as constants, because the answer
    moves with the window. Nothing in :mod:`boole.scenes` should work out a
    board coordinate any other way.
    """

    banner_x: int
    banner_y: int
    grid_x: int
    grid_y: int
    panel_x: int
    panel_y: int
    footer_y: int

    def tile(self, row: int, col: int) -> tuple[int, int]:
        """The top-left cell of one tile."""
        return (self.grid_x + col * (TILE_W + GAP),
                self.grid_y + row * (TILE_H + GAP))


def layout(cols: int, rows: int) -> Layout:
    """Centre the block in a terminal of ``cols`` x ``rows``.

    The same arithmetic the arcade floor centres its card grid with. At exactly
    :data:`MIN_COLS` x :data:`MIN_ROWS` this returns the coordinates the board
    was drawn at when it was pinned to the corner, so the smallest supported
    terminal is unchanged and only roomier ones see a difference.
    """
    x = max(MARGIN_X, (cols - CONTENT_W) // 2)
    y = max(0, (rows - CONTENT_H) // 2)
    return Layout(
        banner_x=x,
        banner_y=y,
        grid_x=x,
        grid_y=y + TOP,
        panel_x=x + GRID_W + PANEL_GAP,
        panel_y=y + TOP,
        footer_y=y + TOP + GRID_H + 1,
    )


# ── Colour arithmetic ───────────────────────────────────────────────
#
# Two jobs. Mixing derives the handful of roles a terminal needs that neither
# the stylesheet nor the Wii table has a slot for, so they stay in relation to
# the palette they belong to instead of being two dozen more hand-typed hexes.
# Contrast picks the ink for a tile, which the other two ports get away with
# not doing: the web sets a colour per value and the Wii is read from a sofa,
# but a cell here is one background with one glyph on it, and #ffd700 on PS1's
# silver ramp is a 1.6:1 number nobody can read.


def _rgb(colour: str) -> tuple[int, int, int]:
    return (int(colour[1:3], 16), int(colour[3:5], 16), int(colour[5:7], 16))


def _mix(a: str, b: str, t: float) -> str:
    """``a`` moved ``t`` of the way toward ``b``."""
    return "#{:02x}{:02x}{:02x}".format(
        *(round(x + (y - x) * t) for x, y in zip(_rgb(a), _rgb(b), strict=True))
    )


def _channel(v: float) -> float:
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def luminance(colour: str) -> float:
    """Relative luminance of ``#rrggbb``, per WCAG."""
    r, g, b = (c / 255 for c in _rgb(colour))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio, 1.0 to 21.0."""
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)


#: WCAG AA for body text: help lines, gate names written out as words, and
#: anything else that is a sentence rather than a symbol.
READABLE = 4.5

#: WCAG AA for *large* text, which is what a numeral centred in a seven-by-three
#: block of cells is.
#:
#: The distinction is not a loophole, it is the only way to keep a theme. Game
#: Boy is four shades of one green by design, and against its middle ramp steps
#: nothing in the family clears 4.5 — so at the body-text bar most of that board
#: comes out in #ffffff, which is both off-joke and incoherent beside the two
#: tiles that do keep their green. At the large-text bar the same board reads
#: green numerals on its dark steps and dark ones on its light steps, which is
#: what a Game Boy actually looks like. Nothing is allowed below this.
TILE_READABLE = 3.0


@cache
def _readable(bg: str, candidates: tuple[str, ...], floor: float) -> str:
    """The first candidate that clears ``floor`` on ``bg``, else the best.

    Ordered rather than scored: earlier candidates are the ones that belong to
    the theme, so this takes the most in-family colour that works rather than
    the most contrasting one available.

    Cached because it is asked sixteen times a frame and the answer for a given
    background never changes.
    """
    for colour in candidates:
        if contrast(bg, colour) >= floor:
            return colour
    return max(candidates, key=lambda c: contrast(bg, c))


@dataclass(frozen=True)
class Palette:
    """One mode's colours.

    Field for field the Wii's ``Palette`` struct, minus what a terminal has no
    use for and plus what it does. ``label`` is the theme's ``.score-label``
    out of ``themes.css``, the one role the Wii table has no slot for.
    """

    #: The mode key this belongs to, and the console it is dressed as.
    key: str
    console: str

    bg: str           #: ``board_bg`` — behind the grid, and the screen
    empty_tile: str   #: ``cell_bg``
    tile_text: str    #: ``tile_text`` — the preferred ink for a numeral
    border: str       #: ``border``
    #: ``ramp[5]``, coolest to hottest. Five steps, not one colour per value:
    #: an 8-bit board has 255 of them and no palette survives that, so a value
    #: is placed by its position within the *current* ceiling. Same reasoning
    #: and the same arithmetic as the other two ports.
    ramp: tuple[str, str, str, str, str]
    accent: str       #: ``gate_bg`` — the title, and anything that shouts
    accent_text: str  #: ``gate_text``
    #: ``gate_color[4]``, in ``board.GATES`` order: XOR, OR, AND, NOT.
    gates: tuple[str, str, str, str]
    #: ``.score-label`` from ``themes.css``.
    label: str

    # ── Derived roles ───────────────────────────────────────────────

    @property
    def panel_label(self) -> str:
        """Stat names, beside the values they name.

        The web's ``.score-label`` hue pulled toward the background rather than
        the hue itself. Three of the eight themes set label and value to the
        same colour, which works on a page where one of them is bold and twice
        the size and says nothing in a grid of cells where colour is the whole
        difference.
        """
        return _mix(self.label, self.bg, 0.35)

    @property
    def muted(self) -> str:
        """Key hints and help text: under the labels, as the labels are under
        the values."""
        return _mix(self.label, self.bg, 0.60)

    @property
    def panel_value(self) -> str:
        return self.tile_text

    @property
    def menu_box(self) -> str:
        return _mix(self.bg, self.accent, 0.12)

    @property
    def menu_selection_bg(self) -> str:
        return _mix(self.bg, self.accent, 0.30)

    # ── Tiles ───────────────────────────────────────────────────────

    def ink(self, bg: str) -> str:
        """A legible glyph colour on ``bg``, preferring the theme's own.

        Falls back through the palette's own background before reaching for
        plain black or white, so a tile that cannot wear ``tile_text`` still
        wears something out of its own theme wherever that is legible.
        """
        return _readable(bg, (self.tile_text, self.bg, "#000000", "#ffffff"),
                         TILE_READABLE)

    def legible(self, colour: str) -> str:
        """``colour`` if it reads against the screen, else the nearest thing
        in the palette that does.

        For drawing a tile's colour as *text* — the gate table in the HUD and
        in the rules, where each gate is named in the colour it wears on the
        board. Half the gate backgrounds are deliberately near-black, which is
        right for a tile and invisible as a word.
        """
        return _readable(self.bg, (colour, self.tile_text, self.accent,
                                   "#ffffff"), READABLE)

    def tile_colors(self, value: int, max_value: int, *,
                    empty: int = 0, gate: bool = False) -> tuple[str, str]:
        """Background and foreground for a tile, by where it sits in the width."""
        if value == empty:
            return self.empty_tile, self.empty_tile
        if gate:
            # Gates are the negative half of the cell alphabet: XOR is -1 and
            # NOT is -4, which is ``board.GATES`` order and the order ``gates``
            # is written in. The same indexing the Wii does.
            bg = self.gates[-value - 1]
            return bg, self.ink(bg)
        span = max(1, max_value)
        idx = min(len(self.ramp) - 1, (value - 1) * len(self.ramp) // span)
        bg = self.ramp[idx]
        return bg, self.ink(bg)


#: In :data:`boole.modes.MODES` order, which is also ``ModeId`` order on the
#: Wii, so this ports index for index and a lookup stays an index rather than
#: a search.
PALETTES: tuple[Palette, ...] = (
    Palette(
        key="crumb", console="Game Boy",
        bg="#0f380f", empty_tile="#0f380f", tile_text="#9bbc0f",
        border="#0f380f",
        ramp=("#1a3a10", "#244d16", "#2e620d", "#507a10", "#729010"),
        accent="#8bac0f", accent_text="#0f380f",
        gates=("#4a7a6a", "#a09050", "#3a4a6a", "#080f08"),
        label="#9bbc0f",
    ),
    Palette(
        key="trit", console="NES",
        bg="#0a0a2a", empty_tile="#1a1a3a", tile_text="#ffffff",
        border="#0a0a2a",
        ramp=("#22224a", "#6b2020", "#8b2500", "#bb3a00", "#dd4f10"),
        accent="#4169e1", accent_text="#ffffff",
        gates=("#00b8a0", "#7b2fbe", "#901870", "#0a0a18"),
        label="#ffffff",
    ),
    Palette(
        key="nibble", console="SNES",
        bg="#0f0f1e", empty_tile="#1a1040", tile_text="#ffffff",
        border="#0f0f1e",
        ramp=("#1a1040", "#2e1870", "#4a1ea0", "#6a22c8", "#8a2be2"),
        accent="#c0a0ff", accent_text="#1a1040",
        gates=("#00d4aa", "#c86820", "#2a2070", "#100820"),
        label="#c0a0ff",
    ),
    Palette(
        key="pentad", console="Genesis",
        bg="#001a33", empty_tile="#003366", tile_text="#ffd700",
        border="#001a33",
        ramp=("#012244", "#1a3a7a", "#1060b0", "#aa7700", "#cc9900"),
        accent="#00bfff", accent_text="#001a33",
        gates=("#00c864", "#e05878", "#183848", "#060c14"),
        label="#00e5ff",
    ),
    Palette(
        key="hexad", console="Arcade",
        bg="#0f0500", empty_tile="#2d1000", tile_text="#ffa500",
        border="#1a0800",
        ramp=("#3a1500", "#6a1a00", "#991a00", "#cc3300", "#dd6600"),
        accent="#ffa500", accent_text="#1a0800",
        gates=("#00c8d4", "#7030c0", "#1a5020", "#0a0400"),
        label="#ffd080",
    ),
    Palette(
        key="ascii", console="Neo Geo",
        bg="#2d0052", empty_tile="#4b0082", tile_text="#00ffff",
        border="#2d0052",
        ramp=("#3a0066", "#880040", "#bb0066", "#0088aa", "#00aacc"),
        accent="#ff1493", accent_text="#ffffff",
        gates=("#ff7800", "#e03020", "#506010", "#080410"),
        label="#ffffff",
    ),
    # The web's PS1 tiles are gradients; a flat mid-tone of each is what the
    # Wii kept, and the ramp already carries the sense of metal.
    Palette(
        key="byte", console="PS1",
        bg="#0a0a0a", empty_tile="#1a1a1a", tile_text="#ffd700",
        border="#0a0a0a",
        ramp=("#252525", "#404040", "#606060", "#888888", "#b0b0b0"),
        accent="#ffd700", accent_text="#1a1a1a",
        gates=("#00b848", "#a8c800", "#006878", "#080808"),
        label="#ffd700",
    ),
    # Stays green across every width it climbs through: the mode is the
    # throughline, not the bit count. Same choice as the Wii and the web.
    Palette(
        key="gauntlet", console="Matrix",
        bg="#000000", empty_tile="#001a00", tile_text="#00ff00",
        border="#000000",
        ramp=("#001800", "#002a00", "#004000", "#005c00", "#007a00"),
        accent="#00ff00", accent_text="#000000",
        gates=("#c800c8", "#0060d0", "#a06000", "#d8ffd8"),
        label="#00ff00",
    ),
)

PALETTES_BY_KEY: dict[str, Palette] = {p.key: p for p in PALETTES}

#: What a screen that is not a mode wears: the rules, the score table, and the
#: fallback for a key that names no mode. 4-bit is the game's default mode and
#: the look the TUI had before it had eight.
DEFAULT = PALETTES_BY_KEY["nibble"]


def palette_for(mode_key: str) -> Palette:
    """The palette a mode wears.

    Keyed by the mode, never by the bit width — that is what keeps Gauntlet
    green all the way up.
    """
    return PALETTES_BY_KEY.get(mode_key, DEFAULT)


# ── Colours that are not a theme ────────────────────────────────────
#
# The same reward in all three ports, and part of no console's palette.

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
#   - #8b6914 is dimmer than most of every ramp, so the best tile on the board
#     spends part of each second looking duller than a lesser one beside it.
#     Same mistake as a starfield louder than the ship it is behind.
#
# So the sweep runs #ffd700 -> #ffe87c and back, both the web's own stops, with
# one interpolated step to keep it from reading as a blink. Every stop clears
# 10:1 against the text and outshines every tile colour in every palette bar
# the very top ramp step, which in practice this tile is the one wearing.
GOLD = ("#ffd700", "#ffdd3f", "#ffe87c", "#ffdd3f")
GOLD_FG = "#3a2000"
#: Frames per shimmer step. Four steps at 20fps is 2.4s, the web's 2.5s as
#: near as a whole number of frames gets.
GOLD_PERIOD = 12

#: Game over. An alarm rather than a decoration, so it is the one colour that
#: does not change with the console. It clears :data:`READABLE` on all eight
#: backgrounds, which the tests check rather than trust.
OVER_FG = "#ff6b6b"

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
