#include <string.h>
#include "board.h"
#include "modes.h"

int board_is_gate(int value) {
    return value == GATE_XOR || value == GATE_OR ||
           value == GATE_AND || value == GATE_NOT;
}

void board_init(Board *b, int bits, int gauntlet) {
    memset(b, 0, sizeof(*b));
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
static int advance_line(Board *b, int *line, int score_it) {
    int packed[BOARD_SIZE];
    int n = 0;
    for (int i = 0; i < BOARD_SIZE; i++) {
        if (line[i] != TILE_EMPTY) packed[n++] = line[i];
    }

    int out[BOARD_SIZE];
    int outn = 0;
    int merged = 0;
    int i = 0;

    while (i < n) {
        int current = packed[i];

        /* NOT + NOT: two inversions are no inversion, and both are consumed. */
        if (current == GATE_NOT && i + 1 < n && packed[i + 1] == GATE_NOT) {
            i += 2;
            merged = 1;
            continue;
        }

        /* NOT applied to the number on either side. */
        if (current == GATE_NOT && i + 1 < n && !board_is_gate(packed[i + 1])) {
            int r = score_it ? resolve_gate(b, GATE_NOT, packed[i + 1], 0)
                             : board_apply_gate(b, GATE_NOT, packed[i + 1], 0);
            if (r != 0) { out[outn++] = r; if (score_it) award_height(b, r); }
            i += 2;
            merged = 1;
            continue;
        }
        if (!board_is_gate(current) && i + 1 < n && packed[i + 1] == GATE_NOT) {
            int r = score_it ? resolve_gate(b, GATE_NOT, current, 0)
                             : board_apply_gate(b, GATE_NOT, current, 0);
            if (r != 0) { out[outn++] = r; if (score_it) award_height(b, r); }
            i += 2;
            merged = 1;
            continue;
        }

        /* number gate number. NOT is excluded: it is unary and was handled. */
        if (!board_is_gate(current) && i + 2 < n &&
            board_is_gate(packed[i + 1]) && packed[i + 1] != GATE_NOT &&
            !board_is_gate(packed[i + 2])) {
            int r = score_it ? resolve_gate(b, packed[i + 1], current, packed[i + 2])
                             : board_apply_gate(b, packed[i + 1], current, packed[i + 2]);
            out[outn++] = r;
            if (score_it) {
                b->score += r;
                b->last_gained += r;
                award_height(b, r);
            }
            i += 3;
            merged = 1;
            continue;
        }

        /* Idempotence: equal numbers consolidate to one of themselves. */
        if (i + 1 < n && current == packed[i + 1] && !board_is_gate(current)) {
            out[outn++] = current;
            if (score_it) {
                b->score += current;
                b->last_gained += current;
                award_height(b, current);
            }
            i += 2;
            merged = 1;
            continue;
        }

        out[outn++] = current;
        i++;
    }

    while (outn < BOARD_SIZE) out[outn++] = TILE_EMPTY;

    int changed = 0;
    for (int k = 0; k < BOARD_SIZE; k++) {
        if (line[k] != out[k]) changed = 1;
        line[k] = out[k];
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

    int changed = 0;
    for (int index = 0; index < BOARD_SIZE; index++) {
        int line[BOARD_SIZE];
        read_line(b, dir, index, line);

        int before[BOARD_SIZE];
        memcpy(before, line, sizeof(before));

        advance_line(b, line, 1);

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
            advance_line(&copy, line, 0);
            if (memcmp(before, line, sizeof(before)) != 0) any = 1;
        }
        if (any) return 0;
    }
    return 1;
}

int board_spawn(Board *b, int roll) {
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

    if (roll < 0) roll = 0;
    int slot = (roll / 7) % n;
    int kind = roll % 100;

    int value;
    if (kind < 18) {
        /* A gate is useless without numbers to sit between, so they stay a
           minority of spawns however wide the mode gets. */
        static const int gates[] = { GATE_XOR, GATE_OR, GATE_AND, GATE_NOT };
        value = gates[(roll / 3) % 4];
    } else if (kind < 70) {
        value = 1;
    } else if (kind < 90) {
        value = 2;
    } else {
        value = (b->max_value >= 3) ? 3 : b->max_value;
    }

    b->cells[empty[slot][0]][empty[slot][1]] = value;
    return 1;
}
