"""Choose-your-egg: a smooth horizontal carousel of full-size egg sprites.
Hatchable eggs lead, buyable ones follow (pointing at the shop), and the tail
carries at most GOALS_SHOWN sealed silhouettes — the countable goals you are
CLOSEST to.  (Hardened 2026-07-04: the arc-3 goal board rode ALL ~44 sealed
eggs, which read as the unlock system being gone; the rest are a footer count.)
←→ glide, ENTER hatches the centred egg, ESC backs out."""
from __future__ import annotations
from . import egg as egg_mod
from . import menu
from . import persistence
from .digicorescreen import silhouette
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
        self.unlocked = egg_mod.hatchable_eggs(prog, owned)    # owned + temp -- only eggs you can hatch
        self.total = egg_mod.count()
        self.hint = egg_mod.locked_hint(prog, owned)
        self.locked = sum(1 for s, _ in self.states.values() if s == "locked")
        self.wins = prog["wins"]
        # hatchable eggs lead, buyable follow, and the tail carries at most
        # GOALS_SHOWN sealed silhouettes -- the countable goals you're CLOSEST
        # to (hardened 2026-07-04: the arc-3 board rode all ~44 sealed eggs and
        # read as the unlock system being gone; the rest stay a footer count)
        self.carousel = self._build_carousel()
        self.n = len(self.carousel)
        self.i = 0               # cursor opens on the first egg (position 1/N)
        self.pos = 0.0           # continuous carousel target
        self.scroll = 0.0        # eased current position, chases self.pos
        self.frame_i = 0
        self.msg = ""            # transient footer note (e.g. "Licensed!")
        self.msg_t = 0
        self.sfx = None
        self.entering = False    # secret-code (DVPet password) entry mode
        self.buf = ""

    def _refresh(self):
        """Recompute unlock state after a permanent change (purchase / password)."""
        prog = persistence.get_progress()
        owned = persistence.get_eggs_owned()
        self.prog = prog
        self.states = egg_mod.egg_states(prog, owned)
        self.unlocked = egg_mod.hatchable_eggs(prog, owned)
        self.hint = egg_mod.locked_hint(prog, owned)
        self.locked = sum(1 for st, _ in self.states.values() if st == "locked")
        self.wins = prog["wins"]
        self.carousel = self._build_carousel()
        self.n = len(self.carousel)
        self.i = max(0, min(self.i, self.n - 1))

    GOALS_SHOWN = 3            # sealed eggs on the carousel: only the nearest goals

    def _build_carousel(self):
        buyable = [i for i, (st, _) in sorted(self.states.items()) if st == "buyable"]
        locked = [i for i, (st, _) in sorted(self.states.items()) if st == "locked"]
        goals = sorted((i for i in locked
                        if egg_mod.unlock_ratio(i, self.prog) is not None),
                       key=lambda i: -egg_mod.unlock_ratio(i, self.prog))[:self.GOALS_SHOWN]
        return self.unlocked + buyable + goals

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

    @property
    def captures_text(self):
        return self.entering           # only swallow q-as-text while typing a secret code

    def key(self, k):
        if self.entering:
            return self._key_code(k)
        if k in ("c", "C"):                            # enter a secret code
            self.entering, self.buf = True, ""
            return None
        if k in ("right", "l", "down", "j"):
            self.pos += 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("left", "h", "up", "k"):
            self.pos -= 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("enter", "space"):
            idx = self.carousel[self.i]
            state, price = self.states.get(idx, ("owned", 0))
            if state == "locked":
                self.sfx = "error"
                prog_txt = egg_mod.unlock_progress(idx, self.prog)
                self._flash(f"Sealed — {prog_txt}" if prog_txt else "Sealed.")
                return None
            if state == "buyable":
                self.sfx = "error"
                self._flash(f"License: {price} bits — at the town shop.")
                return None
            return ("done", idx)                       # hatch the centred egg
        elif k == "escape":
            return ("done", None)                      # back out without choosing
        return None

    def _key_code(self, k):
        if k == "escape":
            self.entering, self.buf = False, ""
            return None
        if k == "enter":
            idx = egg_mod.redeem_password(self.buf)   # one matcher for both entries; it persists
            self.entering = False
            if idx is not None:
                self._refresh()
                if idx in self.unlocked:
                    self.i = self.unlocked.index(idx)
                    self.pos = self.scroll = float(self.i)
                self.sfx = "select"
                self._flash("Unlocked %s!" % egg_mod.hatch_name(idx))
            else:
                self.sfx = "error"
                self._flash("No such code.")
            self.buf = ""
            return None
        if k == "backspace":
            self.buf = self.buf[:-1]
        elif len(k) == 1 and k.isprintable():
            self.buf = (self.buf + k)[:24]
        return None

    def _egg(self, pos):
        return self.carousel[pos % self.n]

    def _frame(self, pos, center):
        idx = self._egg(pos)
        fr = egg_mod.record(idx)["frames"]
        if self.states.get(idx, ("owned", 0))[0] == "locked":
            return silhouette(fr[0])                   # a sealed egg keeps its shape only
        if center and self.scroll == self.pos:         # settled: idle wobble on the chosen egg
            return fr[(self.frame_i // 5) % 2] or fr[0]
        return fr[0]

    def _note(self, idx):
        state, price = self.states.get(idx, ("owned", 0))
        name = egg_mod.hatch_name(idx)
        if state == "locked":
            prog_txt = egg_mod.unlock_progress(idx, self.prog)
            return f"sealed — {prog_txt}" if prog_txt else "sealed"
        if state == "buyable":
            return f"{name} — license {price}b at the shop"
        if state == "temp":
            return "hatches: %s  (this gen only)" % name
        return "hatches: %s" % name

    def text(self):
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
        out.append_text(menu.note(self._note(self._egg(self.i))))
        if self.entering:
            out.append_text(menu.footer(f"code: {self.buf}_   ENTER ok  ESC cancel"))
        elif self.msg:
            out.append_text(menu.footer(self.msg))
        elif self.locked > 0 and self.hint and (self.frame_i // 30) % 3 == 1:
            out.append_text(menu.footer(f"{self.locked} locked · {self.hint}"))
        elif self.locked > 0 and (self.frame_i // 30) % 3 == 2:
            out.append_text(menu.footer("C: enter a secret code"))
        else:
            out.append_text(menu.footer("←→ browse   ENTER pick   ESC back"))
        return out
