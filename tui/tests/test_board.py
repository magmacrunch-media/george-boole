"""The Boolean rules, checked against the same assertions as the other ports.

Ported from ``wii/tests/test_board.c``, which was itself ported from
``web/tests/test-game-logic.js``. All three builds have to agree on every one
of these or the same game plays differently in three places, and that
divergence is invisible until a player notices.

Nothing here imports the engine or Textual: the rules are pure Python, which is
the property that makes them testable in under a second.
"""

import pytest

from boole import modes
from boole.board import (
    BOARD_SIZE,
    GATE_AND,
    GATE_NOT,
    GATE_OR,
    GATE_XOR,
    TILE_EMPTY,
    Board,
    Direction,
    is_gate,
)

E = TILE_EMPTY


def board(bits=4, gauntlet=False):
    return Board(bits=bits, gauntlet=gauntlet)


def row_after_move(bits, row_in, direction=Direction.LEFT):
    """Run one row through a move and report the resulting row."""
    b = board(bits)
    for c in range(BOARD_SIZE):
        b.cells[0][c] = row_in[c]
    b.move(direction)
    return list(b.cells[0])


# ── is_gate ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("value", [GATE_XOR, GATE_OR, GATE_AND, GATE_NOT])
def test_gates_are_gates(value):
    assert is_gate(value)


@pytest.mark.parametrize("value", [0, 1, 7, 255])
def test_numbers_are_not_gates(value):
    assert not is_gate(value)


# ── apply_gate ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "bits,gate,lhs,rhs,want",
    [
        (2, GATE_XOR, 1, 2, 3),
        (2, GATE_XOR, 3, 3, 0),
        (2, GATE_XOR, 1, 1, 0),
        (2, GATE_XOR, 2, 2, 0),
        (3, GATE_XOR, 0, 5, 5),
        (3, GATE_XOR, 5, 0, 5),
        (2, GATE_OR, 1, 2, 3),
        (2, GATE_OR, 3, 3, 3),
        (2, GATE_OR, 1, 1, 1),
        (3, GATE_OR, 0, 5, 5),
        (3, GATE_OR, 5, 3, 7),
        (2, GATE_AND, 1, 2, 0),
        (2, GATE_AND, 3, 3, 3),
        (2, GATE_AND, 1, 3, 1),
        (3, GATE_AND, 5, 3, 1),
        (3, GATE_AND, 6, 3, 2),
    ],
)
def test_binary_gates(bits, gate, lhs, rhs, want):
    assert board(bits).apply_gate(gate, lhs, rhs) == want


@pytest.mark.parametrize(
    "bits,lhs,want",
    [
        # NOT is bit-width dependent, which is the whole point of the modes.
        (2, 0, 3), (2, 1, 2), (2, 2, 1), (2, 3, 0),
        (3, 0, 7), (3, 7, 0),
        (4, 5, 10),
    ],
)
def test_not_is_width_dependent(bits, lhs, want):
    assert board(bits).apply_gate(GATE_NOT, lhs, 0) == want


# ── Moves ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "bits,row_in,want",
    [
        (2, [1, 2, 3, 0], [1, 2, 3, 0]),          # no merge
        (2, [1, 1, 0, 0], [1, E, E, E]),          # same merge
        (2, [2, 2, 0, 0], [2, E, E, E]),
        (2, [3, 3, 0, 0], [3, E, E, E]),
        (2, [1, 2, 1, 2], [1, 2, 1, 2]),          # no merge, different
    ],
)
def test_basic_moves(bits, row_in, want):
    assert row_after_move(bits, row_in) == want


@pytest.mark.parametrize(
    "bits,row_in,want",
    [
        # Idempotence: equal numbers consolidate to one of themselves.
        (2, [1, 1, 0, 0], [1, E, E, E]),
        (2, [2, 2, 0, 0], [2, E, E, E]),
        (2, [3, 3, 0, 0], [3, E, E, E]),
        (3, [5, 5, 0, 0], [5, E, E, E]),
        (3, [7, 7, 0, 0], [7, E, E, E]),
    ],
)
def test_idempotent_merges(bits, row_in, want):
    assert row_after_move(bits, row_in) == want


@pytest.mark.parametrize(
    "row_in,want,why",
    [
        ([1, GATE_XOR, 2, 0], [3, E, E, E], "1 XOR 2 = 3"),
        ([3, GATE_XOR, 3, 0], [E, E, E, E], "3 XOR 3 = 0 clears"),
        ([1, GATE_OR, 2, 0], [3, E, E, E], "1 OR 2 = 3"),
        ([3, GATE_AND, 3, 0], [3, E, E, E], "3 AND 3 = 3"),
        ([1, GATE_AND, 2, 0], [E, E, E, E], "1 AND 2 = 0 clears"),
    ],
)
def test_gate_sandwiches(row_in, want, why):
    assert row_after_move(2, row_in) == want, why


@pytest.mark.parametrize(
    "row_in,want,why",
    [
        ([GATE_NOT, 1, 0, 0], [2, E, E, E], "NOT then 1 = 2"),
        ([1, GATE_NOT, 0, 0], [2, E, E, E], "1 then NOT = 2"),
        ([GATE_NOT, GATE_NOT, 0, 0], [E, E, E, E], "NOT NOT cancels"),
        ([GATE_NOT, GATE_NOT, 1, 0], [1, E, E, E], "NOT NOT then 1 survives"),
    ],
)
def test_not_patterns(row_in, want, why):
    assert row_after_move(2, row_in) == want, why


@pytest.mark.parametrize(
    "bits,row_in,want,why",
    [
        (2, [0, 0, 0, 0], [E, E, E, E], "all empty"),
        (3, [1, 2, 3, 4], [1, 2, 3, 4], "full row, no merge"),
        (2, [GATE_NOT, 0, 0, 0], [GATE_NOT, E, E, E], "lone NOT waits for a number"),
    ],
)
def test_edges(bits, row_in, want, why):
    assert row_after_move(bits, row_in) == want, why


def test_a_run_of_nots_cancels_rather_than_resolving_one_at_a_time():
    # Without the "NOT pair behind a number" case, this resolves stepwise and
    # scores every intermediate value, claiming heights no tile rested on.
    b = board(4)
    b.cells[0][0] = 5
    b.cells[0][1] = GATE_NOT
    b.cells[0][2] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.cells[0][0] == 5
    assert b.score == 0


# ── Overflow and promotion ──────────────────────────────────────────


def test_not_of_the_ceiling_clears_the_tile_and_pays():
    # The only way to overflow: a bitwise op on in-range operands can never
    # exceed the ceiling, but NOT of the ceiling lands on 0, which cannot be a
    # tile.
    b = board(2)
    b.cells[0][0] = 3
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.cells[0][0] == TILE_EMPTY
    assert b.last_overflow_bonus == 9
    assert b.score == 9


def test_eight_bit_overflow_pays_765():
    b = board(8)
    b.cells[0][0] = 255
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.last_overflow_bonus == 765
    # A single move worth hundreds is why the score is not a counter.
    assert b.score >= 765


def test_gauntlet_promotes_on_reaching_the_ceiling():
    b = board(2, gauntlet=True)
    assert b.bits == 2
    b.cells[0][0] = 3
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.bits == 3
    assert b.max_value == 7
    assert b.last_upgraded


def test_a_fixed_mode_never_promotes():
    b = board(2, gauntlet=False)
    b.cells[0][0] = 3
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.bits == 2


def test_gauntlet_stops_climbing_at_eight_bit():
    b = board(8, gauntlet=True)
    b.cells[0][0] = 255
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.bits == 8
    assert not b.last_upgraded


# ── Scoring ─────────────────────────────────────────────────────────


def test_an_operation_is_worth_its_result():
    b = board(3)
    b.cells[0][0] = 5
    b.cells[0][1] = GATE_OR
    b.cells[0][2] = 3
    b.move(Direction.LEFT)
    assert b.cells[0][0] == 7
    assert b.score >= 7


def test_no_height_bonus_below_what_was_already_earned():
    b = board(4)
    b.highest_earned = 15
    b.cells[0][0] = 5
    b.cells[0][1] = 5
    b.move(Direction.LEFT)
    assert b.last_height_bonus == 0


@pytest.mark.parametrize(
    "bits,value,want",
    [
        (3, 7, 14),      # double, in every mode
        (6, 40, 80),
        (8, 200, 400),
        (3, 2, 0),       # nothing below the floor
        (2, 3, 0),       # 2-bit never pays a height bonus
    ],
)
def test_height_bonus_is_double_above_the_floor(bits, value, want):
    assert modes.height_bonus(bits, value) == want


def test_a_unary_not_is_worth_its_result():
    # The Wii port awarded the height bonus for a unary NOT but never the
    # operation itself, which cost most in the wide modes. Pinned here.
    b = board(8)
    b.highest_earned = 255          # height bonuses out of the way
    b.cells[0][0] = GATE_NOT
    b.cells[0][1] = 50
    b.move(Direction.LEFT)
    assert b.cells[0][0] == 205
    assert b.score == 205


def test_a_unary_not_is_worth_the_same_from_either_side():
    b = board(8)
    b.highest_earned = 255
    b.cells[0][0] = 50
    b.cells[0][1] = GATE_NOT
    b.move(Direction.LEFT)
    assert b.score == 205


def test_line_order_decides_which_line_wins_a_first_time_bonus():
    # A first-time height bonus pays once, to whichever line gets there first,
    # so resolution order is a scoring rule. Collapsing up, the columns are
    # taken right to left: the right column builds 61 and the left builds 32,
    # and going left to right would pay for both.
    b = board(6)
    b.cells[0][0] = 31
    b.cells[1][0] = GATE_NOT
    b.cells[0][1] = 60
    b.cells[1][1] = GATE_OR
    b.cells[2][1] = 49
    b.move(Direction.UP)
    assert b.cells[0][0] == 32      # NOT 31 at 6-bit
    assert b.cells[0][1] == 61      # 60 OR 49
    assert b.score == 93 + 122      # the later, smaller value earns no bonus


# ── Directions ──────────────────────────────────────────────────────


def test_right_moving_merge_lands_on_the_right_edge():
    b = board(2)
    b.cells[0][2] = 1
    b.cells[0][3] = 1
    b.move(Direction.RIGHT)
    assert b.cells[0][3] == 1
    assert b.cells[0][0] == TILE_EMPTY


def test_upward_merge_lands_on_the_top_edge():
    b = board(2)
    b.cells[2][1] = 2
    b.cells[3][1] = 2
    b.move(Direction.UP)
    assert b.cells[0][1] == 2


def test_downward_merge_lands_on_the_bottom_edge():
    b = board(2)
    b.cells[0][1] = 2
    b.cells[1][1] = 2
    b.move(Direction.DOWN)
    assert b.cells[3][1] == 2


def test_a_no_op_move_reports_no_change():
    # Or the game spawns a tile for an input the player never actually made.
    b = board(2)
    b.cells[0][0] = 1
    b.cells[1][0] = 2
    assert not b.move(Direction.LEFT)


# ── Game over ───────────────────────────────────────────────────────


CHECKER = [
    [1, 2, 1, 2],
    [2, 1, 2, 1],
    [1, 2, 1, 2],
    [2, 1, 2, 1],
]


def checkerboard(bits=4):
    b = board(bits)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            b.cells[r][c] = CHECKER[r][c]
    return b


def test_an_empty_board_is_neither_full_nor_over():
    b = board(4)
    assert not b.is_full()
    assert not b.game_over()


def test_a_checkerboard_with_no_gates_is_over():
    b = checkerboard()
    assert b.is_full()
    assert b.game_over()


def test_a_cornered_gate_cannot_save_the_board():
    # A binary gate needs a number on both sides, and a corner has only one
    # neighbour along each line.
    b = checkerboard()
    b.cells[3][3] = GATE_XOR
    assert b.is_full()
    assert b.game_over()


def test_an_interior_gate_keeps_a_full_board_alive():
    b = checkerboard()
    b.cells[1][1] = GATE_XOR        # row 1 becomes 2, XOR, 2, 1
    assert b.is_full()
    assert not b.game_over()


def test_checking_for_game_over_does_not_score():
    b = checkerboard()
    b.cells[0][0] = 1
    b.cells[0][1] = 1
    before = b.score
    b.game_over()
    assert b.score == before


# ── Spawning ────────────────────────────────────────────────────────


def test_sixteen_spawns_fill_the_board_and_the_seventeenth_refuses():
    b = board(4)
    for i in range(16):
        assert b.spawn(i * 137)
    assert b.is_full()
    assert not b.spawn(5)


def test_nothing_spawns_outside_the_modes_range():
    for roll in range(0, 3000, 7):
        b = board(2)
        b.spawn(roll)
        for row in b.cells:
            for v in row:
                if v == TILE_EMPTY or is_gate(v):
                    continue
                assert 1 <= v <= b.max_value, f"spawned {v} outside 1..{b.max_value}"


def test_two_bit_never_spawns_its_ceiling():
    # The web game's "2-bit fix": with only three values, a board that hands
    # you the ceiling has handed you the whole mode.
    seen = set()
    for roll in range(4000):
        b = board(2)
        b.spawn(roll)
        seen.add(b.cells[b.spawn_at[0]][b.spawn_at[1]])
    assert 1 in seen
    assert 2 in seen
    assert 3 not in seen


@pytest.mark.parametrize("bits", [2, 3, 4, 5, 6, 7, 8])
def test_the_gate_share_out_of_spawn_matches_the_table(bits):
    # The share coming out of spawn(), not just out of the table: this is the
    # check that would have caught a flat 18% at every width.
    samples = 6000
    gates = 0
    for roll in range(samples):
        b = board(bits)
        b.spawn(roll)
        if is_gate(b.cells[b.spawn_at[0]][b.spawn_at[1]]):
            gates += 1
    pct = (gates * 100) // samples
    want = modes.gate_spawn_pct(bits)
    assert want - 4 <= pct <= want + 4, f"{bits}-bit spawned {pct}%, wanted ~{want}%"


def test_highest_value_ignores_gates_and_empties():
    b = board(4)
    assert b.highest_value() == 0
    b.cells[0][0] = GATE_NOT
    b.cells[1][1] = 9
    b.cells[2][2] = 4
    assert b.highest_value() == 9


# ── Mode tables ─────────────────────────────────────────────────────


@pytest.mark.parametrize("bits,want", [(2, 3), (3, 7), (4, 15), (8, 255)])
def test_ceilings(bits, want):
    assert modes.max_value(bits) == want


@pytest.mark.parametrize(
    "bits,want",
    [(2, 9), (3, 21), (4, 45), (5, 93), (6, 189), (7, 381), (8, 765)],
)
def test_overflow_bonuses(bits, want):
    assert modes.overflow_bonus(bits) == want


@pytest.mark.parametrize(
    "bits,want",
    [(2, 45), (3, 32), (4, 24), (5, 20), (6, 20), (7, 18), (8, 18)],
)
def test_gate_spawn_rates(bits, want):
    assert modes.gate_spawn_pct(bits) == want


def test_two_bits_height_floor_is_unreachable():
    assert modes.height_threshold(2) > modes.max_value(2)


@pytest.mark.parametrize(
    "bits,want", [(3, 6), (4, 5), (5, 15), (6, 31), (7, 42), (8, 85)]
)
def test_height_thresholds(bits, want):
    assert modes.height_threshold(bits) == want


@pytest.mark.parametrize(
    "bits,highest,roll,want",
    [
        # 2-bit: 1 or 2, never the ceiling.
        (2, 0, 0, 1), (2, 2, 49, 1), (2, 2, 50, 2), (2, 2, 99, 2),
        # 3-bit opens up once anything has been built.
        (3, 3, 0, 1), (3, 3, 19, 1), (3, 3, 20, 2), (3, 3, 40, 3),
        (3, 3, 60, 4), (3, 3, 80, 5), (3, 3, 99, 5),
        (3, 2, 50, 2),                      # falls back before anything is built
        # Opening board: 60/40.
        (4, 1, 59, 1), (4, 1, 60, 2),
        # Highest 2..3: 50/50.
        (4, 3, 49, 1), (4, 3, 50, 2),
        # Highest 4..7: 40/35/25.
        (4, 7, 39, 1), (4, 7, 40, 2), (4, 7, 74, 2), (4, 7, 75, 3),
        # Highest 8..15: 40/30/20/10.
        (4, 8, 39, 1), (4, 8, 40, 2), (4, 8, 70, 3), (4, 8, 90, 4), (4, 8, 99, 4),
        # Highest 16..31: 1-6.
        (5, 16, 29, 1), (5, 16, 30, 2), (5, 16, 50, 3),
        (5, 16, 70, 4), (5, 16, 85, 5), (5, 16, 95, 6),
        # Highest 32..63: 1-8.
        (6, 32, 24, 1), (6, 32, 25, 2), (6, 32, 40, 3), (6, 32, 55, 4),
        (6, 32, 70, 5), (6, 32, 80, 6), (6, 32, 90, 7), (6, 32, 96, 8),
        # Highest 64+: the even ladder up to 12.
        (8, 64, 19, 1), (8, 64, 20, 2), (8, 64, 35, 4), (8, 64, 50, 6),
        (8, 64, 65, 8), (8, 64, 78, 10), (8, 64, 88, 12), (8, 64, 99, 12),
        # An out-of-range roll must land somewhere legal.
        (4, 8, -1, 1), (4, 8, 500, 4),
    ],
)
def test_spawn_table(bits, highest, roll, want):
    assert modes.spawn_value(bits, highest, roll) == want


def test_mode_ids_are_distinct():
    # Table ids become filenames, so they must be distinct and plain.
    keys = [m.key for m in modes.MODES]
    assert len(keys) == len(set(keys))


def test_gauntlet_is_the_only_climbing_mode():
    climbing = [m.key for m in modes.MODES if m.gauntlet]
    assert climbing == ["gauntlet"]
    assert modes.MODES_BY_KEY["gauntlet"].start_bits == 2
    assert modes.MODES_BY_KEY["byte"].start_bits == 8


# ── The rules stand alone ───────────────────────────────────────────


def test_the_rules_import_without_the_engine():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; from boole.board import Board; "
         "b = Board(bits=4); b.spawn(1); "
         "print('magmacrunch' in sys.modules, 'textual' in sys.modules)"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "False False"


# ── The gold personal-best tile ──────────────────────────────────────


def test_the_best_value_built_is_the_one_that_is_gold():
    b = board(4)
    b.cells[0][0] = 5
    b.cells[0][1] = 5
    b.move(Direction.LEFT)          # 5 merges to 5, above the 4-bit floor
    assert b.highest_earned == 5
    assert b.is_personal_best(5)
    assert not b.is_personal_best(4)
    assert not b.is_personal_best(6)


def test_nothing_is_gold_before_anything_has_been_earned():
    b = board(4)
    b.cells[0][0] = 9
    assert not b.is_personal_best(9)
    assert not b.is_personal_best(TILE_EMPTY)


def test_two_bit_has_no_gold_tile_at_all():
    # Every 2-bit value can spawn, so the mode pays no height bonus and has
    # nothing to celebrate. The gold follows the bonus rather than being a
    # second rule that could disagree with it.
    b = board(2)
    b.cells[0][0] = 1
    b.cells[0][1] = 1
    b.move(Direction.LEFT)
    assert b.highest_earned == 1
    assert not b.is_personal_best(1)
    assert not any(b.is_personal_best(v) for v in range(1, 4))


def test_a_value_below_the_floor_is_tracked_but_not_gilded():
    # highest_earned advances so the bonus is not paid twice, and the tile
    # still gets nothing — the web draws the same distinction.
    b = board(8)
    b.cells[0][0] = 3
    b.cells[0][1] = 3
    b.move(Direction.LEFT)
    assert b.highest_earned == 3
    assert modes.height_bonus(8, 3) == 0
    assert not b.is_personal_best(3)


def test_gates_and_empty_cells_are_never_gold():
    b = board(4)
    b.highest_earned = 9
    assert b.is_personal_best(9)
    for value in (TILE_EMPTY, GATE_XOR, GATE_OR, GATE_AND, GATE_NOT):
        assert not b.is_personal_best(value)


def test_no_spawn_can_ever_reach_the_height_floor():
    """The reason asking about the *value* is safe.

    The web tracks a specific tile instance so that a spawn landing on the
    best value cannot steal the gold; this build asks whether the value is the
    best one earned. The two can only disagree if a spawn is able to produce a
    value at or above the floor — so check every value every table can hand
    out, at every width, against that width's floor. Exhaustive rather than
    sampled: it is 100 rolls across 8 widths and it is the whole argument.
    """
    for bits in range(2, modes.MAX_BITS + 1):
        floor = modes.height_threshold(bits)
        for highest_on_board in range(0, modes.max_value(bits) + 1):
            for roll in range(100):
                spawned = modes.spawn_value(bits, highest_on_board, roll)
                assert spawned < floor, (
                    f"{bits}-bit spawns {spawned}, at or above the {floor} "
                    f"floor — a spawned tile could be gilded"
                )
