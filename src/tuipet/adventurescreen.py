"""Adventure — travel a zone, fight encounters/boss, all in the display box."""
from __future__ import annotations
from . import data
from .adventure import Adventure
from .battlescreen import BattlePanel
from .render import render_scene
from . import grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM
from . import menu
COLS, ROWS = 40, 7
BAR_W = 28


class AdventurePanel:
    def __init__(self, pet):
        self.pet = pet
        self.adv = Adventure(pet)
        self.frame_i = 0
        self.travelling = True
        self.sub = None
        self._pending = None
        self._travel_t = 0

    def anim(self):
        if self.sub is not None:
            self.sub.anim()
            self.sfx = getattr(self.sub, "sfx", None)   # bubble nested battle sfx up to on_frame's drain
            self.sub.sfx = None
            return
        self.frame_i += 1
        self._travel_t += 1
        if self._travel_t >= 3 and self.travelling and not self.adv.done:
            self._travel_t = 0
            ev = self.adv.travel()
            if ev and ev[0] in ("encounter", "boss"):
                self.travelling = False
                self._pending = (ev[0] == "boss", ev[1])
                self.sub = BattlePanel(self.pet, ev[1])
            elif ev and ev[0] == "town":
                self.sfx = "reward"          # reached the rest-town: life + energy restored
            elif ev and ev[0] == "refused":
                self.travelling = False      # Refusing: travelSpeed 0 -- SPACE re-issues the walk
                self.sfx = "refuse"

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                was_boss, enemy = self._pending
                self._pending = None
                self.sub = None
                if r[1] is None:
                    self.adv.last = "Fled the battle."
                    if was_boss:
                        self.adv.boss_pending = False   # re-arm: the zone boss can be retried
                        self.travelling = False         # stopped at the gate -- SPACE to face it again
                        return None
                else:
                    self.adv.resolve(r[1].won, was_boss, enemy)
                self.travelling = not self.adv.done
            return None
        if k == "space" and not self.adv.done:
            if not self.travelling:
                # re-issuing the walk = DVPet canTravel: checkRefused; checkCompliant
                refused = self.pet.check_refused()
                self.pet.check_compliant()
                if refused:
                    self.adv.last = f"{self.pet.name} refuses to walk!"
                    self.sfx = "refuse"
                    return None
            self.travelling = not self.travelling
        elif k in ("escape", "a"):          # a (the opening key) also closes, like shop/habitat
            return ("done", None)
        return None

    def _frames(self):
        rec = data.load_sprites()[1][self.pet.num]
        roles = data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        a = self.adv
        pet_rows = grid.prep(self._frames(), ph=ROWS * 2)     # fit to the strip, grounded
        ew = grid.width(pet_rows)
        lo, hi = grid.roam_bounds(ew)                         # walk within the 32 grid (x4..36)
        x = lo + int((hi - lo) * (a.pct / 100))
        scene = render_scene([(pet_rows, x, True)], COLS, ROWS, LCD_ON, LCD_BG)
        fill = round(a.pct / 100 * BAR_W)
        lives = "♥" * a.lives + "·" * (3 - a.lives)   # dot = lost life (heart glyph reads hollow)
        out = menu.bar("ADVENTURE", f"Map {a.mi + 1}-{a.zi + 1}")
        out.append_text(scene)
        out.append("\n", style=INK)
        out.append("█" * fill, style=INK_B)               # bright fill, matches STATUS bars
        out.append("─" * (BAR_W - fill), style=DIM)       # dim empty track
        out.append(f" {a.pct}%\n", style=INK)
        out.append(f"Life {lives}   Bits {self.pet.bits}   Bag {sum(self.pet.inventory.values())}\n", style=INK)
        out.append_text(menu.note(a.last or ""))
        if a.done:
            out.append_text(menu.footer("Journey complete!   ESC"))
        elif self.travelling:
            out.append_text(menu.footer("travelling...   SPACE stop   ESC out"))
        else:
            out.append_text(menu.footer("stopped.   SPACE go   ESC out"))
        return out
