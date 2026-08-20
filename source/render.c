#include <stdio.h>
#include "magnolia.h"
#include "render.h"

/* The board is a square block of four cells with a gap between them, centred
   horizontally and sitting below the HUD. Sized so a 4x4 grid of three-digit
   numbers is legible at CRT distance -- which is what caps the cell count, not
   the arithmetic. */
#define CELL      74
#define GAP        6
#define BOARD_X  168
#define BOARD_Y  128
#define RADIUS     6

const char *render_gate_label(int value) {
    switch (value) {
        case GATE_XOR: return "XOR";
        case GATE_OR:  return "OR";
        case GATE_AND: return "AND";
        case GATE_NOT: return "NOT";
        default:       return "";
    }
}

static int cell_x(int col) { return BOARD_X + col * (CELL + GAP); }
static int cell_y(int row) { return BOARD_Y + row * (CELL + GAP); }

/* Numerals shrink as they get longer so that 255 fits the same cell 7 does,
   instead of overflowing it. */
static unsigned int digit_size(int value) {
    if (value >= 100) return 16;
    if (value >= 10)  return 20;
    return 24;
}

void render_board(const Board *b, const Palette *p) {
    int span = BOARD_SIZE * CELL + (BOARD_SIZE - 1) * GAP;
    ui_draw_panel(BOARD_X - GAP, BOARD_Y - GAP,
                  span + GAP * 2, span + GAP * 2,
                  p->board_bg, p->border, RADIUS);

    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            int value = board_get(b, r, c);
            int x = cell_x(c), y = cell_y(r);

            u32 fill = palette_tile_color(p, value, b->max_value);
            ui_draw_panel(x, y, CELL, CELL, fill, p->border, RADIUS);

            if (value == TILE_EMPTY) continue;

            if (board_is_gate(value)) {
                ui_draw_text_centered_in(x, y, CELL, CELL,
                                         render_gate_label(value), 16, p->gate_text);
            } else {
                char buf[8];
                snprintf(buf, sizeof(buf), "%d", value);
                ui_draw_text_centered_in(x, y, CELL, CELL,
                                         buf, digit_size(value), p->tile_text);
            }
        }
    }
}

void render_hud(const Board *b, const Palette *p, ModeId mode) {
    char buf[48];

    snprintf(buf, sizeof(buf), "%d", b->score);
    ui_draw_centered_text(34, buf, 28, p->tile_text);

    /* Gauntlet climbs widths mid-run, so the ceiling is worth showing: it is
       the number the player is actually aiming at. */
    if (mode_is_gauntlet(mode)) {
        snprintf(buf, sizeof(buf), "GAUNTLET  %d-BIT  REACH %d",
                 b->bits, b->max_value);
    } else {
        snprintf(buf, sizeof(buf), "%s  MAX %d", mode_name(mode), b->max_value);
    }
    ui_draw_centered_text(84, buf, 12, p->gate_bg);

    if (b->last_overflow_bonus > 0) {
        snprintf(buf, sizeof(buf), "OVERFLOW  +%d", b->last_overflow_bonus);
        ui_draw_centered_text(438, buf, 14, p->gate_bg);
    } else if (b->last_height_bonus > 0) {
        snprintf(buf, sizeof(buf), "NEW HIGH  +%d", b->last_height_bonus);
        ui_draw_centered_text(438, buf, 14, p->tile_text);
    }
}
