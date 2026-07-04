"""Jogress DNA fusion, rendered in the display box: pick a partner, watch the
two parents converge and flash, then the fused form is revealed -- DVPet's
startJogressAnim -> jogressFlash -> fused."""
from __future__ import annotations
from . import data, jogress
from .render import render_scene
from . import grid

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, SIL_DAY  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
# every phase rides the ONE locked arena over the habitat scenery (audit
# 2026-07-04 -- the pick strip was a squat 7-row band, the cinematics 9, all
# on a flat pale LCD while the rest of the game stages its creatures)
COLS, ROWS = 40, 12
FUSE_ROWS = 12
VISIBLE = 2
FUSE_STEPS = 16


class JogressPanel:
    def __init__(self, pet):
        self.pet = pet
        self.options = jogress.options(pet)
        self.cursor = 0
        self.frame_i = 0
        self.fused = None
        self.result_msg = ""
        self.phase = "pick"            # pick | fusing | fused
        self.fuse_step = 0
        self.old_num = None
        self.partner_num = None

    def anim(self):
        self.frame_i += 1
        if self.phase == "fusing":
            self.fuse_step += 1
            if self.fuse_step >= FUSE_STEPS:
                self.phase = "fused"

    def key(self, k):
        if self.phase == "pick" and self.options and k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.options)
        elif self.phase == "pick" and self.options and k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.options)
        elif k in ("enter", "space"):
            if self.phase == "fused":
                return ("done", self.result_msg)
            if self.phase == "pick" and self.options:
                opt = self.options[self.cursor]
                self.old_num = self.pet.num            # remember the parents before fusing
                self.partner_num = opt["partner_num"]
                self.result_msg = jogress.fuse(self.pet, opt["num"])
                self.fused = opt
                self.phase = "fusing"
                self.fuse_step = 0
        elif k == "escape":
            return ("done", self.result_msg or None)
        return None

    def _palette(self):
        bgimg = self.pet.background()
        return (SIL_DAY if bgimg else LCD_ON), bgimg   # never white over a bg (paint() rule)

    def _sprite(self, num, role="idle"):
        rec = data.load_sprites()[1][num]
        roles = data.ROLES[role]
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

        if self.phase == "fusing":
            return self._render_fusing(out)

        if self.phase == "fused":
            on, bgimg = self._palette()
            scene = render_scene([grid.center(self._sprite(self.fused["num"], "happy"), ph=FUSE_ROWS * 2)],
                                 COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg)
            out.append_text(scene)
            out.append("\n")
            out.append_text(menu.note(self.result_msg, tick=self.frame_i))
            out.append_text(menu.footer("the fusion stabilises...   SPACE"))
            return out

        # pick
        opt = self.options[self.cursor]
        pet_rows = self._sprite(self.pet.num)
        par_rows = self._sprite(opt["partner_num"]) if opt["partner_num"] else []
        on, bgimg = self._palette()
        scene = render_scene(grid.faceoff(pet_rows, par_rows, ph=ROWS * 2),
                             COLS, ROWS, on, LCD_BG, bgimg=bgimg)
        out.append_text(scene)
        out.append("\n")
        self.cursor = menu.list_window(
            out, self.options, self.cursor, VISIBLE,
            lambda o, i: f"+{o['partner_name'][:10]} = {o['name'][:12]}({o['attribute'][:2]})")
        out.append_text(menu.footer("↑↓ pick   ENTER fuse   ESC out"))
        return out

    def _render_fusing(self, out):
        ph = FUSE_ROWS * 2
        pf = grid.prep(self._sprite(self.old_num), ph)
        rf = grid.prep(self._sprite(self.partner_num), ph) if self.partner_num else []
        pw = grid.width(pf)
        rw = grid.width(rf)
        t = self.fuse_step / FUSE_STEPS
        pet_start, par_start = grid.X0, grid.X1 - rw           # parents start at the grid edges...
        pet_target = grid.X0 + (grid.W - pw) // 2              # ...and slide to the grid centre and merge
        par_target = grid.X0 + (grid.W - rw) // 2
        pet_x = int(pet_start + (pet_target - pet_start) * t)
        par_x = int(par_start + (par_target - par_start) * t)
        overlay = []
        if self.fuse_step >= FUSE_STEPS - 5:                  # a flash as the DNA merges (grid-bounded)
            overlay = [(x, y) for y in range(ph) for x in range(grid.X0, grid.X1)
                       if (x + y + self.fuse_step) % 2 == 0]
        on, bgimg = self._palette()
        scene = render_scene([(pf, pet_x, True), (rf, par_x, False)],   # face inward as they converge
                             COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg, overlay=overlay)
        out.append_text(scene)
        out.append("\n")
        out.append_text(menu.note("DNA... connect!"))
        out.append_text(menu.footer(""))
        return out
