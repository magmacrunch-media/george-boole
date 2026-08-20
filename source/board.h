#ifndef BOARD_H
#define BOARD_H

/* The board and the Boolean rules, with no rendering and no libogc in sight.
 *
 * Kept pure so it compiles and runs on a development machine: these rules must
 * match the web game exactly, and checking that against an emulator one build at
 * a time would be slow enough that it would stop happening. `make test` runs the
 * whole rule set in under a second.
 */

#define BOARD_SIZE 4
#define BOARD_CELLS (BOARD_SIZE * BOARD_SIZE)

/* Gates live in the same array as values, as negative numbers. It reads oddly
   but it is what makes a gate slide, collide and occupy space exactly like a
   tile does -- which is the whole game. 0 is an empty cell. */
#define TILE_EMPTY  0
#define GATE_XOR   -1
#define GATE_OR    -2
#define GATE_AND   -3
#define GATE_NOT   -4

typedef enum {
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
    DIR_DOWN
} BoardDir;

typedef struct {
    int cells[BOARD_SIZE][BOARD_SIZE];

    int bits;          /* current bit width */
    int max_value;     /* 2^bits - 1 */
    int gauntlet;      /* whether reaching the ceiling promotes a bit width */
    int reached_max;   /* ceiling reached at the current width */

    int score;
    int highest_earned; /* best value built by merging, not spawned */

    /* Set by the last board_move() so the caller can react without re-deriving
       anything: play a sound, flash a bonus, promote the mode. */
    int last_gained;
    int last_overflow_bonus;
    int last_height_bonus;
    int last_upgraded;
} Board;

int  board_is_gate(int value);

/* gate is one of GATE_*; `b` supplies the bit width. For GATE_NOT, `rhs` is
   ignored. */
int  board_apply_gate(const Board *b, int gate, int lhs, int rhs);

void board_init(Board *b, int bits, int gauntlet);

/* Slides and resolves one row/column at a time in `dir`. Returns 1 when the
   board changed, which is the condition for spawning a new tile. */
int  board_move(Board *b, BoardDir dir);

/* Places a tile or gate in a random empty cell. Returns 0 when the board is
   full. `roll` supplies randomness in 0..9999 so tests can be deterministic. */
int  board_spawn(Board *b, int roll);

/* No empty cell and no legal move left. */
int  board_is_full(const Board *b);
int  board_game_over(const Board *b);

int  board_get(const Board *b, int row, int col);
void board_set(Board *b, int row, int col, int value);

#endif
