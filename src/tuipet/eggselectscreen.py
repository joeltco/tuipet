"""Choose-your-egg: a smooth horizontal carousel of full-size egg sprites in the
display box. ←→ slide between eggs with an eased glide, neighbours peek in at the
edges, and ENTER hatches the centred egg."""
from __future__ import annotations
from . import egg as egg_mod
from . import menu
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
    def __init__(self):
        self.n = egg_mod.count()
        self.i = 0
        self.pos = 0.0           # continuous carousel target (may run past [0,n))
        self.scroll = 0.0        # eased current position, chases self.pos
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1
        diff = self.pos - self.scroll
        if abs(diff) < SNAP:
            self.scroll = self.pos
        else:
            self.scroll += diff * EASE

    def key(self, k):
        if k in ("right", "l", "down", "j"):
            self.pos += 1
            self.i = int(self.pos) % self.n
        elif k in ("left", "h", "up", "k"):
            self.pos -= 1
            self.i = int(self.pos) % self.n
        elif k in ("enter", "space"):
            return ("done", self.i)
        return None

    def _frame(self, idx, center):
        fr = egg_mod.record(idx % self.n)["frames"]
        if center and self.scroll == self.pos:       # settled: idle wobble on the chosen egg
            return fr[(self.frame_i // 5) % 2] or fr[0]
        return fr[0]

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
        out.append_text(menu.note(f"hatches: {egg_mod.hatch_name(self.i)}"))
        out.append_text(menu.footer("←→ browse      ENTER hatch"))
        return out
