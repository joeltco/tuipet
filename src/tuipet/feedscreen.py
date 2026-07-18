"""Feed menu — the canon on-LCD icon picker (BASIC VPET 2026-07-16, cloned
from the v0.4.x rebuild).

The classic two-item feed: MEAT fills a hunger heart (+1 weight, refused at a
full belly); the PILL cures an active sickness/injury spell, restores a
strength heart, +7 energy, +5 weight.  Both are free and infinite — the
richer consumables (fruits, premium meat, junk food) live in the BAG as
shop items.  The whole DVPet food catalog left with the item system.

The source draws this as a MENU ON THE LCD (decompile `Rn()`): the meat glyph
`me` sits top-centre, the pill glyph `he` directly below it, and the cursor
arrow `O` sits at the left margin pointing at the selected row.  Glyphs are
the EXACT bitmaps ripped from the decompile (`me`/`he`/`O`), not hand-drawn.
"""
from __future__ import annotations
from . import grid, menu, render
from .theme import INK, INK_B, DIM, ACCENT, POS  # noqa: F401  (theme.apply propagation)

# --- authentic LCD glyphs (decompile: me / he / O) --------------------------
MEAT = ["00000011",
        "00011101",
        "00101110",
        "01011110",
        "01111110",
        "01011100",
        "10111000",
        "11000000"]

PILL = ["00001110",
        "00010011",
        "00101111",
        "01011111",
        "10001110",
        "10000100",
        "10001000",
        "01110000"]

# BOTH rows are EATEN on their own ripped bite strips (decompile EATING
# state: the item glyph steps full -> bitten -> nearly-gone as the mon chews;
# nothing drawn after the last bite).  `me`/`ge`/`_e` and `he`/`ve`/`ye`
# ripped verbatim; the closing None is the eaten-away frame, same shape as
# the food atlas strips.
MEAT_BITES = [MEAT,
              ["00000011",
               "00000101",
               "00000110",
               "00001110",
               "01111110",
               "01011100",
               "10111000",
               "11000000"],
              ["00000011",
               "00000001",
               "00000010",
               "00000110",
               "00011110",
               "01011100",
               "10111000",
               "11000000"],
              None]

PILL_BITES = [PILL,
              ["00000000",
               "00010000",
               "00101000",
               "01011000",
               "10001100",
               "10000100",
               "10001000",
               "01110000"],
              ["00000000",
               "00000000",
               "00100000",
               "01000000",
               "10000000",
               "10000000",
               "10000000",
               "01100000"],
              None]

CURSOR = ["1000",
          "1100",
          "1110",
          "1111",
          "1110",
          "1100",
          "1000"]

# layout (decompile Rn coords, LCD-absolute): icons at x15, cursor at the
# left margin; the two 8px icons stack to fill the 16px band
ICON_X = 15
CURSOR_X = grid.X0

ROWS_MENU = [("meat", "Meat", "hunger +1 · weight +1"),
             ("pill", "Pill", "cures · effort +1 · energy +7")]


class FeedPanel:
    def __init__(self, pet):
        self.pet = pet
        self.cursor = 0
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "pick"), ("ENTER", "feed"), ("ESC", "out"))

    def key(self, k):
        if k in ("up", "k", "down", "j"):
            self.cursor = 1 - self.cursor
        elif k in ("enter", "space"):
            kind, label, _ = ROWS_MENU[self.cursor]
            if kind == "meat":
                msg = self.pet.feed_meat()
                # the staple meat eats through its own ripped me/ge/_e bite
                # strip, like the pill (decompile EATING state, 2026-07-18);
                # the DVPet f:0 icon stays with the bag consumables
                if self.pet.anim == "eat":
                    return ("done", ("fed", {"key": "meat", "name": "Meat"}, msg))
                if "full" in msg:
                    return ("done", ("full", {"key": "meat", "name": "Meat"}, msg))
                return ("done", ("refused", {"key": "meat", "name": "Meat"}, msg))
            was_sick = self.pet.sick or self.pet.is_injured()
            msg = self.pet.feed_pill()
            if self.pet.anim == "eat":
                out = "Cured!" if was_sick else "A tonic — strength and pep."
                # the pill is EATEN (decompile EATING state, pill-anim fix
                # 2026-07-18): it rides the eat fx on its own ripped
                # he/ve/ye bite strip -- "pill" resolves to PILL_BITES
                return ("done", ("healed", {"key": "pill", "name": "Pill"}, out))
            return ("done", ("refused", {"key": "pill", "name": "Pill"}, msg))
        elif k in ("escape", "f"):
            return ("done", None)
        return None

    def text(self):
        """The LCD scene: meat over pill, cursor on the selected row."""
        overlay = render.blit(MEAT, ICON_X, grid.TOP + 0)
        overlay += render.blit(PILL, ICON_X, grid.TOP + 8)
        overlay += render.blit(CURSOR, CURSOR_X, grid.TOP + (0 if self.cursor == 0 else 9))
        return menu.paint([], self.pet.background(), rows=grid.ROWS,
                          cols=grid.COLS, overlay=overlay, clip=grid.WINDOW)
