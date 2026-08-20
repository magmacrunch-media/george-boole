/* The Boolean rules, checked against the web game's own assertions.
 *
 * Ported from arcade/george-boole/tests/test-game-logic.js. The Wii build and
 * the web build have to agree on every one of these or the same game plays
 * differently in two places, and that divergence is invisible until a player
 * notices. Pure C, so it runs here in a second:
 *
 *   make test
 */
#include <stdio.h>
#include <string.h>
#include "board.h"
#include "modes.h"
#include "palette.h"

static int checks = 0, failures = 0;

static void ok(int cond, const char *what) {
    checks++;
    if (!cond) { printf("  FAIL: %s\n", what); failures++; }
}

static void eq(int got, int want, const char *what) {
    checks++;
    if (got != want) {
        printf("  FAIL: %s (got %d, want %d)\n", what, got, want);
        failures++;
    }
}

static Board bits_board(int bits) {
    Board b;
    board_init(&b, bits, 0);
    return b;
}

static int gate_at(int bits, int gate, int lhs, int rhs) {
    Board b = bits_board(bits);
    return board_apply_gate(&b, gate, lhs, rhs);
}

/* Runs one row through a move and reports the resulting row. */
static void row_after_move(int bits, const int in[4], int out[4]) {
    Board b;
    board_init(&b, bits, 0);
    for (int c = 0; c < 4; c++) b.cells[0][c] = in[c];
    board_move(&b, DIR_LEFT);
    for (int c = 0; c < 4; c++) out[c] = b.cells[0][c];
}

static void eq_row(int bits, const int in[4], const int want[4], const char *what) {
    int got[4];
    row_after_move(bits, in, got);
    checks++;
    if (memcmp(got, want, sizeof(got)) != 0) {
        printf("  FAIL: %s\n         got  [%d %d %d %d]\n         want [%d %d %d %d]\n",
               what, got[0], got[1], got[2], got[3],
               want[0], want[1], want[2], want[3]);
        failures++;
    }
}

static void test_is_gate(void) {
    printf("is_gate\n");
    ok(board_is_gate(GATE_XOR), "XOR is a gate");
    ok(board_is_gate(GATE_OR),  "OR is a gate");
    ok(board_is_gate(GATE_AND), "AND is a gate");
    ok(board_is_gate(GATE_NOT), "NOT is a gate");
    ok(!board_is_gate(0), "0 is not a gate");
    ok(!board_is_gate(1), "1 is not a gate");
    ok(!board_is_gate(7), "7 is not a gate");
}

static void test_gates(void) {
    printf("apply_gate\n");
    /* XOR */
    eq(gate_at(2, GATE_XOR, 1, 2), 3, "1 XOR 2 = 3");
    eq(gate_at(2, GATE_XOR, 3, 3), 0, "3 XOR 3 = 0");
    eq(gate_at(2, GATE_XOR, 1, 1), 0, "1 XOR 1 = 0");
    eq(gate_at(2, GATE_XOR, 2, 2), 0, "2 XOR 2 = 0");
    eq(gate_at(3, GATE_XOR, 0, 5), 5, "0 XOR 5 = 5");
    eq(gate_at(3, GATE_XOR, 5, 0), 5, "5 XOR 0 = 5");
    /* OR */
    eq(gate_at(2, GATE_OR, 1, 2), 3, "1 OR 2 = 3");
    eq(gate_at(2, GATE_OR, 3, 3), 3, "3 OR 3 = 3");
    eq(gate_at(2, GATE_OR, 1, 1), 1, "1 OR 1 = 1");
    eq(gate_at(3, GATE_OR, 0, 5), 5, "0 OR 5 = 5");
    eq(gate_at(3, GATE_OR, 5, 3), 7, "5 OR 3 = 7");
    /* AND */
    eq(gate_at(2, GATE_AND, 1, 2), 0, "1 AND 2 = 0");
    eq(gate_at(2, GATE_AND, 3, 3), 3, "3 AND 3 = 3");
    eq(gate_at(2, GATE_AND, 1, 3), 1, "1 AND 3 = 1");
    eq(gate_at(3, GATE_AND, 5, 3), 1, "5 AND 3 = 1");
    eq(gate_at(3, GATE_AND, 6, 3), 2, "6 AND 3 = 2");
    /* NOT is bit-width dependent, which is the whole point of the modes. */
    eq(gate_at(2, GATE_NOT, 0, 0), 3, "NOT 0 = 3 (2-bit)");
    eq(gate_at(2, GATE_NOT, 1, 0), 2, "NOT 1 = 2 (2-bit)");
    eq(gate_at(2, GATE_NOT, 2, 0), 1, "NOT 2 = 1 (2-bit)");
    eq(gate_at(2, GATE_NOT, 3, 0), 0, "NOT 3 = 0 (2-bit)");
    eq(gate_at(3, GATE_NOT, 0, 0), 7, "NOT 0 = 7 (3-bit)");
    eq(gate_at(3, GATE_NOT, 7, 0), 0, "NOT 7 = 0 (3-bit)");
    eq(gate_at(4, GATE_NOT, 5, 0), 10, "NOT 5 = 10 (4-bit)");
}

static void test_basic(void) {
    printf("move: basic\n");
    { const int in[4]={1,2,3,0}, w[4]={1,2,3,0}; eq_row(2,in,w,"no merge"); }
    { const int in[4]={1,1,0,0}, w[4]={1,0,0,0}; eq_row(2,in,w,"same merge"); }
    { const int in[4]={2,2,0,0}, w[4]={2,0,0,0}; eq_row(2,in,w,"same merge 2"); }
    { const int in[4]={3,3,0,0}, w[4]={3,0,0,0}; eq_row(2,in,w,"same merge 3"); }
    { const int in[4]={1,2,1,2}, w[4]={1,2,1,2}; eq_row(2,in,w,"no merge, different"); }
}

static void test_idempotent(void) {
    printf("move: idempotence\n");
    { const int in[4]={1,1,0,0}, w[4]={1,0,0,0}; eq_row(2,in,w,"1+1=1"); }
    { const int in[4]={2,2,0,0}, w[4]={2,0,0,0}; eq_row(2,in,w,"2+2=2"); }
    { const int in[4]={3,3,0,0}, w[4]={3,0,0,0}; eq_row(2,in,w,"3+3=3"); }
    { const int in[4]={5,5,0,0}, w[4]={5,0,0,0}; eq_row(3,in,w,"5+5=5 (3-bit)"); }
    { const int in[4]={7,7,0,0}, w[4]={7,0,0,0}; eq_row(3,in,w,"7+7=7 (3-bit)"); }
}

static void test_gate_patterns(void) {
    printf("move: gate sandwiches\n");
    { const int in[4]={1,GATE_XOR,2,0}, w[4]={3,0,0,0}; eq_row(2,in,w,"1 XOR 2 = 3"); }
    { const int in[4]={3,GATE_XOR,3,0}, w[4]={0,0,0,0}; eq_row(2,in,w,"3 XOR 3 = 0 clears"); }
    { const int in[4]={1,GATE_OR,2,0},  w[4]={3,0,0,0}; eq_row(2,in,w,"1 OR 2 = 3"); }
    { const int in[4]={3,GATE_AND,3,0}, w[4]={3,0,0,0}; eq_row(2,in,w,"3 AND 3 = 3"); }
    { const int in[4]={1,GATE_AND,2,0}, w[4]={0,0,0,0}; eq_row(2,in,w,"1 AND 2 = 0 clears"); }
}

static void test_not_patterns(void) {
    printf("move: NOT\n");
    { const int in[4]={GATE_NOT,1,0,0},        w[4]={2,0,0,0}; eq_row(2,in,w,"NOT then 1 = 2"); }
    { const int in[4]={1,GATE_NOT,0,0},        w[4]={2,0,0,0}; eq_row(2,in,w,"1 then NOT = 2"); }
    { const int in[4]={GATE_NOT,GATE_NOT,0,0}, w[4]={0,0,0,0}; eq_row(2,in,w,"NOT NOT cancels"); }
    { const int in[4]={GATE_NOT,GATE_NOT,1,0}, w[4]={1,0,0,0}; eq_row(2,in,w,"NOT NOT then 1 survives"); }
}

static void test_edges(void) {
    printf("move: edges\n");
    { const int in[4]={0,0,0,0}, w[4]={0,0,0,0}; eq_row(2,in,w,"all empty"); }
    { const int in[4]={1,2,3,4}, w[4]={1,2,3,4}; eq_row(3,in,w,"full row, no merge"); }
    { const int in[4]={GATE_NOT,0,0,0}, w[4]={GATE_NOT,0,0,0};
      eq_row(2,in,w,"lone NOT waits for a number"); }
}

static void test_overflow(void) {
    printf("overflow and promotion\n");

    /* NOT of the ceiling lands on 0, which cannot be a tile: the tile clears and
       the bonus pays. This is the only way to overflow -- a bitwise op on
       in-range operands can never exceed the ceiling. */
    Board b;
    board_init(&b, 2, 0);
    b.cells[0][0] = 3;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.cells[0][0], TILE_EMPTY, "NOT ceiling clears the tile");
    eq(b.last_overflow_bonus, 9, "2-bit overflow pays 9");
    eq(b.score, 9, "overflow bonus reaches the score");

    board_init(&b, 8, 0);
    b.cells[0][0] = 255;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.last_overflow_bonus, 765, "8-bit overflow pays 765");

    /* An 8-bit overflow alone is 765 points, which an increment-by-one score
       could not express -- this is what scoring_add() exists for. */
    ok(b.score >= 765, "a single move can be worth hundreds");

    printf("gauntlet\n");
    board_init(&b, 2, 1);
    eq(b.bits, 2, "gauntlet starts at 2-bit");
    b.cells[0][0] = 3;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.bits, 3, "reaching the ceiling promotes a bit width");
    eq(b.max_value, 7, "ceiling follows the width");
    ok(b.last_upgraded, "the promotion is reported to the caller");

    /* A plain mode must never promote, however high you climb. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 3;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.bits, 2, "a fixed mode stays at its width");
}

static void test_scoring(void) {
    printf("scoring\n");
    Board b;

    board_init(&b, 3, 0);
    b.cells[0][0] = 5;
    b.cells[0][1] = GATE_OR;
    b.cells[0][2] = 3;
    board_move(&b, DIR_LEFT);
    eq(b.cells[0][0], 7, "5 OR 3 = 7");
    ok(b.score >= 7, "an operation is worth its result");

    /* A height bonus is for building a value, not being handed one. */
    board_init(&b, 4, 0);
    b.highest_earned = 15;
    b.cells[0][0] = 5;
    b.cells[0][1] = 5;
    board_move(&b, DIR_LEFT);
    eq(b.last_height_bonus, 0, "no height bonus below what was already earned");

    eq(mode_height_bonus(3, 7), 14, "3-bit pays double for a high value");
    eq(mode_height_bonus(3, 2), 0,  "3-bit pays nothing below its floor");
    eq(mode_height_bonus(2, 3), 0,  "2-bit never pays a height bonus");
}

static void test_directions(void) {
    printf("directions\n");
    Board b;

    board_init(&b, 2, 0);
    b.cells[0][2] = 1;
    b.cells[0][3] = 1;
    board_move(&b, DIR_RIGHT);
    eq(b.cells[0][3], 1, "right-moving merge lands on the right edge");
    eq(b.cells[0][0], TILE_EMPTY, "and nothing is left behind");

    board_init(&b, 2, 0);
    b.cells[2][1] = 2;
    b.cells[3][1] = 2;
    board_move(&b, DIR_UP);
    eq(b.cells[0][1], 2, "upward merge lands on the top edge");

    board_init(&b, 2, 0);
    b.cells[0][1] = 2;
    b.cells[1][1] = 2;
    board_move(&b, DIR_DOWN);
    eq(b.cells[3][1], 2, "downward merge lands on the bottom edge");

    /* A move that changes nothing must say so, or the game spawns a tile for
       an input the player never actually made. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 1;
    b.cells[1][0] = 2;
    ok(!board_move(&b, DIR_LEFT), "a no-op move reports no change");
}

static void test_game_over(void) {
    printf("game over\n");
    Board b;

    board_init(&b, 4, 0);
    ok(!board_is_full(&b), "an empty board is not full");
    ok(!board_game_over(&b), "an empty board is not over");

    /* Full, but every neighbour differs and no gate is present: nothing can
       resolve in any direction. */
    board_init(&b, 4, 0);
    int pattern[4][4] = {
        { 1, 2, 1, 2 },
        { 2, 1, 2, 1 },
        { 1, 2, 1, 2 },
        { 2, 1, 2, 1 }
    };
    for (int r = 0; r < 4; r++)
        for (int c = 0; c < 4; c++) b.cells[r][c] = pattern[r][c];
    ok(board_is_full(&b), "checkerboard is full");
    ok(board_game_over(&b), "checkerboard with no gates is over");

    /* A gate in a corner cannot save anyone: a binary gate needs a number on
       both sides, and a corner has only one neighbour along each line. */
    b.cells[3][3] = GATE_XOR;
    ok(board_is_full(&b), "still full with a corner gate");
    ok(board_game_over(&b), "a cornered gate cannot resolve, so it is still over");

    /* The same gate one cell inward has numbers either side of it and revives
       the board. */
    for (int r = 0; r < 4; r++)
        for (int c = 0; c < 4; c++) b.cells[r][c] = pattern[r][c];
    b.cells[1][1] = GATE_XOR;   /* row 1 becomes 2, XOR, 2, 1 */
    ok(board_is_full(&b), "still full with an interior gate");
    ok(!board_game_over(&b), "an interior gate keeps a full board alive");

    /* Probing for a legal move must not award points. */
    board_init(&b, 4, 0);
    for (int r = 0; r < 4; r++)
        for (int c = 0; c < 4; c++) b.cells[r][c] = pattern[r][c];
    b.cells[0][0] = 1; b.cells[0][1] = 1;
    int before = b.score;
    board_game_over(&b);
    eq(b.score, before, "checking for game over does not score");
}

static void test_spawn(void) {
    printf("spawn\n");
    Board b;
    board_init(&b, 4, 0);

    for (int i = 0; i < BOARD_CELLS; i++) {
        ok(board_spawn(&b, i * 137) == 1, "spawns while cells remain");
    }
    ok(board_is_full(&b), "16 spawns fill the board");
    ok(board_spawn(&b, 5) == 0, "a full board refuses to spawn");

    /* Nothing may spawn outside the mode's range, or a tile appears that the
       rules cannot express. */
    board_init(&b, 2, 0);
    for (int roll = 0; roll < 3000; roll += 7) {
        Board t;
        board_init(&t, 2, 0);
        board_spawn(&t, roll);
        for (int r = 0; r < 4; r++) {
            for (int c = 0; c < 4; c++) {
                int v = t.cells[r][c];
                if (v == TILE_EMPTY) continue;
                checks++;
                if (!board_is_gate(v) && (v < 1 || v > t.max_value)) {
                    printf("  FAIL: spawned %d outside 1..%d\n", v, t.max_value);
                    failures++;
                }
            }
        }
    }
}

static void test_modes(void) {
    printf("modes\n");
    eq(mode_max_value(2), 3,   "2-bit ceiling is 3");
    eq(mode_max_value(3), 7,   "3-bit ceiling is 7");
    eq(mode_max_value(4), 15,  "4-bit ceiling is 15");
    eq(mode_max_value(8), 255, "8-bit ceiling is 255");

    eq(mode_overflow_bonus(2), 9,   "2-bit overflow bonus");
    eq(mode_overflow_bonus(3), 21,  "3-bit overflow bonus");
    eq(mode_overflow_bonus(4), 45,  "4-bit overflow bonus");
    eq(mode_overflow_bonus(5), 93,  "5-bit overflow bonus");
    eq(mode_overflow_bonus(6), 189, "6-bit overflow bonus");
    eq(mode_overflow_bonus(7), 381, "7-bit overflow bonus");
    eq(mode_overflow_bonus(8), 765, "8-bit overflow bonus");

    ok(mode_is_gauntlet(MODE_GAUNTLET), "gauntlet is the climbing mode");
    ok(!mode_is_gauntlet(MODE_4BIT), "nibble is not");
    eq(mode_start_bits(MODE_GAUNTLET), 2, "gauntlet starts at 2-bit");
    eq(mode_start_bits(MODE_8BIT), 8, "byte starts at 8-bit");

    /* Table ids become filenames, so they must be distinct and plain. */
    for (int i = 0; i < MODE_COUNT; i++) {
        for (int j = i + 1; j < MODE_COUNT; j++) {
            checks++;
            if (strcmp(mode_id((ModeId)i), mode_id((ModeId)j)) == 0) {
                printf("  FAIL: modes %d and %d share an id\n", i, j);
                failures++;
            }
        }
    }
}

static void test_palette(void) {
    printf("palette\n");
    const Palette *gb = palette_for(MODE_2BIT);
    const Palette *mx = palette_for(MODE_GAUNTLET);
    ok(gb != mx, "each mode has its own palette");

    /* The ramp must actually spread across a mode's range, or a wide board
       renders as one flat colour and the numbers carry all the meaning. */
    u32 low  = palette_tile_color(gb, 1, 3);
    u32 high = palette_tile_color(gb, 3, 3);
    ok(low != high, "low and high tiles differ in a 2-bit mode");

    const Palette *ps = palette_for(MODE_8BIT);
    ok(palette_tile_color(ps, 1, 255) != palette_tile_color(ps, 255, 255),
       "low and high tiles differ in an 8-bit mode");

    /* Out-of-range must clamp, not index past the ramp. */
    ok(palette_tile_color(gb, 999, 3) == palette_tile_color(gb, 3, 3),
       "an over-range value clamps to the top of the ramp");
    ok(palette_tile_color(gb, 0, 3) == gb->cell_bg, "0 is an empty cell");
    ok(palette_tile_color(gb, GATE_XOR, 3) == gb->gate_bg, "a gate uses the gate colour");

    /* Every step distinct, so adjacent values are told apart on a CRT. */
    for (int m = 0; m < MODE_COUNT; m++) {
        const Palette *p = palette_for((ModeId)m);
        for (int i = 0; i < 5; i++) {
            for (int j = i + 1; j < 5; j++) {
                checks++;
                if (p->ramp[i] == p->ramp[j]) {
                    printf("  FAIL: mode %d ramp steps %d and %d are identical\n", m, i, j);
                    failures++;
                }
            }
        }
    }
}

int main(void) {
    test_is_gate();
    test_gates();
    test_basic();
    test_idempotent();
    test_gate_patterns();
    test_not_patterns();
    test_edges();
    test_overflow();
    test_scoring();
    test_directions();
    test_game_over();
    test_spawn();
    test_modes();
    test_palette();

    printf("\n%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
