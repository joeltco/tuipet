"""Backgrounds — the scene picker (the Great Simplification, 2026-07-15).

The habitat screen's successor: habitats, climate and the thermostat are
gone; the scene behind the mon is a picked cosmetic.  Browsed AS SCENES
(the settled picker grammar): the LCD live-previews the pet standing in the
selected backdrop, the picker line rides the #msg strip.  Basic scenes are
free; the fancy ones cost bits (Joel's tiering)."""
from __future__ import annotations
from . import backgrounds as bgs
from . import data, grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG, SIL_DAY  # noqa: F401  (theme.apply propagation)
from . import menu

COLS, ROWS = 40, 12


class BackgroundPanel:
    def __init__(self, pet):
        self.pet = pet
        # free scenes first (the starter shelf), then by price and name
        self.rows = sorted(bgs.CATALOG, key=lambda k: (bgs.price(k), bgs.name(k)))
        self.cursor = next((i for i, k in enumerate(self.rows)
                            if k == pet.bg_current), 0)
        self.frame_i = 0
        self.msg = "pick a scene — it hangs behind the mon"

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        if k in ("up", "k", "left", "h"):          # the strip reads sideways too
            self.cursor = (self.cursor - 1) % len(self.rows)
        elif k in ("down", "j", "right", "l"):
            self.cursor = (self.cursor + 1) % len(self.rows)
        elif k in ("enter", "space"):
            key = self.rows[self.cursor]
            if key == self.pet.bg_current:
                self.msg = f"Already up: {bgs.name(key)}."
            elif self.pet.owns_background(key):
                self.msg = self.pet.pick_background(key)
            else:
                self.msg = self.pet.buy_background(key)
        elif k in ("escape", "e"):
            return ("done", self.msg)
        return None

    def _tag(self, key):
        if key == self.pet.bg_current:
            return "● here"
        if self.pet.owns_background(key):
            return "○ owned"
        p = bgs.price(key)
        return f"{p}b" if p else "free"

    def strip(self):
        # budgeted to HUD_W 40 (menu-bounds law): the name field scrolls,
        # the chrome stands still
        from .render import marquee
        key = self.rows[self.cursor]
        return (f"[b]▸{marquee(bgs.name(key), 13, self.frame_i // 2)}[/]"
                f" {self._tag(key)}"
                f" {self.cursor + 1}/{len(self.rows)}"
                f" [dim]←→ ENTER ESC[/]")

    def text(self):
        """The selected backdrop AS A SCENE: the pet stands in it --
        window-shopping included (render-only preview)."""
        key = self.rows[self.cursor]
        fr = data.bob_frame(self.pet.num, self.frame_i,
                            egg_type=getattr(self.pet, "egg_type", 0))
        placements = [grid.center(grid.prep(fr, ph=ROWS * 2))] if fr else []
        return menu.paint(placements, self.pet.background(file=key),
                          rows=ROWS, cols=COLS)
