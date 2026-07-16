"""Training — the timing drill (the clone rebuild, 2026-07-15).

One drill, the same bar the battle uses: a marker sweeps 0..24 and SPACE
locks it.  The mega zone (care-widened, exactly the battle's window) is a
clean strike; the ±5 shoulder is a normal hit; wide is a whiff.  Locking
also SAVES the hit-type — the next battle fires with today's form.  Every
attempt counts a training toward evolution (energy -2); a clean strike
also sheds a little weight.

The show: the bar, then the pet turns and FIRES — strike/impact/aftermath
on the same strikefx rails as battle.
"""
from __future__ import annotations
from . import data
from . import grid
from . import menu
from . import strikefx
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG  # noqa: F401  (theme.apply propagation)

COLS, ROWS = 40, 12
BAR_MAX = 24
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, WEARY = 0, 1, 6, 5, 7, 9
VERDICT_T = 14

ENERGY_NEED = 2

# the source minigame's 3x5 font, verbatim -- only the glyphs "HIT!" touches
# (the source table has NO '!': it falls back to the blank space glyph, so
# the label reads HIT on real hardware too)
_FONT_3X5 = {
    "H": [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1],
    "I": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1],
    "T": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    " ": [0] * 15,
}


def can_train(pet):
    """'' when a drill may start, else the reason.  A sleeper doesn't block:
    dragging it to the bar is a DISTURB -- +1 mistake and a grumpy wake
    (source rule L93; audit 2026-07-15, wired in app.action_train)."""
    if pet.dead or pet.stage == "Egg" or pet.num < 0:
        return "No one to train."
    if pet.energy < ENERGY_NEED:
        return "Too tired to train."
    return ""


class TrainingPanel:
    def __init__(self, pet):
        from .battlescreen import mega_window
        self.pet = pet
        self.frame_i = 0
        self.phase = "bar"            # bar -> shoot -> done
        self.bar = 0
        self.bar_dir = 1
        self.mega_lo, self.mega_hi = mega_window(pet)
        self.grade = None             # mega / normal / miss
        self.success = False
        self.result = ""
        self.i = 0
        self.sfx = None

    # ---- driving ----
    def anim(self):
        self.frame_i += 1
        if self.phase == "bar":
            self.bar += self.bar_dir
            if self.bar >= BAR_MAX or self.bar <= 0:
                self.bar_dir = -self.bar_dir
                self.bar = max(0, min(BAR_MAX, self.bar))
        elif self.phase == "shoot":
            self.i += 1
            fr = self.timeline[min(self.i, len(self.timeline) - 1)]
            m = fr.get("m")
            if m != self._last_m:
                self.sfx = strikefx.beat_sfx(m, fr.get("double"))
                self._last_m = m
            if self.i >= len(self.timeline) - 1:
                self._verdict += 1
                if self._verdict >= VERDICT_T:
                    self.phase = "done"

    def _lock(self):
        if self.pet.battles >= 999 or self.mega_lo <= self.bar <= self.mega_hi:
            g = "mega"
        elif self.mega_lo - 5 <= self.bar <= self.mega_hi + 5:
            g = "normal"
        else:
            g = "miss"
        self.grade = g
        self.success = g != "miss"
        self.pet.saved_hit_type = g
        self.pet.train_result(self.success)
        self.result = {"mega": "A PERFECT strike!",
                       "normal": "A solid hit.",
                       "miss": "Whiffed it..."}[g]
        self.sfx = "confirm" if self.success else "refuse"
        # the strike is the battle's own volley: windup -> fire -> the
        # TARGET breaks (hit) or stands (miss)
        self.timeline = strikefx.build_volley(self.success, g == "mega")
        self._last_m = None
        self._verdict = 0
        self.phase = "shoot"
        self.i = 0

    def key(self, k):
        if self.phase == "bar":
            if k in ("space", "enter"):
                self._lock()
            elif k == "escape":
                return ("done", None)
            return None
        if self.phase == "shoot":
            return None
        if k in ("space", "enter", "escape", "t"):
            return ("done", self.result)
        return None

    def strip(self):
        if self.phase == "bar":
            return menu.hints(("SPACE", "strike"), ("ESC", "back"))
        if self.phase == "done":
            return menu.hints(("SPACE", "done"))
        return ""

    # ---- rendering ----
    def _rows(self, pose):
        rec = data.record_for(self.pet.num)
        fr = rec["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _bar_overlay(self):
        """The canon timing bar, pixel for pixel from the source's
        TRAINING_MINIGAME render (Joel 2026-07-15: 'do it canon style'):
        HIT! in the 3x5 font at (9,0) -- the source font has no '!', so it
        blanks, exactly like the original -- the 28x5 outlined track at
        (2,7), single-pixel ticks above and below the mega window's edges,
        and the moving 2x3 marker at (3+pos, 8)."""
        pts = []

        def L(x, y):                              # the source's pixel-set
            pts.append((grid.X0 + x, grid.TOP + y))

        def B(x, y, w, h):                        # the source's rect outline
            for i in range(w):
                L(x + i, y), L(x + i, y + h - 1)
            for i in range(h):
                L(x, y + i), L(x + w - 1, y + i)

        def R(s, x, y):                           # the source's 3x5 font run
            for ci, ch in enumerate(s):
                g = _FONT_3X5.get(ch, _FONT_3X5[" "])
                for gy in range(5):
                    for gx in range(3):
                        if g[gy * 3 + gx]:
                            L(x + ci * 4 + gx, y + gy)

        R("HIT!", 9, 0)
        B(2, 7, 28, 5)
        lo, hi = 3 + self.mega_lo, 3 + self.mega_hi + 1
        for tx in (lo, hi):                       # the mega window's ticks
            L(tx, 6), L(tx, 12)
        B(3 + self.bar, 8, 2, 3)                  # the marker (outline == solid at 2 wide)
        return pts

    def _bar_text(self):
        return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                          overlay=self._bar_overlay(), clip=grid.WINDOW)

    def _wall_overlay(self, m):
        """The standing target wall.  Wall_1 stands through the whole volley;
        only a MEGA break crumbles it to Wall_2 (source TRAINING_SHOOT rule).
        The old code read width/sprite off the OUTER {"Wall_1","Wall_2"} dict
        and silently drew NO target at all (audit 2026-07-15)."""
        which = "Wall_2" if m == "break" and self.grade == "mega" else "Wall_1"
        e = data.load_battle_fx().get("wall", {}).get(which)
        if not isinstance(e, dict):
            return []
        w, h = int(e.get("width", 8)), int(e.get("height", 8))
        px = e.get("sprite") or []
        if len(px) < w * h:
            return []
        rows_ = ["".join("1" if px[y * w + x] else "0" for x in range(w))
                 for y in range(h)]
        return strikefx.blit(rows_, grid.X0, grid.FLOOR - h)

    def _shoot_text(self):
        """The pet fires LEFT at the target wall on battle's ALTERNATING
        views -- there is no room for pet + flight + wall in the 32px window,
        which is exactly why the source cuts to a wall-only view from frame 3
        (audit 2026-07-15: a single view flew the orb backwards, the wall
        never drew, and the hit flash strobed OVER the pet):
        windup/fire_out -> the pet's view, orb exits the window;
        fire_in        -> the WALL's view, orb crosses and lands on its face;
        hit            -> the flash owns the whole screen (like battle);
        break/miss     -> the verdict tableau: pet beside the wall (a MEGA
                          leaves it crumbled -- source keeps Wall_1 otherwise)."""
        from .battlescreen import EXPLODE, _full
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        m = fr.get("m")
        tint = data.mon_ink(self.pet.num)
        if m == "hit":
            return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                              overlay=_full(EXPLODE[fr.get("f", 0)]),
                              clip=grid.WINDOW)
        if m == "fire_in":                       # the wall's view: no pet
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            overlay = self._wall_overlay(m)
            overlay += strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
                                           grid.X0 + 8, fr.get("double"),
                                           color=tint)
            return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                              overlay=overlay, clip=grid.WINDOW)
        if m == "windup":
            pose = (TURN, TURN, IDLE, IDLE, ATTACK, ATTACK)[min(fr.get("wu", 0), 5)]
        elif m == "fire_out":
            pose = ATTACK
        elif m == "break":
            pose = CHEER_A if (self.frame_i // 3) % 2 else CHEER_B
        elif m == "miss":
            pose = WEARY
        else:
            pose = IDLE
        place, mouth = strikefx.place_combatant(True, self._rows(pose))
        overlay = [] if m in ("windup", "fire_out") else self._wall_overlay(m)
        if m == "fire_out":                      # the pet's view: orb exits
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            overlay += strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
                                           mouth, fr.get("double"), color=tint)
        return menu.paint(place, self.pet.background(), rows=ROWS, cols=COLS,
                          overlay=overlay, clip=grid.WINDOW)

    def text(self):
        if self.phase == "bar":
            return self._bar_text()
        if self.phase == "done":
            out = menu.header("TRAIN", "")
            out.append_text(menu.blanks(2))
            out.append_text(menu.row(f"  {self.result}"))
            out.append_text(menu.note(f"form saved: {self.grade}"))
            out.append_text(menu.blanks(2))
            out.append_text(menu.footer("SPACE done"))
            return out
        return self._shoot_text()
