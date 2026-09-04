"""``python -m boole`` — play George Boole in a terminal."""

from __future__ import annotations

import argparse

from boole import modes


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="boole",
        description="George Boole Has Entered The Chat - terminal version.",
    )
    parser.add_argument(
        "-m", "--mode", default=None,
        choices=[mode.key for mode in modes.MODES],
        help="skip the menu and start this mode; each is a bit width, and "
             "gauntlet climbs from 2-bit. Omit to choose from the title screen.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="fix the spawn sequence, for a reproducible run",
    )
    parser.add_argument(
        "--ascii", action="store_true", dest="ascii_only",
        help="draw with plain ASCII instead of block, arrow and suit "
             "glyphs. Detected automatically from the terminal's "
             "encoding; this forces it, for a font that lacks the "
             "pictures. MAGMACRUNCH_ASCII=1 says the same for every "
             "cabinet at once.",
    )
    args = parser.parse_args()

    # Imported here, not at module scope, so --help works without the engine
    # or its terminal extra installed.
    from boole.app import run

    # Naming a mode is an instruction to play it, so the menu would be in the
    # way. Esc still reaches it.
    run(args.mode or "nibble", args.seed,
        skip_menu=args.mode is not None, ascii_only=args.ascii_only)


if __name__ == "__main__":
    main()
