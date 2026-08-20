#ifndef MODES_H
#define MODES_H

/* Bit modes.
 *
 * Every mode is "n-bit": values run 0..2^n-1 and the ceiling is the max value.
 * Gauntlet starts at 2-bit and climbs a mode each time the ceiling is reached,
 * which is why the mode is state rather than a constant.
 *
 * Names are the bit-culture ones from the web game, not invented here: a
 * 4-bit quantity really is a nibble.
 */

typedef enum {
    MODE_2BIT,
    MODE_3BIT,
    MODE_4BIT,
    MODE_5BIT,
    MODE_6BIT,
    MODE_7BIT,
    MODE_8BIT,
    MODE_GAUNTLET,
    MODE_COUNT
} ModeId;

/* Display name ("crumb", "nibble", "byte", "gauntlet"). */
const char *mode_name(ModeId mode);

/* Short label used for the leaderboard table id and file name. */
const char *mode_id(ModeId mode);

/* Bit width a run in this mode starts at. Gauntlet starts at 2. */
int mode_start_bits(ModeId mode);

/* Whether reaching the ceiling promotes to the next bit width. */
int mode_is_gauntlet(ModeId mode);

/* 2^bits - 1. */
int mode_max_value(int bits);

/* Points for clearing the ceiling: max_value * 3. At 8-bit that is 765, which
   is why the running score cannot be an increment-by-one counter. */
int mode_overflow_bonus(int bits);

/* The lowest value worth a first-time-reached bonus at this width. Low values
   are reached constantly and rewarding them would drown out everything else. */
int mode_height_threshold(int bits);

/* Points for reaching `value` for the first time. 0 when it is not worth one. */
int mode_height_bonus(int bits, int value);

#endif
