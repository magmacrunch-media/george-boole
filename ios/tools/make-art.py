#!/usr/bin/env python3
"""Generate the app icon and launch images into the Xcode asset catalogs.

    python ios/tools/make-art.py        # needs Pillow

Both files it writes are binaries Capacitor shipped as placeholders, and a
binary in git with no way to remake it is a dead end the first time somebody
wants it a shade different. Hence a script: the art is source, not an artifact.

## Why not the existing art

`web/apple-touch-icon.png` is George Boole in pixel sunglasses, which is the
game's joke and the right image -- at 180x180. An app icon is 1024x1024 and
there is no larger copy, so it would have to be upscaled four times over, and
a photographic portrait upscaled that far is mush. The album art
(`assets/album-art/george-boole.jpg` in the website repo, 1200x1200) is the
right size and the right palette, but it is a wordmark: seven words of pixel
text that stop being words at 60x60, which is where an icon is actually read.

So the icon is drawn here, from the same palette, as the one thing the game
has that survives being tiny -- the four gates on a 2x2 board. The splash
keeps the wordmark, because a launch image is full-screen and text is legible.

## The pixels are deliberate

Everything is drawn at 128px and scaled up with NEAREST, so the edges stay
hard and the result is pixel art rather than a smooth vector shrunk down. The
glow is added afterwards, from a blurred copy of the upscaled art, which is
how the album art reads too: crisp pixel letters, soft bloom around them.

Press Start 2P has no glyphs for U+2295, U+2228 or U+2227 -- all three render
the same .notdef box, which is why the gates are drawn from primitives here
instead of typed. In the browser they work because the page falls through to a
system font, and a bundle cannot rely on that.
"""

from pathlib import Path

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
TILE_FILL = (18, 24, 48)


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


# ── glyphs, drawn from primitives at the small scale ─────────────────────────


def glyph_xor(d, box, colour, w):
    """Circle with a cross through it."""
    d.ellipse(box, outline=colour, width=w)
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    d.line([(x0 + w, cy), (x1 - w, cy)], fill=colour, width=w)
    d.line([(cx, y0 + w), (cx, y1 - w)], fill=colour, width=w)


def glyph_or(d, box, colour, w):
    """A V."""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    d.line([(x0, y0), (cx, y1)], fill=colour, width=w)
    d.line([(cx, y1), (x1, y0)], fill=colour, width=w)


def glyph_and(d, box, colour, w):
    """A caret -- the V inverted, which is exactly what the operator is."""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    d.line([(x0, y1), (cx, y0)], fill=colour, width=w)
    d.line([(cx, y0), (x1, y1)], fill=colour, width=w)


def glyph_not(d, box, colour, w):
    """Bar with a tick down from its right end."""
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    d.line([(x0, cy), (x1, cy)], fill=colour, width=w)
    d.line([(x1 - w // 2, cy), (x1 - w // 2, y1)], fill=colour, width=w)


GLYPHS = [glyph_xor, glyph_or, glyph_and, glyph_not]


def build_icon(size=1024, small=128):
    """2x2 of gate tiles. The one thing here that still reads at 60x60."""
    art = Image.new("RGBA", (small, small), (0, 0, 0, 0))
    d = ImageDraw.Draw(art)

    tile, gap = 44, 8
    span = tile * 2 + gap
    origin = (small - span) // 2
    stroke = 3

    for i, draw_glyph in enumerate(GLYPHS):
        col, row = i % 2, i // 2
        x = origin + col * (tile + gap)
        y = origin + row * (tile + gap)
        colour = CYAN if i % 2 == 0 else MAGENTA
        d.rectangle([x, y, x + tile, y + tile], fill=TILE_FILL, outline=colour, width=stroke)
        pad = 11
        draw_glyph(d, (x + pad, y + pad, x + tile - pad, y + tile - pad), colour, stroke)

    art = art.resize((size, size), Image.NEAREST)

    # iOS masks the icon to a rounded square (radius ~22.4% of the side) and
    # never shows the corners. The asset catalog previews the full square, so
    # art that runs into a corner looks fine right up until it is on a home
    # screen with its edges bitten off. Check rather than eyeball it.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * 0.2237), fill=255
    )
    clipped = Image.composite(
        Image.new("L", (size, size), 0), art.getchannel("A"), mask
    ).getbbox()
    if clipped:
        raise SystemExit(f"icon art is outside the iOS corner mask at {clipped}; pull it in.")

    out = gradient(size)
    out = screen(out, bloom(art, radius=size // 64, strength=0.85))
    out = screen(out, bloom(art, radius=size // 200, strength=1.0))
    out.alpha_composite(art)
    # App icons must be fully opaque -- iOS masks the corners itself, and an
    # alpha channel is rejected at upload rather than at review.
    return out.convert("RGB")


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
SAFE_WIDTH = 0.38


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

    lines = [("GEORGE", title, CYAN), ("BOOLE", title, CYAN), ("HAS ENTERED THE CHAT", tag, MAGENTA)]
    heights = [title.size, title.size, tag.size]
    gaps = [round(title.size * 0.35), round(title.size * 0.85)]
    total = sum(heights) + sum(gaps)

    y = (size - total) // 2
    widest = 0
    for i, (text, font, colour) in enumerate(lines):
        w = d.textlength(text, font=font)
        widest = max(widest, w)
        d.text(((size - w) / 2, y), text, font=font, fill=colour)
        y += heights[i] + (gaps[i] if i < len(gaps) else 0)

    # The check that the constant above is actually being honoured. 0.46 is the
    # narrowest band any current iPhone shows; refuse to write art that would
    # be cropped, since the asset catalog will happily preview it intact.
    if widest > size * 0.44:
        raise SystemExit(
            f"splash wordmark is {widest / size:.0%} of the square, past the "
            f"{0.44:.0%} safe width. scaleAspectFill would crop it on a phone."
        )
    print(f"  wordmark {widest / size:.0%} of the square (safe band is 46%)")

    out = screen(out, bloom(art, radius=size // 90, strength=0.8))
    out = screen(out, bloom(art, radius=size // 300, strength=1.0))
    out.alpha_composite(art)
    return out.convert("RGB")


def main():
    icon_dir = ASSETS / "AppIcon.appiconset"
    splash_dir = ASSETS / "Splash.imageset"
    if not icon_dir.is_dir() or not splash_dir.is_dir():
        raise SystemExit(f"asset catalogs not found under {ASSETS}. Run `npx cap add ios` first.")

    icon = build_icon()
    icon.save(icon_dir / "AppIcon-512@2x.png")
    print(f"wrote {icon_dir.name}/AppIcon-512@2x.png  {icon.size[0]}x{icon.size[1]}")

    splash = build_splash()
    # Capacitor registers the same image at 1x, 2x and 3x.
    for name in ("splash-2732x2732.png", "splash-2732x2732-1.png", "splash-2732x2732-2.png"):
        splash.save(splash_dir / name)
        print(f"wrote {splash_dir.name}/{name}  {splash.size[0]}x{splash.size[1]}")


if __name__ == "__main__":
    main()
