"""Training — the authentic DM20 SOLO drill: the wall-mash.

Sourced (humulos DM20 manual + wikimon): single-Digimon training is NOT a high/low
shadow-box. Your Digimon attacks a brick WALL; you MASH the button to fill the meter.
Hit it at least MASH_TARGET times in the window and the wall is destroyed → success,
+1 Effort (Strength) and a training credit toward evolution. Below that → it fails.

(The high/low-vs-shield game is DM20 *tag* training — two connected Digimon — and
belongs in the online/connect mode, not here. See AUTHENTIC_REBUILD.md.)

The stat outcome stays in Pet.apply_training; this module is the presentation.
"""
from __future__ import annotations
from . import data
from .render import render_scene
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, MID, ACCENT, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)

COLS = 40
ARENA_ROWS = 12               # the app's ONE locked LCD area (== app SCREEN_ROWS / battle ROWS)
PX_H = ARENA_ROWS * 2

# authentic DM20 single training: ">=13 hits" destroys the wall (manual). A window to do it in.
MASH_TARGET = 13              # full success (wall destroyed) -> +1 Effort + training credit
MASH_PARTIAL = 8             # a weaker showing still lands some hits but doesn't fully break it
MASH_WINDOW = 30             # ticks to mash (10 Hz -> ~3s)
MASH_KEYS = frozenset({" ", "space", "a", "up", "down", "enter", "return"})  # any "punch" button

# wall geometry (left cell of the 32-wide play window; floor 2px off the LCD bottom)
WALL_W = 12
WALL_H = 16
WALL_X = 4
WALL_BOT = PX_H - 2          # 22: bottom row of the wall
SPRITE_W = 16
PET_X = 20                   # the mon stands in the right cell, facing the wall (left)


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _brick(x, y):
    """Brick texture: solid except mortar lines (horizontal every 4 rows, vertical
    every 4 cols offset per course)."""
    if y % 4 == 3:
        return False
    off = 2 if (y // 4) % 2 else 0
    return (x + off) % 4 != 0


def _wall_overlay(taps):
    """Pixels of the brick wall, crumbling from the top as `taps` climbs toward MASH_TARGET."""
    broke = min(taps, MASH_TARGET) * WALL_H // MASH_TARGET     # rows knocked out from the top
    pts = []
    for ly in range(broke, WALL_H):                            # the surviving lower courses
        for lx in range(WALL_W):
            if _brick(lx, ly):
                pts.append((WALL_X + lx, WALL_BOT - WALL_H + ly))
    return pts


class TrainingPanel:
    def __init__(self, pet):
        self.pet = pet
        self.phase = "play"          # play | done
        self.frame_i = 0
        self.taps = 0
        self.timer = MASH_WINDOW
        self.lunge_t = 0             # >0 = the mon is mid-punch (lunges at the wall)
        self.success = False
        self.full = False            # full wall break (>= MASH_TARGET)
        self.result = None
        self.flash = "MASH to smash the wall!"
        self.sfx = None

    # ---- result -------------------------------------------------------------
    def _resolve(self):
        self.full = self.taps >= MASH_TARGET
        self.success = self.taps >= MASH_PARTIAL
        hits = 3 if self.full else (2 if self.success else 1)
        self.result = self.pet.apply_training(hits, 0, game="hp")
        self.phase = "done"
        self.sfx = "win" if self.full else ("attack" if self.success else "refuse")
        self.flash = ("WALL SMASHED!" if self.full
                      else ("nice — some hits landed" if self.success else "too slow…")) + "   (SPACE)"

    # ---- input --------------------------------------------------------------
    def key(self, k):
        if self.phase == "done":
            return ("done", self.result)
        if k in ("escape", "q"):
            return ("done", None)            # abort with no result
        if k in MASH_KEYS:
            self.taps += 1
            self.lunge_t = 2
            self.sfx = "attack"
            if self.taps >= MASH_TARGET:     # wall already destroyed -> end early, full success
                self._resolve()
        return None

    # ---- per-frame ----------------------------------------------------------
    def anim(self):
        self.frame_i += 1
        if self.lunge_t > 0:
            self.lunge_t -= 1
        if self.phase == "play":
            self.timer -= 1
            if self.timer <= 0:
                self._resolve()

    # ---- render -------------------------------------------------------------
    def _palette(self):
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return on, bgimg

    def _pet_frame(self):
        rec = data.load_sprites()[1][self.pet.num]
        fr = rec["frames"]
        roles = data.ROLES
        # punching = the attack pose mid-lunge, else idle; fall back to frame 0 for short sheets
        role = "attack" if self.lunge_t > 0 else "idle"
        idx = roles.get(role, [0])[0]
        return (fr[idx] if idx < len(fr) else fr[0]) or fr[0]

    def text(self):
        on, bgimg = self._palette()
        taps = self.taps
        overlay = _wall_overlay(taps) if (self.phase != "done" or not self.full) else []
        # the mon lunges LEFT toward the wall on each punch
        xpet = PET_X - (3 if self.lunge_t > 0 else 0)
        frame = self._pet_frame()
        # mirror=False -> sprites face left by default, toward the wall on the left
        return render_scene([(frame, xpet, False)], COLS, ARENA_ROWS, on, LCD_BG,
                            overlay=overlay, bgimg=bgimg)
