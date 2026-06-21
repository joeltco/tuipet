"""Choose-your-egg screen — DVPet's Choose_Egg menu. Arrow through the real egg
sprites and pick one to start the game with."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import egg as egg_mod
from .render import render_screen

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 26, 12


class EggSelectScreen(ModalScreen):
    CSS = """
    EggSelectScreen { align: center middle; }
    #egg { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 30; height: 17; }
    """
    BINDINGS = [
        ("left", "move(-1)", "Prev"), ("h", "move(-1)", "Prev"),
        ("right", "move(1)", "Next"), ("l", "move(1)", "Next"),
        ("enter", "pick", "Choose"), ("space", "pick", "Choose"),
    ]

    def __init__(self):
        super().__init__()
        self.n = max(1, len(egg_mod._real_eggs() or [1]))
        self.i = 0

    def compose(self):
        yield Static(id="egg")

    def on_mount(self):
        self.view = self.query_one("#egg", Static)
        self.render_view()

    def action_move(self, d):
        self.i = (self.i + d) % self.n
        self.render_view()

    def action_pick(self):
        self.dismiss(self.i)

    def render_view(self):
        rec = egg_mod.record(self.i)
        rows = rec["frames"][0]
        out = Text()
        out.append(f"CHOOSE YOUR EGG   {self.i + 1}/{self.n}\n", style=INK_B)
        out.append_text(render_screen(rows, COLS, ROWS, LCD_ON, LCD_BG))
        out.append("\n  ◄  pick  ►    ENTER start", style=DIM)
        self.view.update(out)
