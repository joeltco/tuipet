"""Backgrounds — the scene picker (restored 2026-07-17: "add the e action
back to change backgrounds").

The clone's picker grammar, minus the price walls it had already dropped:
the LCD live-previews the pet standing in the browsed backdrop, the picker
line rides the #msg strip, ENTER commits.  Row 0 is the egg's own scene
(the default wiring stays the truth; a pick merely overrides it)."""
from __future__ import annotations
from . import backgrounds as bgs
from . import data, grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)
from . import menu

COLS, ROWS = 40, 12


class BackgroundPanel:
    def __init__(self, pet):
        self.pet = pet
        self.rows = [""] + list(bgs.PICKS)          # "" = follow the egg
        self.cursor = next((i for i, k in enumerate(self.rows)
                            if k == pet.bg_pick), 0)
        self.frame_i = 0
        self.msg = "pick a scene — it hangs behind the mon"
        self.sfx = None

    def anim(self):
        self.frame_i += 1

    def _key_of(self, row):
        """The scene a row previews (row 0 = the egg's own)."""
        return row or bgs.scene_for_egg(self.pet.egg_type)

    def key(self, k):
        if k in ("up", "k", "left", "h"):          # the strip reads sideways too
            self.cursor = (self.cursor - 1) % len(self.rows)
        elif k in ("down", "j", "right", "l"):
            self.cursor = (self.cursor + 1) % len(self.rows)
        elif k in ("enter", "space"):
            key = self.rows[self.cursor]
            if key == self.pet.bg_pick:
                self.msg = "Already up."
            else:
                self.msg = self.pet.pick_background(key)
                self.sfx = "confirm"
        elif k in ("escape", "e"):
            return ("done", self.msg)
        return None

    def _name(self, row):
        if not row:
            return "%s (egg's own)" % bgs.name(bgs.scene_for_egg(self.pet.egg_type))
        return bgs.name(row)

    def _tag(self, row):
        return "● here" if row == self.pet.bg_pick else ""

    def strip(self):
        # budgeted to HUD_W 40 (menu-bounds law): the name field scrolls,
        # the chrome stands still
        from .render import marquee
        return (f"[b]▸{marquee(self._name(self.rows[self.cursor]), 14, self.frame_i // 2)}[/]"
                f" {self.cursor + 1}/{len(self.rows)}"
                f" [dim]←→ ENTER ESC[/]")

    def text(self):
        """The browsed backdrop AS A SCENE: the pet stands in it --
        window-shopping included (render-only preview)."""
        key = self._key_of(self.rows[self.cursor])
        fr = data.bob_frame(self.pet.num, self.frame_i,
                            egg_type=getattr(self.pet, "egg_type", 0))
        placements = [grid.center(grid.prep(fr, ph=ROWS * 2))] if fr else []
        return menu.paint(placements, self.pet.background(file=key),
                          rows=ROWS, cols=COLS)
