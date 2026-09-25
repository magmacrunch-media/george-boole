#!/usr/bin/env python3
"""Draw the Game Center art: one image per leaderboard and per achievement.

    python ios/tools/make-boards.py                 # needs Pillow
    python ios/tools/make-boards.py --sheet out.png # a contact sheet to judge

App Store Connect wants **1024 x 1024**, PNG or JPEG, at least 72 ppi, RGB.
An achievement image is required; a leaderboard image is optional and worth
having anyway, since the board is otherwise a list of numbers with a blank
square beside it. Checked against Apple's reference pages on 2026-09-19,
where a guess of 512 would have been wrong.

## Nothing here is retyped

The eight modes come from `tui/boole/modes.py` and the seven discoveries from
`web/js/codex.js`, both parsed, both counted. The ids are built the way
`ios/shim/gamekit-achievements.js` builds them and checked against its own
list. So a mode renamed or a discovery added cannot leave the art saying
something the game does not, which is the failure these files are most prone
to: an image is not compiled, and nothing else would notice.

## The gate symbols are drawn, not typed

Press Start 2P has no glyph for U+2295, U+2228, U+2227 or U+00AC, and renders
all four as the same .notdef box -- the same reason the icon's gates were
drawn from primitives. So a formula is laid out token by token: text runs go
through the font, gate symbols are drawn with lines and arcs, and the two are
measured against each other so the row stays centred.
"""

import argparse
import importlib.util
import re
from pathlib import Path

from PIL import Image, ImageDraw

IOS = Path(__file__).resolve().parent.parent
REPO = IOS.parent
OUT = IOS / "store" / "game-center"

SIZE = 1024

# make-art.py owns the gradient, the font loader and the palette. Its name has
# a hyphen, so it is loaded by path rather than imported; it runs nothing at
# import time.
_spec = importlib.util.spec_from_file_location("make_art", IOS / "tools" / "make-art.py")
art = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(art)

WHITE = (240, 238, 250)
DIM = (150, 142, 176)
# #ffd700, the NOT gate's colour in web/css/codex.css and the game's third
# accent after cyan and magenta. Only the achievement cards use it: a
# leaderboard has no points.
GOLD = (255, 215, 0)


# ── what the game says ──────────────────────────────────────────────────────


def read_modes():
    """The eight modes: (key, display name, bits, gauntlet)."""
    text = (REPO / "tui" / "boole" / "modes.py").read_bytes().decode()
    found = re.findall(r'Mode\("([a-z]+)",\s*"([a-z]+)",\s*(\d+)(,\s*gauntlet=True)?\)', text)
    modes = [(key, name, int(bits), bool(g)) for key, name, bits, g in found]
    if len(modes) != 8:
        raise SystemExit(f"expected 8 modes in tui/boole/modes.py, found {len(modes)}")
    return modes


def read_discoveries():
    """The seven discoveries: (id, title, formula)."""
    text = (REPO / "web" / "js" / "codex.js").read_bytes().decode()
    found = re.findall(
        r"id: '([a-z_]+)',\s*\n\s*title: '([^']+)',\s*\n\s*challenge: '[^']*',\s*\n\s*formula: '([^']*)'",
        text,
    )
    if len(found) != 7:
        raise SystemExit(f"expected 7 discoveries in web/js/codex.js, found {len(found)}")
    return found


def read_achievement_ids():
    """The ids the shim will report, so the art is named the same."""
    text = (IOS / "shim" / "gamekit-achievements.js").read_bytes().decode()
    prefix = re.search(r"var PREFIX = '([^']+)'", text)
    learn = re.search(r"var LEARN = \[([^\]]+)\]", text, re.DOTALL)
    if not prefix or not learn:
        raise SystemExit("could not read PREFIX or LEARN from gamekit-achievements.js")
    ids = re.findall(r"'([a-z_]+)'", learn.group(1))
    if len(ids) != 7:
        raise SystemExit(f"expected 7 learn ids in the shim, found {len(ids)}")
    return prefix.group(1), ids


# App Store Connect's two hard limits, which the shim's header quotes and an
# earlier plan of 300 for the Gauntlet clear would have broken.
MAX_PER_ACHIEVEMENT = 100
MAX_TOTAL = 1000


def read_points(achievement_ids):
    """{id: points}, from the budget table in the achievements shim's header.

    The table is by pattern rather than by id -- `overflow.<n>bit  x7  50 each
    350` -- so the counts are part of what is checked: a row claiming seven of
    something the shim does not build seven of is caught here rather than
    discovered on the form.
    """
    text = (IOS / "shim" / "gamekit-achievements.js").read_bytes().decode()

    rows = re.findall(r"^ \*   (\S+)\s+x(\d+)\s+(\d+)(?: each)?\s+(\d+)\s*$", text, re.M)
    if not rows:
        raise SystemExit("could not read the points table from gamekit-achievements.js")

    stated = re.search(r"^ \*\s+(\d+), leaving (\d+)", text, re.M)
    if not stated:
        raise SystemExit("the points table has no total line")

    def bucket(ident):
        if ident.startswith("overflow."):
            return "overflow.<n>bit"
        if ident.startswith("learn."):
            return "learn.<id>"
        return ident

    points = {}
    for pattern, count, each, subtotal in rows:
        count, each, subtotal = int(count), int(each), int(subtotal)
        if each > MAX_PER_ACHIEVEMENT:
            raise SystemExit(f"{pattern}: {each} points, over Apple's {MAX_PER_ACHIEVEMENT} per achievement")
        if count * each != subtotal:
            raise SystemExit(f"{pattern}: {count} x {each} is {count * each}, not the {subtotal} stated")
        matched = [i for i in achievement_ids if bucket(i) == pattern]
        if len(matched) != count:
            raise SystemExit(
                f"{pattern}: the table says x{count}, the shim builds {len(matched)}"
            )
        for i in matched:
            points[i] = each

    missing = [i for i in achievement_ids if i not in points]
    if missing:
        raise SystemExit(f"no points row covers {missing}")

    total = sum(points.values())
    if total != int(stated.group(1)):
        raise SystemExit(f"the rows total {total}, the table says {stated.group(1)}")
    if total > MAX_TOTAL:
        raise SystemExit(f"the achievements total {total}, over Apple's {MAX_TOTAL}")
    return points, total, int(stated.group(2))


# ── the gate symbols, drawn ─────────────────────────────────────────────────


def glyph_xor(d, box, colour, w):
    """A circle with a cross through it."""
    x0, y0, x1, y1 = box
    d.ellipse(box, outline=colour, width=w)
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
    """The V inverted, which is what the operator is."""
    x0, y0, x1, y1 = box
    cx = (x0 + x1) // 2
    d.line([(x0, y1), (cx, y0)], fill=colour, width=w)
    d.line([(cx, y0), (x1, y1)], fill=colour, width=w)


def glyph_not(d, box, colour, w):
    """A bar with a tick down from its right end."""
    x0, y0, x1, y1 = box
    cy = (y0 + y1) // 2
    d.line([(x0, cy), (x1, cy)], fill=colour, width=w)
    d.line([(x1 - w // 2, cy), (x1 - w // 2, y1)], fill=colour, width=w)


GLYPHS = {"⊕": glyph_xor, "∨": glyph_or, "∧": glyph_and, "¬": glyph_not}


def tokenize(formula):
    """Split a formula into ('text', str) and ('glyph', symbol) runs."""
    # Two characters the pixel font also lacks, spelled instead of drawn.
    formula = formula.replace("…", "...").replace("→", "->")
    tokens = []
    run = ""
    for ch in formula:
        if ch in GLYPHS:
            if run:
                tokens.append(("text", run))
                run = ""
            tokens.append(("glyph", ch))
        else:
            run += ch
    if run:
        tokens.append(("text", run))
    return tokens


def draw_formula(d, formula, font, colour, centre_x, top, size):
    """Lay the formula out in one row, centred on `centre_x`."""
    tokens = tokenize(formula)
    widths = []
    for kind, value in tokens:
        widths.append(size if kind == "glyph" else d.textlength(value, font=font))

    x = centre_x - sum(widths) / 2
    stroke = max(3, size // 12)
    for (kind, value), width in zip(tokens, widths):
        if kind == "glyph":
            pad = size * 0.12
            GLYPHS[value](
                d,
                (round(x + pad), round(top + pad), round(x + size - pad), round(top + size - pad)),
                colour,
                stroke,
            )
        else:
            d.text((x, top), value, font=font, fill=colour)
        x += width


# ── the images ──────────────────────────────────────────────────────────────


# Nothing may touch the edges: Game Center rounds these corners and shows
# them at several sizes, so the widest line is held inside this fraction.
SAFE_WIDTH = 0.78


def fit_text(d, text, start, minimum=28):
    """The largest size at which `text` fits the safe width."""
    limit = SIZE * SAFE_WIDTH
    size = start
    while size > minimum:
        font = art.load_font(size)
        if d.textlength(text, font=font) <= limit:
            return font
        size -= 4
    return art.load_font(minimum)


def fit_formula(d, formula, start, minimum=24):
    """The largest size at which the laid-out formula fits.

    Measured the way it is drawn, a glyph counting as one square of the font
    size: "not 11111111 = 00000000" is 20 tokens wide and ran off both edges
    at a size the short ones were comfortable at.
    """
    limit = SIZE * SAFE_WIDTH
    tokens = tokenize(formula)
    size = start
    while size > minimum:
        font = art.load_font(size)
        width = sum(size if kind == "glyph" else d.textlength(value, font=font)
                    for kind, value in tokens)
        if width <= limit:
            return font, size
        size -= 3
    return art.load_font(minimum), minimum


# The publisher's mark is composited at this y, so nothing drawn may reach it.
MARK_TOP = 760


def card(title, subtitle, formula, badge=""):
    """One 1024 square: title, subtitle, formula, points, the publisher's mark.

    Everything sits inside the middle 80%: Game Center rounds these corners
    and crops at several sizes, and the asset catalog is not what shows them.

    `badge` is the points line, and only achievements have one.
    """
    out = art.gradient(SIZE)
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    title_font = fit_text(d, title, 96)
    sub_font = fit_text(d, subtitle, 40)

    w = d.textlength(title, font=title_font)
    d.text(((SIZE - w) / 2, 300), title, font=title_font, fill=art.CYAN)

    sub_top = 300 + title_font.size + 56
    w = d.textlength(subtitle, font=sub_font)
    d.text(((SIZE - w) / 2, sub_top), subtitle, font=sub_font, fill=art.MAGENTA)

    bottom = sub_top + sub_font.size
    if formula:
        formula_top = bottom + 70
        formula_font, formula_size = fit_formula(d, formula, 54)
        draw_formula(d, formula, formula_font, WHITE, SIZE / 2, formula_top, formula_size)
        bottom = formula_top + formula_size

    if badge:
        badge_font = fit_text(d, badge, 32)
        badge_top = bottom + 56
        # A long title shrinks its font and pulls everything up, so this cannot
        # be checked by arithmetic on the defaults alone. The mark is composited
        # after the bloom and would simply be drawn over.
        if badge_top + badge_font.size > MARK_TOP - 16:
            raise SystemExit(
                f"the points line on {title!r} reaches {badge_top + badge_font.size}px, "
                f"into the publisher's mark at {MARK_TOP}px"
            )
        w = d.textlength(badge, font=badge_font)
        d.text(((SIZE - w) / 2, badge_top), badge, font=badge_font, fill=GOLD)

    out = art.screen(out, art.bloom(layer, radius=SIZE // 90, strength=0.8))
    out = art.screen(out, art.bloom(layer, radius=SIZE // 320, strength=1.0))
    out.alpha_composite(layer)

    mark = art.load_mark()
    if mark is not None:
        height = 96
        scaled = mark.resize(
            (max(1, round(mark.width * height / mark.height)), height), Image.LANCZOS
        )
        faded = scaled.copy()
        faded.putalpha(scaled.getchannel("A").point(lambda v: round(v * 0.5)))
        out.alpha_composite(faded, ((SIZE - scaled.width) // 2, MARK_TOP))

    # RGB, as the spec asks: an alpha channel here is a rejected upload.
    return out.convert("RGB")


def build_all():
    modes = read_modes()
    discoveries = read_discoveries()
    prefix, learn_ids = read_achievement_ids()

    codex_ids = [d[0] for d in discoveries]
    if codex_ids != learn_ids:
        raise SystemExit(
            "the codex and the achievement shim disagree about the discoveries:\n"
            f"  codex: {codex_ids}\n  shim:  {learn_ids}"
        )

    # The ids in the order they are drawn, so the points table is checked
    # against what this script actually builds rather than against itself.
    overflow_bits = [bits for _k, _n, bits, gauntlet in modes if not gauntlet]
    achievement_ids = (
        [f"overflow.{b}bit" for b in overflow_bits]
        + ["gauntlet.clear"]
        + [f"learn.{i}" for i in learn_ids]
    )
    points, total, spare = read_points(achievement_ids)
    pts = lambda ident: f"{points[ident]} POINTS"  # noqa: E731

    images = []

    # A leaderboard has no points, so it gets no badge.
    for key, name, bits, gauntlet in modes:
        if gauntlet:
            images.append((f"leaderboards/{key}", card("GAUNTLET", name.upper(), "2 -> 8 BIT")))
        else:
            ones = "1" * bits
            images.append(
                (f"leaderboards/{key}", card(f"{bits}-BIT", name.upper(), f"MAX {ones}"))
            )

    for bits in overflow_bits:
        ident = f"overflow.{bits}bit"
        images.append(
            (
                f"achievements/{ident}",
                card("OVERFLOW", f"{bits}-BIT", f"¬{'1' * bits} = {'0' * bits}", pts(ident)),
            )
        )

    images.append(
        (
            "achievements/gauntlet.clear",
            card("GAUNTLET", "CLEARED", "2 -> 8 BIT", pts("gauntlet.clear")),
        )
    )

    for ident, title, formula in discoveries:
        aid = f"learn.{ident}"
        images.append((f"achievements/{aid}", card(title.upper(), "DISCOVERY", formula, pts(aid))))

    return prefix, images, total, spare


def contact_sheet(images, columns=6):
    cell = 190
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell, rows * cell), (10, 10, 20))
    for i, (_name, image) in enumerate(images):
        sheet.paste(image.resize((cell - 10, cell - 10), Image.LANCZOS),
                    ((i % columns) * cell + 5, (i // columns) * cell + 5))
    return sheet


def main():
    ap = argparse.ArgumentParser(description="Draw the Game Center leaderboard and achievement art.")
    ap.add_argument("--sheet", metavar="PNG", help="also write a contact sheet here")
    args = ap.parse_args()

    prefix, images, total, spare = build_all()
    for folder in ("leaderboards", "achievements"):
        (OUT / folder).mkdir(parents=True, exist_ok=True)

    for name, image in images:
        path = OUT / f"{name}.png"
        image.save(path)
    print(f"wrote {len(images)} images to {OUT.relative_to(REPO)}")
    print(f"  ids carry the prefix {prefix}")
    print(f"  points {total} of {MAX_TOTAL}, leaving {spare}, as the shim's table has it")

    if args.sheet:
        contact_sheet(images).save(args.sheet)
        print(f"  sheet {args.sheet}")


if __name__ == "__main__":
    main()
