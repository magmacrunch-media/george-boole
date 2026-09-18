#!/usr/bin/env python3
"""George Boole in pixel sunglasses: the app icon, and the portrait the web
game uses on its loading and title screens.

    python ios/tools/make-boole-pixel.py          # app icon only
    python ios/tools/make-boole-pixel.py --web    # also the web portrait files

Two sprites, deliberately. PORTRAIT is the title-screen figure, drawn to be
seen at 96-128px on the game's own dark background. ICON is the same man
redrawn for a home screen, where he is 60pt on a wallpaper nobody chose for
him. The first icon was PORTRAIT scaled up, and at home-screen size it was a
dark blob: dark hair and a near-black coat on dark navy, and sunglasses --
the whole joke -- black on brown. What ICON changes, and why:

  - a bright magenta ground (the splash tagline's colour), so the dark
    figure reads as a silhouette on light and dark wallpaper alike, plus a
    deeper version of it as the dark-appearance icon, since iOS otherwise
    dims the bright one until the magenta is nearly black;
  - a one-cell outline around the figure, which is what keeps a pixel sprite
    legible at any scale;
  - cyan lenses with a white glint, so the sunglasses are the first thing
    seen rather than the last, and a cyan bow tie that echoes them;
  - head and shoulders only, filling the square, the coat running off the
    bottom like a portrait crop, and the outline kept clear of iOS's
    rounded corners.

Judge a change at 60, 120 and 180px, not at 1024: `--sheet <png>` writes
those sizes, masked, on a light and a dark wallpaper.

Outputs:
  - ios/App/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png
    and AppIcon-512@2x-dark.png
  - ios/assets/apple-touch-icon.png (180x180, the icon; package.mjs puts it in
    the bundle, where Safari's add-to-home-screen shows it)
  - with --web: web/apple-touch-icon.png (180x180) and web/img/boole-pixel.png
    (128x128), both from PORTRAIT. The site's icon is its own decision, so a
    plain run leaves web/ alone.

make-art.py draws the launch image. It used to draw the icon too, which is
how two scripts came to write the same file.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent
WEB = REPO / "web"
ASSETS = IOS / "App" / "App" / "App" / "Assets.xcassets"

# ── palette ──────────────────────────────────────────────────────────────────

SKIN = (210, 170, 130)
SKIN_SHADOW = (170, 130, 95)
HAIR = (55, 40, 30)
BEARD = (50, 35, 25)
COAT = (20, 20, 30)
SHIRT = (200, 200, 210)
GLASSES = (10, 10, 10)
GLASSES_LENS = (30, 60, 90)
TOP = (10, 10, 20)
MID = (22, 33, 62)
BOT = (26, 26, 46)
CYAN = (77, 227, 247)
MAGENTA = (232, 56, 200)

# ── 32x32 portrait ──────────────────────────────────────────────────────────

# Each row is 32 values.  0=background, 1=skin, 2=hair, 3=beard, 4=coat,
# 5=shirt, 6=glasses frame, 7=glasses lens, 8=skin shadow, 9=eye highlight
PORTRAIT = [
    # 0: background above head
    [0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0,0,0],
    # 1: top of head
    [0,0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0,0],
    # 2: hair widens
    [0,0,0,0,0,0,0,0,0,2,2,2,2,2,2,2,2,2,2,2,2,2,2,0,0,0,0,0,0,0,0,0],
    # 3: hair + forehead
    [0,0,0,0,0,0,0,0,2,2,2,1,1,1,1,1,1,1,1,1,1,2,2,2,0,0,0,0,0,0,0,0],
    # 4: forehead
    [0,0,0,0,0,0,0,2,2,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,0,0,0,0,0,0,0,0],
    # 5: forehead + temples
    [0,0,0,0,0,0,0,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,0,0,0,0,0,0,0,0],
    # 6: eyebrow line
    [0,0,0,0,0,0,0,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,0,0,0,0,0,0,0,0],
    # 7: eyes + glasses
    [0,0,0,0,0,0,0,2,1,6,6,6,6,6,1,1,6,6,6,6,6,1,1,2,0,0,0,0,0,0,0,0],
    # 8: glasses lenses
    [0,0,0,0,0,0,0,2,8,6,7,7,7,6,1,1,6,7,7,7,6,8,1,2,0,0,0,0,0,0,0,0],
    # 9: under glasses / nose bridge
    [0,0,0,0,0,0,0,2,8,6,6,6,6,6,1,1,6,6,6,6,6,8,1,2,0,0,0,0,0,0,0,0],
    # 10: nose
    [0,0,0,0,0,0,0,0,8,1,1,1,1,1,8,8,1,1,1,1,1,8,0,0,0,0,0,0,0,0,0,0],
    # 11: nose tip
    [0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0],
    # 12: mustache starts
    [0,0,0,0,0,0,0,0,0,1,3,3,3,3,3,3,3,3,3,3,1,0,0,0,0,0,0,0,0,0,0,0],
    # 13: mustache
    [0,0,0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0,0],
    # 14: mouth / upper lip
    [0,0,0,0,0,0,0,0,0,3,3,3,3,1,1,1,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0,0],
    # 15: beard
    [0,0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0],
    # 16: beard
    [0,0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0],
    # 17: beard widens
    [0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0],
    # 18: lower beard
    [0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0],
    # 19: chin / beard bottom
    [0,0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0],
    # 20: beard end + neck
    [0,0,0,0,0,0,0,0,0,3,3,3,3,3,3,3,3,3,3,3,3,0,0,0,0,0,0,0,0,0,0,0],
    # 21: neck
    [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0],
    # 22: collar
    [0,0,0,0,0,0,0,0,0,4,5,5,4,4,4,4,4,4,5,5,4,0,0,0,0,0,0,0,0,0,0,0],
    # 23: upper coat + shirt
    [0,0,0,0,0,0,0,0,4,4,5,5,4,4,4,4,4,4,5,5,4,4,0,0,0,0,0,0,0,0,0,0],
    # 24: coat
    [0,0,0,0,0,0,0,4,4,4,5,4,4,4,4,4,4,4,4,5,4,4,4,0,0,0,0,0,0,0,0,0],
    # 25: coat
    [0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0],
    # 26: coat
    [0,0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0,0],
    # 27: coat
    [0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0],
    # 28: coat
    [0,0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0,0],
    # 29: coat bottom
    [0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0],
    # 30: coat bottom
    [0,0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0,0],
    # 31: bottom edge
    [0,0,0,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,0,0,0,0,0],
]

PALETTE = {
    0: None,       # transparent
    1: SKIN,
    2: HAIR,
    3: BEARD,
    4: COAT,
    5: SHIRT,
    6: GLASSES,
    7: GLASSES_LENS,
    8: SKIN_SHADOW,
    9: (255, 255, 255),  # eye highlight (unused but reserved)
}

# â”€â”€ 32x32 icon â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# One character per cell. '.' is background.
ICON = [
    "................................",
    "................................",
    "................................",
    "...........HHHHHHHHHH...........",
    ".........HHHhhhhHHHHHH..........",
    "........HHhhhhHHHHHHHHH.........",
    "........HHHSSSSSSSSSSHHH........",
    "........HHSSSSSSSSSSSSHH........",
    "........HSSSSSSSSSSSSSSH........",
    ".......KKKKKKKKKKKKKKKKKK.......",
    ".......KWCCCCCKKKKWCCCCCK.......",
    ".......KCCCCCCKSSKCCCCCCK.......",
    ".......KccccccKSSKccccccK.......",
    "........KKKKKKSssSKKKKKK........",
    "........HSSSSSSssSSSSSSH........",
    "........BSSBBBBBBBBBBSSB........",
    "........BBBBBBSSSSBBBBBB........",
    "........BBBBBBBBBBBBBBBB........",
    "........BBBBBBBBBBBBBBBB........",
    ".........BBBBBBBBBBBBBB.........",
    "..........BBBBBBBBBBBB..........",
    "........OOTTBBBBBBBBTTOO........",
    ".....OOOOOTTTBBBBBBTTTOOOOO.....",
    "..OOOOOOOOOTTTBBBBTTTOOOOOOOOO..",
    "OOOOOOOOOOOTTTCKKCTTTOOOOOOOOOOO",
    "OOOOOOOOOOOoTCCKKCCToOOOOOOOOOOO",
    "OOOOOOOOOOOOoTTTTTToOOOOOOOOOOOO",
    "OOOOOOOOOOOOOoTTTToOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOoTToOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOOooOOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
    "OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",
]

ICON_PALETTE = {
    "H": (52, 34, 26),     # hair
    "h": (96, 64, 44),     # hair highlight
    "S": (240, 198, 152),  # skin
    "s": (206, 152, 110),  # skin shadow
    "B": (60, 40, 30),     # beard
    "K": (8, 8, 14),       # frames, bow tie knot
    "C": (77, 227, 247),   # lens, bow tie -- the title's cyan
    "c": (20, 150, 190),   # lower lens
    "W": (255, 255, 255),  # glint
    "O": (28, 30, 58),     # coat
    "o": (58, 62, 104),    # lapel edge
    "T": (238, 238, 246),  # shirt
}
ICON_OUTLINE = (14, 6, 26)

# Radial ground: bright behind the head, deep purple at the edges.
ICON_GLOW = (255, 96, 214)
ICON_EDGE = (96, 24, 140)

# The dark-appearance icon, which iOS 18 and later show on a dark home screen.
# Without one the system dims the light icon itself, and its magenta goes
# nearly black; this keeps the hue and lets the cyan carry the contrast.
ICON_GLOW_DARK = (122, 28, 104)
ICON_EDGE_DARK = (26, 8, 38)


def draw_portrait(size=32):
    """Draw the 32x32 Boole portrait, centered with iOS mask clearance."""
    # Find actual content bounds
    rows_with_content = [y for y, row in enumerate(PORTRAIT) if any(v != 0 for v in row)]
    if not rows_with_content:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))
    min_y, max_y = rows_with_content[0], rows_with_content[-1]
    content_h = max_y - min_y + 1
    # Find horizontal bounds
    min_x = min(x for row in PORTRAIT for x, v in enumerate(row) if v != 0)
    max_x = max(x for row in PORTRAIT for x, v in enumerate(row) if v != 0)
    content_w = max_x - min_x + 1
    # Center vertically, nudge left for bottom-right corner mask clearance
    offset_y = (size - content_h) // 2 - min_y
    offset_x = (size - content_w) // 2 - min_x
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y, row in enumerate(PORTRAIT):
        for x, val in enumerate(row):
            if val == 0:
                continue
            nx = x + offset_x
            ny = y + offset_y
            if 0 <= nx < size and 0 <= ny < size:
                img.putpixel((nx, ny), PALETTE[val] + (255,))
    return img


def gradient(size):
    """Vertical three-stop gradient with scanlines."""
    img = Image.new("RGB", (size, size))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / (size - 1)
        if t < 0.5:
            a, b, u = TOP, MID, t * 2
        else:
            a, b, u = MID, BOT, (t - 0.5) * 2
        d.line([(0, y), (size, y)], fill=tuple(round(a[i] + (b[i] - a[i]) * u) for i in range(3)))
    step = max(2, size // 180)
    dark = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    for y in range(0, size, step * 2):
        dd.rectangle([0, y, size, y + step - 1], fill=(0, 0, 0, 28))
    return Image.alpha_composite(img.convert("RGBA"), dark)


def bloom(art, radius, strength=1.0):
    """Blurred copy for glow effect."""
    glow = art.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        alpha = glow.getchannel("A").point(lambda v: min(255, round(v * strength)))
        glow.putalpha(alpha)
    return glow


def screen(base, layer):
    """Light-additive composite."""
    out = base.copy()
    out.alpha_composite(layer)
    return out


def draw_icon():
    """ICON at 32x32, with a one-cell outline around the figure."""
    n = len(ICON)
    for i, row in enumerate(ICON):
        if len(row) != n:
            raise SystemExit(f"ICON row {i} is {len(row)} cells wide, not {n}")

    def filled(x, y):
        return 0 <= x < n and 0 <= y < n and ICON[y][x] != "."

    art = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    for y, row in enumerate(ICON):
        for x, ch in enumerate(row):
            if ch != ".":
                art.putpixel((x, y), ICON_PALETTE[ch] + (255,))
            elif any(filled(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                art.putpixel((x, y), ICON_OUTLINE + (255,))
    return art


def icon_ground(size, dark=False):
    """The radial magenta ground, with the scanlines the whole game wears."""
    glow, edge = (ICON_GLOW_DARK, ICON_EDGE_DARK) if dark else (ICON_GLOW, ICON_EDGE)
    img = Image.new("RGB", (size, size))
    px = img.load()
    cx, cy, reach = size * 0.5, size * 0.38, size * 0.78
    for y in range(size):
        for x in range(size):
            t = min(1.0, ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / reach)
            px[x, y] = tuple(round(glow[i] + (edge[i] - glow[i]) * t) for i in range(3))
    step = size // 64
    lines = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    for y in range(0, size, step * 2):
        d.rectangle([0, y, size, y + step - 1], fill=(0, 0, 0, 22))
    return Image.alpha_composite(img.convert("RGBA"), lines)


def corner_mask(size):
    """iOS's rounded square, near enough: radius about 22.4% of the side."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * 0.2237), fill=255
    )
    return mask


def build_icon(size=1024, dark=False):
    small = draw_icon()
    art = small.resize((size, size), Image.NEAREST)

    # iOS rounds the corners itself, and the asset catalog previews the full
    # square, so a clipped figure looks fine right up until it is on a home
    # screen. What matters is the outline: the coat may run off the edges like
    # a portrait crop, where the rounding only trims solid colour, but a corner
    # cutting through the outline bites a visible notch out of the silhouette.
    outline = Image.new("L", small.size, 0)
    for y in range(small.size[1]):
        for x in range(small.size[0]):
            if small.getpixel((x, y)) == ICON_OUTLINE + (255,):
                outline.putpixel((x, y), 255)
    bitten = Image.composite(
        Image.new("L", (size, size), 0), outline.resize((size, size), Image.NEAREST), corner_mask(size)
    ).getbbox()
    if bitten:
        raise SystemExit(f"icon outline is outside the iOS corner mask at {bitten}; pull it in.")

    out = icon_ground(size, dark)
    out.alpha_composite(art)
    # App icons must be opaque; an alpha channel is rejected at upload.
    return out.convert("RGB")


def build_sheet(icon, dark_icon):
    """Both icons at 180, 120 and 60, masked: the light one on a light
    wallpaper, the dark one on a dark wallpaper, which is where each is
    actually shown."""
    sheet = Image.new("RGB", (480, 460), (236, 232, 226))
    ImageDraw.Draw(sheet).rectangle([0, 230, 480, 460], fill=(22, 24, 30))
    for y0, art in ((25, icon), (255, dark_icon)):
        x = 20
        for s in (180, 120, 60):
            sheet.paste(art.resize((s, s), Image.LANCZOS), (x, y0), corner_mask(s))
            x += s + 40
    return sheet


# â”€â”€ the web portrait â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def build_touch_icon(size=180):
    """web/apple-touch-icon.png, from PORTRAIT."""
    art = draw_portrait(32)
    art = art.resize((size, size), Image.NEAREST)

    out = gradient(size)
    out = screen(out, bloom(art, radius=size // 20, strength=0.7))
    out.alpha_composite(art)
    return out.convert("RGB")


def main():
    ap = argparse.ArgumentParser(description="Draw George Boole: the app icon, and optionally the web portrait.")
    ap.add_argument("--web", action="store_true", help="also write the web portrait files")
    ap.add_argument("--sheet", metavar="PNG", help="write a 60/120/180px preview sheet here")
    args = ap.parse_args()

    icon_dir = ASSETS / "AppIcon.appiconset"
    if not icon_dir.is_dir():
        raise SystemExit(f"asset catalog not found: {icon_dir}")

    icon = build_icon()
    icon_path = icon_dir / "AppIcon-512@2x.png"
    icon.save(icon_path)
    print(f"icon     {icon_path.relative_to(REPO)}  {icon.size[0]}x{icon.size[1]}")

    # The dark-appearance variant. Contents.json carries the appearances entry
    # that pairs it with the one above; the system derives the tinted icon
    # itself, so there is no third file.
    dark_icon = build_icon(dark=True)
    dark_path = icon_dir / "AppIcon-512@2x-dark.png"
    dark_icon.save(dark_path)
    print(f"dark     {dark_path.relative_to(REPO)}  {dark_icon.size[0]}x{dark_icon.size[1]}")

    assets = IOS / "assets"
    assets.mkdir(exist_ok=True)
    touch = icon.resize((180, 180), Image.LANCZOS)
    touch_path = assets / "apple-touch-icon.png"
    touch.save(touch_path)
    print(f"touch    {touch_path.relative_to(REPO)}  {touch.size[0]}x{touch.size[1]}")

    if args.sheet:
        build_sheet(icon, dark_icon).save(args.sheet)
        print(f"sheet    {args.sheet}")

    if args.web:
        web_touch = build_touch_icon()
        web_path = WEB / "apple-touch-icon.png"
        web_touch.save(web_path)
        print(f"web      {web_path.relative_to(REPO)}  {web_touch.size[0]}x{web_touch.size[1]}")

        # 32x32 scaled 4x with NEAREST, for the loading and title screens.
        raw_path = WEB / "img" / "boole-pixel.png"
        raw_path.parent.mkdir(exist_ok=True)
        display = draw_portrait(32).resize((128, 128), Image.NEAREST)
        display.save(raw_path)
        print(f"portrait {raw_path.relative_to(REPO)}  {display.size[0]}x{display.size[1]}")


if __name__ == "__main__":
    main()
