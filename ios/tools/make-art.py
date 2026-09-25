#!/usr/bin/env python3
"""Generate the launch image into the Xcode asset catalog.

    python ios/tools/make-art.py        # needs Pillow

The file it writes is a binary Capacitor shipped as a placeholder, and a
binary in git with no way to remake it is a dead end the first time somebody
wants it a shade different. Hence a script: the art is source, not an artifact.

The app icon is not drawn here any more; make-boole-pixel.py owns it. This file
used to draw one too -- the four gates on a 2x2 board -- and the pixel portrait
script, added on 2026-09-13, overwrote it -- so the icon on disk depended on
which had run last, and this docstring described a picture that was gone.

## The pixels are deliberate

The wordmark is Press Start 2P drawn at full size, with the glow added
afterwards from a blurred copy of the art, which is how the album art reads
too: crisp pixel letters, soft bloom around them.
"""

from pathlib import Path

import argparse

from PIL import Image, ImageDraw, ImageFilter, ImageFont

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent
ASSETS = IOS / "App" / "App" / "App" / "Assets.xcassets"

# The website repo carries the self-hosted font; package.mjs resolves it the
# same way. Kept in step with the candidates there.
FONT_CANDIDATES = [
    REPO.parent / "website" / "fonts" / "PressStart2P-Regular.ttf",
    REPO.parent.parent / "web" / "website" / "fonts" / "PressStart2P-Regular.ttf",
]

# The title card's gradient, top to bottom, and the album art's two accents.
TOP = (10, 10, 20)
MID = (22, 33, 62)
BOT = (26, 26, 46)
CYAN = (77, 227, 247)
MAGENTA = (232, 56, 200)
# Quiet beside the two accents, the way the title screen's line is quiet
# beside the start button.
PUBLISHER = (150, 142, 176)


def gradient(size):
    """Vertical three-stop gradient with the scanlines the whole game wears."""
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        if t < 0.5:
            a, b, u = TOP, MID, t * 2
        else:
            a, b, u = MID, BOT, (t - 0.5) * 2
        d.line([(0, y), (size, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * u) for i in range(3)))

    # Scanlines: every other line at the pixel scale, darkened rather than
    # drawn, so they read as a CRT and not as stripes.
    step = max(2, size // 180)
    dark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    for y in range(0, size, step * 2):
        dd.rectangle([0, y, size, y + step - 1], fill=(0, 0, 0, 28))
    return Image.alpha_composite(img.convert("RGBA"), dark)


def bloom(art, radius, strength=1.0):
    """A blurred copy of the art, to be screened underneath it."""
    glow = art.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        alpha = glow.getchannel("A").point(lambda v: min(255, round(v * strength)))
        glow.putalpha(alpha)
    return glow


def screen(base, layer):
    """Composite `layer` onto `base` the way light adds, not the way paint does."""
    out = base.copy()
    out.alpha_composite(layer)
    return out


def load_font(px):
    for c in FONT_CANDIDATES:
        if c.exists():
            return ImageFont.truetype(str(c), px)
    raise SystemExit(
        "PressStart2P-Regular.ttf not found. It lives in the website repo.\n"
        + "\n".join(f"  looked in {c}" for c in FONT_CANDIDATES)
    )


# How much of the square launch image is actually on screen.
#
# LaunchScreen.storyboard scales this with `scaleAspectFill`, so on a portrait
# phone the square is scaled to fill the HEIGHT and the width is cropped to the
# device's aspect ratio. A 2732 square on a 1320x2868 iPhone shows a 1257px
# band -- 46% of the width. Anything wider than that is cut off at both ends,
# and the first draft of this file put the wordmark at 52%, which would have
# clipped "GEORGE" on every modern iPhone while looking perfect in the asset
# catalog. 38% leaves a margin inside the narrowest band.
#
# Note this one is a SIZING fraction: the lines below are built from it. The
# limits the art is then checked against are the two below, and they are
# separate numbers. makemecookies calls its limits SAFE_WIDTH/SAFE_HEIGHT,
# which is the same name for a different thing, and confusing the two is how
# its guards ended up on the wrong axes.
SAFE_WIDTH = 0.38

# The crop limits, checked after layout. Named because a shared tool reads
# them: `hypnopompia/tools/check-launch-crop.mjs` derives what each supported
# orientation actually shows from Info.plist and fails if either of these
# allows more than that. Both games declare these two names, in whichever file
# draws their launch image.
#
# Which axis each one guards is decided by Info.plist, NOT by copying the other
# game. This app's iPhone is portrait, so `scaleAspectFill` crops the WIDTH at
# 46%; the height is cropped only by a landscape iPad, at about 75%.
# makemecookies is landscape and has these two figures the other way round.
CROP_WIDTH = 0.44
CROP_HEIGHT = 0.70


def load_mark():
    """The magmacrunch media mark, white on transparency.

    make-logo.py derives it from the website's black-on-transparent original
    and writes it into web/, which is where the title screen reads it from.
    Using that file rather than the original keeps one definition of what the
    mark looks like; if it is missing, this returns None and the splash is
    drawn without it rather than failing over a decoration.
    """
    mark = REPO / "web" / "img" / "mc-logo.png"
    if not mark.exists():
        print(f"  no mark at {mark.relative_to(REPO)} -- run tools/make-logo.py")
        return None
    return Image.open(mark).convert("RGBA")


def build_splash(size=2732):
    """The wordmark, as on the album art. Full screen, so text is fine here."""
    out = gradient(size)
    art = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(art)

    # The font is monospaced, so the two title lines line up on their own and
    # the tagline scales off the same unit. "HAS ENTERED THE CHAT" is 20
    # characters against "GEORGE"'s 6, so 0.30 lands it at the same width --
    # which is what the album art does, and why the two edges align.
    probe = load_font(100)
    unit = d.textlength("GEORGE", font=probe) / 100
    title = load_font(round(size * SAFE_WIDTH / unit))
    tag = load_font(round(size * SAFE_WIDTH / unit * 0.30))

    # The publisher, as on the title screen. Part of the centred block rather
    # than pinned near the square's bottom edge, because which edges survive
    # depends on the device: scaleAspectFill crops the sides on a portrait
    # phone and the top and bottom on a landscape iPad, so the only region
    # certain to be on screen is the middle of both axes.
    pub = load_font(round(size * SAFE_WIDTH / unit * 0.22))

    lines = [
        ("GEORGE", title, CYAN),
        ("BOOLE", title, CYAN),
        ("HAS ENTERED THE CHAT", tag, MAGENTA),
        ("MAGMACRUNCH MEDIA", pub, PUBLISHER),
    ]
    heights = [title.size, title.size, tag.size, pub.size]
    gaps = [round(title.size * 0.35), round(title.size * 0.85), round(title.size * 1.05)]
    total = sum(heights) + sum(gaps)

    # The mark sits above the publisher's name, the same pairing the title
    # screen uses, and joins the block's height so the checks below cover it.
    mark = load_mark()
    mark_height = round(pub.size * 2.2) if mark else 0
    mark_gap = round(pub.size * 0.8) if mark else 0
    total += mark_height + mark_gap

    y = (size - total) // 2
    widest = 0
    for i, (text, font, colour) in enumerate(lines):
        if mark is not None and text == "MAGMACRUNCH MEDIA":
            scaled = mark.resize(
                (max(1, round(mark.width * mark_height / mark.height)), mark_height),
                Image.LANCZOS,
            )
            art.alpha_composite(scaled, ((size - scaled.width) // 2, y))
            widest = max(widest, scaled.width)
            y += mark_height + mark_gap

        w = d.textlength(text, font=font)
        widest = max(widest, w)
        d.text(((size - w) / 2, y), text, font=font, fill=colour)
        y += heights[i] + (gaps[i] if i < len(gaps) else 0)

    # The check that the constant above is actually being honoured. 0.46 is the
    # narrowest band any current iPhone shows; refuse to write art that would
    # be cropped, since the asset catalog will happily preview it intact.
    if widest > size * CROP_WIDTH:
        raise SystemExit(
            f"splash wordmark is {widest / size:.0%} of the square, past the "
            f"{CROP_WIDTH:.0%} safe width. scaleAspectFill would crop it on a phone."
        )
    print(f"  wordmark {widest / size:.0%} of the square (safe band is 46%)")

    # The same check on the other axis, which only started to matter with a
    # fourth line. A landscape iPad fills the width and crops the top and
    # bottom, showing about the middle 75% of the square's height.
    if total > size * CROP_HEIGHT:
        raise SystemExit(
            f"splash block is {total / size:.0%} of the square's height, past "
            f"{CROP_HEIGHT:.0%}. A landscape iPad shows about the middle 75%."
        )
    print(f"  block    {total / size:.0%} of the height (safe band is 75%)")

    out = screen(out, bloom(art, radius=size // 90, strength=0.8))
    out = screen(out, bloom(art, radius=size // 300, strength=1.0))
    out.alpha_composite(art)
    return out.convert("RGB")


# Capacitor registers the same image at 1x, 2x and 3x, and Contents.json
# references all three filenames.
NAMES = ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png")


def main():
    ap = argparse.ArgumentParser(description="Draw the launch image into the Xcode asset catalog.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the committed launch image is missing, malformed, or would crop")
    args = ap.parse_args()

    splash_dir = ASSETS / "Splash.imageset"
    if not splash_dir.is_dir():
        raise SystemExit(f"asset catalog not found under {ASSETS}. Run `npx cap add ios` first.")

    if args.check:
        # Drawn for its assertions, and the image is then thrown away.
        #
        # That is the whole point rather than a shortcut. build_splash() sizes
        # every line from SAFE_WIDTH and then checks the laid-out result
        # against the crop, and the font it measures comes from the WEBSITE
        # repo. A font swapped there changes the metrics and could push the
        # wordmark past the band a phone shows, with nothing in this repo
        # looking. This is what looks.
        #
        # What it cannot do is compare the drawn image to the committed one.
        # Press Start 2P goes through FreeType, which does not rasterise
        # identically across versions or platforms, so that comparison is true
        # only on the machine that last drew it -- see make-boards.py's header,
        # where the same check was tried and failed on every image in CI.
        build_splash()

        bad = 0
        for name in NAMES:
            path = splash_dir / name
            if not path.exists():
                print(f"MISS  {path.relative_to(REPO)}")
                bad += 1
                continue
            with Image.open(path) as im:
                if im.size != (2732, 2732):
                    print(f"WRONG {path.relative_to(REPO)} is {im.size[0]}x{im.size[1]}, not 2732x2732")
                    bad += 1

        # The three filenames are one image. Comparing them to each other is
        # portable in a way comparing them to a fresh draw is not, and a
        # half-finished regeneration is exactly how they would come apart.
        if not bad:
            blobs = {(splash_dir / n).read_bytes() for n in NAMES}
            if len(blobs) != 1:
                print(f"WRONG the {len(NAMES)} splash files are not the same image")
                bad += 1

        if bad:
            raise SystemExit("run: python ios/tools/make-art.py   and commit the result")
        print(f"launch image present as {len(NAMES)} identical files, and fits the crop")
        return

    splash = build_splash()
    for name in NAMES:
        splash.save(splash_dir / name)
        print(f"wrote {splash_dir.name}/{name}  {splash.size[0]}x{splash.size[1]}")


if __name__ == "__main__":
    main()
