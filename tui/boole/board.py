"""The board and the Boolean rules — no rendering, no terminal, no engine.

A port of ``wii/source/board.c``, which is the version of these rules that was
already separated from its renderer and checked against the web game's own
assertions. Porting from ``web/js/game.js`` instead would have meant lifting
logic back out of ~25 ``document.*`` call sites and a constructor that caches
DOM nodes.

The three implementations have to agree exactly or the same game plays
differently in three places, and that divergence is invisible until a player
notices. ``tests/test_board.py`` is the C suite's assertion table, ported.

**Not ported:** the ``TileMove`` provenance that ``board_move`` fills in on the
Wii. It exists so the renderer can slide tiles to their destinations instead of
teleporting them, it is written but never read by the rules, and a terminal
redrawing a 4x4 grid does not animate. Omitting it cannot change behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from boole import modes

BOARD_SIZE = 4
BOARD_CELLS = BOARD_SIZE * BOARD_SIZE

# Gates live in the same grid as values, as negative numbers. It reads oddly
# but it is what makes a gate slide, collide and occupy space exactly like a
# tile does — which is the whole game. 0 is an empty cell.
TILE_EMPTY = 0
GATE_XOR = -1
GATE_OR = -2
GATE_AND = -3
GATE_NOT = -4

GATES = (GATE_XOR, GATE_OR, GATE_AND, GATE_NOT)

GATE_SYMBOLS = {GATE_XOR: "⊕", GATE_OR: "∨", GATE_AND: "∧", GATE_NOT: "¬"}
GATE_NAMES = {GATE_XOR: "XOR", GATE_OR: "OR", GATE_AND: "AND", GATE_NOT: "NOT"}

_MASK32 = 0xFFFFFFFF


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


def is_gate(value: int) -> bool:
    return value in GATES


def gate_symbol(value: int) -> str:
    return GATE_SYMBOLS.get(value, "?")


@dataclass
class Board:
    """A 4x4 grid of values and gates, and the rules that resolve them."""

    bits: int = 4
    gauntlet: bool = False

    cells: list[list[int]] = field(init=False)
    max_value: int = field(init=False)
    reached_max: bool = field(init=False, default=False)

    score: int = field(init=False, default=0)
    #: Best value built by merging, not spawned — what the height bonus reads.
    highest_earned: int = field(init=False, default=0)

    # Set by the last move() so the caller can react without re-deriving
    # anything: play a sound, flash a bonus, promote the mode.
    last_gained: int = field(init=False, default=0)
    last_overflow_bonus: int = field(init=False, default=0)
    last_height_bonus: int = field(init=False, default=0)
    last_upgraded: bool = field(init=False, default=False)

    #: Where spawn() last placed a tile, or (-1, -1).
    spawn_at: tuple[int, int] = field(init=False, default=(-1, -1))
    #: The tile that earned a Gauntlet promotion, or (-1, -1). Reset by every
    #: move; the app sets it, exactly as main.c does on the Wii.
    rainbow_at: tuple[int, int] = field(init=False, default=(-1, -1))

    def __post_init__(self) -> None:
        self.cells = [[TILE_EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.max_value = modes.max_value(self.bits)

    # ── Accessors ───────────────────────────────────────────────────

    def get(self, row: int, col: int) -> int:
        return self.cells[row][col]

    def set(self, row: int, col: int, value: int) -> None:
        self.cells[row][col] = value

    def highest_value(self) -> int:
        """Highest number on the board; gates are negative and empties are 0."""
        return max((v for row in self.cells for v in row), default=0)

    def is_full(self) -> bool:
        return all(v != TILE_EMPTY for row in self.cells for v in row)

    def is_personal_best(self, value: int) -> bool:
        """Whether a tile holding ``value`` wears the gold plate.

        The web build tracks the marker as a parallel 4x4 boolean board that
        slides, merges and rotates alongside the values, so that exactly one
        *tile instance* is gold. The Wii asks this question of the value
        instead (``render.c``), and this is that predicate — a method rather
        than three copies of the expression, which is the only thing that
        differs from the C.

        Asking about the value cannot accidentally gild a spawn, which is the
        thing the web comments are careful about. A spawn can never reach
        :func:`modes.height_threshold`: the highest a table hands out is 5 at
        3-bit (floor 6), 4 at 4-bit (floor 5), 8 at 6-bit (floor 31) and 12
        from ``spawn_late`` (floor 42 at 7-bit, 85 at 8-bit). So requiring a
        bonus to have been paid already restricts this to values built by
        merging.

        It is not identical to the web: two tiles that both hold the best value
        are both gold here, and the web golds whichever one got there first.
        Written down in the repo's ``AGENTS.md`` rather than papered over.
        """
        return (value == self.highest_earned
                and self.highest_earned > 0
                and modes.height_bonus(self.bits, self.highest_earned) > 0)

    # ── Gates ───────────────────────────────────────────────────────

    def apply_gate(self, gate: int, lhs: int, rhs: int = 0) -> int:
        """Raw gate arithmetic. NOT is unary and bit-width dependent, which is
        the whole point of the modes; ``rhs`` is ignored for it."""
        if gate == GATE_XOR:
            return lhs ^ rhs
        if gate == GATE_OR:
            return lhs | rhs
        if gate == GATE_AND:
            return lhs & rhs
        if gate == GATE_NOT:
            return (~lhs) & self.max_value
        return lhs

    def _reached_ceiling(self) -> None:
        """Promotion happens the first time the ceiling is reached at a given
        width. The flag resets with the width, so each rung is earned on its own."""
        if self.reached_max:
            return
        self.reached_max = True

        if self.gauntlet and self.bits < modes.MAX_BITS:
            self.bits += 1
            self.max_value = modes.max_value(self.bits)
            self.reached_max = False
            self.last_upgraded = True

    def _resolve_gate(self, gate: int, lhs: int, rhs: int) -> int:
        """Apply a gate and pay any overflow bonus.

        Both operands are already within the bit width, so a bitwise result is
        too — the ceiling can only be cleared by NOT of the ceiling itself,
        which lands on 0. A tile of 0 cannot exist, so that is the overflow:
        the tile clears and the bonus pays.
        """
        result = self.apply_gate(gate, lhs, rhs)

        if result == 0 and gate == GATE_NOT and lhs == self.max_value:
            bonus = modes.overflow_bonus(self.bits)
            self.score += bonus
            self.last_gained += bonus
            self.last_overflow_bonus += bonus
            self._reached_ceiling()
            return 0
        return result

    def _award_height(self, value: int) -> None:
        """First-time height bonuses only pay for values built by merging. A
        value that merely spawned was not an achievement, and paying for it
        would make the best strategy "wait"."""
        if value <= self.highest_earned:
            return

        bonus = modes.height_bonus(self.bits, value)
        self.highest_earned = value
        if bonus > 0:
            self.score += bonus
            self.last_gained += bonus
            self.last_height_bonus += bonus
        if value == self.max_value:
            self._reached_ceiling()

    def _operate(self, gate: int, lhs: int, rhs: int, score_it: bool) -> int:
        """Resolve one gate and pay for it.

        Every gate is worth its result, so scoring lives here rather than being
        repeated at each pattern. A zero result is a cleared tile, worth nothing.
        """
        result = (self._resolve_gate(gate, lhs, rhs) if score_it
                  else self.apply_gate(gate, lhs, rhs))
        if score_it and result != 0:
            self.score += result
            self.last_gained += result
            self._award_height(result)
        return result

    # ── Line resolution ─────────────────────────────────────────────

    @staticmethod
    def _collapse(cells: list[int], at: int, count: int, result: int) -> None:
        """Fold ``count`` cells at ``at`` into their result, closing the gap.

        A result of ``TILE_EMPTY`` means the operation consumed its operands and
        produced nothing — two NOTs cancelling, or a gate landing on zero.
        """
        cells[at:at + count] = [] if result == TILE_EMPTY else [result]

    def _advance_line(self, line: list[int], score_it: bool) -> list[int]:
        """Collapse one line toward index 0 and resolve it.

        Everything the game is about happens here, and **the order of the cases
        is the rule set** — an earlier pattern shadows a later one that would
        also have matched.

        The line is re-scanned from the same position after each resolution
        rather than walked once, so a result can feed the next operation in the
        same move: 1 XOR 2 makes a 3, and a 3 already sitting beside it then
        consolidates with it. That is the web game's behaviour and this is a
        port of it.
        """
        cells = [v for v in line if v != TILE_EMPTY]
        i = 0

        while i < len(cells):
            n = len(cells)

            # NOT + NOT: two inversions are no inversion, and both are consumed.
            if cells[i] == GATE_NOT and i + 1 < n and cells[i + 1] == GATE_NOT:
                self._collapse(cells, i, 2, TILE_EMPTY)
                continue

            # NOT applied to the number after it.
            if cells[i] == GATE_NOT and i + 1 < n and not is_gate(cells[i + 1]):
                result = self._operate(GATE_NOT, cells[i + 1], 0, score_it)
                self._collapse(cells, i, 2, result)
                continue

            # A NOT pair cancels behind a number too. Without this the next case
            # matches first and a run of NOTs resolves one at a time, scoring
            # every intermediate value and claiming heights no tile rested on.
            if (not is_gate(cells[i]) and i + 2 < n
                    and cells[i + 1] == GATE_NOT and cells[i + 2] == GATE_NOT):
                self._collapse(cells, i + 1, 2, TILE_EMPTY)
                continue

            # NOT applied to the number before it.
            if not is_gate(cells[i]) and i + 1 < n and cells[i + 1] == GATE_NOT:
                result = self._operate(GATE_NOT, cells[i], 0, score_it)
                self._collapse(cells, i, 2, result)
                continue

            # number gate number. NOT is excluded: it is unary and was handled.
            if (not is_gate(cells[i]) and i + 2 < n
                    and is_gate(cells[i + 1]) and cells[i + 1] != GATE_NOT
                    and not is_gate(cells[i + 2])):
                result = self._operate(cells[i + 1], cells[i], cells[i + 2], score_it)
                self._collapse(cells, i, 3, result)
                continue

            # Idempotence: equal numbers consolidate to one of themselves —
            # 1 OR 1 is 1, not 2. The only case that advances, because a
            # consolidated tile is settled where a gate result is not.
            if i + 1 < n and not is_gate(cells[i]) and cells[i] == cells[i + 1]:
                value = cells[i]
                if score_it:
                    self.score += value
                    self.last_gained += value
                    self._award_height(value)
                self._collapse(cells, i, 2, value)
                i += 1
                continue

            i += 1

        return cells + [TILE_EMPTY] * (BOARD_SIZE - len(cells))

    def _read_line(self, direction: Direction, index: int) -> list[int]:
        """Read a row or column running in the direction of travel, so
        :meth:`_advance_line` only ever collapses toward index 0."""
        last = BOARD_SIZE - 1
        if direction is Direction.LEFT:
            return [self.cells[index][k] for k in range(BOARD_SIZE)]
        if direction is Direction.RIGHT:
            return [self.cells[index][last - k] for k in range(BOARD_SIZE)]
        if direction is Direction.UP:
            return [self.cells[k][index] for k in range(BOARD_SIZE)]
        return [self.cells[last - k][index] for k in range(BOARD_SIZE)]

    def _write_line(self, direction: Direction, index: int, line: list[int]) -> None:
        last = BOARD_SIZE - 1
        for k in range(BOARD_SIZE):
            if direction is Direction.LEFT:
                self.cells[index][k] = line[k]
            elif direction is Direction.RIGHT:
                self.cells[index][last - k] = line[k]
            elif direction is Direction.UP:
                self.cells[k][index] = line[k]
            else:
                self.cells[last - k][index] = line[k]

    @staticmethod
    def _line_index(direction: Direction, step: int) -> int:
        """Which line to resolve on step 0..3.

        Lines are independent, so this cannot change where a tile lands — but a
        first-time height bonus pays once, to whichever line reaches the value
        first, and the web game collapses by rotating the board and always
        taking rows in order. That makes its right and up run through the lines
        backwards. Matching the points means matching the order.
        """
        if direction in (Direction.RIGHT, Direction.UP):
            return BOARD_SIZE - 1 - step
        return step

    # ── Moves ───────────────────────────────────────────────────────

    def move(self, direction: Direction) -> bool:
        """Slide and resolve every line. True when the board changed, which is
        the condition for spawning a new tile."""
        self.last_gained = 0
        self.last_overflow_bonus = 0
        self.last_height_bonus = 0
        self.last_upgraded = False
        self.spawn_at = (-1, -1)
        self.rainbow_at = (-1, -1)

        changed = False
        for step in range(BOARD_SIZE):
            index = self._line_index(direction, step)
            before = self._read_line(direction, index)
            after = self._advance_line(before, score_it=True)
            if after != before:
                changed = True
                self._write_line(direction, index, after)
        return changed

    def game_over(self) -> bool:
        """No empty cell and no legal move left."""
        if not self.is_full():
            return False

        # Full is not over while some direction still resolves something.
        # Scoring is off, so probing for a legal move cannot award points.
        for direction in Direction:
            for index in range(BOARD_SIZE):
                before = self._read_line(direction, index)
                if self._advance_line(before, score_it=False) != before:
                    return False
        return True

    # ── Spawning ────────────────────────────────────────────────────

    def spawn(self, roll: int) -> bool:
        """Place a tile or gate in a random empty cell. False when full.

        ``roll`` is the only randomness that enters, so a test can pin a spawn
        exactly. It is a whole word rather than a small number because three
        independent choices come out of it — which cell, gate or number, and
        which value — and a four-digit roll cannot carry three hundred-way
        decisions without them correlating.
        """
        empty = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
                 if self.cells[r][c] == TILE_EMPTY]
        if not empty:
            return False

        # Three decisions, three streams. The roll is mixed before the first of
        # them because callers pass consecutive or evenly spaced numbers — tests
        # always do — and the low bits of those would otherwise walk the cell
        # and the value in lockstep. Stepping an LCG between the streams keeps
        # them independent of each other. Masked to 32 bits to match the C,
        # where these are unsigned ints and the overflow is the algorithm.
        r0 = (int(roll) * 2654435761 + 0x9E3779B9) & _MASK32
        r1 = (r0 * 1103515245 + 12345) & _MASK32
        r2 = (r1 * 1103515245 + 12345) & _MASK32

        slot = (r0 >> 16) % len(empty)
        gate_roll = (r1 >> 16) % 100
        value_roll = (r2 >> 16) % 100

        if gate_roll < modes.gate_spawn_pct(self.bits):
            # 100 divides by 4, so the value roll doubles as an unbiased pick
            # of which gate — it has nothing else to do on a gate spawn.
            value = GATES[value_roll % 4]
        else:
            value = modes.spawn_value(self.bits, self.highest_value(), value_roll)

        row, col = empty[slot]
        self.cells[row][col] = value
        self.spawn_at = (row, col)
        return True
