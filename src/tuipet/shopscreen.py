"""The shop + bag screen (the clone rebuild, 2026-07-15).

SHOP: the fixed catalog, tabbed by category; ENTER buys.  BAG: what you
own, ENTER uses it (Pet.use_item — a crest egg from the bag triggers an
armor evolution), R sells it back for half.  TAB flips between the two.
"""
from __future__ import annotations
from . import shop
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)
from . import menu


class ShopPanel:
    def __init__(self, pet, start_mode="shop", bag_only=False):
        self.pet = pet
        self.mode = start_mode
        self.bag_only = bag_only        # road bag: use/sell only
        self.tabs = shop.categories()
        self.tab = 0
        self.cursor = 0
        self.frame_i = 0
        self.sfx = None
        self.msg = "Your bag." if start_mode == "bag" else "Welcome! Spend your bits."

    def anim(self):
        self.frame_i += 1

    def strip(self):
        if self.mode == "shop":
            return menu.hints(("←→", "cat"), ("ENTER", "buy"), ("TAB", "bag"))
        if self.bag_only:
            return menu.hints(("ENTER", "use"), ("R", "sell"), ("ESC", "out"))
        return menu.hints(("ENTER", "use"), ("R", "sell"), ("TAB", "shop"))

    # ---- data ----
    def _rows(self):
        if self.mode == "shop":
            return shop.shelf(self.tabs[self.tab % len(self.tabs)])
        out = []
        for k, n in sorted(self.pet.inventory.items()):
            e = shop.entry(k)
            if e:
                out.append(dict(e, count=n))
        return out

    # ---- keys ----
    def _use(self, e):
        p = self.pet
        if e["category"] == shop.ARMOR_CATEGORY:
            old = p.num
            if p.item_evolve(e["key"]) is not None:
                p.take_item(e["key"])
                return ("done", ("evolve", old))
            self.msg = f"{p.name} can't use {e['name']} right now."
            self.sfx = "error"
            return None
        out = p.use_item(e["key"])
        if out is None:
            self.msg = "You don't have that."
            self.sfx = "error"
        elif out == "":
            self.msg = f"{e['name']} does nothing here."
        else:
            self.msg = out
            self.sfx = "confirm"
        return None

    def key(self, k):
        rows = self._rows()
        n = len(rows)
        if k == "tab" and not self.bag_only:
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.cursor = 0
            self.msg = "Your bag." if self.mode == "bag" else "Welcome back!"
            return None
        if k in ("left", "h") and self.mode == "shop":
            self.tab = (self.tab - 1) % len(self.tabs)
            self.cursor = 0
        elif k in ("right", "l") and self.mode == "shop":
            self.tab = (self.tab + 1) % len(self.tabs)
            self.cursor = 0
        elif k in ("up", "k") and n:
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j") and n:
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space") and n:
            e = rows[self.cursor % n]
            if self.mode == "shop":
                self.msg, self.sfx = shop.buy(self.pet, e)
            else:
                return self._use(e)
        elif k == "r" and self.mode == "bag" and n:
            e = rows[self.cursor % n]
            self.msg, self.sfx = shop.sell(self.pet, e)
        elif k in ("escape", "o", "i"):
            return ("done", self.msg if self.sfx else None)
        return None

    # ---- render ----
    def text(self):
        p = self.pet
        rows = self._rows()
        if self.mode == "shop":
            cat = self.tabs[self.tab % len(self.tabs)]
            out = menu.header("SHOP", f"{cat} · {p.bits}b")
        else:
            out = menu.header("BAG", f"{sum(p.inventory.values())} items · {p.bits}b")
        if not rows:
            out.append_text(menu.blanks(2))
            out.append_text(menu.note("Nothing here." if self.mode == "shop"
                                      else "The bag is empty."))
            out.append_text(menu.blanks(3))
            out.append_text(menu.footer("ESC out"))
            return out
        self.cursor = min(self.cursor, len(rows) - 1)
        sel = rows[self.cursor]
        out.append_text(menu.note(shop.effect_line(sel)))

        def fmt(e, i):
            if self.mode == "shop":
                return f"{e['name'][:22]:<22} {e['price']:>6}b"
            return f"{e['name'][:22]:<22} x{e.get('count', 1)}"

        self.cursor = menu.list_window(out, rows, self.cursor, 6, fmt)
        out.append_text(menu.footer("←→ cat  ENTER " +
                                    ("buy" if self.mode == "shop" else "use") +
                                    "  TAB flip  ESC out"))
        return out
