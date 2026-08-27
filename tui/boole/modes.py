"""Bit modes and their tuning tables.

Every mode is "n-bit": values run 0..2^n-1 and the ceiling is the max value.
Gauntlet starts at 2-bit and climbs a mode each time the ceiling is reached,
which is why the width is state rather than a constant.

The tables here are transcribed from ``wii/source/modes.c``, which was itself
transcribed from the web game. They are not chosen here, and changing one is a
gameplay change that has to land in all three ports — see the repo AGENTS.md.
``tests/test_board.py`` pins every threshold for that reason.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_BITS = 1
MAX_BITS = 8


@dataclass(frozen=True)
class Mode:
    """One selectable difficulty.

    ``key`` is the leaderboard table id and file name, so it must stay stable
    and distinct. Names are the bit-culture ones from the web game, not
    invented here: a 4-bit quantity really is a nibble.
    """

    key: str
    name: str
    start_bits: int
    gauntlet: bool = False

    @property
    def label(self) -> str:
        if self.gauntlet:
            return f"{self.name} · climbs from {self.start_bits}-bit"
        return f"{self.name} · {self.start_bits}-bit"


MODES: tuple[Mode, ...] = (
    Mode("crumb", "crumb", 2),
    Mode("trit", "trit", 3),
    Mode("nibble", "nibble", 4),
    Mode("pentad", "pentad", 5),
    Mode("hexad", "hexad", 6),
    Mode("ascii", "ascii", 7),
    Mode("byte", "byte", 8),
    Mode("gauntlet", "gauntlet", 2, gauntlet=True),
)

MODES_BY_KEY: dict[str, Mode] = {m.key: m for m in MODES}


def max_value(bits: int) -> int:
    """``2**bits - 1``, with the width clamped to what the rules can express."""
    bits = min(max(bits, MIN_BITS), MAX_BITS)
    return (1 << bits) - 1


def overflow_bonus(bits: int) -> int:
    """Points for clearing the ceiling: ``max_value * 3``.

    At 8-bit that is 765, which is why the score cannot be an
    increment-by-one counter.
    """
    return max_value(bits) * 3


def height_threshold(bits: int) -> int:
    """The lowest value worth a first-time-reached bonus at this width.

    Drawn where the spawn table stops handing values out for free: celebrating
    a value the board produces on its own is not celebrating anything.
    """
    if bits == 2:
        # Every 2-bit value can spawn, so nothing there is an achievement. The
        # web game returns Infinity; one above the ceiling is the same rule
        # written in ints.
        return max_value(bits) + 1
    if bits == 3:
        return 6
    if bits == 4:
        return 5
    if bits in (5, 6):
        return max_value(bits) // 2
    return max_value(bits) // 3


def height_bonus(bits: int, value: int) -> int:
    """Points for reaching ``value`` for the first time; 0 when not worth one.

    Double, in every mode. Reaching a value for the first time is the one thing
    in the game that cannot be repeated, and it is paid accordingly.
    """
    if value < height_threshold(bits):
        return 0
    return value * 2


def gate_spawn_pct(bits: int) -> int:
    """Percent chance a spawn is a gate rather than a number.

    Tapered: a 2-bit board is mostly gates because three values on their own
    give the player almost nothing to do, and a byte board barely needs them.
    Gauntlet reads this from the width it has climbed to, so the mix shifts as
    the run progresses.
    """
    if bits <= 2:
        return 45
    if bits == 3:
        return 32
    if bits == 4:
        return 24
    if bits <= 6:
        return 20
    return 18


# A cumulative distribution: the first step whose bound a roll in 0..99 falls
# under wins. Written this way so each table reads as the same shape as the
# chain of `rand() <` comparisons it was transcribed from.
_SPAWN_2BIT = ((50, 1), (100, 2))
_SPAWN_3BIT = ((20, 1), (40, 2), (60, 3), (80, 4), (100, 5))
_SPAWN_H1 = ((60, 1), (100, 2))
_SPAWN_H3 = ((50, 1), (100, 2))
_SPAWN_H7 = ((40, 1), (75, 2), (100, 3))
_SPAWN_H15 = ((40, 1), (70, 2), (90, 3), (100, 4))
_SPAWN_H31 = ((30, 1), (50, 2), (70, 3), (85, 4), (95, 5), (100, 6))
_SPAWN_H63 = ((25, 1), (40, 2), (55, 3), (70, 4), (80, 5), (90, 6), (96, 7), (100, 8))
_SPAWN_LATE = ((20, 1), (35, 2), (50, 4), (65, 6), (78, 8), (88, 10), (100, 12))


def _pick(steps: tuple[tuple[int, int], ...], roll100: int) -> int:
    for bound, value in steps:
        if roll100 < bound:
            return value
    return steps[-1][1]


def spawn_value(bits: int, highest_on_board: int, roll100: int) -> int:
    """The value a number-spawn takes.

    Spawns scale with progress rather than staying at 1-2-3 forever: a byte
    board seeded one tile at a time is a grind, not a difficulty. Keyed on the
    board's *current* highest rather than the best ever reached, so clearing
    the board eases the spawns back down with it.
    """
    roll100 = min(max(roll100, 0), 99)

    if bits <= 2:
        # The 2-bit ceiling never spawns: with only three values, a board that
        # hands you the top one has handed you the whole mode.
        steps = _SPAWN_2BIT
    elif bits == 3 and highest_on_board >= 3:
        # 3-bit opens up early. There is so little room to climb that waiting
        # for a 1 and a 2 to meet is most of the run.
        steps = _SPAWN_3BIT
    elif highest_on_board <= 1:
        steps = _SPAWN_H1
    elif highest_on_board <= 3:
        steps = _SPAWN_H3
    elif highest_on_board <= 7:
        steps = _SPAWN_H7
    elif highest_on_board <= 15:
        steps = _SPAWN_H15
    elif highest_on_board <= 31:
        steps = _SPAWN_H31
    elif highest_on_board <= 63:
        steps = _SPAWN_H63
    else:
        steps = _SPAWN_LATE

    # No branch above can exceed its own ceiling, but a table transcribed by
    # hand should not be able to produce a tile the rules cannot express.
    return min(_pick(steps, roll100), max_value(bits))
