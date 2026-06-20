"""Jogress screen — pick a fusion partner and DNA-evolve into the fusion form."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data, jogress
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
SEL = f"bold #9bbc0f on {LCD_ON}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 10
VISIBLE = 4


class JogressScreen(ModalScreen):
    CSS = """
    JogressScreen { align: center middle; }
    #jog { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 50; height: 19; }
    """
    BINDINGS = [
        ("up", "move(-1)", "Up"), ("k", "move(-1)", "Up"),
        ("down", "move(1)", "Down"), ("j", "move(1)", "Down"),
        ("enter", "fuse", "Fuse"), ("space", "fuse", "Fuse"),
        ("escape", "leave", "Cancel"),
    ]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.options = jogress.options(pet)
        self.cursor = 0
        self.frame_i = 0
        self.fused = None
        self.result_msg = ""

    def compose(self):
        yield Static(id="jog")

    def on_mount(self):
        self.view = self.query_one("#jog", Static)
        self.set_interval(0.4, self._anim)
        self.render_view()

    def _anim(self):
        self.frame_i += 1
        self.render_view()

    def action_move(self, d):
        if self.options and not self.fused:
            self.cursor = (self.cursor + d) % len(self.options)
        self.render_view()

    def action_fuse(self):
        if self.fused:
            self.dismiss(self.result_msg); return
        if not self.options:
            return
        opt = self.options[self.cursor]
        self.result_msg = jogress.fuse(self.pet, opt["num"])
        self.fused = opt
        self.render_view()

    def action_leave(self):
        self.dismiss(self.result_msg or None)

    def _idle(self, num):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES["happy"] if self.fused else data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def render_view(self):
        out = Text()
        out.append("JOGRESS — DNA Fusion\n", style=INK_B)
        if not self.options:
            out.append("\n  No partner resonates with your pet right now.\n", style=DIM)
            out.append("  (Jogress unlocks at Champion+ with a matching partner.)\n\n\n\n", style=DIM)
            out.append("ESC back", style=DIM)
            self.view.update(out)
            return

        opt = self.fused or self.options[self.cursor]
        if self.fused:
            scene = render_scene([(self._idle(opt["num"]), (COLS - 16) // 2, False)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
        else:
            pet_rows = self._idle(self.pet.num)
            par_rows = self._idle(opt["partner_num"]) if opt["partner_num"] else []
            pw = max((len(r) for r in par_rows), default=0)
            scene = render_scene(
                [(pet_rows, 2, False), (par_rows, COLS - pw - 2, True)],
                COLS, ROWS, LCD_ON, LCD_BG)
        out.append_text(scene)
        out.append("\n")
        if self.fused:
            out.append(f"{self.result_msg}\n", style=INK_B)
            out.append("\n\n", style=INK)
            out.append("the fusion stabilises...  (SPACE)", style=DIM)
            self.view.update(out)
            return

        lo = max(0, min(self.cursor - VISIBLE // 2, len(self.options) - VISIBLE))
        for i in range(lo, min(lo + VISIBLE, len(self.options))):
            o = self.options[i]
            sel = i == self.cursor
            mark = ">" if sel else " "
            line = f"{mark} + {o['partner_name'][:12]:12} = {o['name'][:14]} ({o['attribute'][:2]})"
            out.append(line[:46] + "\n", style=SEL if sel else INK)
        for _ in range(VISIBLE - min(VISIBLE, len(self.options))):
            out.append("\n", style=INK)
        out.append("↑↓ pick   ENTER fuse   ESC cancel", style=DIM)
        self.view.update(out)
