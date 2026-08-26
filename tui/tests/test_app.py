"""The terminal front end, driven headlessly.

These cover what ``test_board.py`` cannot: that the rules are wired to the
screen correctly. They need the engine and its terminal extra, and are skipped
without them so the rule tests still run on a bare checkout.

Textual's ``run_test`` pilot gives a real app with a real event loop and a real
size, so key handling, the frame loop and resize are exercised as they are in
play — no mocking of the parts most likely to break.
"""

import asyncio

import pytest

pytest.importorskip("textual", reason='needs: pip install -e ".[dev]" with texastoast[tui]')

from boole import modes  # noqa: E402
from boole.app import MIN_COLS, MIN_ROWS, BooleApp, tile_colors  # noqa: E402
from boole.board import (  # noqa: E402
    GATE_NOT,
    GATE_OR,
    GATE_XOR,
    TILE_EMPTY,
    Direction,
)


def buffer_text(app: BooleApp) -> str:
    return app.game.surface.buffer.to_text()


def blank_board(app: BooleApp) -> None:
    app.board.cells = [[TILE_EMPTY] * 4 for _ in range(4)]


async def _piloted(app: BooleApp, size=(80, 24)):
    """Start the Textual app for ``app`` and hand back its pilot context."""
    from texastoast.core.tui_game import _GameApp

    textual_app = _GameApp(app.game, app.game.surface)
    app.game._app = textual_app
    return textual_app.run_test(size=size)


def run(coro):
    return asyncio.run(coro)


# ── Rendering ───────────────────────────────────────────────────────


def test_the_board_and_panel_render():
    async def go():
        app = BooleApp(mode_key="nibble", seed=7)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            text = buffer_text(app)
            assert "GEORGE BOOLE HAS ENTERED THE CHAT" in text
            assert "SCORE" in text
            assert "nibble" in text
            assert "XOR" in text
            app.game.quit()

    run(go())


def test_keys_move_the_board_and_score():
    async def go():
        app = BooleApp(mode_key="nibble", seed=7)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            for key in ["left", "up", "right", "down"] * 4:
                await pilot.press(key)
                await asyncio.sleep(0.06)
            assert app.board.score > 0
            app.game.quit()

    run(go())


def test_a_too_small_terminal_says_so_instead_of_clipping():
    async def go():
        app = BooleApp(seed=1)
        async with await _piloted(app, size=(MIN_COLS, MIN_ROWS)) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.2)
            assert "too small" not in buffer_text(app)

            await pilot.resize_terminal(MIN_COLS - 1, MIN_ROWS)
            await asyncio.sleep(0.2)
            assert "too small" in buffer_text(app)

            await pilot.resize_terminal(100, 30)
            await asyncio.sleep(0.2)
            text = buffer_text(app)
            assert "too small" not in text
            assert "GEORGE BOOLE" in text
            app.game.quit()

    run(go())


def test_resizing_does_not_corrupt_the_layout():
    async def go():
        app = BooleApp(seed=1)
        async with await _piloted(app, size=(80, 24)) as pilot:
            await pilot.pause()
            for width, height in [(120, 40), (59, 20), (90, 26)]:
                await pilot.resize_terminal(width, height)
                await asyncio.sleep(0.2)
                assert app.r.width == width
                assert app.r.height == height
                # Every line must fit the terminal — a stale wider buffer
                # would show up as an over-long row.
                for line in buffer_text(app).split("\n"):
                    assert len(line) <= width
            app.game.quit()

    run(go())


def test_the_game_over_banner_renders():
    async def go():
        app = BooleApp(seed=1)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            app.over = True
            app.board.score = 1234
            app.render()
            assert "GAME OVER — 1234 points." in buffer_text(app)
            app.game.quit()

    run(go())


# ── Game flow ───────────────────────────────────────────────────────


def test_gauntlet_climbs_from_two_bit_to_eight_and_stops():
    app = BooleApp(mode_key="gauntlet", seed=3)
    seen = [app.board.bits]
    for _ in range(8):
        blank_board(app)
        app.board.cells[0][0] = app.board.max_value
        app.board.cells[0][1] = GATE_NOT
        app.do_move(Direction.LEFT)
        seen.append(app.board.bits)
    assert seen == [2, 3, 4, 5, 6, 7, 8, 8, 8]


def test_a_merge_onto_the_ceiling_marks_the_rainbow_tile():
    app = BooleApp(mode_key="gauntlet", seed=3)
    blank_board(app)
    app.board.cells[0][0] = 1
    app.board.cells[0][1] = GATE_OR
    app.board.cells[0][2] = 2          # 1 OR 2 = 3, the 2-bit ceiling
    app.do_move(Direction.LEFT)
    assert app.board.last_upgraded
    assert app.board.rainbow_at == (0, 0)
    assert app.board.cells[0][0] == 3


def test_not_of_the_ceiling_promotes_but_leaves_no_tile_to_mark():
    # It clears the tile, so there is nothing to paint. The Wii's identical
    # search finds nothing here either — this is faithful, not a miss.
    app = BooleApp(mode_key="gauntlet", seed=3)
    blank_board(app)
    app.board.cells[0][0] = 3
    app.board.cells[0][1] = GATE_NOT
    app.do_move(Direction.LEFT)
    assert app.board.last_upgraded
    assert app.board.rainbow_at == (-1, -1)


def test_a_fixed_mode_never_marks_a_rainbow():
    app = BooleApp(mode_key="crumb", seed=3)
    blank_board(app)
    app.board.cells[0][0] = 1
    app.board.cells[0][1] = GATE_OR
    app.board.cells[0][2] = 2
    app.do_move(Direction.LEFT)
    assert not app.board.last_upgraded
    assert app.board.rainbow_at == (-1, -1)
    assert app.board.bits == 2


def test_a_no_op_move_neither_spawns_nor_scores():
    app = BooleApp(mode_key="nibble", seed=5)
    app.board.cells = [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    before = [row[:] for row in app.board.cells]
    score = app.board.score
    app.do_move(Direction.LEFT)
    assert app.board.cells == before
    assert app.board.score == score


def test_a_board_that_cannot_move_ends_the_run():
    # Normally caught after a successful move; this is the path where the board
    # arrives dead, which would otherwise leave the player with no banner.
    app = BooleApp(mode_key="nibble", seed=5)
    app.board.cells = [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    app.do_move(Direction.LEFT)
    assert app.over


def test_an_interior_gate_keeps_a_full_board_alive():
    app = BooleApp(mode_key="nibble", seed=5)
    app.board.cells = [[1, 2, 1, 2], [2, GATE_XOR, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    app.do_move(Direction.LEFT)
    assert not app.over


def test_restart_deals_two_tiles_and_clears_the_score():
    app = BooleApp(mode_key="nibble", seed=11)
    app.board.score = 500
    app.over = True
    app.restart()
    filled = sum(1 for row in app.board.cells for v in row if v != TILE_EMPTY)
    assert filled == 2
    assert app.board.score == 0
    assert not app.over


def test_switching_mode_restarts_at_that_width():
    app = BooleApp(mode_key="crumb", seed=11)
    app.set_mode(modes.MODES_BY_KEY["byte"])
    assert app.board.bits == 8
    assert app.board.max_value == 255
    assert app.mode.key == "byte"


def test_next_mode_wraps_around_the_list():
    app = BooleApp(mode_key="gauntlet", seed=11)
    app.next_mode()
    assert app.mode.key == modes.MODES[0].key


def test_the_flash_line_reports_what_a_move_was_worth():
    app = BooleApp(mode_key="nibble", seed=11)
    blank_board(app)
    app.board.cells[0][0] = 5
    app.board.cells[0][1] = GATE_OR
    app.board.cells[0][2] = 3
    app.do_move(Direction.LEFT)
    assert app.flash.startswith("+")
    assert "NEW HIGH" in app.flash


def test_a_seeded_run_is_reproducible():
    def play(seed):
        app = BooleApp(mode_key="nibble", seed=seed)
        for direction in list(Direction) * 5:
            app.do_move(direction)
        return [row[:] for row in app.board.cells], app.board.score

    assert play(99) == play(99)


# ── Colour mapping ──────────────────────────────────────────────────


def test_an_empty_tile_hides_its_glyph():
    bg, fg = tile_colors(TILE_EMPTY, 15)
    assert bg == fg


def test_gates_get_their_own_colour_not_a_ramp_position():
    gate_bg, _ = tile_colors(GATE_NOT, 15)
    for value in range(1, 16):
        assert tile_colors(value, 15)[0] != gate_bg


def test_the_ramp_spans_the_whole_width_in_every_mode():
    # Otherwise byte mode would live permanently at the cool end.
    for max_value in (3, 15, 255):
        low = tile_colors(1, max_value)[0]
        high = tile_colors(max_value, max_value)[0]
        assert low != high
