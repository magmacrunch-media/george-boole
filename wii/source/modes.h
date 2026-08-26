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
 *
 * The tuning tables at the bottom of this header are transcribed from the web
 * game rather than chosen here. They live beside the mode metadata because that
 * is what they are keyed on, and because modes.c is host-testable: a
 * mistranscribed threshold fails in `make test` rather than on a television.
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
   are reached constantly and rewarding them would drown out everything else.
   At 2-bit every value can spawn, so the floor is deliberately unreachable. */
int mode_height_threshold(int bits);

/* Points for reaching `value` for the first time. 0 when it is not worth one. */
int mode_height_bonus(int bits, int value);

/* Percent chance a spawn is a gate rather than a number, by bit width. The web
   game tapers this: a 2-bit board is mostly gates because three values on their
   own give the player almost nothing to do, and a byte board barely needs them.
   Gauntlet reads it from the width it has climbed to, so the mix shifts as the
   run progresses. */
int mode_gate_spawn_pct(int bits);

/* The value a number-spawn takes, given the highest number currently on the
   board and a roll in 0..99.

   Spawns scale with progress rather than staying at 1-2-3 forever: a byte board
   seeded one tile at a time is a grind, not a difficulty. Keyed on the board's
   current highest rather than the best ever reached, so clearing the board eases
   the spawns back down with it. */
int mode_spawn_value(int bits, int highest_on_board, int roll100);

#endif
