"""Habitat — buy/move homes, browsed AS SCENES (audit 2026-07-04: habitats are
scenery, yet the picker was a bare text list — you bought a backdrop sight
unseen while the theme picker live-previews).  The LCD shows the pet standing
in the selected habitat; the picker line rides the #msg strip; climate and
ownership details live on the status card.

THE THERMOSTAT lives here too (rebuild 2026-07-14): canon DVPet's temperature
readout is DRAGGABLE — setTempGoal drives the room 1°/game-min toward your
target, and the goal clears on arrival (weather takes back over).  +/- sets
the heat, 0 turns it off.  This — not the futon — is the answer to a cold pet
(Joel: "futons aren't supposed to be the go-to if the mon is cold")."""
from __future__ import annotations
from . import data, grid
from . import weather as wx

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG, SIL_DAY  # noqa: F401  (theme.apply propagation)
from . import menu

COLS, ROWS = 40, 12


class HabitatPanel:
    def __init__(self, pet):
        self.pet = pet
        self.rows = sorted(data.load_habitats().values(), key=lambda h: (h["price"], h["id"]))
        self.cursor = next((i for i, h in enumerate(self.rows) if h["id"] == pet.habitat), 0)
        self.frame_i = 0
        self.msg = self._climate_msg()

    def _climate_msg(self):
        """The room report: current temp, the pet's comfort band, heat state."""
        p = self.pet
        lo, hi = p.ideal_temp
        heat = f" · heat→{int(p.temp_goal)}°" if p.heat_on() else ""
        return f"{int(p.temp)}° now · likes {lo}-{hi}°{heat} · +/- heat"

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
        elif k in ("plus", "equals_sign", "+", "="):
            self._adjust_heat(+5)
        elif k in ("minus", "hyphen", "-", "_"):
            self._adjust_heat(-5)
        elif k in ("0", "zero"):
            self.pet.clear_temp_goal()
            self.msg = "Thermostat off — weather takes over."
        elif k in ("escape", "e"):
            return ("done", self.msg)
        return None

    def _adjust_heat(self, d):
        """Turn the heat up/down: the first nudge arms the thermostat FROM the
        current temperature (canon mousePressed: an unset goal starts at
        getTemp), then each press steps the goal 5°."""
        p = self.pet
        base = p.temp_goal if p.heat_on() else p.temp
        p.set_temp_goal(max(0, min(wx.MAX_TEMP, round(base + d))))
        lo, hi = p.ideal_temp
        word = ("cozy" if lo <= p.temp_goal <= hi else
                ("hot!" if p.temp_goal > hi else "cold!"))
        self.msg = f"heat→{int(p.temp_goal)}° ({word}) · now {int(p.temp)}° · 0 off"

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
