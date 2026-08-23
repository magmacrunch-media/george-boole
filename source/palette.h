#ifndef PALETTE_H
#define PALETTE_H

/* Colours are just packed RGBA, so this header stays usable on a development
   machine where <gccore.h> does not exist -- otherwise the palette would be the
   one part of the game that could only be checked by looking at a television.
   devkitPPC defines GEKKO for the console build. */
#ifdef GEKKO
#include <gccore.h>
#else
typedef unsigned int u32;
#endif

/* Packed the same way GRRLIB reads a colour (r<<24 | g<<16 | b<<8 | a), but
   spelled out here rather than borrowed from RGBA(): that macro is not a
   constant expression in the console build, so a static palette table cannot be
   initialised with it. */
#define PAL_RGBA(r, g, b, a)                                    \
    ((u32)(((u32)((r) & 0xFF) << 24) | ((u32)((g) & 0xFF) << 16) \
         | ((u32)((b) & 0xFF) << 8)  |  (u32)((a) & 0xFF)))

/* From a 0xRRGGBB literal, which is how the values read in the stylesheet. */
#define PAL_RGB(hex)                        \
    PAL_RGBA(((hex) >> 16) & 0xFF,          \
             ((hex) >> 8)  & 0xFF,          \
              (hex)        & 0xFF, 255)

#include "modes.h"

/* Per-mode colour, ported from the web game's css/themes.css.
 *
 * Each bit mode wears a console era: 2-bit is a Game Boy, 4-bit is a SNES,
 * 8-bit is a PS1, Gauntlet is the Matrix. That is the joke and it is worth
 * keeping, so these are the real hex values out of the stylesheet rather than
 * an approximation of them -- a player who knows the browser version should
 * recognise the board on a television.
 *
 * Tiles are shaded by a five-step intensity ramp rather than one colour per
 * value: an 8-bit board has 255 possible values and no palette survives that.
 * Intensity is the value's position between 1 and the mode's ceiling.
 */

typedef struct {
    u32 board_bg;     /* behind the grid */
    u32 cell_bg;      /* an empty cell */
    u32 tile_text;    /* numerals on a tile */
    u32 border;
    u32 ramp[5];      /* low value -> high value */
    u32 gate_bg;      /* UI accent colour (menus, HUD text) */
    u32 gate_text;    /* UI accent text colour */
    u32 gate_color[4]; /* per-gate tile background: XOR, OR, AND, NOT */
} Palette;

/* `bits` matters for Gauntlet, which climbs widths inside one mode. */
const Palette *palette_for(ModeId mode);

/* Ramp colour for a value in 1..max_value. Out-of-range values clamp rather
   than reading off the end of the ramp. */
u32 palette_tile_color(const Palette *p, int value, int max_value);

#endif
