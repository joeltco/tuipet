"""Choose-your-egg: a grid of egg thumbnails you scroll through, the selected
one framed, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import egg as egg_mod
from . import menu
from .render import downsample
from .theme import LCD_ON, LCD_BG

GW, GH = 40, 16          # grid pixel area (8 character rows)
PER_ROW, SHOWN = 4, 8    # 2 rows of 4 thumbnails


class EggSelectPanel:
    def __init__(self):
        self.n = egg_mod.count()
        self.i = 0

    def key(self, k):
        if k in ("right", "l"):
            self.i = (self.i + 1) % self.n
        elif k in ("left", "h"):
            self.i = (self.i - 1) % self.n
        elif k in ("down", "j"):
            self.i = (self.i + PER_ROW) % self.n
        elif k in ("up", "k"):
            self.i = (self.i - PER_ROW) % self.n
        elif k in ("enter", "space"):
            return ("done", self.i)
        return None

    def _grid(self):
        buf = [[0] * GW for _ in range(GH)]
        lo = max(0, min(self.i - SHOWN // 2, self.n - SHOWN)) if self.n > SHOWN else 0
        for j in range(SHOWN):
            idx = lo + j
            if idx >= self.n:
                break
            thumb = downsample(egg_mod.record(idx)["frames"][0], 2)  # 8x8
            ox, oy = (j % PER_ROW) * 10, (j // PER_ROW) * 8
            for y, line in enumerate(thumb):
                for x, ch in enumerate(line):
                    if ch == "1" and 0 <= oy + y < GH and 0 <= ox + x < GW:
                        buf[oy + y][ox + x] = 1
            if idx == self.i:                              # frame the selection
                x0, y0, x1, y1 = ox - 1, oy - 1, ox + 8, oy + 8
                for x in range(x0, x1 + 1):
                    for yy in (y0, y1):
                        if 0 <= yy < GH and 0 <= x < GW:
                            buf[yy][x] = 1
                for y in range(y0, y1 + 1):
                    for xx in (x0, x1):
                        if 0 <= y < GH and 0 <= xx < GW:
                            buf[y][xx] = 1
        return buf

    def text(self):
        out = menu.header("CHOOSE YOUR EGG", f"{self.i + 1}/{self.n}")
        buf = self._grid()
        bt = Text()
        for cy in range(GH // 2):
            ty, byy = cy * 2, cy * 2 + 1
            for cx in range(GW):
                tc = LCD_ON if buf[ty][cx] else LCD_BG
                bc = LCD_ON if buf[byy][cx] else LCD_BG
                bt.append("▀", style=f"{tc} on {bc}")
            bt.append("\n")
        out.append_text(bt)
        out.append_text(menu.note(f"hatches: {egg_mod.hatch_name(self.i)}"))
        out.append_text(menu.footer("←→ ↑↓ pick      ENTER start"))
        return out
