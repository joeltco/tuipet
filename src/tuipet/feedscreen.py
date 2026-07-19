"""Feed menu — the canon on-LCD icon picker (BASIC VPET 2026-07-16, cloned
from the v0.4.x rebuild).

The classic two-item feed: MEAT fills a hunger heart (+1 weight, refused at a
full belly); the PILL cures an active sickness spell, restores a
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

# BOTH rows are EATEN (the source's EATING action is the ANIMATION truth:
# the item shrinks bite by bite as the mon chews) -- but the eating FRAMES
# are DVPet atlas rips, the ART truth (Joel 2026-07-18: "all sprites must
# come from dvpet. the dsprite ones suck"): meat eats through f:0 Meat and
# the pill through f:4 Med, both real uniform 4-frame strips.  The 8px
# glyphs above are only the MENU icons.

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

# (the third, description field was dead data -- displayed nowhere; the
# status card carries the real disclosure.  Trimmed, feed audit 2026-07-19.)
ROWS_MENU = [("meat", "Meat"), ("pill", "Pill")]


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
            kind, label = ROWS_MENU[self.cursor]
            if kind == "meat":
                msg = self.pet.feed_meat()
                # the staple meat eats through the DVPet f:0 Meat strip
                # (art truth; the eat ACTION itself is the source's)
                if self.pet.anim == "eat":
                    return ("done", ("fed", {"key": "f:0", "name": "Meat"}, msg))
                if "full" in msg:
                    return ("done", ("full", {"key": "f:0", "name": "Meat"}, msg))
                return ("done", ("refused", {"key": "f:0", "name": "Meat"}, msg))
            was_sick = self.pet.sick   # (the is_injured() leg was the dead
            #                              injury system's hard-False stub;
            #                              feed audit 2026-07-19)
            msg = self.pet.feed_pill()
            if self.pet.anim == "eat":
                out = "Cured!" if was_sick else "A tonic — strength and pep."
                # the pill is EATEN (the source's EATING action, pill-anim
                # fix 2026-07-18) through the DVPet f:41 Food Pill strip --
                # a real capsule (Joel's report 2026-07-19: "wheres the
                # pill? thats a bottle" -- f:4 Med IS a bottle; audited
                # 2026-07-19: nothing else uses f:4, and the bottle strip
                # stays in the atlas.  The assistant's feed fx already
                # wears the same capsule as f:44)
                return ("done", ("healed", {"key": "f:41", "name": "Pill"}, out))
            return ("done", ("refused", {"key": "f:41", "name": "Pill"}, msg))
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
