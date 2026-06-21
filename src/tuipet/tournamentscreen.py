"""Tournament — fight a bracket for trophies, in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data
from .tournament import Tournament
from .battlescreen import BattlePanel
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 9


class TournamentPanel:
    def __init__(self, pet):
        self.pet = pet
        self.tourney = Tournament(pet)
        self.frame_i = 0
        self.sub = None

    def anim(self):
        if self.sub is not None:
            self.sub.anim()
            return
        self.frame_i += 1

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.tourney.record(bool(r[1] and r[1].won))
                self.sub = None
            return None
        t = self.tourney
        if k in ("space", "enter") and not (t.over or self.sub):
            self.sub = BattlePanel(self.pet, t.current_opponent())
        elif k == "escape":
            return ("done", t.last if t.over else None)
        return None

    def _frames(self, num):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        t = self.tourney
        out = Text()
        out.append(f"{t.name}\n", style=INK_B)
        if t.over:
            scene = render_scene([(self._frames(self.pet.num), (COLS - 16) // 2, False)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
            out.append_text(scene)
            out.append(f"\n{'●' * min(self.pet.trophies, 14)}\n", style=INK_B)
            out.append(f"{t.last}\n", style=INK_B)
            out.append("ESC leave", style=DIM)
            return out
        opp = t.current_opponent()
        pet_rows = self._frames(self.pet.num)
        opp_rows = self._frames(opp["num"])
        ow = max(len(r) for r in opp_rows)
        scene = render_scene([(pet_rows, 2, True), (opp_rows, COLS - ow - 2, False)],
                             COLS, ROWS, LCD_ON, LCD_BG)
        out.append(f"{t.round_name}  (match {t.round + 1}/3)\n", style=INK_B)
        out.append_text(scene)
        out.append(f"\nYou vs {opp['name']}[{opp['attribute'][:2]}]\n", style=INK)
        out.append(f"Trophies {self.pet.trophies}\n", style=INK)
        out.append(f"{t.last}\n", style=INK_B)
        out.append("SPACE fight   ESC leave", style=DIM)
        return out
