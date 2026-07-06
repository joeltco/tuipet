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
POSE_T = 6                     # canon pre-fusion beat: both parents flip 1<->5 together
FUSE_STEPS = 16 + POSE_T


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
        return menu.scene_ink(bgimg), bgimg

    def _sprite(self, num, role="idle", idx=None):
        if idx is None:
            return data.bob_frame(num, self.frame_i, role,
                                  egg_type=getattr(self.pet, "egg_type", 0))
        fr = data.frames_for(num, getattr(self.pet, "egg_type", 0))
        return (fr[idx] if idx < len(fr) else None) or fr[0]

    def strip(self):
        """The one-line chrome under the LCD (box-clip audit 2026-07-04: the
        pick list / note / footer stacked in-LCD ran 15-16 lines and the
        physical 12-row box clipped them ALL -- every earlier probe only ever
        measured the 7-line no-partner state, so the v0.2.223 refit missed
        this screen)."""
        if not self.options:
            return ""
        if self.phase == "fusing":
            return "DNA... connect!"
        if self.phase == "fused":
            return f"{self.result_msg}  [dim]· SPACE[/]"
        o = self.options[self.cursor]
        return (f"[b]+{o['partner_name'][:10]} = {o['name'][:12]}[/]"
                f" ({o['attribute'][:2]})  {self.cursor + 1}/{len(self.options)}"
                f"  [dim]· ↑↓ ENTER fuse ESC[/]")

    def text(self):
        if not self.options:
            out = menu.bar("JOGRESS", "DNA Fusion")
            out.append_text(menu.blanks(2))
            out.append_text(menu.note("No partner resonates now."))
            out.append("  Champion+ with a matching partner.\n", style=DIM)
            out.append_text(menu.blanks(1))
            out.append_text(menu.footer("ESC back"))
            return out

        if self.phase == "fusing":
            return self._render_fusing()

        on, bgimg = self._palette()
        if self.phase == "fused":
            return render_scene([grid.center(self._sprite(self.fused["num"], "happy"),
                                             ph=FUSE_ROWS * 2)],
                                COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg)
        # pick: the parents face off; the option strip reads below the LCD
        opt = self.options[self.cursor]
        pet_rows = self._sprite(self.pet.num)
        par_rows = self._sprite(opt["partner_num"]) if opt["partner_num"] else []
        return render_scene(grid.faceoff(pet_rows, par_rows, ph=ROWS * 2),
                            COLS, ROWS, on, LCD_BG, bgimg=bgimg)

    def _render_fusing(self):
        ph = FUSE_ROWS * 2
        if self.fuse_step < POSE_T:
            # canon pre-fusion beat (the Jogress intro anim): BOTH parents stand
            # at their marks flipping ready(1) <-> cheer(5) together, then merge
            idx = 1 if (self.fuse_step // 3) % 2 == 0 else 5
            pf = grid.prep(self._sprite(self.old_num, idx=idx), ph)
            rf = grid.prep(self._sprite(self.partner_num, idx=idx), ph) if self.partner_num else []
            on, bgimg = self._palette()
            return render_scene([(pf, grid.X0, True), (rf, grid.X1 - grid.width(rf), False)],
                                COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg)
        step = self.fuse_step - POSE_T
        total = FUSE_STEPS - POSE_T
        pf = grid.prep(self._sprite(self.old_num), ph)
        rf = grid.prep(self._sprite(self.partner_num), ph) if self.partner_num else []
        pw = grid.width(pf)
        rw = grid.width(rf)
        t = step / total
        pet_start, par_start = grid.X0, grid.X1 - rw           # parents start at the grid edges...
        pet_target = grid.X0 + (grid.W - pw) // 2              # ...and slide to the grid centre and merge
        par_target = grid.X0 + (grid.W - rw) // 2
        pet_x = int(pet_start + (pet_target - pet_start) * t)
        par_x = int(par_start + (par_target - par_start) * t)
        overlay = []
        if step >= total - 5:                                  # a flash as the DNA merges (grid-bounded)
            overlay = [(x, y) for y in range(ph) for x in range(grid.X0, grid.X1)
                       if (x + y + step) % 2 == 0]
        on, bgimg = self._palette()
        return render_scene([(pf, pet_x, True), (rf, par_x, False)],   # face inward as they converge
                            COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg, overlay=overlay)
