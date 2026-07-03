"""Adventure — travel a zone, fight encounters/boss, all in the display box."""
from __future__ import annotations
from . import data
from .adventure import Adventure
from .battlescreen import BattlePanel
from .townscreen import TownPanel
from .render import render_scene
from . import grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM
from . import menu
COLS, ROWS = 40, 7
BAR_W = 28


class AdventurePanel(menu.SubHost):
    def __init__(self, pet):
        self.pet = pet
        self.adv = Adventure(pet)
        self.frame_i = 0
        self.travelling = True
        self.sub = None
        self._pending = None
        self._travel_t = 0
        self.discovering = False    # DiscoverCall: pause for the investigate prompt
        self.town_prompt = None     # a reached town's id: visit or walk on
        self.discovering = False    # DiscoverCall: pause for the investigate prompt
        self.town_prompt = None     # a reached town's id: visit or walk on

    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
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
                self.travelling = False
                self.town_prompt = ev[1]     # its gates are open -- visit?
            elif ev and ev[0] == "refused":
                self.travelling = False      # Refusing: travelSpeed 0 -- SPACE re-issues the walk
                self.sfx = "refuse"
            elif ev and ev[0] == "discover":
                self.travelling = False      # DiscoverCall: stop and ask
                self.discovering = True
                self.sfx = "reward"

    def key(self, k):
        if isinstance(self.sub, TownPanel):
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.sub = None
                self.adv.last = "Back on the road."
                self.travelling = True
            return None
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                was_boss, enemy = self._pending
                self._pending = None
                self.sub = None
                if r[1] is None:
                    self.adv.last = "Fled the battle."
                    self.adv.flee(enemy, was_boss=was_boss)  # canEscape: penalty knockback re-arms the boss
                    if was_boss:
                        self.travelling = False         # knocked back from the gate -- SPACE to approach again
                        return None
                else:
                    self.adv.resolve(r[1].won, was_boss, enemy)
                self.travelling = not self.adv.done
            return None
        if getattr(self, "town_prompt", None) is not None:
            if k in ("enter", "y"):
                self.sub = TownPanel(self.pet, self.town_prompt)
                self.town_prompt = None
            elif k in ("escape", "n", "space"):
                self.town_prompt = None
                self.adv.last = "Passed the town by."
                self.travelling = True
            return None
        if getattr(self, "discovering", False):
            # Investigate_Validation: ENTER looks, ESC walks on
            if k in ("enter", "y"):
                self.discovering = False
                kind, thing = self.adv.investigate()
                if kind == "enemy":
                    self._pending = (False, thing)
                    self.sub = BattlePanel(self.pet, thing)
                elif kind == "item":
                    self.sfx = "reward"
                    self.travelling = True
                else:
                    self.travelling = True
            elif k in ("escape", "n", "space"):
                self.discovering = False
                self.adv.last = "Walked on by."
                self.travelling = True
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
            if getattr(self, "town_prompt", None) is not None:
                foot = "visit the town? ENTER yes  ESC no"
            elif self.discovering:
                foot = "investigate? ENTER yes  ESC no"
            else:
                foot = "stopped.   SPACE go   ESC out"
            out.append_text(menu.footer(foot))
        return out
