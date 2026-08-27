"""The screens, driven headlessly.

These cover what ``test_board.py`` cannot: that the rules are wired to the
screen correctly, and that the menu and the board hand off to each other. They
need the engine and its terminal extra, and are skipped without them so the
rule tests still run on a bare checkout.

Textual's ``run_test`` pilot gives a real app with a real event loop and a real
size, so key handling, the frame loop and resize are exercised as they are in
play — no mocking of the parts most likely to break.
"""

import asyncio

import pytest

pytest.importorskip("textual", reason='needs: pip install -e ".[dev]" with texastoast[tui]')

from texastoast.core.tui_host import TuiHost  # noqa: E402
from texastoast.ui import bigtext  # noqa: E402

from boole import (  # noqa: E402
    modes,
    scenes,  # noqa: E402
    theme,
)
from boole.app import BooleApp  # noqa: E402
from boole.arcade import GAME  # noqa: E402
from boole.board import (  # noqa: E402
    GATE_NOT,
    GATE_OR,
    GATE_XOR,
    TILE_EMPTY,
    Direction,
)
from boole.scenes import GameScene, MenuScene  # noqa: E402


def buffer_text(app: BooleApp) -> str:
    return app.host.game.surface.buffer.to_text()


class _Blank:
    """Stands in for whatever a launcher would have underneath a game."""

    def update(self, dt):
        pass

    def render(self):
        pass


def blank_board(scene: GameScene) -> None:
    scene.board.cells = [[TILE_EMPTY] * 4 for _ in range(4)]


def settle(app: BooleApp) -> None:
    """Apply the stack's pending push/pop, which the engine defers a frame."""
    app.host.stack.update(0.0)


def hosted(mode_key="nibble", seed=5) -> BooleApp:
    """A session on a real host, built the way the standalone command does."""
    host = TuiHost(title=GAME.info.title, fps=GAME.info.fps,
                   hold_ms=GAME.info.hold_ms)
    app = BooleApp(host, mode_key=mode_key, seed=seed)
    host.push_scene(app.root_scene)
    settle(app)
    return app


def game_app(mode_key="nibble", seed=5) -> tuple[BooleApp, GameScene]:
    app = hosted(mode_key, seed)
    app.start_mode(app.mode)
    settle(app)
    return app, app.host.scene


async def _piloted(app: BooleApp, size=(80, 24)):
    from texastoast.core.tui_game import _GameApp

    textual_app = _GameApp(app.host.game, app.host.game.surface)
    app.host.game._app = textual_app
    return textual_app.run_test(size=size)


def run(coro):
    return asyncio.run(coro)


# ── The stack ───────────────────────────────────────────────────────


def test_the_menu_is_the_bottom_of_the_stack():
    app = hosted(seed=1)
    assert isinstance(app.host.scene, MenuScene)
    assert not app.in_game


def test_naming_a_mode_starts_a_game_over_the_menu():
    app, scene = game_app("byte")
    assert app.in_game
    assert scene.board.bits == 8
    # The menu is still underneath, which is what Esc lands on.
    assert len(app.host.stack) == 2
    assert isinstance(app.host.stack.scenes[0], MenuScene)


def test_the_menu_opens_on_the_mode_already_selected():
    # Not at the top of the list: reopening the menu should put the cursor
    # where the player left it, not make them scroll back every time.
    app = hosted("byte", seed=1)
    assert app.host.scene.menu.selected_index == modes.MODES.index(
        modes.MODES_BY_KEY["byte"])


def test_choosing_a_mode_pushes_a_game():
    app = hosted("crumb", seed=1)
    menu = app.host.scene
    assert menu.menu.selected_index == 0
    menu.handle_key("down")
    menu.handle_key("enter")
    settle(app)
    assert app.in_game
    assert app.host.scene.mode is modes.MODES[1]


def test_escape_pops_back_to_the_menu():
    app, scene = game_app()
    scene.handle_key("escape")
    settle(app)
    assert isinstance(app.host.scene, MenuScene)
    assert len(app.host.stack) == 1


def test_the_menu_is_usable_again_after_a_game_is_popped():
    # Menu.confirm() hides the menu as it fires, so without on_resume the
    # screen underneath comes back empty.
    app = hosted(seed=1)
    app.host.scene.handle_key("enter")
    settle(app)
    assert app.in_game

    app.host.scene.handle_key("escape")
    settle(app)
    menu = app.host.scene
    assert menu.menu.active, "the menu should be live again, not blank"


def test_a_game_is_not_updated_while_the_menu_is_on_top():
    # Modality is the stack: popping the game means it stops getting frames,
    # with no flag anywhere saying so.
    app, scene = game_app()
    before = scene.frame
    app.host.stack.update(0.1)
    assert scene.frame > before

    scene.handle_key("escape")
    settle(app)
    frozen = scene.frame
    for _ in range(5):
        app.host.stack.update(0.1)
    assert scene.frame == frozen


def test_keys_reach_only_the_top_scene():
    app, scene = game_app()
    menu = app.host.stack.scenes[0]
    selected = menu.menu.selected_index

    app.host.stack.dispatch_key("down")          # a menu key, while a game is up
    assert menu.menu.selected_index == selected


# ── Menu rendering ──────────────────────────────────────────────────


def test_the_menu_screen_renders_every_mode():
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            text = buffer_text(app)
            # 80x24 gets the game's own title-card treatment: the name in
            # block letters, the rest of it in text underneath.
            assert bigtext.lines("GEORGE BOOLE")[0] in text
            assert "HAS ENTERED THE CHAT" in text
            assert "how to play" in text
            for mode in modes.MODES:
                assert mode.name in text, f"{mode.name} missing from the menu"
            app.host.quit()

    run(go())


def test_every_rung_of_the_ladder_spells_the_whole_name():
    """A title that fits by dropping half of itself is not the title. What the
    ladder trades away is how much is drawn rather than typed."""
    for big, rest in theme.TITLE_LADDER:
        spelled = (big.replace("\n", " ") + " " + rest).split()
        assert spelled == theme.BANNER.split(), f"{big!r} + {rest!r}"


def test_a_tall_terminal_draws_the_whole_name_in_block_letters():
    """The puzzles card on magmacrunch.com breaks it over three lines, and
    with the rows to spare that is what this does too."""
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(80, 38)) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            text = buffer_text(app)
            for word in ("GEORGE BOOLE", "HAS ENTERED", "THE CHAT"):
                assert bigtext.lines(word)[0].strip() in text, word
            assert "HAS ENTERED THE CHAT" not in text, "no text rung needed here"
            assert "how to play" in text
            app.host.quit()

    run(go())


def test_the_title_never_lands_where_the_menu_will_draw():
    """The engine's Menu centres itself vertically, so the room a title has
    moves with the window. Reserving a fixed number of rows would let a tall
    terminal draw a title the menu then paints over."""
    from boole.scenes import _menu_box_top

    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(80, 30)) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            r = app.renderer
            top = _menu_box_top(r)
            buf = app.host.game.surface.buffer
            rows = buf.to_text().split("\n")
            below = "".join(rows[top:])
            assert "crumb" in below, "the box does not start where we think"
            app.host.quit()

    run(go())


def test_a_short_terminal_gets_the_plain_banner_instead_of_block_letters():
    """The mode menu is eight rows of list inside a box. A title that pushed
    it off the screen would be a title nobody could get past."""
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(theme.MENU_MIN_COLS,
                                             theme.MENU_MIN_ROWS)) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            text = buffer_text(app)
            assert theme.BANNER in text
            assert bigtext.lines("GEORGE BOOLE")[0].strip() not in text
            assert "crumb" in text, "the menu is still reachable"
            app.host.quit()

    run(go())


def test_menu_rows_carry_the_bit_width_not_just_the_name():
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            text = buffer_text(app)
            assert "4-bit" in text
            assert "ceiling 15" in text
            assert "climbs 2→8-bit" in text
            app.host.quit()

    run(go())


def test_the_selection_marker_follows_the_arrow_keys():
    async def go():
        app = hosted("crumb", seed=1)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            assert "> crumb" in buffer_text(app)

            await pilot.press("down")
            await asyncio.sleep(0.15)
            assert "> trit" in buffer_text(app)

            await pilot.press("up")
            await asyncio.sleep(0.15)
            assert "> crumb" in buffer_text(app)
            app.host.quit()

    run(go())


def test_enter_starts_the_highlighted_mode_end_to_end():
    async def go():
        app = hosted("crumb", seed=1)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            await asyncio.sleep(0.25)
            assert app.in_game
            # Opened on crumb, two rows down is nibble.
            assert app.host.scene.mode.key == "nibble"
            assert "SCORE" in buffer_text(app)
            app.host.quit()

    run(go())


def test_escape_from_a_game_shows_the_menu_again_end_to_end():
    async def go():
        app = hosted("crumb", seed=1)
        app.start_mode(app.mode)
        settle(app)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            assert "SCORE" in buffer_text(app)

            await pilot.press("escape")
            await asyncio.sleep(0.25)
            assert "how to play" in buffer_text(app)
            app.host.quit()

    run(go())


def test_a_too_small_terminal_says_so_on_both_screens():
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(30, 10)) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            assert "too small" in buffer_text(app)

            await pilot.resize_terminal(100, 30)
            await asyncio.sleep(0.25)
            assert "how to play" in buffer_text(app)

            await pilot.press("enter")
            await asyncio.sleep(0.25)
            await pilot.resize_terminal(40, 12)
            await asyncio.sleep(0.25)
            assert "too small" in buffer_text(app)
            app.host.quit()

    run(go())


# ── Board rendering ─────────────────────────────────────────────────


def test_the_board_and_panel_render():
    async def go():
        app, _ = game_app()
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            text = buffer_text(app)
            assert theme.BANNER in text
            assert "SCORE" in text
            assert "XOR" in text
            app.host.quit()

    run(go())


def test_glyphs_keep_the_background_of_the_tile_they_sit_on():
    # The bug this guards: text used to overwrite the cell background, so every
    # number sat in a black box punched through its own tile.
    async def go():
        app, scene = game_app()
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            buf = app.host.game.surface.buffer
            holes = [
                (x, y) for y in range(buf.height) for x in range(buf.width)
                if buf.get(x, y).char != " " and buf.get(x, y).bg is None
            ]
            assert holes == []
            app.host.quit()

    run(go())


def test_keys_move_the_board_and_score():
    async def go():
        app, scene = game_app(seed=7)
        async with await _piloted(app) as pilot:
            await pilot.pause()
            await asyncio.sleep(0.25)
            for key in ["left", "up", "right", "down"] * 4:
                await pilot.press(key)
                await asyncio.sleep(0.06)
            assert scene.board.score > 0
            app.host.quit()

    run(go())


def test_resizing_does_not_corrupt_the_layout():
    async def go():
        app, _ = game_app()
        async with await _piloted(app, size=(80, 24)) as pilot:
            await pilot.pause()
            for width, height in [(120, 40), (59, 20), (90, 26)]:
                await pilot.resize_terminal(width, height)
                await asyncio.sleep(0.2)
                assert app.renderer.width == width
                assert app.renderer.height == height
                for line in buffer_text(app).split("\n"):
                    assert len(line) <= width
            app.host.quit()

    run(go())


def test_the_game_over_banner_renders():
    async def go():
        app, scene = game_app()
        async with await _piloted(app) as pilot:
            await pilot.pause()
            scene.over = True
            scene.board.score = 1234
            scene.render()
            assert "GAME OVER — 1234 points." in buffer_text(app)
            app.host.quit()

    run(go())


# ── Game flow ───────────────────────────────────────────────────────


def test_gauntlet_climbs_from_two_bit_to_eight_and_stops():
    _, scene = game_app("gauntlet", seed=3)
    seen = [scene.board.bits]
    for _ in range(8):
        blank_board(scene)
        scene.board.cells[0][0] = scene.board.max_value
        scene.board.cells[0][1] = GATE_NOT
        scene.do_move(Direction.LEFT)
        seen.append(scene.board.bits)
    assert seen == [2, 3, 4, 5, 6, 7, 8, 8, 8]


def test_a_merge_onto_the_ceiling_marks_the_rainbow_tile():
    _, scene = game_app("gauntlet", seed=3)
    blank_board(scene)
    scene.board.cells[0][0] = 1
    scene.board.cells[0][1] = GATE_OR
    scene.board.cells[0][2] = 2          # 1 OR 2 = 3, the 2-bit ceiling
    scene.do_move(Direction.LEFT)
    assert scene.board.last_upgraded
    assert scene.board.rainbow_at == (0, 0)
    assert scene.board.cells[0][0] == 3


def test_not_of_the_ceiling_promotes_but_leaves_no_tile_to_mark():
    # It clears the tile, so there is nothing to paint. The Wii's identical
    # search finds nothing here either — this is faithful, not a miss.
    _, scene = game_app("gauntlet", seed=3)
    blank_board(scene)
    scene.board.cells[0][0] = 3
    scene.board.cells[0][1] = GATE_NOT
    scene.do_move(Direction.LEFT)
    assert scene.board.last_upgraded
    assert scene.board.rainbow_at == (-1, -1)


def test_a_fixed_mode_never_marks_a_rainbow():
    _, scene = game_app("crumb", seed=3)
    blank_board(scene)
    scene.board.cells[0][0] = 1
    scene.board.cells[0][1] = GATE_OR
    scene.board.cells[0][2] = 2
    scene.do_move(Direction.LEFT)
    assert not scene.board.last_upgraded
    assert scene.board.rainbow_at == (-1, -1)
    assert scene.board.bits == 2


def test_a_no_op_move_neither_spawns_nor_scores():
    _, scene = game_app()
    scene.board.cells = [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    before = [row[:] for row in scene.board.cells]
    score = scene.board.score
    scene.do_move(Direction.LEFT)
    assert scene.board.cells == before
    assert scene.board.score == score


def test_a_board_that_cannot_move_ends_the_run():
    _, scene = game_app()
    scene.board.cells = [[1, 2, 1, 2], [2, 1, 2, 1], [1, 2, 1, 2], [2, 1, 2, 1]]
    scene.do_move(Direction.LEFT)
    assert scene.over


def test_an_interior_gate_keeps_a_full_board_alive():
    _, scene = game_app()
    scene.board.cells = [[1, 2, 1, 2], [2, GATE_XOR, 2, 1],
                         [1, 2, 1, 2], [2, 1, 2, 1]]
    scene.do_move(Direction.LEFT)
    assert not scene.over


def test_restart_deals_two_tiles_and_clears_the_score():
    _, scene = game_app(seed=11)
    scene.board.score = 500
    scene.over = True
    scene.restart()
    filled = sum(1 for row in scene.board.cells for v in row if v != TILE_EMPTY)
    assert filled == 2
    assert scene.board.score == 0
    assert not scene.over


def test_the_flash_line_reports_what_a_move_was_worth():
    _, scene = game_app(seed=11)
    blank_board(scene)
    scene.board.cells[0][0] = 5
    scene.board.cells[0][1] = GATE_OR
    scene.board.cells[0][2] = 3
    scene.do_move(Direction.LEFT)
    assert scene.flash.startswith("+")
    assert "NEW HIGH" in scene.flash


def test_a_seeded_run_is_reproducible():
    def play(seed):
        _, scene = game_app(seed=seed)
        for direction in list(Direction) * 5:
            scene.do_move(direction)
        return [row[:] for row in scene.board.cells], scene.board.score

    assert play(99) == play(99)


# ── Best scores ─────────────────────────────────────────────────────


def test_the_best_score_is_kept_per_mode_and_survives_the_menu():
    app, scene = game_app("crumb", seed=11)
    scene.board.score = 250
    scene._end()
    assert app.best["crumb"] == 250

    scene.handle_key("escape")
    settle(app)
    app.start_mode(modes.MODES_BY_KEY["byte"])
    settle(app)
    assert app.best["crumb"] == 250
    assert app.host.scene.mode.key == "byte"
    assert app.best.get("byte", 0) == 0


def test_a_lower_score_does_not_replace_the_best():
    app, scene = game_app("crumb", seed=11)
    app.record_best(scene.mode, 400)
    app.record_best(scene.mode, 100)
    assert app.best["crumb"] == 400


# ── Colour mapping ──────────────────────────────────────────────────


def test_an_empty_tile_hides_its_glyph():
    bg, fg = theme.tile_colors(TILE_EMPTY, 15)
    assert bg == fg


def test_gates_get_their_own_colour_not_a_ramp_position():
    gate_bg, _ = theme.tile_colors(GATE_NOT, 15, gate=True)
    for value in range(1, 16):
        assert theme.tile_colors(value, 15)[0] != gate_bg


def test_the_ramp_spans_the_whole_width_in_every_mode():
    # Otherwise byte mode would live permanently at the cool end.
    for max_value in (3, 15, 255):
        low = theme.tile_colors(1, max_value)[0]
        high = theme.tile_colors(max_value, max_value)[0]
        assert low != high


# ── Launchable by an arcade ─────────────────────────────────────────
#
# The game has to work two ways: as its own command, and seated by a launcher
# that owns the terminal. The difference must be invisible to the game.


def test_the_entry_point_object_is_a_valid_arcade_game():
    from texastoast.arcade import ArcadeGame

    assert isinstance(GAME, ArcadeGame)


def test_the_declared_info_matches_what_the_game_actually_needs():
    assert GAME.info.key == "george-boole"
    assert GAME.info.min_cols == theme.MIN_COLS
    assert GAME.info.min_rows == theme.MIN_ROWS
    # Turn-based: edge input, or one arrow press slides across the board.
    assert GAME.info.hold_ms == 0


def test_starting_returns_a_scene_without_pushing_it():
    host = TuiHost(title="t", fps=20)
    scene = GAME.start(host)
    host.stack.update(0)
    assert isinstance(scene, MenuScene)
    assert host.scene is None, "start() must leave the pushing to the caller"


def test_a_launcher_can_seat_the_game_over_its_own_menu():
    host = TuiHost(title="arcade", fps=20)

    class ArcadeMenu:
        def update(self, dt):
            pass

        def render(self):
            pass

    arcade_menu = ArcadeMenu()
    host.push_scene(arcade_menu)
    host.seat(GAME)
    host.stack.update(0)
    assert isinstance(host.scene, MenuScene)

    # Esc from the game's mode menu returns to the arcade, not the shell.
    host.scene.handle_key("escape")
    host.stack.update(0)
    assert host.scene is arcade_menu


def test_escape_from_the_mode_menu_ends_a_standalone_session():
    # Same key, same call — but with nothing underneath there is nowhere to go
    # but out, and the host decides that, not the game.
    host = TuiHost(title="t", fps=20)
    quit_calls = []
    host.quit = lambda: quit_calls.append(1)
    host.seat(GAME)
    host.stack.update(0)

    host.scene.handle_key("escape")
    assert quit_calls == [1]


def test_seating_applies_the_declared_frame_rate_and_input():
    from texastoast.core.loop import GameLoop
    from texastoast.core.scheduler import ManualScheduler

    host = TuiHost(title="t", fps=60, hold_ms=999)
    host._game._loop = GameLoop(ManualScheduler(), lambda dt: None,
                                lambda: None, fps=60)
    host.seat(GAME)
    assert round(host.game.loop.target_fps) == GAME.info.fps
    assert host.input.hold_ms == GAME.info.hold_ms


def test_a_seated_game_plays():
    host = TuiHost(title="t", fps=20)
    host.push_scene(_Blank())      # stand in for an arcade menu
    host.seat(GAME)
    host.stack.update(0)

    host.scene.handle_key("enter")          # start the highlighted mode
    host.stack.update(0)
    assert isinstance(host.scene, GameScene)

    for key in ["left", "up", "right", "down"] * 3:
        host.scene.handle_key(key)
    assert host.scene.board.score >= 0

# ── How to play ─────────────────────────────────────────────────────


def test_the_menu_offers_the_rules_under_the_modes():
    """The row is not a mode, and _chose has to tell it apart by index."""
    app = hosted(seed=1)
    menu = app.host.scene
    assert menu.menu._items[-1]["label"] == scenes.HOW_TO_PLAY
    assert len(menu.menu._items) == len(modes.MODES) + 1


def test_choosing_it_opens_the_rules_rather_than_a_game():
    app = hosted(seed=1)
    menu = app.host.scene
    menu.menu._selected = len(modes.MODES)
    menu.handle_key("enter")
    settle(app)
    assert isinstance(app.host.scene, scenes.RulesScene)
    assert not app.in_game


def test_h_opens_the_rules_too():
    app = hosted(seed=1)
    app.host.scene.handle_key("h")
    settle(app)
    assert isinstance(app.host.scene, scenes.RulesScene)


def test_any_other_key_goes_back_to_the_menu():
    app = hosted(seed=1)
    app.host.scene.handle_key("h")
    settle(app)
    app.host.scene.handle_key("x")
    settle(app)
    assert isinstance(app.host.scene, MenuScene)


def test_the_rules_scroll_rather_than_truncating():
    """Laid out at 80 columns the rules run past a standard terminal, so a
    screen that stopped would lose overflow and Gauntlet - the two headings a
    new player most needs, being the parts not obvious from the board."""
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("h")
            await asyncio.sleep(0.3)
            top = buffer_text(app)
            assert "MOVES" in top
            assert "more" in top, "should say there is more below"

            for _ in range(30):
                await pilot.press("down")
            await asyncio.sleep(0.3)
            end = buffer_text(app)
            assert "GAUNTLET" in end
            for gate in ("XOR", "OR", "AND", "NOT"):
                assert gate in end, f"{gate} missing from the gate table"
            app.host.quit()

    run(go())


def test_the_rules_never_write_over_their_own_hint():
    """The viewport is the height less five rows. One out and a line of rules
    lands on the hint, which is how it was first written."""
    async def go():
        app = hosted(seed=1)
        async with await _piloted(app, size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("h")
            await asyncio.sleep(0.3)
            rows = buffer_text(app).splitlines()
            hint = rows[app.renderer.height - 2]
            assert hint.strip().startswith("↑↓ scroll"), hint
            assert "goes back" in hint
            app.host.quit()

    run(go())


def test_scrolling_stops_at_both_ends():
    app = hosted(seed=1)
    app.host.scene.handle_key("h")
    settle(app)
    rules = app.host.scene
    rules.handle_key("up")
    assert rules.offset == 0, "scrolled above the top"
    for _ in range(200):
        rules.handle_key("down")
    assert rules.offset == rules._max_offset()
    assert isinstance(app.host.scene, scenes.RulesScene), "still on the rules"
