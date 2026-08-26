#include "palette.h"
#include "board.h"

#define RGB(hex) PAL_RGB(hex)

/* Values transcribed from css/gates.css and css/themes.css. Kept in the same
   order as ModeId so the lookup is an index rather than a search. Gate colour
   philosophy from gates.css: XOR = teal/aqua (tension), OR = warm amber/gold
   (additive), AND = cool steel blue (restrictive), NOT = inverted dark (flipped).
   Within each theme the hues are shifted to avoid collisions with the ramp. */
static const Palette palettes[MODE_COUNT] = {
    /* 2-bit -- Game Boy */
    { RGB(0x0f380f), RGB(0x0f380f), RGB(0x9bbc0f), RGB(0x0f380f),
      { RGB(0x1a3a10), RGB(0x244d16), RGB(0x2e620d), RGB(0x507a10), RGB(0x729010) },
      RGB(0x8bac0f), RGB(0x0f380f),
      { RGB(0x4a7a6a), RGB(0xa09050), RGB(0x3a4a6a), RGB(0x080f08) } },

    /* 3-bit -- NES */
    { RGB(0x0a0a2a), RGB(0x1a1a3a), RGB(0xffffff), RGB(0x0a0a2a),
      { RGB(0x22224a), RGB(0x6b2020), RGB(0x8b2500), RGB(0xbb3a00), RGB(0xdd4f10) },
      RGB(0x4169e1), RGB(0xffffff),
      { RGB(0x00b8a0), RGB(0x7b2fbe), RGB(0x901870), RGB(0x0a0a18) } },

    /* 4-bit -- SNES */
    { RGB(0x0f0f1e), RGB(0x1a1040), RGB(0xffffff), RGB(0x0f0f1e),
      { RGB(0x1a1040), RGB(0x2e1870), RGB(0x4a1ea0), RGB(0x6a22c8), RGB(0x8a2be2) },
      RGB(0xc0a0ff), RGB(0x1a1040),
      { RGB(0x00d4aa), RGB(0xc86820), RGB(0x2a2070), RGB(0x100820) } },

    /* 5-bit -- Genesis */
    { RGB(0x001a33), RGB(0x003366), RGB(0xffd700), RGB(0x001a33),
      { RGB(0x012244), RGB(0x1a3a7a), RGB(0x1060b0), RGB(0xaa7700), RGB(0xcc9900) },
      RGB(0x00bfff), RGB(0x001a33),
      { RGB(0x00c864), RGB(0xe05878), RGB(0x183848), RGB(0x060c14) } },

    /* 6-bit -- Arcade */
    { RGB(0x0f0500), RGB(0x2d1000), RGB(0xffa500), RGB(0x1a0800),
      { RGB(0x3a1500), RGB(0x6a1a00), RGB(0x991a00), RGB(0xcc3300), RGB(0xdd6600) },
      RGB(0xffa500), RGB(0x1a0800),
      { RGB(0x00c8d4), RGB(0x7030c0), RGB(0x1a5020), RGB(0x0a0400) } },

    /* 7-bit -- Neo Geo */
    { RGB(0x2d0052), RGB(0x4b0082), RGB(0x00ffff), RGB(0x2d0052),
      { RGB(0x3a0066), RGB(0x880040), RGB(0xbb0066), RGB(0x0088aa), RGB(0x00aacc) },
      RGB(0xff1493), RGB(0xffffff),
      { RGB(0xff7800), RGB(0xe03020), RGB(0x506010), RGB(0x080410) } },

    /* 8-bit -- PS1. The web tiles are gradients; a flat mid-tone of each is
       what survives a CRT, and the ramp already carries the sense of metal. */
    { RGB(0x0a0a0a), RGB(0x1a1a1a), RGB(0xffd700), RGB(0x0a0a0a),
      { RGB(0x252525), RGB(0x404040), RGB(0x606060), RGB(0x888888), RGB(0xb0b0b0) },
      RGB(0xffd700), RGB(0x1a1a1a),
      { RGB(0x00b848), RGB(0xa8c800), RGB(0x006878), RGB(0x080808) } },

    /* Gauntlet -- Matrix. Stays green across every width it climbs through:
       the mode is the throughline, not the bit count. */
    { RGB(0x000000), RGB(0x001a00), RGB(0x00ff00), RGB(0x000000),
      { RGB(0x001800), RGB(0x002a00), RGB(0x004000), RGB(0x005c00), RGB(0x007a00) },
      RGB(0x00ff00), RGB(0x000000),
      { RGB(0xc800c8), RGB(0x0060d0), RGB(0xa06000), RGB(0xd8ffd8) } },
};

const Palette *palette_for(ModeId mode) {
    if (mode < 0 || mode >= MODE_COUNT) return &palettes[0];
    return &palettes[mode];
}

u32 palette_tile_color(const Palette *p, int value, int max_value) {
    if (board_is_gate(value)) {
        static const int gate_idx[] = {
            [0 - GATE_XOR] = 0,
            [0 - GATE_OR]  = 1,
            [0 - GATE_AND] = 2,
            [0 - GATE_NOT] = 3,
        };
        return p->gate_color[gate_idx[0 - value]];
    }
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
