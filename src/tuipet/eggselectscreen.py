"""Choose-your-egg, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import egg as egg_mod
from .render import render_screen

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 38, 10


class EggSelectPanel:
    def __init__(self):
        self.n = egg_mod.count()
        self.i = 0

    def key(self, k):
        if k in ("right", "l"):
            self.i = (self.i + 1) % self.n
        elif k in ("left", "h"):
            self.i = (self.i - 1) % self.n
        elif k in ("enter", "space"):
            return ("done", self.i)
        return None

    def text(self):
        rec = egg_mod.record(self.i)
        out = Text()
        out.append(f"CHOOSE YOUR EGG   {self.i + 1}/{self.n}\n", style=INK_B)
        out.append_text(render_screen(rec["frames"][0], COLS, ROWS, LCD_ON, LCD_BG))
        out.append(f"\n  hatches: {egg_mod.hatch_name(self.i)}\n", style=INK_B)
        out.append("  <-  pick  ->    ENTER", style=DIM)
        return out
