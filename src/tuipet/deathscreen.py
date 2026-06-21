"""Memorial screen shown when the pet passes away."""
from __future__ import annotations
from . import data, menu
from .render import render_screen
from .theme import LCD_ON, LCD_BG, DIM

COLS, ROWS = 40, 7
GRAVE = (data.load_effects().get("grave") or [None])[0]


class DeathPanel:
    def __init__(self, pet):
        self.pet = pet

    def key(self, k):
        if k == "n":
            return ("done", "new")
        if k in ("escape", "enter", "space"):
            return ("done", None)
        return None

    def text(self):
        p = self.pet
        mins = int(p.age_seconds) // 60
        out = menu.bar("MEMORIAL", "")
        if GRAVE:
            out.append_text(render_screen(GRAVE, COLS, ROWS, LCD_ON, LCD_BG))
            out.append("\n")
        out.append_text(menu.note(f"R.I.P.  {p.name}"))
        out.append(f"gen {p.generation}  ·  lived {mins}m  ·  {p.stage}\n", style=DIM)
        out.append_text(menu.footer("N  a new egg      ESC  let it rest"))
        return out
