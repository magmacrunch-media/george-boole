"""Wiring — what outlives a single run, and how the screens reach it.

Everything that draws lives in :mod:`boole.scenes`; everything that decides
lives in :mod:`boole.board`. This holds them together.

**The terminal is not owned here.** It belongs to a
:class:`~texastoast.core.tui_host.TuiHost`, which this is handed. That is what
lets the game run as its own command *and* be seated by a launcher without
knowing which happened: building the terminal, holding the scene stack and
routing keys is identical either way, so the engine does it and the game does
not have a second copy.

What is left here is genuinely this game's: which mode is selected, and the
best score in each.
"""

from __future__ import annotations

from typing import Any

from magmacrunch.engine.scores import ScoreBook

from boole import modes
from boole.scenes import GameScene, MenuScene


class BooleApp:
    """A session of George Boole, drawing on somebody else's terminal."""

    #: The key the browser build posts under, so a shared board later is a
    #: shared board and not two boards with the same name.
    SCORE_KEY = "george-boole"

    def __init__(self, host: Any, mode_key: str = "nibble",
                 seed: int | None = None, scores: ScoreBook | None = None):
        self.host = host
        self.seed = seed
        self.mode = modes.MODES_BY_KEY.get(mode_key, modes.MODES_BY_KEY["nibble"])

        #: The high score table, on disk and outliving the session.
        #:
        #: One board for the whole game rather than eight, with the mode kept
        #: in each entry. Eight boards would fragment a table nobody fills —
        #: crumb and byte are not different games, they are the same game at
        #: different widths, and a single ranked list says which width somebody
        #: was brave enough to play at.
        self.scores = scores or ScoreBook(self.SCORE_KEY)
        #: What the player last typed, so a second run does not ask again.
        self.initials = "AAA"
        #: Where the last recorded run landed, for the game-over screen.
        self.last_rank: int | None = None

        #: The mode menu. The caller pushes it — a game that pushed its own
        #: scene would take that decision away from whatever is seating it.
        self.root_scene = MenuScene(self)

    # ── What the scenes reach for ───────────────────────────────────

    @property
    def renderer(self):
        return self.host.renderer

    @property
    def game(self):
        """The terminal app.

        Named ``game`` because that is what the scenes called it when this
        class owned one. It is the host's now.
        """
        return self.host

    def start_mode(self, mode: modes.Mode) -> None:
        """Begin a run, over the menu, which waits underneath."""
        self.mode = mode
        self.host.push_scene(GameScene(self, mode))

    def show_rules(self) -> None:
        """The rules, over whatever is showing. Any key pops them."""
        from boole.scenes import RulesScene

        self.host.push_scene(RulesScene(self))

    def to_menu(self) -> None:
        """Leave the current run for the mode menu underneath it."""
        self.host.pop_scene()

    def leave(self) -> None:
        """Leave the game entirely.

        Popping the mode menu. Run on its own that is the last scene and the
        session ends; seated by a launcher the arcade menu is underneath and
        this returns to it. The game does not need to know which — see
        ``TuiHost.pop_scene``.
        """
        self.host.pop_scene()

    def best_in(self, mode_key: str) -> int:
        """The best score on record in one mode.

        Filtered out of the single board rather than read from a per-mode one.
        Read from the file each time rather than cached: the file is the truth,
        and a cache goes stale the moment anything else writes to it.
        """
        scores = [e.score for e in self.scores.load()
                  if e.extra.get("mode") == mode_key]
        return max(scores, default=0)

    def qualifies(self, score: int) -> bool:
        """Whether a score is worth asking for initials over."""
        return score > 0 and self.scores.qualifies(score)

    def record(self, mode: modes.Mode, score: int, initials: str | None = None):
        """Put a score on the board, under the mode it was set in."""
        self.initials = initials or self.initials
        result = self.scores.save(self.initials, score, mode=mode.key)
        self.last_rank = result.rank
        return result

    def show_scores(self) -> None:
        """The high score table, over the mode menu."""
        from boole.scenes import ScoresScene

        self.host.push_scene(ScoresScene(self))

    def enter_initials(self, mode: modes.Mode, score: int) -> None:
        """Ask who just did that, over the finished board."""
        from boole.scenes import InitialsScene

        self.host.push_scene(InitialsScene(self, mode, score))

    # ── Introspection, for tests ────────────────────────────────────

    @property
    def scene(self):
        return self.host.scene

    @property
    def in_game(self) -> bool:
        return isinstance(self.host.scene, GameScene)


def run(mode_key: str = "nibble", seed: int | None = None,
        skip_menu: bool = False) -> None:
    """Play George Boole as its own command."""
    from magmacrunch.engine.core.tui_host import TuiHost

    from boole.arcade import GAME

    host = TuiHost(title=GAME.info.title, fps=GAME.info.fps,
                   hold_ms=GAME.info.hold_ms)
    app = BooleApp(host, mode_key, seed)
    host.push_scene(app.root_scene)
    if skip_menu:
        host.push_scene(GameScene(app, app.mode))
    host.run()
