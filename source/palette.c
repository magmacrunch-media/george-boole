#include "palette.h"
#include "board.h"

#define RGB(hex) PAL_RGB(hex)

/* Values transcribed from css/themes.css. Kept in the same order as ModeId so
   the lookup is an index rather than a search. */
static const Palette palettes[MODE_COUNT] = {
    /* 2-bit -- Game Boy */
    { RGB(0x0f380f), RGB(0x0f380f), RGB(0x9bbc0f), RGB(0x0f380f),
      { RGB(0x1a3a10), RGB(0x244d16), RGB(0x2e620d), RGB(0x507a10), RGB(0x729010) },
      RGB(0x8bac0f), RGB(0x0f380f) },

    /* 3-bit -- NES */
    { RGB(0x0a0a2a), RGB(0x1a1a3a), RGB(0xffffff), RGB(0x0a0a2a),
      { RGB(0x22224a), RGB(0x6b2020), RGB(0x8b2500), RGB(0xbb3a00), RGB(0xdd4f10) },
      RGB(0x4169e1), RGB(0xffffff) },

    /* 4-bit -- SNES */
    { RGB(0x0f0f1e), RGB(0x1a1040), RGB(0xffffff), RGB(0x0f0f1e),
      { RGB(0x1a1040), RGB(0x2e1870), RGB(0x4a1ea0), RGB(0x6a22c8), RGB(0x8a2be2) },
      RGB(0xc0a0ff), RGB(0x1a1040) },

    /* 5-bit -- Genesis */
    { RGB(0x001a33), RGB(0x003366), RGB(0xffd700), RGB(0x001a33),
      { RGB(0x012244), RGB(0x1a3a7a), RGB(0x1060b0), RGB(0xaa7700), RGB(0xcc9900) },
      RGB(0x00bfff), RGB(0x001a33) },

    /* 6-bit -- Arcade */
    { RGB(0x0f0500), RGB(0x2d1000), RGB(0xffa500), RGB(0x1a0800),
      { RGB(0x3a1500), RGB(0x6a1a00), RGB(0x991a00), RGB(0xcc3300), RGB(0xdd6600) },
      RGB(0xffa500), RGB(0x1a0800) },

    /* 7-bit -- Neo Geo */
    { RGB(0x2d0052), RGB(0x4b0082), RGB(0x00ffff), RGB(0x2d0052),
      { RGB(0x3a0066), RGB(0x880040), RGB(0xbb0066), RGB(0x0088aa), RGB(0x00aacc) },
      RGB(0xff1493), RGB(0xffffff) },

    /* 8-bit -- PS1. The web tiles are gradients; a flat mid-tone of each is
       what survives a CRT, and the ramp already carries the sense of metal. */
    { RGB(0x0a0a0a), RGB(0x1a1a1a), RGB(0xffd700), RGB(0x0a0a0a),
      { RGB(0x252525), RGB(0x404040), RGB(0x606060), RGB(0x888888), RGB(0xb0b0b0) },
      RGB(0xffd700), RGB(0x1a1a1a) },

    /* Gauntlet -- Matrix. Stays green across every width it climbs through:
       the mode is the throughline, not the bit count. */
    { RGB(0x000000), RGB(0x001a00), RGB(0x00ff00), RGB(0x000000),
      { RGB(0x001800), RGB(0x002a00), RGB(0x004000), RGB(0x005c00), RGB(0x007a00) },
      RGB(0x00ff00), RGB(0x000000) },
};

const Palette *palette_for(ModeId mode) {
    if (mode < 0 || mode >= MODE_COUNT) return &palettes[0];
    return &palettes[mode];
}

u32 palette_tile_color(const Palette *p, int value, int max_value) {
    if (board_is_gate(value)) return p->gate_bg;
    if (value <= 0) return p->cell_bg;
    if (max_value < 1) max_value = 1;
    if (value > max_value) value = max_value;

    /* Position in the ramp by value, not by bit index: on a wide mode almost
       every tile would otherwise sit in the bottom step. */
    int step = ((value - 1) * 5) / max_value;
    if (step < 0) step = 0;
    if (step > 4) step = 4;
    return p->ramp[step];
}
