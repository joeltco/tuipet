"""Town egg market (Joel 2026-07-21: "different towns sell different eggs --
all shops feel unique").  Each town stocks a DISTINCT band of digitama
(shop.town_egg_stock), shown as a grid of the REAL 8x8 egg thumbnails
(downsampled x2 -- the June 21 egg-select grid, restored) with a frame around
the selection.  ENTER buys the centred egg outright (bits -> egg_own); it
joins your hatch carousel.  Eggs still unlock FREE by condition elsewhere;
this is the road shortcut, priced.  ←→ ↑↓ browse, ENTER buy, ESC leave."""
from __future__ import annotations
from rich.text import Text
from . import egg as egg_mod, menu, persistence, shop
from .render import downsample
from .theme import LCD_ON, LCD_BG  # noqa: F401  (theme.apply propagation)

GW, GH = 40, 16              # grid pixel area (8 character rows)
PER_ROW, SHOWN = 4, 8        # 2 rows of 4 thumbnails


class TownEggPanel:
    def __init__(self, pet, town_id=0):
        self.pet = pet
        self.town_id = town_id
        self.stock = shop.town_egg_stock(town_id)      # egg indices this town sells
        self.owned = set(persistence.get_eggs_owned())
        self.n = len(self.stock)
        self.i = 0
        self.frame_i = 0
        self.sfx = None
        self.msg = "The town egg vendor — pick one up for the road."
        self.msg_t = 0

    def anim(self):
        self.frame_i += 1
        if self.msg_t > 0:
            self.msg_t -= 1

    def _flash(self, text):
        self.msg, self.msg_t = text, 26

    def strip(self):
        return menu.hints(("←→↑↓", "browse"), ("ENTER", "buy"), ("ESC", "leave"))

    # -- input -----------------------------------------------------------------
    def key(self, k):
        if not self.n:
            return ("done", None) if k == "escape" else None
        if k in ("right", "l"):
            self.i = (self.i + 1) % self.n
        elif k in ("left", "h"):
            self.i = (self.i - 1) % self.n
        elif k in ("down", "j"):
            self.i = (self.i + PER_ROW) % self.n
        elif k in ("up", "k"):
            self.i = (self.i - PER_ROW) % self.n
        elif k in ("enter", "space"):
            self._buy()
        elif k == "escape":
            return ("done", None)
        return None

    def _buy(self):
        idx = self.stock[self.i]
        if idx in self.owned:
            self._flash("You already own that egg.")
            self.sfx = "error"
            return
        price = shop.egg_price(idx)
        if not self.pet.spend_bits(price):
            self._flash(f"{price}b — not enough bits.")
            self.sfx = "error"
            return
        persistence.egg_own(idx)
        self.owned.add(idx)
        self.sfx = "reward"
        self._flash(f"Bought the {egg_mod.hatch_name(idx)} egg — it's on your carousel!")

    # -- render (the real 8x8 thumbnails, framed selection) --------------------
    def _grid(self):
        buf = [[0] * GW for _ in range(GH)]
        lo = max(0, min(self.i - SHOWN // 2, self.n - SHOWN)) if self.n > SHOWN else 0
        for j in range(SHOWN):
            pos = lo + j
            if pos >= self.n:
                break
            idx = self.stock[pos]
            thumb = downsample(egg_mod.record(idx)["frames"][0], 2)   # 16x16 /2 = 8x8
            ox, oy = (j % PER_ROW) * 10, (j // PER_ROW) * 8
            for y, line in enumerate(thumb):
                for x, ch in enumerate(line):
                    if ch == "1" and 0 <= oy + y < GH and 0 <= ox + x < GW:
                        buf[oy + y][ox + x] = 1
            if pos == self.i:                              # frame the selection
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
        if not self.n:
            out = menu.header("EGG MARKET", "0/0")
            out.append_text(menu.blanks(4))
            out.append_text(menu.note("This town's vendor is out of eggs."))
            out.append_text(menu.footer("ESC leave"))
            return out
        out = menu.header("EGG MARKET", f"{self.i + 1}/{self.n}")
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
        idx = self.stock[self.i]
        tag = "owned" if idx in self.owned else f"{shop.egg_price(idx)}b"
        line = self.msg if self.msg_t > 0 else f"{egg_mod.hatch_name(idx)} — {tag}"
        out.append_text(menu.note(line, tick=self.frame_i))
        out.append_text(menu.footer("←→ ↑↓ browse   ENTER buy   ESC leave"))
        return out
