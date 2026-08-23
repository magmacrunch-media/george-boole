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
#include "screens.h"
#include "assets.h"

/* SFX slots, in load order. Six of magnolia's eight, which leaves room without
   inviting a seventh sound nobody asked for. */
#define SFX_MOVE      0
#define SFX_SPAWN     1
#define SFX_MERGE     2
#define SFX_GAMEOVER  3
#define SFX_VICTORY   4
#define SFX_HIGHSCORE 5

/* The music is 24kHz mono. The source is nearly four minutes and would decode to
   about 43MB at 48kHz stereo, against a console with 24MB -- see
   tools/convert-audio.sh, which is where that decision lives. */
#define MUSIC_RATE 24000

#define PREF_MUSIC   "music"
#define PREF_SFX     "sfx"
#define PREF_BINARY  "binary"

static int music_on  = 1;
static int sfx_on    = 1;
static int binary_on = 0;

/* SD card status, checked once after init. Drives the settings screen message
   and can be queried by the startup report. */
static int sd_mounted = 0;

static void sfx(int slot) {
    if (sfx_on) audio_play_sfx(slot);
}

static void apply_music(void) {
    /* Muting is engine-wide, so the sfx toggle is honoured in sfx() rather than
       here -- otherwise turning the music off would silence the effects too. */
    audio_set_muted(!music_on);
}

/* One leaderboard per mode. Registered up front so every table is loaded off the
   card once, rather than on each mode change. */
static int score_table[MODE_COUNT];

static Board board;
static ModeId mode = MODE_2BIT;
static MenuGrid mode_menu;

/* The title is a list rather than a single "press A": this game has rules that
   need explaining before the first move makes sense, and a how-to nobody can
   find is the same as not having one. A one-column MenuGrid is that list. */
static MenuGrid title_menu;

/* Screens reached from the title. They are overlays on GS_TITLE rather than
   engine states: the shell owns the run, and none of these is part of one. */
typedef enum {
    OVERLAY_NONE,
    OVERLAY_HOWTO,
    OVERLAY_SETTINGS,
    OVERLAY_CREDITS
} Overlay;

static Overlay overlay = OVERLAY_NONE;

/* Progress of the current move's animation, 0..1. Starts at 1 so a fresh board
   is simply drawn rather than animating in from nowhere. */
static float anim_t = 1.0f;
static int howto_page = 0;
static int settings_cursor = 0;
static int total_moves = 0;

static void start_run(void) {
    board_init(&board, mode_start_bits(mode), mode_is_gauntlet(mode));
    scoring_reset();
    scoring_select_table(score_table[mode]);
    total_moves = 0;

    /* Two tiles to open with, or the first move has nothing to act on. */
    board_spawn(&board, (unsigned int)rand());
    board_spawn(&board, (unsigned int)rand());
    anim_t = 1.0f;

    printf("run: mode=%s bits=%d max=%d\n",
           mode_name(mode), board.bits, board.max_value);
}

/* Returns 1 when the player chose PLAY and the shell should take over. */
static int update_title(const Palette *p) {
    if (overlay != OVERLAY_NONE) {
        switch (overlay) {
            case OVERLAY_HOWTO:    screens_draw_howto(p, howto_page); break;
            case OVERLAY_SETTINGS: screens_draw_settings(p, settings_cursor,
                                                         music_on, sfx_on,
                                                         binary_on,
                                                         sd_mounted); break;
            case OVERLAY_CREDITS:  screens_draw_credits(p); break;
            default: break;
        }

        if (input_back_pressed()) {
            overlay = OVERLAY_NONE;
            sfx(SFX_MOVE);
            return 0;
        }

        if (overlay == OVERLAY_HOWTO) {
            if (input_dir_repeat(INPUT_DIR_RIGHT) && howto_page < HOWTO_PAGES - 1) {
                howto_page++;
                sfx(SFX_MOVE);
            }
            if (input_dir_repeat(INPUT_DIR_LEFT) && howto_page > 0) {
                howto_page--;
                sfx(SFX_MOVE);
            }
        } else if (overlay == OVERLAY_SETTINGS) {
            if (input_dir_repeat(INPUT_DIR_UP))   settings_cursor = SETTING_MUSIC;
            if (input_dir_repeat(INPUT_DIR_DOWN)) settings_cursor = SETTING_BINARY;

            if (input_a_pressed()) {
                if (settings_cursor == SETTING_MUSIC) {
                    music_on = !music_on;
                    prefs_set_int(PREF_MUSIC, music_on);
                    apply_music();
                } else if (settings_cursor == SETTING_SFX) {
                    sfx_on = !sfx_on;
                    prefs_set_int(PREF_SFX, sfx_on);
                } else {
                    binary_on = !binary_on;
                    prefs_set_int(PREF_BINARY, binary_on);
                }
                /* Played after the toggle, so turning effects on says so. */
                sfx(SFX_MERGE);
            }
        }
        return 0;
    }

    screens_draw_title(p, &title_menu);

    if (input_dir_repeat(INPUT_DIR_UP) && menu_grid_move(&title_menu, 0, -1))   sfx(SFX_MOVE);
    if (input_dir_repeat(INPUT_DIR_DOWN) && menu_grid_move(&title_menu, 0, +1)) sfx(SFX_MOVE);

    if (input_a_pressed()) {
        switch (title_menu.cursor) {
            case TITLE_PLAY:     sfx(SFX_MERGE); return 1;
            case TITLE_HOWTO:    overlay = OVERLAY_HOWTO; howto_page = 0; break;
            case TITLE_SETTINGS: overlay = OVERLAY_SETTINGS; settings_cursor = 0; break;
            case TITLE_CREDITS:  overlay = OVERLAY_CREDITS; break;
            default: break;
        }
        sfx(SFX_MOVE);
    }
    return 0;
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
    render_board(&board, p, binary_on);
    ui_draw_dim_overlay(RGBA(0, 0, 0, 190));
    ui_draw_centered_text(150, "GAME OVER", 28, p->tile_text);

    char buf[48];
    snprintf(buf, sizeof(buf), "%d points - Max Value: %d",
             scoring_get(), board.highest_earned);
    ui_draw_centered_text(200, buf, 18, p->gate_bg);

    if (gs->is_high_score) {
        snprintf(buf, sizeof(buf), "HIGH SCORE  RANK %d  MOVES %d",
                 gs->rank, total_moves);
        ui_draw_centered_text(240, buf, 14, p->tile_text);
    }
    ui_draw_centered_text(320, "A: continue", 12, p->gate_bg);
    renderer_finish();
}

static void draw_paused(const Palette *p) {
    render_board(&board, p, binary_on);
    ui_draw_dim_overlay(RGBA(0, 0, 0, 190));
    ui_draw_centered_text(100, "PAUSED", 28, p->tile_text);

    /* Compact gate reference -- the board has no side panel on a 4:3 TV, and
       this is exactly when a player wants to look something up. */
    int y = 170;
    ui_draw_centered_text(y, "GATES", 14, p->tile_text);
    y += 28;
    ui_draw_centered_text(y, "XOR, OR, AND: binary operators", 10, p->gate_bg);
    y += 20;
    ui_draw_centered_text(y, "Slide between two numbers", 10, p->gate_bg);
    y += 28;
    ui_draw_centered_text(y, "NOT: unary operator", 10, p->gate_bg);
    y += 20;
    ui_draw_centered_text(y, "Slide into a single number", 10, p->gate_bg);
    y += 20;
    ui_draw_centered_text(y, "Two NOTs cancel each other", 10, p->gate_bg);

    ui_draw_centered_text(400, "A: resume", 12, p->gate_bg);
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

    /* clock_dt() rather than a frame count: the animation should take the same
       time on NTSC and PAL, and look the same if a frame is ever dropped. */
    if (anim_t < 1.0f) {
        anim_t += clock_dt() / RENDER_ANIM_SECONDS;
        if (anim_t > 1.0f) anim_t = 1.0f;
    }

    /* Input is held off mid-slide. It lasts about a sixth of a second, and
       accepting a second move part-way through would discard the provenance the
       animation is drawing from and make tiles jump. */
    int accepting = (anim_t >= 1.0f);

#if DEBUG_AUTOPLAY_FRAMES
    static int autoframe = 0;
    if (accepting && ++autoframe % DEBUG_AUTOPLAY_FRAMES == 0) {
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

    if (accepting) {
        if (input_left_pressed())  moved = board_move(&board, DIR_LEFT);
        else if (input_right_pressed()) moved = board_move(&board, DIR_RIGHT);
        else if (input_up_pressed())    moved = board_move(&board, DIR_UP);
        else if (input_down_pressed())  moved = board_move(&board, DIR_DOWN);
    }

    if (moved) {
        anim_t = 0.0f;
        scoring_add(board.last_gained);
        total_moves++;

        /* In Gauntlet, when a merge reaches the ceiling and promotes the width,
           mark the tile that earned it as rainbow so the renderer can cycle its
           hue. The old ceiling is the value to look for: the tile still holds it
           at this point, before the spawn overwrites an empty cell. */
        if (board.last_upgraded) {
            int old_max = mode_max_value(board.bits - 1);
            for (int r = 0; r < BOARD_SIZE; r++) {
                for (int c = 0; c < BOARD_SIZE; c++) {
                    if (board.cells[r][c] == old_max) {
                        board.rainbow_row = r;
                        board.rainbow_col = c;
                        goto found_rainbow;
                    }
                }
            }
        }
        found_rainbow:

        board_spawn(&board, (unsigned int)rand());

        /* One sound per move, chosen by what the move was worth: a merge is
           more interesting than a slide, and an overflow more than either. */
        if (board.last_overflow_bonus > 0) sfx(SFX_VICTORY);
        else if (board.last_gained > 0)    sfx(SFX_MERGE);
        else                               sfx(SFX_MOVE);

        if (board.last_upgraded) {
            sfx(SFX_SPAWN);
            printf("gauntlet: promoted to %d-bit (max %d)\n",
                   board.bits, board.max_value);
        }
    }

    render_board_animated(&board, p, anim_t, binary_on);
    render_hud(&board, p, mode);
    renderer_finish();

    /* Only once the board has settled: testing mid-slide would end the run on a
       position the player has not been shown yet. */
    if (anim_t >= 1.0f && board_game_over(&board)) {
        printf("run over: mode=%s score=%d bits=%d\n",
               mode_name(mode), scoring_get(), board.bits);
        gs->moves = total_moves;
        gs->highest_earned = board.highest_earned;
        gamestate_end_run(gs, scoring_get());
        sfx(gs->is_high_score ? SFX_HIGHSCORE : SFX_GAMEOVER);
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
    sd_mounted = magnolia_sd_mounted();

    input_init();
    audio_init();

    audio_load_sfx_mem(SFX_MOVE,      move_pcm,      move_pcm_size);
    audio_load_sfx_mem(SFX_SPAWN,     spawn_pcm,     spawn_pcm_size);
    audio_load_sfx_mem(SFX_MERGE,     merge_pcm,     merge_pcm_size);
    audio_load_sfx_mem(SFX_GAMEOVER,  gameover_pcm,  gameover_pcm_size);
    audio_load_sfx_mem(SFX_VICTORY,   victory_pcm,   victory_pcm_size);
    audio_load_sfx_mem(SFX_HIGHSCORE, highscore_pcm, highscore_pcm_size);

    for (int i = 0; i < MODE_COUNT; i++) {
        score_table[i] = scoring_add_table(mode_id((ModeId)i));
        if (score_table[i] < 0) score_table[i] = 0;
    }

    /* Reopen on whatever mode was played last -- it is nearly always the one
       the player wants again. */
    mode = (ModeId)prefs_get_int("mode", MODE_2BIT);
    if (mode < 0 || mode >= MODE_COUNT) mode = MODE_2BIT;

    music_on  = prefs_get_int(PREF_MUSIC, 1) ? 1 : 0;
    sfx_on    = prefs_get_int(PREF_SFX, 1) ? 1 : 0;
    binary_on = prefs_get_int(PREF_BINARY, 0) ? 1 : 0;
    apply_music();
    audio_play_music_mem_fmt(music_pcm, music_pcm_size, AUDIO_MONO_16, MUSIC_RATE);

    menu_grid_init(&mode_menu, MODE_COUNT, 4, 2);
    menu_grid_set_cursor(&mode_menu, mode);

    /* One column: the same widget, used as a vertical list. */
    menu_grid_init(&title_menu, TITLE_ITEM_COUNT, 1, TITLE_ITEM_COUNT);

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
            /* PLUS pauses: the board freezes and a gate reference appears.
               HOME quits entirely (handled above). */
            if (input_plus_pressed()) {
                gamestate_pause(&gs);
            } else {
                update_playing(&gs, p);
            }
            continue;
        }

        if (gamestate_current(&gs) == GS_PAUSED) {
            draw_paused(p);
            if (input_a_pressed() || input_plus_pressed()) {
                gamestate_resume(&gs);
                sfx(SFX_MOVE);
            }
            continue;
        }

        if (gamestate_current(&gs) == GS_TITLE) {
            /* The title is the game's, so gamestate_update() is not called for
               it: the engine would take A as "start", and here A means whichever
               of four things is under the cursor. */
            if (update_title(p)) gamestate_set(&gs, GS_MENU);
            continue;
        }

        switch (gamestate_current(&gs)) {
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
