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

# the half-eaten pill (DSprite SYMBOL_HALF_PILL): a bite taken out of the top
HALF_PILL = ["00000000",
             "00000000",
             "00000000",
             "01100000",
             "11010000",
             "10101000",
             "10011000",
             "01110000"]

# BOTH rows are EATEN -- the source's EATING action is the ANIMATION truth
# (the item shrinks bite by bite as the mon chews).  MEAT eats through the
# DVPet f:0 Meat sheet-strip (art truth, Joel 2026-07-18: "all sprites must
# come from dvpet").  The PILL, though, eats through ITS OWN menu glyph, the
# DSprite way (EatingAnimationScreen.setSprites(SYMBOL_PILL, SYMBOL_HALF_PILL,
# SYMBOL_EMPTY) -- main.cpp case 1): full -> half -> gone, so the picked pill
# IS the eaten pill (pill-anim fix 2026-07-20; the old DVPet f:41 capsule never
# matched the picker -- Joel: "those are not the same sprites").  The eat fx
# pulls this via the "sym:pill" icon key; the None tail is the eaten-away frame
# blit() tolerates.  So the MEAT glyph above is menu-only, but PILL is both.
# DSprite's pill has ONLY these two art frames (SYMBOL_PILL, SYMBOL_HALF_PILL --
# there is no third bite stage in the source), so the strip is paced full ->
# half -> half -> gone across the eat fx's food_beats: the half-eaten pill holds
# through the middle of the chew instead of flashing by (2-frame rebalance, Joel
# 2026-07-20 "the pill eating animation only has 2 frames?").
PILL_FRAMES = [PILL, HALF_PILL, HALF_PILL, None]

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
# R3 (2026-07-23, Joel "make them symmetric"): the BANDAGE joins the Pill
# here as a free, always-available cure.  Two ailments, two care BUTTONS --
# the 300b shelf entry is gone; ailments cost time, not bits.
ROWS_MENU = [("meat", "Meat"), ("pill", "Pill"), ("bandage", "Bandage")]


class FeedPanel:
    def __init__(self, pet):
        self.pet = pet
        # an AILING pet opens on its own cure: the HUD nag names it, and
        # meat would only be refused -- don't make the cure extra presses in
        # the most-repeated care loop (QOL sweep 2026-07-23; the bandage leg
        # joined with R3).  Sick outranks hurt when both are true: sickness
        # is the older, louder alarm.
        self.cursor = 1 if pet.sick else (2 if pet.is_injured() else 0)
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return menu.hints(("↑↓", "pick"), ("ENTER", "feed"), ("ESC", "out"))

    def key(self, k):
        if k in ("up", "k", "down", "j"):
            # a THIRD row retired the old two-row toggle (1 - cursor), which
            # silently ignored direction and could never reach row 2
            step = -1 if k in ("up", "k") else 1
            self.cursor = (self.cursor + step) % len(ROWS_MENU)
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
            if kind == "bandage":
                msg = self.pet.heal_bandage()
                from .petbase import _Refused
                if isinstance(msg, _Refused) or "patched" not in str(msg):
                    return ("done", ("refused", {"key": "i:80",
                                                 "name": "Bandage"}, str(msg)))
                # the bandage is WORN, not eaten: its own canon Bandaging
                # script plays (items.csv i:80 AnimationType), the show that
                # was written for it on 2026-07-23
                return ("done", ("bandaged", {"key": "i:80",
                                              "name": "Bandage"}, str(msg)))
            was_sick = self.pet.sick   # (the is_injured() leg was the dead
            #                              injury system's hard-False stub;
            #                              feed audit 2026-07-19)
            msg = self.pet.feed_pill()
            if self.pet.anim == "eat":
                out = "Cured!" if was_sick else "A tonic — strength and pep."
                # the pill is EATEN (the source's EATING action) through ITS
                # OWN menu glyph -- the DSprite pill route (SYMBOL_PILL ->
                # SYMBOL_HALF_PILL -> gone), so the picked pill IS the eaten
                # pill (pill-anim fix 2026-07-20, replacing the DVPet f:41
                # capsule that never matched the picker)
                return ("done", ("healed", {"key": "sym:pill", "name": "Pill"}, out))
            return ("done", ("refused", {"key": "sym:pill", "name": "Pill"}, msg))
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
