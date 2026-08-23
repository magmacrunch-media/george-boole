#include <string.h>
#include "board.h"
#include "modes.h"

int board_is_gate(int value) {
    return value == GATE_XOR || value == GATE_OR ||
           value == GATE_AND || value == GATE_NOT;
}

void board_init(Board *b, int bits, int gauntlet) {
    memset(b, 0, sizeof(*b));
    b->spawn_row = -1;
    b->spawn_col = -1;
    b->bits      = bits;
    b->max_value = mode_max_value(bits);
    b->gauntlet  = gauntlet ? 1 : 0;
}

int board_get(const Board *b, int row, int col) { return b->cells[row][col]; }
void board_set(Board *b, int row, int col, int value) { b->cells[row][col] = value; }

/* Promotion happens the first time the ceiling is reached at a given width. The
   flag resets with the width, so each rung has to be earned on its own. */
static void reached_ceiling(Board *b) {
    if (b->reached_max) return;
    b->reached_max = 1;

    if (b->gauntlet && b->bits < 8) {
        b->bits++;
        b->max_value = mode_max_value(b->bits);
        b->reached_max = 0;
        b->last_upgraded = 1;
    }
}

int board_apply_gate(const Board *b, int gate, int lhs, int rhs) {
    switch (gate) {
        case GATE_XOR: return lhs ^ rhs;
        case GATE_OR:  return lhs | rhs;
        case GATE_AND: return lhs & rhs;
        case GATE_NOT: return (~lhs) & b->max_value;
        default:       return lhs;
    }
}

/* Both operands are already within the bit width, so a bitwise result is too --
   the ceiling can only be cleared by NOT of the ceiling itself, which lands on
   0. A tile of 0 cannot exist, so that is the overflow: the tile clears and the
   bonus pays. The web game also guards `result > maxValue`, which no bitwise
   operation on in-range operands can reach. */
static int resolve_gate(Board *b, int gate, int lhs, int rhs) {
    int result = board_apply_gate(b, gate, lhs, rhs);

    if (result == 0 && gate == GATE_NOT && lhs == b->max_value) {
        int bonus = mode_overflow_bonus(b->bits);
        b->score += bonus;
        b->last_gained += bonus;
        b->last_overflow_bonus += bonus;
        reached_ceiling(b);
        return 0;
    }
    return result;
}

/* First-time height bonuses only pay for values built by merging. A value that
   merely spawned was not an achievement, and paying for it would make the best
   strategy "wait". */
static void award_height(Board *b, int value) {
    if (value <= b->highest_earned) return;

    int bonus = mode_height_bonus(b->bits, value);
    b->highest_earned = value;
    if (bonus > 0) {
        b->score += bonus;
        b->last_gained += bonus;
        b->last_height_bonus += bonus;
    }
    if (value == b->max_value) reached_ceiling(b);
}

/* Collapses one line toward index 0 and resolves it. Everything the game is
   about happens here, and the order of the cases is the rule set:
   NOT cancels NOT, NOT consumes a neighbouring number from either side, a gate
   between two numbers applies to both, and equal numbers merge to themselves
   (idempotence -- 1 OR 1 is 1, not 2). */
/* Which original positions produced each surviving cell.
 *
 * A line is re-scanned after every resolution, so a result can become an operand
 * for the next one -- which means a cell's provenance is the union of everything
 * that fed it, and a whole line can end up arriving in one place. Hence a set per
 * cell rather than the three slots one sandwich needs. Only collected for real
 * moves; the game-over probe passes NULL and skips the bookkeeping. */
typedef struct {
    int src[BOARD_SIZE][BOARD_SIZE];
    int n[BOARD_SIZE];
} LineTrace;

/* Fold `count` cells at `at` into their result, closing the gap behind them.
   `result` of TILE_EMPTY means the operation consumed its operands and produced
   nothing -- two NOTs cancelling, or a gate landing on zero -- and their origins
   go with them, which is what board.h promises. */
static void collapse(int *cells, int org[][BOARD_SIZE], int *orgn, int *len,
                     int at, int count, int result) {
    int keep = (result != TILE_EMPTY);

    if (keep) {
        /* Union first, into a scratch set: the destination is one of the sources,
           so writing it in place would drop its own origins. */
        int fold[BOARD_SIZE];
        int foldn = 0;
        for (int c = at; c < at + count; c++) {
            for (int k = 0; k < orgn[c] && foldn < BOARD_SIZE; k++) {
                fold[foldn++] = org[c][k];
            }
        }
        cells[at] = result;
        orgn[at]  = foldn;
        for (int k = 0; k < foldn; k++) org[at][k] = fold[k];
    }

    int to = keep ? at + 1 : at;
    for (int c = at + count; c < *len; c++, to++) {
        cells[to] = cells[c];
        orgn[to]  = orgn[c];
        for (int k = 0; k < orgn[c]; k++) org[to][k] = org[c][k];
    }
    *len -= count - (keep ? 1 : 0);
}

/* Resolve one gate and pay for it. Every gate is worth its result, so scoring
   lives here rather than being repeated at each pattern; the overflow bonus is
   inside resolve_gate(). A zero result is a cleared tile, worth nothing. */
static int operate(Board *b, int gate, int lhs, int rhs, int score_it) {
    int r = score_it ? resolve_gate(b, gate, lhs, rhs)
                     : board_apply_gate(b, gate, lhs, rhs);
    if (score_it && r != 0) {
        b->score += r;
        b->last_gained += r;
        award_height(b, r);
    }
    return r;
}

/* Collapses one line toward index 0 and resolves it. Everything the game is
   about happens here, and the order of the cases is the rule set.
 *
 * The line is re-scanned from the same position after each resolution rather
 * than walked once, so a result can feed the next operation in the same move:
 * 1 XOR 2 makes a 3, and a 3 already sitting beside it then consolidates with
 * it. That is the web game's behaviour and this is a port of it -- the order of
 * the cases below matters for the same reason, because an earlier pattern
 * shadows a later one that would also have matched. */
static int advance_line(Board *b, int *line, int score_it, LineTrace *tr,
                        int *pack_src) {
    int cells[BOARD_SIZE];
    int org[BOARD_SIZE][BOARD_SIZE];
    int orgn[BOARD_SIZE];
    int len = 0;

    for (int k = 0; k < BOARD_SIZE; k++) {
        if (line[k] == TILE_EMPTY) continue;
        if (pack_src) pack_src[len] = k;
        cells[len]  = line[k];
        org[len][0] = len;
        orgn[len]   = 1;
        len++;
    }

    int merged = 0;
    int i = 0;

    while (i < len) {
        /* NOT + NOT: two inversions are no inversion, and both are consumed. */
        if (cells[i] == GATE_NOT && i + 1 < len && cells[i + 1] == GATE_NOT) {
            collapse(cells, org, orgn, &len, i, 2, TILE_EMPTY);
            merged = 1;
            continue;
        }

        /* NOT applied to the number after it. */
        if (cells[i] == GATE_NOT && i + 1 < len && !board_is_gate(cells[i + 1])) {
            int r = operate(b, GATE_NOT, cells[i + 1], 0, score_it);
            collapse(cells, org, orgn, &len, i, 2, r);
            merged = 1;
            continue;
        }

        /* A NOT pair cancels behind a number too. Without this the next case
           matches first and a run of NOTs resolves one at a time, scoring every
           intermediate value and claiming heights no tile ever rested on. */
        if (!board_is_gate(cells[i]) && i + 2 < len &&
            cells[i + 1] == GATE_NOT && cells[i + 2] == GATE_NOT) {
            collapse(cells, org, orgn, &len, i + 1, 2, TILE_EMPTY);
            merged = 1;
            continue;
        }

        /* NOT applied to the number before it. */
        if (!board_is_gate(cells[i]) && i + 1 < len && cells[i + 1] == GATE_NOT) {
            int r = operate(b, GATE_NOT, cells[i], 0, score_it);
            collapse(cells, org, orgn, &len, i, 2, r);
            merged = 1;
            continue;
        }

        /* number gate number. NOT is excluded: it is unary and was handled. */
        if (!board_is_gate(cells[i]) && i + 2 < len &&
            board_is_gate(cells[i + 1]) && cells[i + 1] != GATE_NOT &&
            !board_is_gate(cells[i + 2])) {
            int r = operate(b, cells[i + 1], cells[i], cells[i + 2], score_it);
            collapse(cells, org, orgn, &len, i, 3, r);
            merged = 1;
            continue;
        }

        /* Idempotence: equal numbers consolidate to one of themselves. The only
           case that advances -- a consolidated tile is settled, where a gate
           result is not. */
        if (i + 1 < len && !board_is_gate(cells[i]) && cells[i] == cells[i + 1]) {
            int value = cells[i];
            if (score_it) {
                b->score += value;
                b->last_gained += value;
                award_height(b, value);
            }
            collapse(cells, org, orgn, &len, i, 2, value);
            merged = 1;
            i++;
            continue;
        }

        i++;
    }

    if (tr) {
        for (int k = 0; k < BOARD_SIZE; k++) tr->n[k] = 0;
        for (int c = 0; c < len; c++) {
            tr->n[c] = orgn[c];
            for (int k = 0; k < orgn[c]; k++) tr->src[c][k] = org[c][k];
        }
    }

    int changed = 0;
    for (int k = 0; k < BOARD_SIZE; k++) {
        int v = (k < len) ? cells[k] : TILE_EMPTY;
        if (line[k] != v) changed = 1;
        line[k] = v;
    }
    return changed || merged;
}

/* Reads a row or column into a line running in the direction of travel, so
   advance_line() only ever has to collapse toward index 0. */
static void read_line(const Board *b, BoardDir dir, int index, int *line) {
    for (int k = 0; k < BOARD_SIZE; k++) {
        switch (dir) {
            case DIR_LEFT:  line[k] = b->cells[index][k]; break;
            case DIR_RIGHT: line[k] = b->cells[index][BOARD_SIZE - 1 - k]; break;
            case DIR_UP:    line[k] = b->cells[k][index]; break;
            case DIR_DOWN:  line[k] = b->cells[BOARD_SIZE - 1 - k][index]; break;
        }
    }
}

/* The cell a line position corresponds to -- the inverse of read_line(), needed
   to turn line-space provenance back into board coordinates. */
static void line_to_cell(BoardDir dir, int index, int k, int *row, int *col) {
    switch (dir) {
        case DIR_LEFT:  *row = index; *col = k; break;
        case DIR_RIGHT: *row = index; *col = BOARD_SIZE - 1 - k; break;
        case DIR_UP:    *row = k; *col = index; break;
        case DIR_DOWN:  *row = BOARD_SIZE - 1 - k; *col = index; break;
        default:        *row = 0; *col = 0; break;
    }
}

/* Which line to resolve on step 0..3.
   Lines are independent, so this cannot change where a tile lands -- but a
   first-time height bonus pays once, to whichever line reaches the value first,
   and the web game collapses by rotating the board and always taking rows in
   order. That makes its right and up run through the lines backwards. Matching
   the points means matching the order. */
static int line_index(BoardDir dir, int step) {
    return (dir == DIR_RIGHT || dir == DIR_UP) ? BOARD_SIZE - 1 - step : step;
}

static void write_line(Board *b, BoardDir dir, int index, const int *line) {
    for (int k = 0; k < BOARD_SIZE; k++) {
        switch (dir) {
            case DIR_LEFT:  b->cells[index][k] = line[k]; break;
            case DIR_RIGHT: b->cells[index][BOARD_SIZE - 1 - k] = line[k]; break;
            case DIR_UP:    b->cells[k][index] = line[k]; break;
            case DIR_DOWN:  b->cells[BOARD_SIZE - 1 - k][index] = line[k]; break;
        }
    }
}

int board_move(Board *b, BoardDir dir) {
    b->last_gained = 0;
    b->last_overflow_bonus = 0;
    b->last_height_bonus = 0;
    b->last_upgraded = 0;
    b->move_count = 0;
    b->spawn_row = -1;
    b->spawn_col = -1;

    int changed = 0;
    for (int step = 0; step < BOARD_SIZE; step++) {
        int index = line_index(dir, step);
        int line[BOARD_SIZE];
        read_line(b, dir, index, line);

        int before[BOARD_SIZE];
        memcpy(before, line, sizeof(before));

        LineTrace tr;
        int pack_src[BOARD_SIZE];
        advance_line(b, line, 1, &tr, pack_src);

        /* Provenance is recorded for every line, moved or not: a tile that
           stayed put still has to be drawn while its neighbours slide. */
        for (int slot = 0; slot < BOARD_SIZE && b->move_count < BOARD_CELLS; slot++) {
            if (line[slot] == TILE_EMPTY) continue;
            for (int c = 0; c < tr.n[slot] && b->move_count < BOARD_CELLS; c++) {
                int origin = pack_src[tr.src[slot][c]];

                TileMove *m = &b->moves[b->move_count++];
                line_to_cell(dir, index, origin, &m->from_row, &m->from_col);
                line_to_cell(dir, index, slot, &m->to_row, &m->to_col);
                m->from_value = before[origin];
                m->to_value   = line[slot];
                m->merged     = (tr.n[slot] > 1);
            }
        }

        if (memcmp(before, line, sizeof(before)) != 0) {
            changed = 1;
            write_line(b, dir, index, line);
        }
    }
    return changed;
}

int board_is_full(const Board *b) {
    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            if (b->cells[r][c] == TILE_EMPTY) return 0;
        }
    }
    return 1;
}

int board_game_over(const Board *b) {
    if (!board_is_full(b)) return 0;

    /* Full is not over while some direction still resolves something. Tested on
       a copy with scoring off, so probing for a legal move cannot award points. */
    for (int d = 0; d < 4; d++) {
        Board copy = *b;
        int any = 0;
        for (int index = 0; index < BOARD_SIZE; index++) {
            int line[BOARD_SIZE], before[BOARD_SIZE];
            read_line(&copy, (BoardDir)d, index, line);
            memcpy(before, line, sizeof(before));
            advance_line(&copy, line, 0, NULL, NULL);
            if (memcmp(before, line, sizeof(before)) != 0) any = 1;
        }
        if (any) return 0;
    }
    return 1;
}

int board_highest_value(const Board *b) {
    int max = 0;
    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            int v = b->cells[r][c];
            if (v > max) max = v;   /* gates are negative, empties are 0 */
        }
    }
    return max;
}

int board_spawn(Board *b, unsigned int roll) {
    int empty[BOARD_CELLS][2];
    int n = 0;
    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            if (b->cells[r][c] == TILE_EMPTY) {
                empty[n][0] = r;
                empty[n][1] = c;
                n++;
            }
        }
    }
    if (n == 0) return 0;

    /* Three decisions, three streams. The roll is mixed before the first of
       them because callers pass consecutive or evenly spaced numbers -- tests
       always do -- and the low bits of those would otherwise walk the cell and
       the value in lockstep. Stepping an LCG between the streams keeps them
       independent of each other. */
    unsigned int r0 = roll * 2654435761u + 0x9E3779B9u;
    unsigned int r1 = r0 * 1103515245u + 12345u;
    unsigned int r2 = r1 * 1103515245u + 12345u;

    int slot       = (int)((r0 >> 16) % (unsigned int)n);
    int gate_roll  = (int)((r1 >> 16) % 100u);
    int value_roll = (int)((r2 >> 16) % 100u);

    int value;
    if (gate_roll < mode_gate_spawn_pct(b->bits)) {
        /* 100 divides by 4, so the value roll doubles as an unbiased pick of
           which gate -- it has nothing else to do on a gate spawn. */
        static const int gates[] = { GATE_XOR, GATE_OR, GATE_AND, GATE_NOT };
        value = gates[value_roll % 4];
    } else {
        value = mode_spawn_value(b->bits, board_highest_value(b), value_roll);
    }

    b->cells[empty[slot][0]][empty[slot][1]] = value;
    b->spawn_row = empty[slot][0];
    b->spawn_col = empty[slot][1];
    return 1;
}
