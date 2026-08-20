#include <stdio.h>
#include "screens.h"
#include "modes.h"

/* Body text is deliberately small and deliberately wrapped rather than
   hand-broken: the safe area is a different width on PAL, and lines split by
   hand only look right on the set they were split for. */
#define BODY_SIZE 11
#define BODY_X     58
#define BODY_W    524

static const char *title_labels[TITLE_ITEM_COUNT] = {
    "PLAY",
    "HOW TO PLAY",
    "SETTINGS",
    "CREDITS"
};

const char *screens_title_label(int item) {
    if (item < 0 || item >= TITLE_ITEM_COUNT) return "";
    return title_labels[item];
}

void screens_draw_title(const Palette *p, const MenuGrid *menu) {
    renderer_draw_background();
    ui_draw_border();

    ui_draw_centered_text(58, "GEORGE BOOLE", 30, p->tile_text);
    ui_draw_centered_text(100, "HAS ENTERED THE CHAT", 14, p->gate_bg);

    for (int i = 0; i < TITLE_ITEM_COUNT; i++) {
        int y = 176 + i * 54;
        int selected = (i == menu->cursor);
        ui_draw_panel(200, y, 240, 42,
                      selected ? p->ramp[3] : p->cell_bg,
                      selected ? p->tile_text : p->border, 6);
        ui_draw_text_centered_in(200, y, 240, 42, title_labels[i], 14,
                                 selected ? p->tile_text : p->gate_bg);
    }

    ui_draw_centered_text(420, "D-PAD: choose   A: select   HOME: quit", 10, p->gate_bg);
    renderer_finish();
}

void screens_draw_howto(const Palette *p, int page) {
    renderer_draw_background();
    ui_draw_border();

    char head[40];
    snprintf(head, sizeof(head), "HOW TO PLAY  %d/%d", page + 1, HOWTO_PAGES);
    ui_draw_centered_text(30, head, 16, p->tile_text);

    int y = 78;
    switch (page) {
        case 0:
            ui_draw_text_shadow(BODY_X, y, "THE TWIST", 14, p->tile_text);
            y += 32;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "Tiles do not double. Two of the same value consolidate into one "
                "of the same value: 1 and 1 make 1. That is idempotence, and it "
                "is why the board fills up rather than climbing on its own.",
                BODY_SIZE, p->gate_bg, 20);
            y += 16;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "To make anything larger you need a gate.",
                BODY_SIZE, p->tile_text, 20);
            break;

        case 1:
            ui_draw_text_shadow(BODY_X, y, "GATES", 14, p->tile_text);
            y += 32;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "XOR, OR and AND are binary: slide a gate so it sits between two "
                "numbers and it applies to both. NOT is unary -- slide it into a "
                "single number from either side. Two NOTs cancel each other.",
                BODY_SIZE, p->gate_bg, 20);
            y += 16;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "Gates take up space like tiles do. A gate stranded in a corner "
                "has nothing to work on.",
                BODY_SIZE, p->gate_bg, 20);
            break;

        default:
            ui_draw_text_shadow(BODY_X, y, "OVERFLOW", 14, p->tile_text);
            y += 32;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "Each mode has a ceiling of 2^n - 1. NOT the ceiling gives zero, "
                "which no tile can hold: the tile clears and you are paid three "
                "times the ceiling. That is the only way past it.",
                BODY_SIZE, p->gate_bg, 20);
            y += 16;
            y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
                "In GAUNTLET, reaching the ceiling promotes you to the next width "
                "instead, all the way to 8-bit.",
                BODY_SIZE, p->tile_text, 20);
            break;
    }

    ui_draw_centered_text(430, "LEFT/RIGHT: page   B: back", 10, p->gate_bg);
    renderer_finish();
}

void screens_draw_settings(const Palette *p, int cursor, int music_on, int sfx_on) {
    renderer_draw_background();
    ui_draw_border();
    ui_draw_centered_text(40, "SETTINGS", 20, p->tile_text);

    const char *labels[SETTING_COUNT] = { "MUSIC", "SOUND EFFECTS" };
    int values[SETTING_COUNT];
    values[SETTING_MUSIC] = music_on;
    values[SETTING_SFX]   = sfx_on;

    for (int i = 0; i < SETTING_COUNT; i++) {
        int y = 140 + i * 70;
        int selected = (i == cursor);

        ui_draw_panel(110, y, 420, 50,
                      selected ? p->ramp[2] : p->cell_bg,
                      selected ? p->tile_text : p->border, 6);
        ui_draw_text_centered_in(130, y, 220, 50, labels[i], 12,
                                 selected ? p->tile_text : p->gate_bg);
        ui_draw_text_centered_in(370, y, 140, 50, values[i] ? "ON" : "OFF", 14,
                                 values[i] ? p->tile_text : p->gate_bg);
    }

    ui_draw_centered_text(330, "A: toggle   B: back", 10, p->gate_bg);
    ui_draw_centered_text(360, "Settings are saved to the SD card.", 10, p->gate_bg);
    renderer_finish();
}

void screens_draw_credits(const Palette *p) {
    renderer_draw_background();
    ui_draw_border();
    ui_draw_centered_text(34, "CREDITS", 18, p->tile_text);

    int y = 84;
    y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
        "\"No general method for the solution of questions in the theory of "
        "probabilities can be established.\"",
        BODY_SIZE, p->gate_bg, 20);
    y += 6;
    ui_draw_text_shadow(BODY_X, y, "-- George Boole, The Laws of Thought, 1854",
                        10, p->tile_text);

    y += 46;
    y = ui_draw_text_wrapped(BODY_X, y, BODY_W,
        "A MagmaCrunch game. Ported from the browser version in the MagmaCrunch "
        "arcade, and built on magnolia, a Wii homebrew engine.",
        BODY_SIZE, p->gate_bg, 20);

    y += 16;
    ui_draw_text_wrapped(BODY_X, y, BODY_W,
        "Type is Press Start 2P by CodeMan38, under the SIL Open Font License.",
        BODY_SIZE, p->gate_bg, 20);

    ui_draw_centered_text(430, "B: back", 10, p->gate_bg);
    renderer_finish();
}
