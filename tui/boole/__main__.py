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
        "-m", "--mode", default="nibble",
        choices=[mode.key for mode in modes.MODES],
        help="difficulty; each is a bit width, gauntlet climbs from 2-bit "
             "(default: %(default)s)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="fix the spawn sequence, for a reproducible run",
    )
    args = parser.parse_args()

    # Imported here, not at module scope, so --help works without the engine
    # or its terminal extra installed.
    from boole.app import run

    run(args.mode, args.seed)


if __name__ == "__main__":
    main()
