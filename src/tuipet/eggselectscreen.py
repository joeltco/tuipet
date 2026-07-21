"""Choose-your-egg: a smooth horizontal carousel of full-size egg sprites.
Only eggs you can actually hatch appear here -- no sealed silhouettes, no goal
teasers (Joel 2026-07-12: "only the available eggs").  Eggs are earned through
play, full stop (the licence shop was cut 2026-07-17): meet a rule's condition
and the egg joins the carousel, permanently when the rule allows.
←→ glide, ENTER hatches the centred egg, ESC backs out."""
from __future__ import annotations
from . import backgrounds as _bgs
from . import data
from . import egg as egg_mod
from . import menu
from . import persistence
from .render import render_scene
from .theme import LCD_ON, LCD_BG  # noqa: F401  (theme.apply propagation)

COLS, ROWS = 40, 10           # scene area, 20px: the egg gets headroom --
#                               the in-LCD text block left (Joel bug report
#                               2026-07-19: "why does the lcd have menu like
#                               section under the egg, when theres perfectly
#                               fine status and message boxes?")
EGG_W = 16
CENTER = (COLS - EGG_W) // 2  # x_left that centres a 16px egg
SPACING = 24                  # px between adjacent eggs (neighbours peek ~4px)
WINDOW = 2                    # eggs drawn each side of centre
TEASE_BEAT = 120              # ticks per footer alternation leg (~12s): long
                              # enough for a FULL marquee pass of the widest
                              # eggUnlock desc (the old 40-tick beat clipped
                              # 32/46 hints mid-word -- tidy sweep 2026-07-18)
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
        """The message-box line: a fresh verdict, then the unlock tease on
        its beat, then the hints (carousel redo 2026-07-19: the LCD is pure
        scene now -- the dossier lives on the STATUS card, the words live
        HERE; the box's own marquee carries over-wide lines).  N advertises
        the egg guide -- the pick is permanent for the generation."""
        if self.msg:
            return self.msg
        if (self.locked > 0 and self.hint
                and self.frame_i % (2 * TEASE_BEAT) >= TEASE_BEAT):
            return f"{self.locked} more out there · {self.hint}"
        return menu.hints(("←→", "browse"), ("ENTER", "pick"), ("N", "guide"))

    def key(self, k):
        if k in ("right", "l", "down", "j"):
            self.pos += 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("left", "h", "up", "k"):
            self.pos -= 1
            self.i = int(self.pos) % self.n if self.n else 0
        elif k in ("pageup", "pagedown") and self.n:
            # the carousel is an EASED float, not a cursor -- feed pos the
            # leap and the existing snap/ease carries it (help audit
            # 2026-07-21).  It wraps like ←→ do, so no page_step clamp here.
            self.pos += 8 if k == "pagedown" else -8
            self.i = int(self.pos) % self.n
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
        """The hatch line (carousel polish 2026-07-18): a multi-target
        digitama keeps its mystery instead of wearing the EGG's label, and
        a species never raised on this profile earns its ★new badge --
        the collection game, surfaced where the choice happens."""
        state = self.states.get(idx, "owned")
        targets = egg_mod.hatch_targets(idx)
        if len(targets) > 1:
            name, new = "???  (two fates stir)", False
        else:
            name = egg_mod.hatch_name(idx)
            album = persistence.get_album()
            new = bool(targets) and data.canonical_num(targets[0]) not in album
        tail = "  (this gen only)" if state == "temp" else ""
        return "hatches: %s%s%s" % (name, "  ★new" if new else "", tail)

    def _scene_bg(self, idx):
        """The browsed egg's OWN backdrop behind the carousel -- the egg
        decides the home scene for the pet's whole life, so the choice
        shows you the home you're choosing (carousel polish 2026-07-18)."""
        frames = data.load_backgrounds().get(_bgs.scene_for_egg(idx))
        return frames[0] if frames else None

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
            # the neighbour PEEKS are wanted (Joel bug report 2026-07-19:
            # "what happened to seeing the edges of the previous and next
            # egg?" -- the 0.5.87 sliver cut went backwards; the cramp was
            # the in-LCD text block, now gone)
            placements.append((self._frame(v, d == 0), x, False))
        bgimg = self._scene_bg(self._egg(self.i))
        scene = render_scene(placements, COLS, ROWS,
                             menu.scene_ink(bgimg), LCD_BG, bgimg=bgimg)
        # the LCD is PURE SCENE (carousel redo 2026-07-19): the dossier
        # rides the STATUS card, the words ride the message strip -- the
        # boxes that exist for them (Joel's bug report, verbatim)
        out = menu.header("CHOOSE YOUR EGG", f"{self.i + 1}/{self.n}")
        out.append_text(scene)
        return out
