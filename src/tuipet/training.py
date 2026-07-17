"""Training — the clone's ONE timing drill (ported 2026-07-17, Joel:
"replace training system with 0.5 system we made"; the classic four-drill
DVPet versus-training left with it).

A marker sweeps 0..24 and SPACE locks it.  The care-widened mega zone is a
clean strike; the ±5 shoulder is a normal hit; wide is a whiff.  Locking
also SAVES the hit-type on the pet (`saved_hit_type` — the clone's battle
fired with today's form; the classic battle doesn't read it yet, so it
stands ready for a 0.5 battle conversion).  Every attempt counts a training
toward the LINES TR gates (energy -2); a clean strike sheds a little weight.
Attribute POWERS no longer grow here (battle wins still grow them — the
canon setPower +1 lives in record_battle); the clone trains form, not stats.

The show: the bar, then the pet turns and FIRES — strike/impact/aftermath
on the same strikefx rails as battle.  The target is the REAL DVPet
training dummy (hp_dummies.json, attribute-matched); a MEGA strike leaves
the floor empty where it stood — no invented crumble art.
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

ENERGY_NEED = 2                 # the clone's "Too tired to train" gate

# the REAL DVPet HP-training dummy (battleBags.png rows; extraction 2026-07)
with open(os.path.join(os.path.dirname(__file__), "data", "hp_dummies.json")) as _f:
    _HP_DUMMIES = json.load(_f)

# the source minigame's 3x5 font, verbatim -- only the glyphs "HIT!" touches
# (the source table has NO '!': it falls back to the blank space glyph, so
# the label reads HIT on real hardware too)
_FONT_3X5 = {
    "H": [1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1],
    "I": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1],
    "T": [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0],
    " ": [0] * 15,
}


def mega_window(pet):
    """Care widens the skill ceiling (the clone's rule, on classic gauges):
    winrate/hunger/effort/energy/age each carry 0.2 of the condition score;
    the mega zone is [12-c, 12+c] on the 0..24 bar (width 1/3/5/7)."""
    from .pet import DAY_LENGTH
    wr = pet.wins / pet.battles if pet.battles > 0 else 0
    hu = pet.hunger / 4.0
    st = pet.strength / 4.0
    en = max(0, pet.energy) / pet.max_energy if pet.max_energy else 0
    ag = min((pet.age_seconds / DAY_LENGTH) / 5, 1)
    o = min(1.0, wr * 0.2 + hu * 0.2 + st * 0.2 + ag * 0.2 + en * 0.2)
    w = 1 + int(o * 3) * 2
    c = w // 2
    return 12 - c, 12 + c


def _dummy_rows(pet, taunt=False):
    """The attribute-matched dummy (canon setAltIcon never flips a prop)."""
    key = {"Vaccine": "vaccine", "Virus": "virus"}.get(pet.attribute, "data")
    return _HP_DUMMIES.get(key + ("_taunt" if taunt else ""), _HP_DUMMIES[key])


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

    def _target_place(self, m):
        """The standing dummy: the REAL DVPet prop, left side, sheet facing
        (canon setAltIcon never flips it).  It TAUNTS a whiff; a MEGA break
        leaves the floor empty after the flash -- the real crumble frame
        doesn't exist in the rips, and tuipet never draws its own art."""
        if m == "break" and self.grade == "mega":
            return []
        rows = _dummy_rows(self.pet, taunt=(m == "miss"))
        place, _mouth = strikefx.place_combatant(False, rows, mirror=False)
        return place

    def _shoot_text(self):
        """The pet fires LEFT at the dummy on battle's ALTERNATING views --
        there is no room for pet + flight + target in the 32px window:
        windup/fire_out -> the pet's view, orb exits the window;
        fire_in        -> the TARGET's view, orb crosses and lands;
        hit            -> the flash owns the whole screen (like battle);
        break/miss     -> the verdict tableau: pet beside the dummy (a MEGA
                          leaves the floor bare; a whiff earns the taunt)."""
        from .battlescreen import EXPLODE, _full
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        m = fr.get("m")
        if m == "hit":
            return menu.paint([], self.pet.background(), rows=ROWS, cols=COLS,
                              overlay=_full(EXPLODE[fr.get("f", 0)]),
                              clip=grid.WINDOW)
        if m == "fire_in":                       # the target's view: no pet
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            place = self._target_place(m)
            overlay = strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
                                          grid.X0 + 14, fr.get("double"))
            return menu.paint(place, self.pet.background(), rows=ROWS, cols=COLS,
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
        if m not in ("windup", "fire_out"):
            place = self._target_place(m) + place
        overlay = []
        if m == "fire_out":                      # the pet's view: orb exits
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            overlay = strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
                                          mouth, fr.get("double"))
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
