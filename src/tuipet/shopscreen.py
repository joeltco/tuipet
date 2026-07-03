"""Shop — DVPet's HOME shop: separate Food and Item pages showing the day's
ROLLED roster (8 food / 12 item slots with real stock counts and sale prices),
plus tuipet's egg page.  The bag keeps its category tabs (Food / Medicine /
Toys / Chips / Special).  Renders in the LCD box."""
from __future__ import annotations
from . import data
from . import shop
from . import egg as egg_mod
from . import persistence
from .render import downsample

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
W = 38
IC_W, IC_ROWS = 10, 4                      # selected-item icon: auto-sized to fit, never clipped
SHOP_TABS = ["food", "item", "egg"]        # DVPet Food_Shop / Item_Shop (+ tuipet eggs)
BAG_CATEGORIES = ["food", "medicine", "toy", "chip"]
BAG_TABS = BAG_CATEGORIES + ["special"]
TAB_LABEL = {"food": "Food", "item": "Items", "egg": "Eggs", "medicine": "Medicine",
             "toy": "Toys", "chip": "Chips", "special": "Special"}


def _effect(e):
    parts = []
    for k, lbl in (("hunger", "food"), ("mood", "mood"), ("weight", "wt"), ("energy", "en"),
                   ("strength", "eff"), ("vaccine", "Va"), ("data", "Da"), ("virus", "Vi")):
        if e.get(k):
            parts.append("%s%+d" % (lbl, e[k]))
    if e.get("cured"):
        parts.append("cure")
    if e.get("healed"):
        parts.append("heal")
    return " ".join(parts) or "-"


class ShopPanel:
    def __init__(self, pet, start_mode="shop"):
        self.pet = pet
        self.mode = start_mode
        self.tab = 0
        self.cursor = 0
        self.msg = "Your bag." if start_mode == "bag" else "Welcome! Spend your bits."

    # ---- data ----
    def _tabs(self):
        return SHOP_TABS if self.mode == "shop" else BAG_TABS

    def _owned_by_cat(self, cat):
        out = []
        for k in self.pet.inventory:
            e = data.consumable_by_key(k)
            if e and data.shop_category(dict(e, key=k)) == cat:
                out.append(dict(e, key=k))
        out.sort(key=lambda e: e.get("price", 0))
        return out

    def _rows(self):
        cat = self._tabs()[self.tab]
        if self.mode == "shop":
            if cat == "egg":
                prog, owned = persistence.get_progress(), persistence.get_eggs_owned()
                return [egg_mod.shop_egg_entry(i, pr) for i, pr in egg_mod.buyable_eggs(prog, owned)]
            # the day's rolled roster (open_shop handles the daily reset + restock)
            out = []
            for slot in shop.open_shop(self.pet, cat == "food"):
                e = shop.entry(slot["key"])
                if e:
                    out.append(dict(e, stock=slot["stock"], sale=slot["sale"], _slot=slot))
            return out
        return self._owned_by_cat(cat)

    # ---- input ----
    def key(self, k):
        tabs = self._tabs()
        rows = self._rows()
        n = len(rows)
        if k in ("left", "h"):
            self.tab = (self.tab - 1) % len(tabs); self.cursor = 0
        elif k in ("right", "l"):
            self.tab = (self.tab + 1) % len(tabs); self.cursor = 0
        elif k in ("up", "k"):
            if n: self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j"):
            if n: self.cursor = (self.cursor + 1) % n
        elif k == "tab":
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.tab = 0; self.cursor = 0
            self.msg = "Your bag." if self.mode == "bag" else "Spend your bits."
        elif k in ("enter", "space") and rows:
            e = rows[min(self.cursor, n - 1)]
            if self.mode == "shop":
                bits0 = self.pet.bits
                if e.get("egg_idx") is not None:
                    self.msg = self._buy_egg(e)
                else:
                    self.msg = self.pet.buy_slot(e["_slot"])
                    e["stock"] = e["_slot"]["stock"]
                self.sfx = "reward" if self.pet.bits < bits0 else "error"   # bought vs can't-afford
            else:
                if (e.get("action") or "") in data.TRANSPORT_ACTIONS:
                    return ("done", ("transport", e["key"]))
                num0 = self.pet.num
                self.msg = self.pet.use_item(e["key"])
                if self.pet.num != num0:
                    return ("done", ("evolve", num0))
                if e["key"].startswith("f:") and self.pet.anim == "eat":
                    return ("done", ("eat", e["key"]))
        elif k == "r" and self.mode == "bag" and rows:
            self.msg = self.pet.sell(rows[min(self.cursor, n - 1)])
        elif k in ("escape", "o", "i"):     # o opens the shop, i opens the bag; both also close
            return ("done", self.msg)
        return None

    def _buy_egg(self, e):
        """Buy a buyable egg: spend bits, unlock it permanently (it then appears in
        the egg select). Eggs are not inventory items."""
        idx, price = e["egg_idx"], e["price"]
        if idx in persistence.get_eggs_owned():
            return "Already unlocked."
        if self.pet.bits < price:
            return "Not enough bits."
        self.pet.bits -= price
        persistence.egg_own(idx)
        return "Unlocked %s! Hatch it next egg." % e["name"]

    # ---- selected-item icon, auto-sized so it never clips ----
    def _icon(self, e):
        blank = [" " * IC_W] * IC_ROWS
        if e and e.get("egg_idx") is not None:
            fr = egg_mod.frames(e["egg_idx"])
        else:
            fr = data.load_icons().get(e["key"]) if e else None
        if not fr:
            return blank
        src = fr[0]
        sh = len(src)
        sw = max((len(r) for r in src), default=0)
        if not sw:
            return blank
        # downsample factor that fits BOTH the cell width (IC_W px) and height (IC_ROWS*2 px)
        factor = max(1, -(-sw // IC_W), -(-sh // (2 * IC_ROWS)))
        bm = downsample(src, factor)
        w = max((len(r) for r in bm), default=0)
        if not w:
            return blank
        if len(bm) % 2:
            bm.append("0" * w)
        lines = []
        for cy in range(0, len(bm), 2):
            t, b = bm[cy].ljust(w, "0"), bm[cy + 1].ljust(w, "0")
            seg = "".join("█" if (t[x] == "1" and b[x] == "1") else
                          ("▀" if t[x] == "1" else ("▄" if b[x] == "1" else " "))
                          for x in range(w))
            lines.append(seg.ljust(IC_W))      # w <= IC_W (factor guarantees it) -> pad, never cut
        return (lines + blank)[:IC_ROWS]

    # ---- render ----
    def text(self):
        tabs = self._tabs()
        rows = self._rows()
        n = len(rows)
        self.cursor = min(self.cursor, max(0, n - 1))

        out = menu.header("SHOP" if self.mode == "shop" else "BAG", "%db" % self.pet.bits)
        # tab bar
        bar = ""
        for i, t in enumerate(tabs):
            lbl = TAB_LABEL[t]
            bar += ("[%s]" % lbl) if i == self.tab else (" %s " % lbl)
        out.append(bar[:W].ljust(W) + "\n", style=INK_B)

        sel = rows[self.cursor] if rows else None
        icon = self._icon(sel) if sel else [" " * IC_W] * IC_ROWS
        tw = W - IC_W - 2
        if sel:
            if sel.get("egg_idx") is not None:
                info = [sel["name"][:tw], "%db" % sel["price"], "permanent egg",
                        "hatch it next egg"]
            else:
                owned = self.pet.inventory.get(sel["key"], 0)
                if self.mode == "shop":
                    price = ("SALE %db" % sel["sale"]) if sel.get("sale") else "%db" % sel["price"]
                    stock = "SOLD OUT" if sel.get("stock", 0) <= 0 else "stock x%d" % sel["stock"]
                    info = [sel["name"][:tw], price, "%s  own %d" % (stock, owned)]
                else:
                    val = shop.resell_price(sel)
                    info = [sel["name"][:tw], "x%d" % owned,
                            ("sell %db" % val) if val else "can't resell"]
                info.append(_effect(sel)[:tw])
            for r in range(IC_ROWS):
                tx = info[r] if r < len(info) else ""
                out.append(icon[r] + "  ", style=INK)
                out.append(tx[:tw] + "\n", style=INK_B if r == 0 else INK)
        else:
            # nothing selected == the tab is empty; the list below already prints the
            # context-aware empty label, so the icon panel stays quiet (one message, not two)
            out.append_text(menu.blanks(IC_ROWS))

        # item list for this tab
        vis = 3
        if not rows:
            if self._tabs()[self.tab] == "egg":
                empty = "(no eggs to buy yet)"
            else:
                empty = "(shelves empty — try tomorrow)" if self.mode == "shop" else "(none owned)"
            out.append_text(menu.row(empty)); shown = 1
        else:
            lo = max(0, min(self.cursor - vis // 2, n - vis))
            shown = 0
            for i in range(lo, min(lo + vis, n)):
                e = rows[i]
                if self.mode == "shop":
                    price = e.get("sale") or e.get("price", 0)
                    qty = "OUT" if e.get("stock", 0) <= 0 else "x%d" % e["stock"]
                    tag = "*" if e.get("sale") else " "
                    label = "%-18s %4s%s %5db" % (e["name"][:18], qty, tag, price)
                else:
                    label = "x%-2d %-26s" % (self.pet.inventory.get(e["key"], 0), e["name"][:26])
                out.append_text(menu.row(label, i == self.cursor)); shown += 1
        out.append_text(menu.blanks(vis - shown))
        out.append_text(menu.note(self.msg))
        if self.mode == "shop":
            out.append_text(menu.footer("←→ category ↑↓ pick ENTER buy TAB bag"))
        else:
            out.append_text(menu.footer("←→ category ENTER use R sell TAB shop"))
        return out
