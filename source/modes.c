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
    /* The web game's per-mode floor, which is drawn where the spawn table stops
       handing values out for free: celebrating a value the board produces on its
       own is not celebrating anything. */
    switch (bits) {
        /* Every 2-bit value can spawn, so nothing there is an achievement. The
           web game returns Infinity; one above the ceiling is the same rule
           written in ints. */
        case 2:  return mode_max_value(bits) + 1;
        case 3:  return 6;
        case 4:  return 5;
        case 5:
        case 6:  return mode_max_value(bits) / 2;
        default: return mode_max_value(bits) / 3;
    }
}

int mode_height_bonus(int bits, int value) {
    if (value < mode_height_threshold(bits)) return 0;
    /* Double, in every mode. Reaching a value for the first time is the one
       thing in the game that cannot be repeated, and it is paid accordingly. */
    return value * 2;
}

int mode_gate_spawn_pct(int bits) {
    if (bits <= 2) return 45;
    if (bits == 3) return 32;
    if (bits == 4) return 24;
    if (bits <= 6) return 20;
    return 18;
}

/* A cumulative distribution: the first step whose `upto` a roll in 0..99 falls
   under wins. Written this way so each table below reads as the same shape as
   the chain of `rand() <` comparisons it was transcribed from. */
typedef struct {
    int upto;
    int value;
} SpawnStep;

static const SpawnStep spawn_2bit[]  = { {50,1}, {100,2} };
static const SpawnStep spawn_3bit[]  = { {20,1}, {40,2}, {60,3}, {80,4}, {100,5} };
static const SpawnStep spawn_h1[]    = { {60,1}, {100,2} };
static const SpawnStep spawn_h3[]    = { {50,1}, {100,2} };
static const SpawnStep spawn_h7[]    = { {40,1}, {75,2}, {100,3} };
static const SpawnStep spawn_h15[]   = { {40,1}, {70,2}, {90,3}, {100,4} };
static const SpawnStep spawn_h31[]   = { {30,1}, {50,2}, {70,3}, {85,4}, {95,5}, {100,6} };
static const SpawnStep spawn_h63[]   = { {25,1}, {40,2}, {55,3}, {70,4},
                                         {80,5}, {90,6}, {96,7}, {100,8} };
static const SpawnStep spawn_late[]  = { {20,1}, {35,2}, {50,4}, {65,6},
                                         {78,8}, {88,10}, {100,12} };

/* Sets both halves of the choice at once: a table and its length are only ever
   correct together. */
#define USE(t) do { steps = (t); n = (int)(sizeof(t) / sizeof((t)[0])); } while (0)

static int pick(const SpawnStep *steps, int n, int roll100) {
    for (int i = 0; i < n; i++) {
        if (roll100 < steps[i].upto) return steps[i].value;
    }
    return steps[n - 1].value;
}

int mode_spawn_value(int bits, int highest_on_board, int roll100) {
    const SpawnStep *steps;
    int n;

    if (roll100 < 0)    roll100 = 0;
    if (roll100 > 99)   roll100 = 99;

    if (bits <= 2) {
        /* The 2-bit ceiling never spawns: with only three values, a board that
           hands you the top one has handed you the whole mode. */
        USE(spawn_2bit);
    } else if (bits == 3 && highest_on_board >= 3) {
        /* 3-bit opens up early. There is so little room to climb that waiting
           for a 1 and a 2 to meet is most of the run. */
        USE(spawn_3bit);
    } else if (highest_on_board <= 1)  { USE(spawn_h1);  }
    else if (highest_on_board <= 3)    { USE(spawn_h3);  }
    else if (highest_on_board <= 7)    { USE(spawn_h7);  }
    else if (highest_on_board <= 15)   { USE(spawn_h15); }
    else if (highest_on_board <= 31)   { USE(spawn_h31); }
    else if (highest_on_board <= 63)   { USE(spawn_h63); }
    else                               { USE(spawn_late); }

    int value = pick(steps, n, roll100);

    /* No branch above can exceed its own ceiling, but a table transcribed by
       hand should not be able to produce a tile the rules cannot express. */
    int max = mode_max_value(bits);
    if (value > max) value = max;
    return value;
}
