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
        # budgeted to HUD_W 40 (menu-bounds audit 2026-07-07: the old chrome
        # ran 44-49 wide, so the WHOLE strip marqueed and the key hints slid
        # out of view) -- the name field scrolls, the chrome stands still:
        # 1+10+1+tag(<=7)+1+1+1+count(5)+1+hint(12) == 40
        from .render import marquee
        h = self.rows[self.cursor]
        a = self._aff(h)
        mark = "♥" if a > 0 else ("✖" if a < 0 else "·")
        return (f"[b]▸{marquee(h['name'], 10, self.frame_i // 2)}[/] {self._tag(h)} {mark}"
                f" {self.cursor + 1}/{len(self.rows)}"
                f" [dim]←→ ENTER ESC[/]")

    def text(self):
        """The selected habitat AS A SCENE: the pet stands in the backdrop it
        would call home — window-shopping included (render-only preview)."""
        h = self.rows[self.cursor]
        fr = data.bob_frame(self.pet.num, self.frame_i,
                            egg_type=getattr(self.pet, "egg_type", 0))
        placements = [grid.center(grid.prep(fr, ph=ROWS * 2))] if fr else []
        return menu.paint(placements, self.pet.background(h["id"]),
                          rows=ROWS, cols=COLS)
