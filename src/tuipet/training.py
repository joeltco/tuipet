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


def can_train(pet):
    """'' when a drill may start, else the reason."""
    if pet.dead or pet.stage == "Egg" or pet.num < 0:
        return "No one to train."
    if pet.asleep:
        return "zzz… asleep"
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

    def _bar_text(self):
        out = menu.header("TRAIN", f"form: {getattr(self.pet, 'saved_hit_type', 'normal')}")
        out.append_text(menu.note("Stop the marker in the zone!"))
        cells = []
        for x in range(BAR_MAX + 1):
            if x == self.bar:
                cells.append("◆")
            elif self.mega_lo <= x <= self.mega_hi:
                cells.append("█")
            elif self.mega_lo - 5 <= x <= self.mega_hi + 5:
                cells.append("▒")
            else:
                cells.append("·")
        out.append_text(menu.blanks(1))
        out.append_text(menu.row("  " + "".join(cells)))
        out.append_text(menu.note("█ mega   ▒ normal   · miss"))
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(f"training this stage: {self.pet.trainings_cur_stage}"))
        out.append_text(menu.footer("SPACE strike   ESC back"))
        return out

    def _shoot_text(self):
        """The pet fires LEFT at a standing target -- the same volley rails
        as battle (windup, orb flight, explosion / whiff)."""
        from .battlescreen import EXPLODE, _full
        fr = self.timeline[min(self.i, len(self.timeline) - 1)]
        m = fr.get("m")
        if m == "windup":
            pose = (TURN, TURN, IDLE, IDLE, ATTACK, ATTACK)[min(fr.get("wu", 0), 5)]
        elif m in ("fire_out", "fire_in"):
            pose = ATTACK
        elif m in ("hit", "break"):
            pose = CHEER_A if (self.frame_i // 3) % 2 else CHEER_B
        elif m == "miss":
            pose = WEARY
        else:
            pose = IDLE
        place, mouth = strikefx.place_combatant(True, self._rows(pose))
        overlay = []
        target = data.load_battle_fx().get("wall")
        trows = None
        if isinstance(target, dict):
            w, h = int(target.get("width", 8)), int(target.get("height", 8))
            px = target.get("sprite") or []
            if len(px) >= w * h:
                trows = ["".join("1" if px[y * w + x] else "0"
                                 for x in range(w)) for y in range(h)]
        if trows and m != "break":                    # the target stands...
            overlay += strikefx.blit(trows, grid.X0,
                                     grid.FLOOR - len(trows))
        if m == "hit":                                # ...and blows on a hit
            overlay += _full(EXPLODE[fr.get("f", 0)])
        if m in ("fire_out", "fire_in"):
            orb = data.attack_orb(self.pet.num, self.pet.attribute, 0,
                                  frame_i=self.frame_i)
            overlay += strikefx.orb_flight(orb, True, m, fr.get("prog", 0),
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
