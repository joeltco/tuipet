"""Feed menu — meat or pill (the clone rebuild, 2026-07-15).

The classic two-item feed: MEAT fills a hunger heart (+1 weight, refused at
a full belly); the PILL cures sickness, restores a strength heart, +7
energy, +5 weight.  Both are free and infinite — the richer consumables
(fruits, premium meat, junk food) live in the BAG ('i') as shop items.
"""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM, ACCENT, POS  # noqa: F401  (theme.apply propagation)

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
        p = self.pet
        out = menu.header("FEED", f"hunger {p.hunger}/{p.hunger_max}  "
                                  f"effort {p.strength}/{p.strength_max}")
        out.append_text(menu.blanks(1))
        for i, (kind, label, effect) in enumerate(ROWS_MENU):
            out.append_text(menu.row(f"{label:<6} {effect}", i == self.cursor))
        out.append_text(menu.blanks(1))
        out.append_text(menu.note("richer food lives in the BAG (i)"))
        out.append_text(menu.footer("↑↓ pick   ENTER feed   ESC out"))
        return out
