"""The lobby's jogress fusion cinematic, rendered in the display box: the two
parents converge and flash, then the fused form is revealed -- the classic V-pet's
startJogressAnim -> jogressFlash -> fused.

The offline partner PICKER that used to live here died with the home-screen
jogress action (v0.2.348: fusion is online-pvp-only, a real roster partner via
the lobby); the dead pick/no-partner phases were stripped in the follow-up
polish arc.  The lobby constructs this panel directly at the result phase and
drives anim()/text(); any key skips the converge to the reveal."""
from __future__ import annotations
from . import data
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
    def __init__(self, pet, old_num, partner_num, fused_num):
        self.pet = pet
        self.frame_i = 0
        self.phase = "fusing"          # fusing | fused
        self.fuse_step = 0
        self.old_num = old_num
        self.partner_num = partner_num
        self.fused_num = fused_num

    def anim(self):
        self.frame_i += 1
        if self.phase == "fusing":
            self.fuse_step += 1
            if self.fuse_step >= FUSE_STEPS:
                self.phase = "fused"

    def key(self, k):
        if self.phase == "fusing" and k in ("enter", "space", "escape"):
            self.phase = "fused"       # skip the converge to the reveal
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

    def text(self):
        if self.phase == "fusing":
            return self._render_fusing()
        on, bgimg = self._palette()
        return render_scene([grid.center(self._sprite(self.fused_num, "happy"),
                                         ph=FUSE_ROWS * 2)],
                            COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg)

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
        if step >= total - 5:                                  # a flash as the DNA merges (window-bounded)
            overlay = [(x, y) for y in range(grid.TOP, grid.FLOOR)
                       for x in range(grid.X0, grid.X1)
                       if (x + y + step) % 2 == 0]
        on, bgimg = self._palette()
        return render_scene([(pf, pet_x, True), (rf, par_x, False)],   # face inward as they converge
                            COLS, FUSE_ROWS, on, LCD_BG, bgimg=bgimg, overlay=overlay)
