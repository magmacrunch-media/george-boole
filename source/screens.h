#ifndef SCREENS_H
#define SCREENS_H

#include "magnolia.h"
#include "palette.h"

/* Everything that is not the board: the title menu and the three screens behind
   it. Kept out of main.c so the game loop stays readable -- these are long on
   text and short on logic, which is the opposite of everything around them. */

typedef enum {
    TITLE_PLAY,
    TITLE_HOWTO,
    TITLE_SETTINGS,
    TITLE_CREDITS,
    TITLE_ITEM_COUNT
} TitleItem;

typedef enum {
    SETTING_MUSIC,
    SETTING_SFX,
    SETTING_BINARY,
    SETTING_COUNT
} SettingItem;

#define HOWTO_PAGES 3

void screens_draw_title(const Palette *p, const MenuGrid *menu);
void screens_draw_howto(const Palette *p, int page);
void screens_draw_settings(const Palette *p, int cursor, int music_on, int sfx_on,
                           int binary_on);
void screens_draw_credits(const Palette *p);

const char *screens_title_label(int item);

#endif
