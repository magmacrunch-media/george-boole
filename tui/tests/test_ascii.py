"""The plain-ASCII fallback, drawn through a real host.

``magmacrunch.engine.ui.glyphs`` decides what this terminal can encode and
``TuiRenderer`` substitutes on the way into the cell buffer, so nothing in
boole asks the question and nothing here can check it by reading the
source. These drive the game and read the buffer back.

Skipped against an older engine rather than failed: the module under test is
in the dependency, and a checkout running against an installed 0.5.0 has not
broken anything -- it just cannot see this yet.
"""

import asyncio

import pytest

pytest.importorskip("textual", reason='needs: pip install -e ".[dev]"')
pytest.importorskip(
    "magmacrunch.engine.ui.glyphs",
    reason="glyph fallback arrived in magmacrunch 0.6.0",
)

from magmacrunch.engine import scores as score_mod  # noqa: E402
from magmacrunch.engine.core.tui_host import TuiHost  # noqa: E402
from magmacrunch.engine.ui.glyphs import Glyphs  # noqa: E402

from boole.arcade import GAME  # noqa: E402,F401

#: The strictest terminal there is. cp1252 and cp437 each keep a few of the
#: glyphs, which is the right answer and a weaker test -- this one leaves
#: nothing to survive by accident.
NOTHING = Glyphs(encoding="ascii")


@pytest.fixture(autouse=True)
def isolated_scores(tmp_path, monkeypatch):
    monkeypatch.setenv(score_mod.DATA_DIR_ENV, str(tmp_path))


def _hosted(glyphs):
    from boole.app import BooleApp
    from boole.scenes import GameScene

    host = TuiHost(title=GAME.info.title, fps=GAME.info.fps,
                   hold_ms=GAME.info.hold_ms, glyphs=glyphs)
    app = BooleApp(host, "nibble", 7)
    host.push_scene(app.root_scene)
    host.stack.update(0.0)
    return host, app, lambda: GameScene(app, app.mode)


async def _drawn(glyphs, into_game):
    """Every cell the game puts on screen, as text."""
    from magmacrunch.engine.core.tui_game import _GameApp

    host, app, make_game = _hosted(glyphs)
    if into_game:
        host.push_scene(make_game())
        host.stack.update(0.0)
    tapp = _GameApp(host.game, host.game.surface)
    host.game._app = tapp
    async with tapp.run_test(size=(80, 26)):
        await asyncio.sleep(0.4)
        text = host.game.surface.buffer.to_text()
        tapp.exit()
    host.quit()
    return text


def drawn(glyphs, into_game=False):
    return asyncio.run(_drawn(glyphs, into_game))


@pytest.mark.parametrize("into_game", [False, True], ids=["title", "game"])
def test_a_terminal_that_can_encode_nothing_still_gets_a_whole_screen(into_game):
    text = drawn(NOTHING, into_game)
    leaked = sorted({c for c in text if ord(c) > 126})
    assert not leaked, f"drawn as unicode on an ASCII terminal: {leaked}"
    assert text.strip(), "the screen came back empty, so this proves nothing"


@pytest.mark.parametrize("into_game", [False, True], ids=["title", "game"])
def test_the_plain_screen_is_laid_out_exactly_like_the_unicode_one(into_game):
    """Substitution happens after this game has measured, so a stand-in of a
    different width would move text off the layout computed for it."""
    plain = drawn(NOTHING, into_game).split("\n")
    rich = drawn(None, into_game).split("\n")
    assert len(plain) == len(rich)
    assert [len(row) for row in plain] == [len(row) for row in rich]


def test_a_capable_terminal_is_left_alone():
    """The fallback is a fallback. Nothing about it should reach a terminal
    that can draw the real glyphs."""
    text = drawn(Glyphs(encoding="utf-8"))
    assert any(ord(c) > 126 for c in text)


def test_the_four_gates_stay_four_different_characters():
    """This game needs the fallback more than its siblings do: the operators
    are the board rather than its decoration, and a board whose AND and XOR
    drew the same character would be unplayable rather than plain."""
    from magmacrunch.engine.ui.glyphs import GROUPS

    plain = set(GROUPS["logic"].values())
    assert len(plain) == 4, plain
    text = drawn(NOTHING, into_game=True)
    for char in plain:
        assert char in text, f"{char} never reached the screen"
