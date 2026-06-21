"""Jogress DNA fusion, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data, jogress
from .render import render_scene

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
SEL = f"bold #9bbc0f on {LCD_ON}"
DIM = f"#5a7a1a on {LCD_BG}"
COLS, ROWS = 40, 9
VISIBLE = 4


class JogressPanel:
    def __init__(self, pet):
        self.pet = pet
        self.options = jogress.options(pet)
        self.cursor = 0
        self.frame_i = 0
        self.fused = None
        self.result_msg = ""

    def anim(self):
        self.frame_i += 1

    def key(self, k):
        if k in ("up", "k") and self.options and not self.fused:
            self.cursor = (self.cursor - 1) % len(self.options)
        elif k in ("down", "j") and self.options and not self.fused:
            self.cursor = (self.cursor + 1) % len(self.options)
        elif k in ("enter", "space"):
            if self.fused:
                return ("done", self.result_msg)
            if self.options:
                opt = self.options[self.cursor]
                self.result_msg = jogress.fuse(self.pet, opt["num"])
                self.fused = opt
        elif k in ("escape", "j"):
            return ("done", self.result_msg or None)
        return None

    def _idle(self, num):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES["happy"] if self.fused else data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def text(self):
        out = Text()
        out.append("JOGRESS - DNA Fusion\n", style=INK_B)
        if not self.options:
            out.append("\n  No partner resonates right now.\n", style=DIM)
            out.append("  (Champion+ with a matching partner.)\n\n\n\n", style=DIM)
            out.append("ESC back", style=DIM)
            return out
        opt = self.fused or self.options[self.cursor]
        if self.fused:
            scene = render_scene([(self._idle(opt["num"]), (COLS - 16) // 2, False)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
        else:
            pet_rows = self._idle(self.pet.num)
            par_rows = self._idle(opt["partner_num"]) if opt["partner_num"] else []
            pw = max((len(r) for r in par_rows), default=0)
            scene = render_scene([(pet_rows, 2, False), (par_rows, COLS - pw - 2, True)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
        out.append_text(scene)
        out.append("\n")
        if self.fused:
            out.append(f"{self.result_msg}\n", style=INK_B)
            out.append("\n", style=INK)
            out.append("the fusion stabilises...  (SPACE)", style=DIM)
            return out
        lo = max(0, min(self.cursor - VISIBLE // 2, len(self.options) - VISIBLE))
        for i in range(lo, min(lo + VISIBLE, len(self.options))):
            o = self.options[i]
            sel = i == self.cursor
            mark = ">" if sel else " "
            line = f"{mark}+{o['partner_name'][:11]:11}={o['name'][:13]}({o['attribute'][:2]})"
            out.append(line[:38] + "\n", style=SEL if sel else INK)
        for _ in range(VISIBLE - min(VISIBLE, len(self.options))):
            out.append("\n", style=INK)
        out.append("up/dn pick  ENTER fuse  ESC out", style=DIM)
        return out
