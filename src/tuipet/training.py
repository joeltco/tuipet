"""Training — the clone's ONE timing drill (ported 2026-07-17, Joel:
"replace training system with 0.5 system we made"; the classic four-drill
DVPet versus-training left with it).

A marker sweeps 0..24 and SPACE locks it.  The care-widened mega zone is a
clean strike; the ±5 shoulder is a normal hit; wide is a whiff.  Locking
also SAVES the hit-type on the pet (`saved_hit_type`) — and the battle
READS it (battle.py builds every fight with it, and the bout's own bar
re-locks it): your last locked form is the form your next fight fires
with.  This doc used to say "the classic battle doesn't read it yet" —
stale since the 0.5 battle landed (drill audit 2026-07-19).  Every
attempt counts a training
toward the LINES TR gates (energy -2); a clean strike sheds a little weight.
Attribute POWERS no longer grow here (battle wins still grow them — the
canon setPower +1 lives in record_battle); the clone trains form, not stats.

The show: the bar, then the pet turns and FIRES — strike/impact/aftermath
on the same strikefx rails as battle, against the 0.5 BRICK WALL (Wall_1/
Wall_2 from the clone's battle_fx rips — DSprite is the ultimate truth for
animations and mechanics; the DVPet dummy that briefly stood here was the
wrong prop, Joel 2026-07-17).  Wall_1 stands through the whole volley;
only a MEGA break crumbles it to Wall_2.
"""
from __future__ import annotations
import json
import os

from . import data
from . import grid
from . import menu
from . import strikefx
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL, POS, NEG  # noqa: F401  (theme.apply propagation)

COLS, ROWS = 40, 12
BAR_MAX = 24
IDLE, TURN, ATTACK, CHEER_A, CHEER_B, WEARY = 0, 1, 6, 5, 7, 9
VERDICT_T = 14

# the 0.5 target wall (Wall_1 standing / Wall_2 crumbled), ported verbatim
# from the clone's battle_fx rips (v0.4.12; row-string form)
with open(os.path.join(os.path.dirname(__file__), "data", "train_wall.json")) as _f:
    _WALL = json.load(_f)

# (the local _FONT_3X5 and ENERGY_NEED left 2026-07-19, drill audit: the
# font moved to strikefx.timing_bar with the bar in v0.5.67 and this copy
# fed nothing; the energy gate lives in petbattle.TRAIN_ENERGY_COST.)


# (mega_window lives in battlescreen -- the drill and the bout share ONE
# window, exactly like the clone)
from .battlescreen import mega_window  # noqa: E402


class TrainingPanel:
    def __init__(self, pet):
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
        self.auto_close = None        # set after the strike: no done page --
        #                               the verdict is the happy/mad anim on
        #                               the main LCD (Joel 2026-07-17)

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
                    # straight home: the aftermath tableau WAS the verdict --
                    # the app closes us and the happy/mad fx plays on the LCD
                    self.auto_close = ("done", self.result)

    def _lock(self):
        # battles >= 999: VERBATIM v0.4.12 (DSprite truth, drill audit
        # 2026-07-19) -- a maxed battle counter never whiffs.  Not a cheat
        # shim; do not "fix" it.
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
            elif k in ("escape", "t"):          # t (the opening key) also closes
                return ("done", None)
        return None                    # the strike plays through; anim() closes us

    def strip(self):
        if self.phase == "bar":
            return menu.hints(("SPACE", "strike"), ("ESC", "out"))
        return ""

    # ---- rendering ----
    def _rows(self, pose):
        rec = data.record_for(self.pet.num)
        fr = rec["frames"]
        return (fr[pose] if pose < len(fr) else None) or fr[0]

    def _bar_overlay(self):
        """The canon timing bar (Joel 2026-07-15: 'do it canon style') --
        the pixel-set moved VERBATIM to strikefx.timing_bar so the battle/
        raid ready screen sweeps the same sprite (Joel 2026-07-19)."""
        return strikefx.timing_bar(self.bar, self.mega_lo, self.mega_hi)

    def _bar_text(self):
        return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                          overlay=self._bar_overlay(), clip=grid.WINDOW)

    def _wall_overlay(self, m):
        """The standing target wall (the clone's rule, verbatim): Wall_1
        stands through the whole volley; only a MEGA break crumbles it to
        Wall_2."""
        from . import render
        which = "Wall_2" if m == "break" and self.grade == "mega" else "Wall_1"
        rows = _WALL.get(which) or []
        return render.blit(rows, grid.X0, grid.FLOOR - len(rows))

    def _shoot_text(self):
        """The pet fires LEFT at the target wall on battle's ALTERNATING
        views -- no room for pet + flight + wall in the 32px window:
        windup/fire_out -> the pet's view, orb exits the window;
        fire_in        -> the WALL's view, orb crosses and lands on its face;
        hit            -> the flash owns the whole screen (like battle);
        break/miss     -> the verdict tableau: pet beside the wall (a MEGA
                          leaves it crumbled -- Wall_1 stands otherwise)."""
        from .battlescreen import EXPLODE, _full
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        m = fr.get("m")
        if m == "hit":
            return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                              overlay=_full(EXPLODE[fr.get("f", 0)]),
                              clip=grid.WINDOW)
        if m == "fire_in":                       # the wall's view: no pet
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            overlay = self._wall_overlay(m)
            overlay += strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
                                           grid.X0 + 8, fr.get("double"))
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
                                           mouth, fr.get("double"))
        return menu.paint(place, self.pet.background(), rows=ROWS, cols=COLS,
                          overlay=overlay, clip=grid.WINDOW)

    def text(self):
        if self.phase == "bar":
            return self._bar_text()
        return self._shoot_text()      # (the done page left: the verdict is
        #                                the anim -- Joel 2026-07-17)
