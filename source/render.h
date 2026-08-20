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
void render_hud(const Board *b, const Palette *p, ModeId mode);

#endif
