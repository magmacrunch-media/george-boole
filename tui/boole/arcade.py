"""What the arcade needs to know to launch this game.

The entry point a launcher resolves. Kept tiny and free of imports that cost
anything: a menu listing several games loads one of these per installed game
just to draw a row, and it should not pay for the game's rules or its screens
to do that.
"""

from __future__ import annotations

from typing import Any

from magmacrunch.engine.arcade import GameInfo

from boole import theme

INFO = GameInfo(
    key="george-boole",
    title="George Boole Has Entered The Chat",
    blurb="2048 played with logic gates — merge, invert, overflow.",
    # Turn-based: the board only changes when a key is pressed, and edge input
    # is what makes one arrow press move one square instead of sliding.
    fps=20,
    hold_ms=0,
    min_cols=theme.MIN_COLS,
    min_rows=theme.MIN_ROWS,
)


class BooleGame:
    """Satisfies :class:`texastoast.arcade.ArcadeGame`."""

    info = INFO

    def start(self, host: Any) -> Any:
        """The mode menu, ready to be pushed.

        Imported here rather than at module scope so that listing this game in
        an arcade menu does not drag in its scenes, its rules, or Textual.
        """
        from boole.app import BooleApp

        return BooleApp(host).root_scene


#: What the entry point resolves to. Stateless — a run's state belongs to the
#: BooleApp that :meth:`BooleGame.start` creates, so replaying makes a new one.
GAME = BooleGame()

__all__ = ["GAME", "INFO", "BooleGame"]
