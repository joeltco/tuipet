"""Habitat — buy/move homes, browsed AS SCENES (audit 2026-07-04: habitats are
scenery, yet the picker was a bare text list — you bought a backdrop sight
unseen while the theme picker live-previews).  The LCD shows the pet standing
in the selected habitat; the picker line rides the #msg strip; climate and
ownership details live on the status card."""
from __future__ import annotations
from . import data, grid
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG, SIL_DAY  # noqa: F401  (theme.apply propagation)
from . import menu

COLS, ROWS = 40, 12


class HabitatPanel:
    def __init__(self, pet):
        self.pet = pet
        self.rows = sorted(data.load_habitats().values(), key=lambda h: (h["price"], h["id"]))
        self.cursor = next((i for i, h in enumerate(self.rows) if h["id"] == pet.habitat), 0)
        self.frame_i = 0
        self.msg = "Pick a home."

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        if k in ("up", "k", "left", "h"):          # the strip reads sideways too
            self.cursor = (self.cursor - 1) % len(self.rows)
        elif k in ("down", "j", "right", "l"):
            self.cursor = (self.cursor + 1) % len(self.rows)
        elif k in ("enter", "space"):
            h = self.rows[self.cursor]
            if h["id"] == self.pet.habitat:
                self.msg = f"Already in {h['name']}."
            elif h["id"] in self.pet.habitats:
                self.msg = self.pet.move_to(h["id"])
            else:
                self.msg = self.pet.buy_habitat(h["id"])
        elif k in ("escape", "e"):
            return ("done", self.msg)
        return None

    def _aff(self, h):
        f, e = self.pet.field, self.pet.element
        c = (f in h["compat_fields"]) + (e in h["compat_elements"])
        i = (f in h["incompat_fields"]) + (e in h["incompat_elements"])
        return c - i

    def _aff_word(self, h):
        a = self._aff(h)
        if a > 0:
            return "♥" * a + " thrives"
        if a < 0:
            return "✖" * -a + " suffers"
        return "neutral"

    def _tag(self, h):
        if h["id"] == self.pet.habitat:
            return "● here"
        if h["id"] in self.pet.habitats:
            return "○ owned"
        return f"{h['price']}b"

    def climate(self, h):
        su, wi = h["temps"]["Summer"], h["temps"]["Winter"]
        return ("climate-controlled" if h["weather_chance"] <= 0
                else f"Su {su[0]}-{su[1]}°  Wi {wi[0]}-{wi[1]}°")

    def strip(self):
        h = self.rows[self.cursor]
        a = self._aff(h)
        mark = "♥" if a > 0 else ("✖" if a < 0 else "·")
        return (f"[b]▸{h['name'][:14]}[/] {self._tag(h)} {mark}"
                f"  {self.cursor + 1}/{len(self.rows)}"
                f"  [dim]· ←→ ENTER buy/move ESC[/]")

    def text(self):
        """The selected habitat AS A SCENE: the pet stands in the backdrop it
        would call home — window-shopping included (render-only preview)."""
        h = self.rows[self.cursor]
        bgimg = self.pet.background(h["id"])
        on = SIL_DAY if bgimg else LCD_ON          # never white over a bg (paint() rule)
        rec = data.load_sprites()[1][self.pet.num]
        roles = data.ROLES["idle"]
        fr = rec["frames"][roles[(self.frame_i // 5) % 2]] or rec["frames"][0]
        return render_scene([grid.center(grid.prep(fr, ph=ROWS * 2))],
                            COLS, ROWS, on, LCD_BG, bgimg=bgimg)
