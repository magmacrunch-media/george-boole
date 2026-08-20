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

/* One tile, at an arbitrary position and size, so the same code draws a tile
   sitting still, sliding, and popping. */
static void draw_tile(int x, int y, int size, int value,
                      const Palette *p, int max_value) {
    u32 fill = palette_tile_color(p, value, max_value);
    ui_draw_panel(x, y, size, size, fill, p->border, RADIUS);

    if (value == TILE_EMPTY) return;

    if (board_is_gate(value)) {
        ui_draw_text_centered_in(x, y, size, size,
                                 render_gate_label(value), 16, p->gate_text);
    } else {
        char buf[8];
        snprintf(buf, sizeof(buf), "%d", value);
        ui_draw_text_centered_in(x, y, size, size, buf, digit_size(value),
                                 p->tile_text);
    }
}

static void draw_frame(const Board *b, const Palette *p, int with_cells) {
    int span = BOARD_SIZE * CELL + (BOARD_SIZE - 1) * GAP;
    ui_draw_panel(BOARD_X - GAP, BOARD_Y - GAP,
                  span + GAP * 2, span + GAP * 2,
                  p->board_bg, p->border, RADIUS);

    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            int value = with_cells ? board_get(b, r, c) : TILE_EMPTY;
            draw_tile(cell_x(c), cell_y(r), CELL, value, p, b->max_value);
        }
    }
}

/* Split of the animation between sliding and the pop that follows it. */
#define SLIDE_FRACTION 0.66f

void render_board_animated(const Board *b, const Palette *p, float t) {
    if (t < 0.0f) t = 0.0f;
    if (t >= 1.0f) {
        render_board(b, p);
        return;
    }

    float slide = t / SLIDE_FRACTION;
    if (slide > 1.0f) slide = 1.0f;

    if (slide < 1.0f) {
        /* Empty grid underneath: every surviving tile is in the move list, so
           drawing the board as well would show each tile twice -- once at its
           destination and once in flight. */
        draw_frame(b, p, 0);

        float e = ease_out_quad(slide);
        for (int i = 0; i < b->move_count; i++) {
            const TileMove *m = &b->moves[i];
            int fx = cell_x(m->from_col), fy = cell_y(m->from_row);
            int tx = cell_x(m->to_col),   ty = cell_y(m->to_row);
            int x = fx + (int)((float)(tx - fx) * e);
            int y = fy + (int)((float)(ty - fy) * e);
            draw_tile(x, y, CELL, m->from_value, p, b->max_value);
        }
        return;
    }

    /* Arrived: the board is the truth again, and whatever just merged or spawned
       swells briefly so the eye is drawn to what changed. */
    float pop = (t - SLIDE_FRACTION) / (1.0f - SLIDE_FRACTION);
    if (pop < 0.0f) pop = 0.0f;
    if (pop > 1.0f) pop = 1.0f;
    float swell = (1.0f - ease_out_quad(pop)) * 0.16f;

    draw_frame(b, p, 0);

    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            int value = board_get(b, r, c);
            if (value == TILE_EMPTY) continue;

            int popping = (r == b->spawn_row && c == b->spawn_col);
            for (int i = 0; i < b->move_count && !popping; i++) {
                if (b->moves[i].merged &&
                    b->moves[i].to_row == r && b->moves[i].to_col == c) popping = 1;
            }

            int size = CELL + (popping ? (int)((float)CELL * swell) : 0);
            int off  = (size - CELL) / 2;
            draw_tile(cell_x(c) - off, cell_y(r) - off, size, value,
                      p, b->max_value);
        }
    }
}

void render_board(const Board *b, const Palette *p) {
    draw_frame(b, p, 1);
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
