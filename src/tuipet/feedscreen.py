"""Feed menu — the canon on-LCD icon picker (clone rebuild 2026-07-16).

The classic two-item feed: MEAT fills a hunger heart (+1 weight, refused at a
full belly); the PILL cures sickness, restores a strength heart, +7 energy, +5
weight.  Both are free and infinite — the richer consumables (fruits, premium
meat, junk food) live in the BAG ('i') as shop items.

The source draws this as a MENU ON THE LCD (decompile `Rn()`): the meat glyph
`me` sits top-centre, the pill glyph `he` directly below it, and the cursor
arrow `O` sits at the left margin pointing at the selected row.  A menu press
flips `feedSelection` 0<->1; the action button feeds the pick.  We match that
here instead of the old text list — feed's siblings (training, battle) all
render graphically on the LCD, so it belongs there too.

Glyphs below are the EXACT bitmaps ripped from the decompile (`me`/`he`/`O`),
not hand-drawn — meat drumstick, pill capsule, right-pointing cursor.
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

CURSOR = ["1000",
          "1100",
          "1110",
          "1111",
          "1110",
          "1100",
          "1000"]

# layout (decompile Rn coords, LCD-absolute): icons at x15, cursor at the left
# margin; the two 8px icons stack to fill the 16px band, cursor y0 -> meat,
# y9 -> pill.
ICON_X = 15
CURSOR_X = grid.X0

ROWS_MENU = [("meat", "Meat", "hunger +1 · weight +1"),
             ("pill", "Pill", "cures sick · effort +1 · energy +7")]


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
                out = self.pet.feed_meat()
                if out == "ate":
                    return ("done", ("fed", {"key": "meat", "name": "Meat"},
                                     "Munch munch."))
                if out == "refuse":
                    return ("done", ("full", {"key": "meat", "name": "Meat"},
                                     f"{self.pet.name} is full."))
                return ("done", None)
            out = self.pet.feed_pill()
            if out == "healed":
                return ("done", ("fed", {"key": "pill", "name": "Pill"},
                                 "Gulp. All better."))
            if out == "refuse":
                return ("done", ("full", {"key": "pill", "name": "Pill"},
                                 f"{self.pet.name} doesn't need it."))
            return ("done", None)
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
