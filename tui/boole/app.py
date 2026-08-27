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

from boole import modes
from boole.scenes import GameScene, MenuScene


class BooleApp:
    """A session of George Boole, drawing on somebody else's terminal."""

    def __init__(self, host: Any, mode_key: str = "nibble",
                 seed: int | None = None):
        self.host = host
        self.seed = seed
        self.mode = modes.MODES_BY_KEY.get(mode_key, modes.MODES_BY_KEY["nibble"])
        #: Best score per mode key, for as long as this session lasts.
        self.best: dict[str, int] = {}

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

    def record_best(self, mode: modes.Mode, score: int) -> None:
        if score > self.best.get(mode.key, 0):
            self.best[mode.key] = score

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
    from texastoast.core.tui_host import TuiHost

    from boole.arcade import GAME

    host = TuiHost(title=GAME.info.title, fps=GAME.info.fps,
                   hold_ms=GAME.info.hold_ms)
    app = BooleApp(host, mode_key, seed)
    host.push_scene(app.root_scene)
    if skip_menu:
        host.push_scene(GameScene(app, app.mode))
    host.run()
