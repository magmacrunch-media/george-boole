#ifndef RENDER_H
#define RENDER_H

#include "board.h"
#include "modes.h"
#include "palette.h"

/* Board and tile drawing. Everything is authored in magnolia's 640x480 design
   space and mapped into the TV-safe area, so the layout does not care which
   video mode is running or how much of the picture the set eats. */

/* Short label for a gate: "XOR", "OR", "AND", "NOT". The mathematical symbols
   the web game uses are not in Press Start 2P, and a missing glyph on a CRT is
   indistinguishable from a bug. */
const char *render_gate_label(int value);

void render_board(const Board *b, const Palette *p);

/* The board mid-move. `t` runs 0..1 across one animation; at 1 this is exactly
   render_board() with the pop finished, so a caller can hand it t=1 forever and
   get the static board.

   Sliding matters more here than in most tile games: a gate sandwich pulls three
   tiles into one cell, and if they simply vanish and a result appears, the rule
   that produced it is invisible. Watching them arrive is the explanation. */
void render_board_animated(const Board *b, const Palette *p, float t);

/* Seconds one move's animation takes. */
#define RENDER_ANIM_SECONDS 0.16f
void render_hud(const Board *b, const Palette *p, ModeId mode);

#endif
