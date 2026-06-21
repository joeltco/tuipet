"""Jogress DNA fusion, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data, jogress
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL
from . import menu
COLS, ROWS = 40, 7
VISIBLE = 3


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
        out = menu.bar("JOGRESS", "DNA Fusion")
        if not self.options:
            out.append_text(menu.blanks(2))
            out.append_text(menu.note("No partner resonates now."))
            out.append("  Champion+ with a matching partner.\n", style=DIM)
            out.append_text(menu.blanks(1))
            out.append_text(menu.footer("ESC back"))
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
            out.append_text(menu.note(self.result_msg))
            out.append_text(menu.footer("the fusion stabilises...   SPACE"))
            return out
        lo = max(0, min(self.cursor - VISIBLE // 2, len(self.options) - VISIBLE))
        shown = 0
        for i in range(lo, min(lo + VISIBLE, len(self.options))):
            o = self.options[i]
            out.append_text(menu.row(f"+{o['partner_name'][:10]} = {o['name'][:12]}({o['attribute'][:2]})", i == self.cursor))
            shown += 1
        out.append_text(menu.blanks(VISIBLE - shown))
        out.append_text(menu.footer("up/dn pick   ENTER fuse   ESC out"))
        return out
