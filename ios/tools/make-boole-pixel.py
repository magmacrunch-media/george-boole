#!/usr/bin/env python3
"""Generate a 32x32 pixel art portrait of George Boole with sunglasses.

Outputs:
  - ios/App/App/App/Assets.xcassets/AppIcon.appiconset/AppIcon-512@2x.png
  - ios/assets/apple-touch-icon.png (180x180)
  - web/apple-touch-icon.png (180x180)

    python ios/tools/make-boole-pixel.py        # needs Pillow
"""

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


def build_icon(size=1024, small=32):
    """Build the app icon from the 32x32 portrait."""
    art = draw_portrait(small)
    art = art.resize((size, size), Image.NEAREST)

    # iOS corner mask: clip art to the rounded rectangle so corners are clean.
    # The coat extends slightly into the mask area at the bottom, which is fine
    # since it's dark on dark — but clip to prevent hard edges at the mask border.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * 0.2237), fill=255
    )
    # Apply mask to alpha channel
    masked_alpha = Image.composite(art.getchannel("A"), Image.new("L", (size, size), 0), mask)
    art.putalpha(masked_alpha)

    out = gradient(size)
    out = screen(out, bloom(art, radius=size // 64, strength=0.85))
    out = screen(out, bloom(art, radius=size // 200, strength=1.0))
    out.alpha_composite(art)
    return out.convert("RGB")


def build_touch_icon(size=180):
    """Build the apple-touch-icon at180x180."""
    art = draw_portrait(32)
    art = art.resize((size, size), Image.NEAREST)

    out = gradient(size)
    out = screen(out, bloom(art, radius=size // 20, strength=0.7))
    out.alpha_composite(art)
    return out.convert("RGB")


def build_web_icon(size=180):
    """Build web/apple-touch-icon.png."""
    return build_touch_icon(size)


def main():
    icon_dir = ASSETS / "AppIcon.appiconset"
    if not icon_dir.is_dir():
        raise SystemExit(f"asset catalog not found: {icon_dir}")

    # App icon (1024x1024)
    icon = build_icon()
    icon_path = icon_dir / "AppIcon-512@2x.png"
    icon.save(icon_path)
    print(f"icon     {icon_path.relative_to(REPO)}  {icon.size[0]}x{icon.size[1]}")

    # ios/assets/apple-touch-icon.png (180x180)
    assets = IOS / "assets"
    assets.mkdir(exist_ok=True)
    touch = build_touch_icon()
    touch_path = assets / "apple-touch-icon.png"
    touch.save(touch_path)
    print(f"touch    {touch_path.relative_to(REPO)}  {touch.size[0]}x{touch.size[1]}")

    # web/apple-touch-icon.png (180x180)
    web_touch = build_web_icon()
    web_path = WEB / "apple-touch-icon.png"
    web_touch.save(web_path)
    print(f"web      {web_path.relative_to(REPO)}  {web_touch.size[0]}x{web_touch.size[1]}")

    # Also save the raw 32x32 for use in the title screen
    raw = draw_portrait(32)
    raw_path = WEB / "img" / "boole-pixel.png"
    raw_path.parent.mkdir(exist_ok=True)
    # Scale up 4x for crisp display (128x128) with NEAREST
    display = raw.resize((128, 128), Image.NEAREST)
    display.save(raw_path)
    print(f"portrait {raw_path.relative_to(REPO)}  {display.size[0]}x{display.size[1]}")

    print("\ndone!")


if __name__ == "__main__":
    main()
