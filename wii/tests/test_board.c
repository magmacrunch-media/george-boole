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

    /* Double in every mode -- the web game has no per-width multiplier, and the
       port paid single above 3-bit for four commits. */
    eq(mode_height_bonus(3, 7),   14,  "3-bit pays double");
    eq(mode_height_bonus(6, 40),  80,  "6-bit pays double too");
    eq(mode_height_bonus(8, 200), 400, "and so does 8-bit");
    eq(mode_height_bonus(3, 2),   0,   "3-bit pays nothing below its floor");
    eq(mode_height_bonus(2, 3),   0,   "2-bit never pays a height bonus");
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

/* The gate mix is the difference between a 2-bit board full of operators and
   one where there is nothing to do. It was flat at 18% for every width until
   this test existed to say otherwise. */
static void test_gate_rate(void) {
    printf("gate rate\n");
    eq(mode_gate_spawn_pct(2), 45, "2-bit is mostly gates");
    eq(mode_gate_spawn_pct(3), 32, "3-bit tapers");
    eq(mode_gate_spawn_pct(4), 24, "4-bit tapers further");
    eq(mode_gate_spawn_pct(5), 20, "5-bit");
    eq(mode_gate_spawn_pct(6), 20, "6-bit shares 5-bit's rate");
    eq(mode_gate_spawn_pct(7), 18, "7-bit");
    eq(mode_gate_spawn_pct(8), 18, "8-bit barely needs them");
}

/* Every band edge and every step inside it. A cumulative table is transcribed
   by hand and a threshold off by one is invisible in play. */
static void test_spawn_table(void) {
    printf("spawn table\n");

    /* 2-bit: 1 or 2, never the ceiling. */
    eq(mode_spawn_value(2, 0, 0),  1, "2-bit low roll");
    eq(mode_spawn_value(2, 2, 49), 1, "2-bit last roll of the 1s");
    eq(mode_spawn_value(2, 2, 50), 2, "2-bit first roll of the 2s");
    eq(mode_spawn_value(2, 2, 99), 2, "2-bit high roll");

    /* 3-bit opens up once anything has been built. */
    eq(mode_spawn_value(3, 3, 0),  1, "3-bit fifths: 1");
    eq(mode_spawn_value(3, 3, 19), 1, "3-bit fifths: end of 1");
    eq(mode_spawn_value(3, 3, 20), 2, "3-bit fifths: 2");
    eq(mode_spawn_value(3, 3, 40), 3, "3-bit fifths: 3");
    eq(mode_spawn_value(3, 3, 60), 4, "3-bit fifths: 4");
    eq(mode_spawn_value(3, 3, 80), 5, "3-bit fifths: 5");
    eq(mode_spawn_value(3, 3, 99), 5, "3-bit fifths: end of 5");
    /* Below a 3 on the board it uses the ordinary progression. */
    eq(mode_spawn_value(3, 2, 50), 2, "3-bit falls back before anything is built");

    /* Opening board: 60/40. */
    eq(mode_spawn_value(4, 1, 59), 1, "opening 1s");
    eq(mode_spawn_value(4, 1, 60), 2, "opening 2s");

    /* Highest 2..3: 50/50. */
    eq(mode_spawn_value(4, 3, 49), 1, "early 1s");
    eq(mode_spawn_value(4, 3, 50), 2, "early 2s");

    /* Highest 4..7: 40/35/25. */
    eq(mode_spawn_value(4, 7, 39), 1, "mid-early 1s");
    eq(mode_spawn_value(4, 7, 40), 2, "mid-early 2s");
    eq(mode_spawn_value(4, 7, 74), 2, "mid-early end of 2s");
    eq(mode_spawn_value(4, 7, 75), 3, "mid-early 3s");

    /* Highest 8..15: 40/30/20/10. */
    eq(mode_spawn_value(4, 8, 39), 1, "mid 1s");
    eq(mode_spawn_value(4, 8, 40), 2, "mid 2s");
    eq(mode_spawn_value(4, 8, 70), 3, "mid 3s");
    eq(mode_spawn_value(4, 8, 90), 4, "mid 4s");
    eq(mode_spawn_value(4, 8, 99), 4, "mid end of 4s");

    /* Highest 16..31: 1-6. */
    eq(mode_spawn_value(5, 16, 29), 1, "late-mid 1s");
    eq(mode_spawn_value(5, 16, 30), 2, "late-mid 2s");
    eq(mode_spawn_value(5, 16, 50), 3, "late-mid 3s");
    eq(mode_spawn_value(5, 16, 70), 4, "late-mid 4s");
    eq(mode_spawn_value(5, 16, 85), 5, "late-mid 5s");
    eq(mode_spawn_value(5, 16, 95), 6, "late-mid 6s");

    /* Highest 32..63: 1-8. */
    eq(mode_spawn_value(6, 32, 24), 1, "late 1s");
    eq(mode_spawn_value(6, 32, 25), 2, "late 2s");
    eq(mode_spawn_value(6, 32, 40), 3, "late 3s");
    eq(mode_spawn_value(6, 32, 55), 4, "late 4s");
    eq(mode_spawn_value(6, 32, 70), 5, "late 5s");
    eq(mode_spawn_value(6, 32, 80), 6, "late 6s");
    eq(mode_spawn_value(6, 32, 90), 7, "late 7s");
    eq(mode_spawn_value(6, 32, 96), 8, "late 8s");

    /* Highest 64+: the even ladder up to 12. */
    eq(mode_spawn_value(8, 64, 19), 1,  "very late 1s");
    eq(mode_spawn_value(8, 64, 20), 2,  "very late 2s");
    eq(mode_spawn_value(8, 64, 35), 4,  "very late 4s");
    eq(mode_spawn_value(8, 64, 50), 6,  "very late 6s");
    eq(mode_spawn_value(8, 64, 65), 8,  "very late 8s");
    eq(mode_spawn_value(8, 64, 78), 10, "very late 10s");
    eq(mode_spawn_value(8, 64, 88), 12, "very late 12s");
    eq(mode_spawn_value(8, 64, 99), 12, "very late end of 12s");

    /* An out-of-range roll must land somewhere legal rather than off the end. */
    eq(mode_spawn_value(4, 8, -1),  1, "a negative roll clamps low");
    eq(mode_spawn_value(4, 8, 500), 4, "an oversized roll clamps high");

    /* The board's highest is what the table reads, gates and empties ignored. */
    Board b;
    board_init(&b, 4, 0);
    eq(board_highest_value(&b), 0, "an empty board has no highest");
    b.cells[0][0] = GATE_NOT;
    b.cells[1][1] = 9;
    b.cells[2][2] = 4;
    eq(board_highest_value(&b), 9, "gates and empties do not count");
}

/* The gate share coming out of board_spawn, not just out of the table: this is
   the check that would have caught the flat 18%. */
static void test_spawn_distribution(void) {
    printf("spawn distribution\n");

    static const int widths[] = { 2, 3, 4, 5, 6, 7, 8 };
    const int samples = 6000;

    for (unsigned int w = 0; w < sizeof(widths) / sizeof(widths[0]); w++) {
        int bits = widths[w];
        int gates = 0;

        for (int roll = 0; roll < samples; roll++) {
            Board t;
            board_init(&t, bits, 0);
            board_spawn(&t, (unsigned int)roll);
            if (board_is_gate(t.cells[t.spawn_row][t.spawn_col])) gates++;
        }

        int pct = (gates * 100) / samples;
        int want = mode_gate_spawn_pct(bits);
        checks++;
        if (pct < want - 4 || pct > want + 4) {
            printf("  FAIL: %d-bit spawned %d%% gates, wanted about %d%%\n",
                   bits, pct, want);
            failures++;
        }
    }
}

/* Named for the reason it exists: the web game's "2-bit fix". With only three
   values, a board that hands you the ceiling has handed you the mode. */
static void test_two_bit_ceiling(void) {
    printf("two-bit ceiling\n");
    int seen_1 = 0, seen_2 = 0, seen_3 = 0;

    for (int roll = 0; roll < 4000; roll++) {
        Board t;
        board_init(&t, 2, 0);
        board_spawn(&t, (unsigned int)roll);
        int v = t.cells[t.spawn_row][t.spawn_col];
        if (v == 1) seen_1 = 1;
        if (v == 2) seen_2 = 1;
        if (v == 3) seen_3 = 1;
    }

    ok(seen_1, "2-bit spawns 1s");
    ok(seen_2, "2-bit spawns 2s");
    ok(!seen_3, "2-bit never spawns its ceiling");
}

static void test_height_thresholds(void) {
    printf("height thresholds\n");
    ok(mode_height_threshold(2) > mode_max_value(2), "2-bit's floor is unreachable");
    eq(mode_height_threshold(3), 6,  "3-bit celebrates 6 and 7");
    eq(mode_height_threshold(4), 5,  "4-bit celebrates 5 and up");
    eq(mode_height_threshold(5), 15, "5-bit is half the ceiling");
    eq(mode_height_threshold(6), 31, "6-bit is half the ceiling");
    eq(mode_height_threshold(7), 42, "7-bit is a third of the ceiling");
    eq(mode_height_threshold(8), 85, "8-bit is a third of the ceiling");
}

/* Both were found by replaying random positions through the browser game and
   diffing the points, not by reading the code -- so they are pinned here. */
static void test_scoring_parity(void) {
    printf("scoring parity\n");
    Board b;

    /* A unary NOT is worth its result, exactly like a gate sandwich is. The
       port awarded the height bonus for one but never the operation itself,
       which cost the most in the wide modes where NOT results are large. */
    board_init(&b, 8, 0);
    b.highest_earned = 255;          /* height bonuses out of the way */
    b.cells[0][0] = GATE_NOT;
    b.cells[0][1] = 50;
    board_move(&b, DIR_LEFT);
    eq(b.cells[0][0], 205, "NOT 50 is 205 at 8-bit");
    eq(b.score, 205, "and it is worth 205");

    board_init(&b, 8, 0);
    b.highest_earned = 255;
    b.cells[0][0] = 50;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.score, 205, "worth the same from the other side");

    /* A first-time height bonus pays once, to whichever line gets there first,
       so which line is resolved first is a scoring rule. Collapsing up, the web
       game takes the columns right to left. Here the right column builds 61 and
       the left builds 32: going left to right would pay for both. */
    board_init(&b, 6, 0);
    b.cells[0][0] = 31; b.cells[1][0] = GATE_NOT;
    b.cells[0][1] = 60; b.cells[1][1] = GATE_OR; b.cells[2][1] = 49;
    board_move(&b, DIR_UP);
    eq(b.cells[0][0], 32, "NOT 31 is 32 at 6-bit");
    eq(b.cells[0][1], 61, "60 OR 49 is 61");
    eq(b.score, 93 + 122, "the later, smaller value earns no second bonus");
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

/* Finds the move landing on a cell, or NULL. */
static const TileMove *move_to(const Board *b, int row, int col) {
    for (int i = 0; i < b->move_count; i++) {
        if (b->moves[i].to_row == row && b->moves[i].to_col == col) return &b->moves[i];
    }
    return NULL;
}

static int moves_to(const Board *b, int row, int col) {
    int n = 0;
    for (int i = 0; i < b->move_count; i++) {
        if (b->moves[i].to_row == row && b->moves[i].to_col == col) n++;
    }
    return n;
}

/* Chaining: a line is re-scanned after each resolution, so a result becomes an
   operand for the next one. Every case here is a position where the port used to
   disagree with the browser game, taken from a replay diff rather than invented. */
static void test_chaining(void) {
    printf("chaining\n");

    /* The plainest case: a gate result meets a tile it can consolidate with. A
       single pass would leave two 3s sitting next to each other. */
    { const int in[4]={1,GATE_XOR,2,3}, w[4]={3,0,0,0};
      eq_row(2, in, w, "1 XOR 2 makes a 3 that consolidates with the 3 beside it"); }

    /* A NOT pair behind a number cancels, so the run resolves once rather than a
       step at a time. Resolving stepwise reaches the same tile but bills three
       operations for it and claims a height no tile ever rested on. */
    { const int in[4]={114,GATE_NOT,GATE_NOT,GATE_NOT}, w[4]={13,0,0,0};
      eq_row(7, in, w, "a run of NOTs behind a number resolves in one step"); }

    Board b;
    board_init(&b, 7, 0);
    b.cells[0][0] = 114;
    b.cells[0][1] = GATE_NOT;
    b.cells[0][2] = GATE_NOT;
    b.cells[0][3] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.score, 13, "and is paid for once, not once per NOT");

    /* Overflow clears the tile and the gate beyond it is left alone. The browser
       game used to treat the cleared cell as a 0 operand, so AND took the 4 with
       it -- this is that case from the other side. */
    { const int in[4]={7,GATE_NOT,GATE_AND,4}, w[4]={GATE_AND,4,0,0};
      eq_row(3, in, w, "a cleared tile is not an operand for the next gate"); }

    /* Provenance has to survive the chain: four tiles end in one cell, and the
       renderer draws a tile arriving from each. Collapsing them into fewer
       origins would show tiles vanishing instead of travelling. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 1;
    b.cells[0][1] = GATE_XOR;
    b.cells[0][2] = 2;
    b.cells[0][3] = 3;
    board_move(&b, DIR_LEFT);
    eq(b.cells[0][0], 3, "the chain lands on one tile");
    eq(moves_to(&b, 0, 0), 4, "and all four tiles are drawn arriving there");
}

static void test_move_tracking(void) {
    printf("move tracking\n");
    Board b;

    /* A lone tile crossing the board: one move, from where it was to where it
       ended, carrying its value. */
    board_init(&b, 2, 0);
    b.cells[0][3] = 2;
    board_move(&b, DIR_LEFT);
    eq(b.move_count, 1, "one surviving tile, one move");
    const TileMove *m = move_to(&b, 0, 0);
    ok(m != NULL, "a move lands on the destination");
    if (m) {
        eq(m->from_col, 3, "it started where the tile was");
        eq(m->to_col, 0, "it ended at the left edge");
        eq(m->from_value, 2, "it carries the value that slid");
        eq(m->merged, 0, "a plain slide is not a merge");
    }

    /* A merge: both sources land on the same cell, each carrying its own value,
       both flagged so the renderer can pop the result. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 1;
    b.cells[0][1] = 1;
    board_move(&b, DIR_LEFT);
    eq(moves_to(&b, 0, 0), 2, "both merged tiles slide to the same cell");
    m = move_to(&b, 0, 0);
    if (m) {
        eq(m->to_value, 1, "idempotent merge resolves to the same value");
        eq(m->merged, 1, "flagged as a merge");
    }

    /* A gate sandwich contributes three sources to one destination. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 1;
    b.cells[0][1] = GATE_OR;
    b.cells[0][2] = 2;
    board_move(&b, DIR_LEFT);
    eq(moves_to(&b, 0, 0), 3, "number, gate and number all slide to one cell");
    m = move_to(&b, 0, 0);
    if (m) eq(m->to_value, 3, "1 OR 2 = 3 at the destination");

    /* Tiles that did not move still have to be drawn while others slide. */
    board_init(&b, 2, 0);
    b.cells[0][0] = 1;
    b.cells[0][3] = 2;
    board_move(&b, DIR_LEFT);
    eq(b.move_count, 2, "a stationary tile is still reported");
    m = move_to(&b, 0, 0);
    if (m) eq(m->from_col, 0, "the stationary tile moves from itself to itself");

    /* Tiles consumed without a result simply vanish -- nothing to slide. */
    board_init(&b, 2, 0);
    b.cells[0][0] = GATE_NOT;
    b.cells[0][1] = GATE_NOT;
    board_move(&b, DIR_LEFT);
    eq(b.move_count, 0, "cancelled NOTs leave nothing to draw");

    /* Every destination a move claims must actually hold a tile, or the
       renderer would draw a tile arriving at an empty cell. */
    board_init(&b, 3, 0);
    for (int r = 0; r < BOARD_SIZE; r++)
        for (int c = 0; c < BOARD_SIZE; c++) b.cells[r][c] = ((r + c) % 3) + 1;
    board_move(&b, DIR_UP);
    for (int i = 0; i < b.move_count; i++) {
        const TileMove *mv = &b.moves[i];
        checks++;
        if (board_get(&b, mv->to_row, mv->to_col) == TILE_EMPTY) {
            printf("  FAIL: move lands on an empty cell (%d,%d)\n",
                   mv->to_row, mv->to_col);
            failures++;
        }
    }

    /* Spawn location is reported so the new tile can be popped in. */
    board_init(&b, 2, 0);
    eq(b.spawn_row, -1, "nothing spawned yet");
    board_spawn(&b, 1234);
    ok(b.spawn_row >= 0 && b.spawn_col >= 0, "spawn reports where it landed");
    ok(board_get(&b, b.spawn_row, b.spawn_col) != TILE_EMPTY,
       "and there is a tile there");
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

    /* Each gate type must return its own per-gate colour. */
    ok(palette_tile_color(gb, GATE_XOR, 3) == gb->gate_color[0],
       "XOR uses gate_color[0]");
    ok(palette_tile_color(gb, GATE_OR, 3) == gb->gate_color[1],
       "OR uses gate_color[1]");
    ok(palette_tile_color(gb, GATE_AND, 3) == gb->gate_color[2],
       "AND uses gate_color[2]");
    ok(palette_tile_color(gb, GATE_NOT, 3) == gb->gate_color[3],
       "NOT uses gate_color[3]");

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

    /* All four gates must be distinct from each other per mode, and none may
       collide with a ramp step -- the property gates.css was designed for. */
    for (int m = 0; m < MODE_COUNT; m++) {
        const Palette *p = palette_for((ModeId)m);
        const int gates[] = { GATE_XOR, GATE_OR, GATE_AND, GATE_NOT };
        for (int i = 0; i < 4; i++) {
            for (int j = i + 1; j < 4; j++) {
                checks++;
                u32 ci = palette_tile_color(p, gates[i], 3);
                u32 cj = palette_tile_color(p, gates[j], 3);
                if (ci == cj) {
                    printf("  FAIL: mode %d gates %d and %d are identical\n",
                           m, gates[i], gates[j]);
                    failures++;
                }
            }
            /* Gate colour must not match any ramp step. */
            u32 gc = palette_tile_color(p, gates[i], 3);
            for (int r = 0; r < 5; r++) {
                checks++;
                if (gc == p->ramp[r]) {
                    printf("  FAIL: mode %d gate %d collides with ramp step %d\n",
                           m, gates[i], r);
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
    test_gate_rate();
    test_spawn_table();
    test_spawn_distribution();
    test_two_bit_ceiling();
    test_height_thresholds();
    test_scoring_parity();
    test_modes();
    test_chaining();
    test_move_tracking();
    test_palette();

    printf("\n%d checks, %d failures\n", checks, failures);
    return failures ? 1 : 0;
}
