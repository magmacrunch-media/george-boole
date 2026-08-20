#include <gccore.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "magnolia.h"
#include "config.h"
#include "board.h"
#include "modes.h"
#include "palette.h"
#include "render.h"

/* One leaderboard per mode. Registered up front so every table is loaded off the
   card once, rather than on each mode change. */
static int score_table[MODE_COUNT];

static Board board;
static ModeId mode = MODE_2BIT;
static MenuGrid mode_menu;

static void start_run(void) {
    board_init(&board, mode_start_bits(mode), mode_is_gauntlet(mode));
    scoring_reset();
    scoring_select_table(score_table[mode]);

    /* Two tiles to open with, or the first move has nothing to act on. */
    board_spawn(&board, rand() % 10000);
    board_spawn(&board, rand() % 10000);

    printf("run: mode=%s bits=%d max=%d\n",
           mode_name(mode), board.bits, board.max_value);
}

static void draw_title(const Palette *p) {
    renderer_draw_background();
    ui_draw_border();
    ui_draw_centered_text(120, "GEORGE BOOLE", 30, p->tile_text);
    ui_draw_centered_text(164, "HAS ENTERED THE CHAT", 16, p->gate_bg);
    ui_draw_centered_text(300, "A: choose a mode", 13, p->tile_text);
    ui_draw_centered_text(330, "HOME: quit", 12, p->gate_bg);
    renderer_finish();
}

static void draw_mode_select(void) {
    const Palette *p = palette_for((ModeId)mode_menu.cursor);
    renderer_draw_background();
    ui_draw_border();
    ui_draw_centered_text(28, "SELECT MODE", 20, p->tile_text);

    /* Four across, two down: every mode visible at once, so the grid never has
       to scroll and the palettes can be compared side by side. */
    const int cw = 140, ch = 104, gx = 30, gy = 84;
    for (int slot = 0; slot < MODE_COUNT; slot++) {
        int i = menu_grid_item_at_slot(&mode_menu, slot);
        if (i < 0) continue;

        int col = slot % mode_menu.cols;
        int row = slot / mode_menu.cols;
        int x = gx + col * (cw + 12);
        int y = gy + row * (ch + 16);

        const Palette *ip = palette_for((ModeId)i);
        int selected = (i == mode_menu.cursor);

        ui_draw_panel(x, y, cw, ch, ip->cell_bg,
                      selected ? ip->tile_text : ip->border, 8);
        ui_draw_text_centered_in(x, y + 8, cw, 30, mode_name((ModeId)i), 14, ip->tile_text);

        char sub[24];
        if (mode_is_gauntlet((ModeId)i)) {
            snprintf(sub, sizeof(sub), "2 - 8 BIT");
        } else {
            snprintf(sub, sizeof(sub), "MAX %d",
                     mode_max_value(mode_start_bits((ModeId)i)));
        }
        ui_draw_text_centered_in(x, y + 44, cw, 24, sub, 11, ip->gate_bg);

        /* The best score for that mode, so the grid doubles as a scoreboard. */
        scoring_select_table(score_table[i]);
        const ScoreEntry *best = scoring_get_entry(0);
        if (best) {
            snprintf(sub, sizeof(sub), "%s %d", best->initials, best->score);
            ui_draw_text_centered_in(x, y + 70, cw, 22, sub, 10, ip->tile_text);
        }
    }

    ui_draw_centered_text(320, "D-PAD: choose   A: play   B: back", 11, p->gate_bg);
    renderer_finish();
}

static void draw_game_over(const Palette *p, const GameStateMachine *gs) {
    render_board(&board, p);
    ui_draw_dim_overlay(RGBA(0, 0, 0, 190));
    ui_draw_centered_text(150, "GAME OVER", 28, p->tile_text);

    char buf[48];
    snprintf(buf, sizeof(buf), "SCORE %d", scoring_get());
    ui_draw_centered_text(200, buf, 18, p->gate_bg);

    if (gs->is_high_score) {
        snprintf(buf, sizeof(buf), "HIGH SCORE  RANK %d", gs->rank);
        ui_draw_centered_text(240, buf, 14, p->tile_text);
    }
    ui_draw_centered_text(320, "A: continue", 12, p->gate_bg);
    renderer_finish();
}

static void draw_initials(const Palette *p, const GameStateMachine *gs) {
    renderer_draw_background();
    ui_draw_border();
    ui_draw_centered_text(110, "NEW HIGH SCORE", 22, p->tile_text);

    char buf[32];
    snprintf(buf, sizeof(buf), "%d", scoring_get());
    ui_draw_centered_text(158, buf, 26, p->gate_bg);

    for (int i = 0; i < 3; i++) {
        char ch[2] = { gs->initials[i], '\0' };
        int x = 250 + i * 50;
        int active = (i == gs->cursor_pos);
        ui_draw_panel(x, 220, 40, 52,
                      active ? p->ramp[3] : p->cell_bg, p->border, 4);
        ui_draw_text_centered_in(x, 220, 40, 52, ch, 24, p->tile_text);
    }

    ui_draw_centered_text(310, "LEFT/RIGHT: letter", 11, p->gate_bg);
    ui_draw_centered_text(332, "DOWN: next   A: done", 11, p->gate_bg);
    renderer_finish();
}

static void draw_high_scores(const Palette *p) {
    renderer_draw_background();
    ui_draw_border();

    char buf[48];
    snprintf(buf, sizeof(buf), "%s  HIGH SCORES", mode_name(mode));
    ui_draw_centered_text(50, buf, 18, p->tile_text);

    int count = scoring_get_count();
    if (count == 0) {
        ui_draw_centered_text(200, "NOTHING YET", 14, p->gate_bg);
    }
    for (int i = 0; i < count && i < 10; i++) {
        const ScoreEntry *e = scoring_get_entry(i);
        if (!e) continue;
        snprintf(buf, sizeof(buf), "%2d  %s  %d", i + 1, e->initials, e->score);
        ui_draw_centered_text(100 + i * 28, buf, 13,
                              i == 0 ? p->tile_text : p->gate_bg);
    }

    ui_draw_centered_text(420, "A: back", 11, p->gate_bg);
    renderer_finish();
}

static void update_playing(GameStateMachine *gs, const Palette *p) {
    int moved = 0;

#if DEBUG_AUTOPLAY_FRAMES
    static int autoframe = 0;
    if (++autoframe % DEBUG_AUTOPLAY_FRAMES == 0) {
        /* Tries each direction in turn rather than picking one at random: a
           random walk can sit for a long time repeating a move that does
           nothing, and the point is to keep the board changing. */
        static int next_dir = 0;
        for (int attempt = 0; attempt < 4 && !moved; attempt++) {
            moved = board_move(&board, (BoardDir)(next_dir % 4));
            next_dir++;
        }
    }
#endif

    if (input_left_pressed())  moved = board_move(&board, DIR_LEFT);
    else if (input_right_pressed()) moved = board_move(&board, DIR_RIGHT);
    else if (input_up_pressed())    moved = board_move(&board, DIR_UP);
    else if (input_down_pressed())  moved = board_move(&board, DIR_DOWN);

    if (moved) {
        scoring_add(board.last_gained);
        board_spawn(&board, rand() % 10000);

        if (board.last_upgraded) {
            printf("gauntlet: promoted to %d-bit (max %d)\n",
                   board.bits, board.max_value);
        }
    }

    render_board(&board, p);
    render_hud(&board, p, mode);
    renderer_finish();

    if (board_game_over(&board)) {
        printf("run over: mode=%s score=%d bits=%d\n",
               mode_name(mode), scoring_get(), board.bits);
        gamestate_end_run(gs, scoring_get());
    }
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    srand(time(NULL));

    SYS_STDIO_Report(true);
    setvbuf(stdout, NULL, _IONBF, 0);
    printf("=== george boole starting ===\n");

    const MagnoliaConfig cfg = {
        .app_name     = APP_NAME,
        .max_scores   = HIGH_SCORE_COUNT,
        .overscan_pct = OVERSCAN_PCT
    };
    if (magnolia_init(&cfg) == -2) return 1;

    input_init();
    audio_init();

    for (int i = 0; i < MODE_COUNT; i++) {
        score_table[i] = scoring_add_table(mode_id((ModeId)i));
        if (score_table[i] < 0) score_table[i] = 0;
    }

    /* Reopen on whatever mode was played last -- it is nearly always the one
       the player wants again. */
    mode = (ModeId)prefs_get_int("mode", MODE_2BIT);
    if (mode < 0 || mode >= MODE_COUNT) mode = MODE_2BIT;

    menu_grid_init(&mode_menu, MODE_COUNT, 4, 2);
    menu_grid_set_cursor(&mode_menu, mode);

    GameStateMachine gs;
    gamestate_init(&gs);
    gamestate_set_menu_enabled(&gs, 1);

#if AUTOSTART_GAMEPLAY
    printf("autostart: skipping menus, entering gameplay directly\n");
    start_run();
    gamestate_set(&gs, GS_PLAYING);
#endif

    while (1) {
        input_scan();
        if (input_home_pressed()) break;

        const Palette *p = palette_for(mode);

        if (gamestate_current(&gs) == GS_PLAYING) {
            update_playing(&gs, p);
            continue;
        }

        switch (gamestate_current(&gs)) {
            case GS_TITLE:       draw_title(p); break;
            case GS_MENU:        draw_mode_select(); break;
            case GS_GAME_OVER:
                draw_game_over(p, &gs);
#if DEBUG_AUTOPLAY_FRAMES
                /* A soak run must not stop at the first game over: the failures
                   worth finding are the ones that need a few hundred merges and
                   several runs to show up. */
                gamestate_set(&gs, GS_PLAYING);
                start_run();
#endif
                break;
            case GS_INITIALS:    draw_initials(p, &gs); break;
            case GS_HIGH_SCORES: draw_high_scores(p); break;
            default:
                renderer_draw_background();
                ui_draw_border();
                renderer_finish();
                break;
        }

        if (gamestate_current(&gs) == GS_MENU) {
            int moved = 0;
            if (input_dir_repeat(INPUT_DIR_LEFT))  moved |= menu_grid_move(&mode_menu, -1, 0);
            if (input_dir_repeat(INPUT_DIR_RIGHT)) moved |= menu_grid_move(&mode_menu, +1, 0);
            if (input_dir_repeat(INPUT_DIR_UP))    moved |= menu_grid_move(&mode_menu, 0, -1);
            if (input_dir_repeat(INPUT_DIR_DOWN))  moved |= menu_grid_move(&mode_menu, 0, +1);
            (void)moved;

            if (input_a_pressed()) {
                mode = (ModeId)mode_menu.cursor;
                prefs_set_int("mode", mode);
                gamestate_menu_confirm(&gs);
            } else {
                gamestate_update(&gs, scoring_get());
            }
            continue;
        }

        /* GS_READY has nothing to show in this game: the mode grid is the only
           choice, so a run starts the moment it is confirmed. */
        if (gamestate_current(&gs) == GS_READY) {
            gamestate_set(&gs, GS_PLAYING);
            start_run();
            continue;
        }

        if (gamestate_update(&gs, scoring_get())) {
            start_run();
        }
    }

    audio_shutdown();
    magnolia_shutdown();
    return 0;
}
