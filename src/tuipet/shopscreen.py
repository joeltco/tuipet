"""The shop + bag screen (the DSprite item system, cloned from the v0.4.x
rebuild -- BASIC VPET 2026-07-16).

SHOP: the fixed catalog, tabbed by category; the HONORS board rides the
last tab (an economy, not an item, so it survives the item-system swap;
the digitama-licence shelf was cut 2026-07-17 -- eggs unlock by condition
only, never by purchase).  ENTER buys.  BAG: what you own, ENTER uses
it (Pet.use_item — a crest egg triggers the classic armor evolution), R
sells it back for half.  TAB flips between the two.
"""
from __future__ import annotations
import textwrap

from . import data
from . import shop
from . import persistence

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)
from . import menu


class ShopPanel:
    def __init__(self, pet, start_mode="shop", bag_only=False):
        self.pet = pet
        self.mode = start_mode
        self.bag_only = bag_only        # road bag: use/sell only
        self.tabs = shop.categories() + ["Honors"]
        self.tab = 0
        self.cursor = 0
        self.frame_i = 0
        self.sfx = None
        self.msg = "Your bag." if start_mode == "bag" else "Welcome! Spend your bits."

    def anim(self):
        self.frame_i += 1

    def strip(self):
        if self.mode == "shop":
            return menu.hints(("←→", "cat"), ("ENTER", "confirm"), ("TAB", "bag"))
        if self.bag_only:
            return menu.hints(("ENTER", "use"), ("R", "sell"), ("ESC", "out"))
        return menu.hints(("ENTER", "use"), ("R", "sell"), ("TAB", "shop"))

    # ---- data ----
    def _rows(self):
        if self.mode == "shop":
            cat = self.tabs[self.tab % len(self.tabs)]
            if cat == "Honors":
                # the HONORS board (prestige sink, 2026-07-14): cosmetic tamer
                # titles, profile-level (they survive generations); ENTER
                # buys, then toggles wearing
                owned = persistence.get_titles_owned()
                worn = persistence.get_title_worn()
                return [dict(t, title_id=t["id"], owned=t["id"] in owned,
                             worn=t["id"] == worn)
                        for t in data.load_titles()]
            return shop.shelf(cat)
        out = []
        for k, n in sorted(self.pet.inventory.items()):
            e = shop.entry(k)
            if e:
                out.append(dict(e, count=n))
        return out

    # ---- keys ----
    def _buy_title(self, e):
        """Buy an honor once, then ENTER toggles wearing it.  Purely cosmetic:
        the worn title rides the STATUS panel border and the lobby card."""
        tid, price = e["title_id"], e["price"]
        if tid in persistence.get_titles_owned():
            if persistence.get_title_worn() == tid:
                persistence.set_title_worn(-1)
                return "Put the %s title away." % e["name"]
            persistence.set_title_worn(tid)
            return "Wearing: %s." % e["name"]
        if not self.pet.spend_bits(price):
            return "Not enough bits."
        persistence.title_own(tid)
        persistence.set_title_worn(tid)
        return "Earned the honor: %s!" % e["name"]

    def _use(self, e):
        p = self.pet
        old = p.num
        out = p.use_item(e["key"])
        if p.num != old:                        # a crest egg fired the armor jump
            return ("done", ("evolve", old))
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
                if e.get("title_id") is not None:
                    self.msg = self._buy_title(e)
                    self.sfx = "confirm"
                else:
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
    def _row_note(self, sel):
        if sel.get("title_id") is not None:
            state = ("worn now" if sel.get("worn")
                     else "owned" if sel.get("owned") else "%db" % sel["price"])
            desc = textwrap.wrap(sel.get("desc") or "a tamer honor", 30)
            return f"{state} · {desc[0] if desc else ''}"
        return shop.effect_line(sel)

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
        out.append_text(menu.note(self._row_note(sel)))

        def fmt(e, i):
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    tag = "worn" if e.get("worn") else ("owned" if e.get("owned")
                                                        else f"{e['price']}b")
                    return f"{e['name'][:22]:<22} {tag:>7}"
                return f"{e['name'][:22]:<22} {e['price']:>6}b"
            return f"{e['name'][:22]:<22} x{e.get('count', 1)}"

        self.cursor = menu.list_window(out, rows, self.cursor, 6, fmt)
        out.append_text(menu.footer("←→ cat  ENTER " +
                                    ("buy" if self.mode == "shop" else "use") +
                                    "  TAB flip  ESC out"))
        return out
