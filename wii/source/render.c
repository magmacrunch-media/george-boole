#include <stdio.h>
#include "magnolia.h"
#include "render.h"
#include "modes.h"

/* The board is a square block of four cells with a gap between them, centred
   horizontally and sitting below the HUD. Sized so a 4x4 grid of three-digit
   numbers is legible at CRT distance -- which is what caps the cell count, not
   the arithmetic. */
#define CELL      74
#define GAP        6
#define BOARD_X  168
#define BOARD_Y  128
#define RADIUS     6

/* Gold tile colour -- a distinct warm gold that reads as special on a CRT. */
#define GOLD_COLOR PAL_RGB(0xffd700)

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

/* HSV hue (0..360) to packed RGB. Saturation and value are fixed at 1.0 for
   maximum brightness on a CRT. */
static u32 hue_to_rgb(float hue) {
    float h = hue / 60.0f;
    int sector = (int)h;
    float f = h - sector;
    unsigned int r, g, b;

    switch (sector % 6) {
        case 0: r = 255; g = (unsigned int)(255 * f); b = 0; break;
        case 1: r = (unsigned int)(255 * (1 - f)); g = 255; b = 0; break;
        case 2: r = 0; g = 255; b = (unsigned int)(255 * f); break;
        case 3: r = 0; g = (unsigned int)(255 * (1 - f)); b = 255; break;
        case 4: r = (unsigned int)(255 * f); g = 0; b = 255; break;
        default: r = 255; g = 0; b = (unsigned int)(255 * (1 - f)); break;
    }
    return PAL_RGB((r << 16) | (g << 8) | b);
}

/* One tile, at an arbitrary position and size, so the same code draws a tile
   sitting still, sliding, and popping. When binary_on is set and the tile is a
   number, the decimal is drawn slightly above centre and the zero-padded binary
   underneath it in a smaller font. is_rainbow cycles the hue; is_gold uses a
   fixed warm gold. */
static void draw_tile(int x, int y, int size, int value,
                      const Palette *p, int max_value,
                      int binary_on, int bits,
                      int is_rainbow, int is_gold) {
    u32 fill;
    if (is_rainbow) {
        static float hue_acc = 0.0f;
        hue_acc += clock_dt() * 180.0f;  /* 180 degrees per second */
        if (hue_acc >= 360.0f) hue_acc -= 360.0f;
        fill = hue_to_rgb(hue_acc);
    } else if (is_gold) {
        fill = GOLD_COLOR;
    } else {
        fill = palette_tile_color(p, value, max_value);
    }
    ui_draw_panel(x, y, size, size, fill, p->border, RADIUS);

    if (value == TILE_EMPTY) return;

    if (board_is_gate(value)) {
        ui_draw_text_centered_in(x, y, size, size,
                                 render_gate_label(value), 16, p->gate_text);
    } else if (binary_on) {
        /* Decimal shifted up, binary below. The offsets are tuned for a 74px
           cell: decimal at 16-24px depending on digit count, binary at 8px. */
        char dec[8], bin[12];
        snprintf(dec, sizeof(dec), "%d", value);
        snprintf(bin, sizeof(bin), "%0*d", bits, value);
        ui_draw_text_centered_in(x, y - 4, size, size, dec, digit_size(value),
                                 p->tile_text);
        ui_draw_text_centered_in(x, y + size / 2 + 2, size, size / 2,
                                 bin, 8, p->gate_bg);
    } else {
        char buf[8];
        snprintf(buf, sizeof(buf), "%d", value);
        ui_draw_text_centered_in(x, y, size, size, buf, digit_size(value),
                                 p->tile_text);
    }
}

static void draw_frame(const Board *b, const Palette *p, int with_cells,
                       int binary_on) {
    int span = BOARD_SIZE * CELL + (BOARD_SIZE - 1) * GAP;
    ui_draw_panel(BOARD_X - GAP, BOARD_Y - GAP,
                  span + GAP * 2, span + GAP * 2,
                  p->board_bg, p->border, RADIUS);

    for (int r = 0; r < BOARD_SIZE; r++) {
        for (int c = 0; c < BOARD_SIZE; c++) {
            int value = with_cells ? board_get(b, r, c) : TILE_EMPTY;
            int is_rainbow = (r == b->rainbow_row && c == b->rainbow_col);
            int is_gold = (value == b->highest_earned && b->highest_earned > 0
                           && mode_height_bonus(b->bits, b->highest_earned) > 0);
            draw_tile(cell_x(c), cell_y(r), CELL, value, p, b->max_value,
                      binary_on, b->bits, is_rainbow, is_gold);
        }
    }
}

/* Split of the animation between sliding and the pop that follows it. */
#define SLIDE_FRACTION 0.66f

void render_board_animated(const Board *b, const Palette *p, float t,
                           int binary_on) {
    if (t < 0.0f) t = 0.0f;
    if (t >= 1.0f) {
        render_board(b, p, binary_on);
        return;
    }

    float slide = t / SLIDE_FRACTION;
    if (slide > 1.0f) slide = 1.0f;

    if (slide < 1.0f) {
        /* Empty grid underneath: every surviving tile is in the move list, so
           drawing the board as well would show each tile twice -- once at its
           destination and once in flight. */
        draw_frame(b, p, 0, binary_on);

        float e = ease_out_quad(slide);
        for (int i = 0; i < b->move_count; i++) {
            const TileMove *m = &b->moves[i];
            int fx = cell_x(m->from_col), fy = cell_y(m->from_row);
            int tx = cell_x(m->to_col),   ty = cell_y(m->to_row);
            int x = fx + (int)((float)(tx - fx) * e);
            int y = fy + (int)((float)(ty - fy) * e);
            /* Rainbow follows the tile to its destination. Gold follows the
               value -- a tile carrying highest_earned stays gold while sliding. */
            int is_rainbow = (m->to_row == b->rainbow_row &&
                              m->to_col == b->rainbow_col);
            int is_gold = (m->from_value == b->highest_earned &&
                           b->highest_earned > 0 &&
                           mode_height_bonus(b->bits, b->highest_earned) > 0);
            draw_tile(x, y, CELL, m->from_value, p, b->max_value,
                      binary_on, b->bits, is_rainbow, is_gold);
        }
        return;
    }

    /* Arrived: the board is the truth again, and whatever just merged or spawned
       swells briefly so the eye is drawn to what changed. */
    float pop = (t - SLIDE_FRACTION) / (1.0f - SLIDE_FRACTION);
    if (pop < 0.0f) pop = 0.0f;
    if (pop > 1.0f) pop = 1.0f;
    float swell = (1.0f - ease_out_quad(pop)) * 0.16f;

    draw_frame(b, p, 0, binary_on);

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
            int is_rainbow = (r == b->rainbow_row && c == b->rainbow_col);
            int is_gold = (value == b->highest_earned && b->highest_earned > 0
                           && mode_height_bonus(b->bits, b->highest_earned) > 0);
            draw_tile(cell_x(c) - off, cell_y(r) - off, size, value,
                      p, b->max_value, binary_on, b->bits, is_rainbow, is_gold);
        }
    }
}

void render_board(const Board *b, const Palette *p, int binary_on) {
    draw_frame(b, p, 1, binary_on);
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
