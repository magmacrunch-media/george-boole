#include "modes.h"

typedef struct {
    const char *name;
    const char *id;
    int         start_bits;
    int         gauntlet;
} ModeInfo;

static const ModeInfo modes[MODE_COUNT] = {
    { "crumb",    "crumb",    2, 0 },
    { "trit",     "trit",     3, 0 },
    { "nibble",   "nibble",   4, 0 },
    { "pentad",   "pentad",   5, 0 },
    { "hexad",    "hexad",    6, 0 },
    { "ascii",    "ascii",    7, 0 },
    { "byte",     "byte",     8, 0 },
    { "gauntlet", "gauntlet", 2, 1 },
};

static const ModeInfo *info(ModeId mode) {
    if (mode < 0 || mode >= MODE_COUNT) return &modes[0];
    return &modes[mode];
}

const char *mode_name(ModeId mode)  { return info(mode)->name; }
const char *mode_id(ModeId mode)    { return info(mode)->id; }
int mode_start_bits(ModeId mode)    { return info(mode)->start_bits; }
int mode_is_gauntlet(ModeId mode)   { return info(mode)->gauntlet; }

int mode_max_value(int bits) {
    if (bits < 1)  bits = 1;
    if (bits > 8)  bits = 8;
    return (1 << bits) - 1;
}

int mode_overflow_bonus(int bits) {
    return mode_max_value(bits) * 3;
}

int mode_height_threshold(int bits) {
    /* Mirrors the web game's per-mode floor. At 3-bit only 6 and 7 pay; from
       4-bit up the floor is a third of the ceiling, so the reward tracks how
       hard the value actually was to build rather than being a flat number. */
    switch (bits) {
        case 2:  return 4;          /* above the 2-bit ceiling: never pays */
        case 3:  return 6;
        default: return mode_max_value(bits) / 3;
    }
}

int mode_height_bonus(int bits, int value) {
    if (value < mode_height_threshold(bits)) return 0;
    /* Double value at 3-bit, plain value above -- the web game pays the small
       mode more generously because there is so much less room to climb. */
    return (bits == 3) ? value * 2 : value;
}
