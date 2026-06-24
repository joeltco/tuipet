"""Adventure — travel a zone, fight encounters/boss, all in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data
from .adventure import Adventure
from .battlescreen import BattlePanel
from .render import render_scene

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
            self.travelling = not self.travelling
        elif k == "escape":
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
        pet_rows = self._frames()
        ew = max(len(r) for r in pet_rows)
        x = 1 + int((COLS - ew - 2) * (a.pct / 100))
        scene = render_scene([(pet_rows, x, True)], COLS, ROWS, LCD_ON, LCD_BG)
        fill = round(a.pct / 100 * BAR_W)
        bar = "[" + "█" * fill + "·" * (BAR_W - fill) + "]"
        lives = "♥" * a.lives + "·" * (3 - a.lives)
        out = menu.bar("ADVENTURE", f"Map {a.mi + 1}-{a.zi + 1}")
        out.append_text(scene)
        out.append(f"\n{bar} {a.pct}%\n", style=INK)
        out.append(f"Life {lives}   Bits {self.pet.bits}   Bag {sum(self.pet.inventory.values())}\n", style=INK)
        out.append_text(menu.note(a.last or ""))
        if a.done:
            out.append_text(menu.footer("Journey complete!   ESC"))
        elif self.travelling:
            out.append_text(menu.footer("travelling...   SPACE stop   ESC out"))
        else:
            out.append_text(menu.footer("stopped.   SPACE go   ESC out"))
        return out
