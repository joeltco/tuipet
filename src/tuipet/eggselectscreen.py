"""Choose-your-egg: a smooth horizontal carousel of full-size egg sprites.
Only eggs you can actually hatch appear here -- no sealed silhouettes, no goal
teasers (Joel 2026-07-12: "only the available eggs").  Eggs are earned through
play, full stop (the licence shop was cut 2026-07-17): meet a rule's condition
and the egg joins the carousel, permanently when the rule allows.
←→ glide, ENTER hatches the centred egg, ESC backs out."""
from __future__ import annotations
from . import egg as egg_mod
from . import menu
from . import persistence
from .render import render_scene
from .theme import LCD_ON, LCD_BG

COLS, ROWS = 40, 8            # scene area (16px tall == one full egg)
EGG_W = 16
CENTER = (COLS - EGG_W) // 2  # x_left that centres a 16px egg
SPACING = 24                  # px between adjacent eggs (neighbours peek ~4px)
WINDOW = 2                    # eggs drawn each side of centre
EASE = 0.34                   # glide fraction closed per 0.1s tick
SNAP = 0.03                   # below this, settle exactly


class EggSelectPanel:
    def __init__(self, pet=None):
        self.pet = pet
        prog = persistence.get_progress()
        owned = persistence.get_eggs_owned()
        for i in egg_mod.auto_owned(prog, owned):     # newly-permanent eggs stick
            persistence.egg_own(i)
            owned.add(i)
        self.prog = prog
        self.states = egg_mod.egg_states(prog, owned)
        self.carousel = egg_mod.hatchable_eggs(prog, owned)   # owned + temp -- the ONLY eggs shown
        self.total = egg_mod.count()
        self.hint = egg_mod.locked_hint(prog, owned)
        self.locked = sum(1 for s in self.states.values() if s == "locked")
        self.n = len(self.carousel)
        self.i = 0               # cursor opens on the first egg (position 1/N)
        self.pos = 0.0           # continuous carousel target
        self.scroll = 0.0        # eased current position, chases self.pos
        self.frame_i = 0
        self.msg = ""            # transient footer note
        self.msg_t = 0
        self.sfx = None

    def anim(self):
        self.frame_i += 1
        if self.msg_t > 0:
            self.msg_t -= 1
            if self.msg_t == 0:
                self.msg = ""
        diff = self.pos - self.scroll
        if abs(diff) < SNAP:
            self.scroll = self.pos
        else:
            self.scroll += diff * EASE

    def _flash(self, text):
        self.msg, self.msg_t = text, 22

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10).  N advertises
        the egg guide -- the pick is permanent for the generation, and the
        carousel alone gives no basis to choose (sweep 2026-07-14)."""
        return menu.hints(("←→", "browse"), ("ENTER", "pick"), ("N", "guide"))

    def key(self, k):
        if k in ("right", "l", "down", "j"):
            self.pos += 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("left", "h", "up", "k"):
            self.pos -= 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("enter", "space"):
            if not self.n:
                return None
            return ("done", self.carousel[self.i])     # hatch the centred egg
        elif k == "n":
            return ("done", "guide")                   # consult the egg guide first
        elif k == "escape":
            return ("done", None)                      # back out without choosing
        return None

    def _egg(self, pos):
        return self.carousel[pos % self.n]

    def _frame(self, pos, center):
        idx = self._egg(pos)
        fr = egg_mod.record(idx)["frames"]
        if center and self.scroll == self.pos:         # settled: idle wobble on the chosen egg
            return fr[(self.frame_i // 5) % 2] or fr[0]
        return fr[0]

    def _note(self, idx):
        state = self.states.get(idx, "owned")
        name = egg_mod.hatch_name(idx)
        if state == "temp":
            return "hatches: %s  (this gen only)" % name
        return "hatches: %s" % name

    def text(self):
        if not self.n:                                 # defensive: starters keep this non-empty
            out = menu.header("CHOOSE YOUR EGG", "0/0")
            out.append_text(menu.blanks(ROWS // 2))
            out.append_text(menu.note("no eggs ready — earn them out in the world"))
            out.append_text(menu.footer("ESC back"))
            return out
        placements = []
        base = round(self.scroll)
        for d in range(-WINDOW, WINDOW + 1):
            v = base + d
            x = CENTER + int(round((v - self.scroll) * SPACING))
            placements.append((self._frame(v, d == 0), x, False))
        scene = render_scene(placements, COLS, ROWS, LCD_ON, LCD_BG)
        out = menu.header("CHOOSE YOUR EGG", f"{self.i + 1}/{self.n}")
        out.append_text(scene)
        out.append("\n")                              # scene has no trailing newline
        out.append_text(menu.note(self._note(self._egg(self.i)), tick=self.frame_i))
        if self.msg:
            out.append_text(menu.footer(self.msg))
        elif self.locked > 0 and self.hint and (self.frame_i // 40) % 2 == 1:
            out.append_text(menu.footer(f"{self.locked} more out there · {self.hint}"))
        else:
            out.append_text(menu.footer("←→ browse   ENTER pick   ESC back"))
        return out
