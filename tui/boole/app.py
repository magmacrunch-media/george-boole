"""Wiring — the game, the renderer, and the scene stack.

Everything that draws lives in :mod:`boole.scenes`; everything that decides
lives in :mod:`boole.board`. This module holds them together and owns the
state that outlives a single run: which mode is selected, and the best score
in each.
"""

from __future__ import annotations

from texastoast.core.tui_game import TuiGame, TuiInput
from texastoast.scene import SceneStack

from boole import modes
from boole.scenes import GameScene, MenuScene

FPS = 20


class BooleApp:
    """Owns the terminal game and the screen stack."""

    def __init__(self, mode_key: str = "nibble", seed: int | None = None,
                 skip_menu: bool = False):
        self.seed = seed
        self.mode = modes.MODES_BY_KEY.get(mode_key, modes.MODES_BY_KEY["nibble"])
        #: Best score per mode key, for the life of this process.
        self.best: dict[str, int] = {}

        # hold_ms=0 gives edge semantics — one keystroke, one move. A decay
        # timer here would turn a single arrow press into a slide across the
        # board, because a terminal reports repeats but never releases.
        self.game = TuiGame(title="George Boole Has Entered The Chat",
                            fps=FPS, input_source=TuiInput(hold_ms=0))
        self.renderer = self.game.renderer

        self.stack = SceneStack()
        self.game.set_update(self.update)
        self.game.set_render(self.stack.render)

        # The menu is always the bottom of the stack, so Esc from a game has
        # somewhere to land and no scene needs an "in menu" flag.
        self.stack.push(MenuScene(self))
        if skip_menu:
            self.stack.push(GameScene(self, self.mode))

    # ── Scene transitions ───────────────────────────────────────────

    def start_mode(self, mode: modes.Mode) -> None:
        """Begin a run. Pushed over the menu, which waits underneath."""
        self.mode = mode
        self.stack.push(GameScene(self, mode))

    def to_menu(self) -> None:
        """Leave the current run. The menu is already there, under it."""
        if len(self.stack) > 1:
            self.stack.pop()

    def record_best(self, mode: modes.Mode, score: int) -> None:
        if score > self.best.get(mode.key, 0):
            self.best[mode.key] = score

    # ── Frame ───────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        """Route keys to the top scene, then run the stack's own update.

        Keys are drained here rather than bound individually because a terminal
        delivers them as a stream and the stack decides who gets them:
        ``dispatch_key`` reaches the top scene only, which is the same modality
        rule that governs updates.
        """
        for key in self.game.input.drain():
            self.stack.dispatch_key(key)
        self.stack.update(dt)

    # ── Introspection, for tests and callers ────────────────────────

    @property
    def scene(self):
        """The scene currently on top."""
        return self.stack.top

    @property
    def in_game(self) -> bool:
        return isinstance(self.stack.top, GameScene)


def run(mode_key: str = "nibble", seed: int | None = None,
        skip_menu: bool = False) -> None:
    BooleApp(mode_key, seed, skip_menu).game.start()
