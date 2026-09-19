#!/usr/bin/env python3
"""Derive the magmacrunch media mark shown on the title screen.

    python ios/tools/make-logo.py        # needs Pillow

Writes `web/img/mc-logo.png`, so the browser game and the App Store bundle
both get it: `package.mjs` copies `web/` wholesale, and the website's
`make sync-george-boole` copies it into `arcade/`. It lives here because this
is where the other art generators live, not because it is iOS-only.

## Why it is derived rather than copied

The source, `assets/logos/MClogoNoText.png` in the website repo, is a 2500x2650
PNG of **pure black on transparency** -- 1.1MB, and invisible on this game's
near-black title screen. Two things have to happen to it:

  - Tint. Only the alpha channel carries the drawing, so the mark is redrawn
    as white from that alpha and the black is discarded entirely.
  - Shrink. It is displayed 32px tall. Shipping 1.1MB inside an offline
    bundle to draw a 32px mark would be most of the size the audio costs.

The result is a few KB, and regenerating it after a logo change is this one
command rather than somebody's memory of an image editor.
"""

import argparse
from pathlib import Path

from PIL import Image

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent
WEB = REPO / "web"

# The website repo, resolved the way package.mjs and make-art.py resolve it.
SOURCE_CANDIDATES = [
    REPO.parent / "website" / "assets" / "logos" / "MClogoNoText.png",
    REPO.parent.parent / "web" / "website" / "assets" / "logos" / "MClogoNoText.png",
]

# Three times the 32px it is drawn at, so it stays sharp on a 3x phone.
HEIGHT = 96
TINT = (255, 255, 255)


def find_source():
    for candidate in SOURCE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise SystemExit(
        "MClogoNoText.png not found. It lives in the website repo.\n"
        + "\n".join(f"  looked in {c}" for c in SOURCE_CANDIDATES)
    )


def build(source, height=HEIGHT):
    art = Image.open(source).convert("RGBA")
    alpha = art.getchannel("A")

    # The source has a wide transparent margin, which at this size would be
    # most of the picture.
    box = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
    if not box:
        raise SystemExit(f"{source} is entirely transparent")
    alpha = alpha.crop(box)

    width = max(1, round(alpha.width * height / alpha.height))
    alpha = alpha.resize((width, height), Image.LANCZOS)

    out = Image.new("RGBA", alpha.size, TINT + (0,))
    out.putalpha(alpha)
    return out


def main():
    ap = argparse.ArgumentParser(description="Derive the magmacrunch media mark.")
    ap.add_argument("--height", type=int, default=HEIGHT, help=f"pixels tall (default {HEIGHT})")
    args = ap.parse_args()

    source = find_source()
    mark = build(source, args.height)
    out = WEB / "img" / "mc-logo.png"
    out.parent.mkdir(exist_ok=True)
    mark.save(out, optimize=True)
    print(f"mark   {out.relative_to(REPO)}  {mark.size[0]}x{mark.size[1]}  "
          f"{out.stat().st_size / 1024:.1f}KB  (from {source})")


if __name__ == "__main__":
    main()
