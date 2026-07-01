"""Choose-your-egg: a smooth horizontal carousel of full-size egg sprites. The DM20
lets you freely pick which version's starter to hatch, so every egg is available —
no unlock/economy gating. ←→ glide, ENTER hatches the centred egg, ESC backs out."""
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
    def __init__(self, pet=None):
        self.pet = pet
        self.n = egg_mod.count()
        self.i = 0               # cursor opens on the first egg (position 1/N)
        self.pos = 0.0           # continuous carousel target
        self.scroll = 0.0        # eased current position, chases self.pos
        self.frame_i = 0
        self.sfx = None

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
            return ("done", self.i)                     # hatch the centred egg
        elif k == "escape":
            return ("done", None)                       # back out without choosing
        return None

    def _frame(self, pos, center):
        fr = egg_mod.record(pos % self.n)["frames"]
        if center and self.scroll == self.pos:          # settled: idle wobble on the chosen egg
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
        out.append_text(menu.footer("←→ browse   ENTER pick   ESC back"))
        return out
