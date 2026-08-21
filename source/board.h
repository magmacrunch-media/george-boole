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

/* Where one tile went during a move, so the renderer can slide it there instead
   of teleporting it. A merge produces several of these sharing a destination:
   each source slides in carrying the value it had, and the result appears when
   they arrive. Without this the board is correct and reads as though nothing
   happened. */
typedef struct {
    int from_row, from_col;
    int to_row, to_col;
    int from_value;   /* what slides */
    int to_value;     /* what it becomes on arrival */
    int merged;       /* more than one tile landed here */
} TileMove;

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

    /* Filled by the last board_move(). Every surviving tile is listed, including
       ones that did not move, so the renderer can draw the whole board from this
       alone while an animation is running. Tiles consumed without a result --
       two NOTs cancelling -- are simply absent. */
    TileMove moves[BOARD_CELLS];
    int move_count;

    /* Where board_spawn() last placed a tile, or -1. */
    int spawn_row, spawn_col;
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
   full.

   `roll` is the only randomness that enters, so a test can pin a spawn exactly.
   It is a whole word rather than a small number because three independent
   choices come out of it -- which cell, gate or number, and which value -- and
   a four-digit roll cannot carry three hundred-way decisions without them
   correlating. */
int  board_spawn(Board *b, unsigned int roll);

/* Highest number on the board, ignoring gates and empty cells; 0 on an empty
   board. This is what the spawn table scales against -- where the player is
   now, not the best they have managed, so clearing the board eases the spawns
   back down with it. */
int  board_highest_value(const Board *b);

/* No empty cell and no legal move left. */
int  board_is_full(const Board *b);
int  board_game_over(const Board *b);

int  board_get(const Board *b, int row, int col);
void board_set(Board *b, int row, int col, int value);

#endif
