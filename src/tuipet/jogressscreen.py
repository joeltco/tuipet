"""Jogress DNA fusion, rendered in the display box: pick a partner, watch the
two parents converge and flash, then the fused form is revealed -- DVPet's
startJogressAnim -> jogressFlash -> fused."""
from __future__ import annotations
from . import data, jogress
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
COLS, ROWS = 40, 7
PLAY_COLS = 32
PLAY_X0 = (COLS - PLAY_COLS) // 2                # 4: centred 32-wide play window
PLAY_R = PLAY_X0 + PLAY_COLS                     # 36
VISIBLE = 3
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
            scene = render_scene([(self._sprite(self.fused["num"], "happy"), PLAY_X0 + (PLAY_COLS - 16) // 2, False)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
            out.append_text(scene)
            out.append("\n")
            out.append_text(menu.note(self.result_msg))
            out.append_text(menu.footer("the fusion stabilises...   SPACE"))
            return out

        # pick
        opt = self.options[self.cursor]
        pet_rows = self._sprite(self.pet.num)
        par_rows = self._sprite(opt["partner_num"]) if opt["partner_num"] else []
        pw = max((len(r) for r in par_rows), default=0)
        scene = render_scene([(pet_rows, PLAY_X0, False), (par_rows, PLAY_R - pw, True)],
                             COLS, ROWS, LCD_ON, LCD_BG)
        out.append_text(scene)
        out.append("\n")
        lo = max(0, min(self.cursor - VISIBLE // 2, len(self.options) - VISIBLE))
        shown = 0
        for i in range(lo, min(lo + VISIBLE, len(self.options))):
            o = self.options[i]
            out.append_text(menu.row(f"+{o['partner_name'][:10]} = {o['name'][:12]}({o['attribute'][:2]})", i == self.cursor))
            shown += 1
        out.append_text(menu.blanks(VISIBLE - shown))
        out.append_text(menu.footer("↑↓ pick   ENTER fuse   ESC out"))
        return out

    def _render_fusing(self, out):
        pet_rows = self._sprite(self.old_num)
        par_rows = self._sprite(self.partner_num) if self.partner_num else []
        pw = max((len(r) for r in pet_rows), default=0)
        rw = max((len(r) for r in par_rows), default=0)
        t = self.fuse_step / FUSE_STEPS
        centre = PLAY_X0 + PLAY_COLS // 2
        if self.fuse_step >= FUSE_STEPS - 5:                  # DNA-merge flash: the two become one
            px_h = ROWS * 2                                   # UNDER the flash -- sprites hidden, never overlap
            overlay = [(x, y) for y in range(px_h) for x in range(COLS) if (x + y + self.fuse_step) % 2 == 0]
            scene = render_scene([], COLS, ROWS, LCD_ON, LCD_BG, overlay=overlay)
        else:
            # converge until they MEET at the centre, edge-to-edge -- never overlapping
            pet_target = centre - pw                         # pet's right edge reaches the centre
            par_target = centre                              # partner's left edge reaches the centre
            pet_x = int(PLAY_X0 + (pet_target - PLAY_X0) * t)
            par_x = int((PLAY_R - rw) - ((PLAY_R - rw) - par_target) * t)
            scene = render_scene([(pet_rows, pet_x, False), (par_rows, par_x, True)],
                                 COLS, ROWS, LCD_ON, LCD_BG)
        out.append_text(scene)
        out.append("\n")
        out.append_text(menu.note("DNA... connect!"))
        out.append_text(menu.footer(""))
        return out
