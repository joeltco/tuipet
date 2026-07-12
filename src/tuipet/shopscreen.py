"""The shop screen: separate Food and Item pages showing the day's rolled
roster (8 food / 12 item slots with real stock counts and sale prices), plus
the egg page.  The bag keeps its category tabs (Food / Medicine / Toys / Chips
/ Special).  Renders in the LCD box."""
from __future__ import annotations
from . import data
from . import shop
from . import egg as egg_mod
from . import persistence

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
W = 38
IC_W, IC_ROWS = menu.IC_W, menu.IC_ROWS    # the shared selected-item icon cell
SHOP_TABS = ["food", "item", "egg"]        # the food, item and egg pages
BAG_CATEGORIES = ["food", "medicine", "toy", "chip"]
BAG_TABS = BAG_CATEGORIES + ["special"]
TAB_LABEL = {"food": "Food", "item": "Items", "egg": "Eggs", "medicine": "Medicine",
             "toy": "Toys", "chip": "Chips", "special": "Special"}


class ShopPanel:
    def __init__(self, pet, start_mode="shop", bag_only=False):
        self.pet = pet
        self.mode = start_mode
        self.bag_only = bag_only        # road bag: use/sell only, no TAB to the shop
        self.tab = 0
        self.cursor = 0
        if start_mode == "bag":
            self.msg = "Your bag."
        elif not shop.home_shop_open(pet):
            self.msg = "Closed for the night — back at 6:00."
        else:
            self.msg = "Welcome! Spend your bits."

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10)."""
        if self.mode == "shop":
            return menu.hints(("←→", "cat"), ("ENTER", "buy"), ("TAB", "bag"))
        if self.bag_only:               # the road bag can't reach the shop
            return menu.hints(("←→", "cat"), ("ENTER", "use"), ("R", "sell"))
        return menu.hints(("←→", "cat"), ("ENTER", "use"),
                          ("R", "sell"), ("TAB", "shop"))

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

    def _shelves_closed(self):
        """The home food/item shelves keep trading hours (6:00-23:00); outside
        them the shutters are down.  The egg page is your licence counter and
        the bag is yours -- neither ever closes."""
        return (self.mode == "shop" and self._tabs()[self.tab] in ("food", "item")
                and not shop.home_shop_open(self.pet))

    def _rows(self):
        cat = self._tabs()[self.tab]
        if self.mode == "shop":
            if cat == "egg":
                # buyable eggs now live in the themed TOWN shops; the home counter is
                # for hatching your owned/starter eggs + password redemption
                return []
            if self._shelves_closed():
                return []                  # shutters down: nothing to browse or buy
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
        if getattr(self, "pw_mode", False):
            # password redemption: type the code, ENTER redeems
            self.pw_text, act = egg_mod.code_key(self.pw_text, k)
            if act == "submit":
                idx = egg_mod.redeem_password(self.pw_text)
                self.msg = ("Password accepted — %s egg unlocked!" % egg_mod.hatch_name(idx)
                            if idx is not None else "Nothing answers that password.")
                self.sfx = "reward" if idx is not None else "error"
                self.pw_mode, self.pw_text = False, ""
                self.captures_text = False
            elif act == "cancel":
                self.pw_mode, self.pw_text = False, ""
                self.captures_text = False
                self.msg = "Never mind."
            self.msg = ("Password: %s_" % self.pw_text) if self.pw_mode else self.msg
            return None
        if k == "p" and self.mode == "shop" and self._tabs()[self.tab] == "egg":
            self.pw_mode, self.pw_text = True, ""
            self.captures_text = True       # the app's global q-quit yields to typing
            self.msg = "Password: _"
            return None
        if k in ("left", "h"):
            self.tab = (self.tab - 1) % len(tabs); self.cursor = 0
        elif k in ("right", "l"):
            self.tab = (self.tab + 1) % len(tabs); self.cursor = 0
        elif k in ("up", "k"):
            if n: self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j"):
            if n: self.cursor = (self.cursor + 1) % n
        elif k == "tab" and not self.bag_only:
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.tab = 0; self.cursor = 0
            self.msg = "Your bag." if self.mode == "bag" else "Spend your bits."
        elif k in ("enter", "space") and rows:
            e = rows[min(self.cursor, n - 1)]
            if self.mode == "shop":
                if e.get("egg_idx") is not None:
                    bits0 = self.pet.bits
                    self.msg = self._buy_egg(e)
                    self.sfx = "reward" if self.pet.bits < bits0 else "error"
                else:
                    self.msg, self.sfx = shop.buy(self.pet, e["_slot"])
                    e["stock"] = e["_slot"]["stock"]
            else:
                if (e.get("action") or "") in data.TRANSPORT_ACTIONS:
                    # the bag handed the app a ride BEFORE any pet gate -- an
                    # EGG could board Zone Transport (egg-shop audit 2026-07-05);
                    # mirror the adventure gates: travel needs a walker, awake
                    if self.pet.stage in ("Egg", "Fresh"):
                        self.msg = "Too young to travel."
                        return None
                    if self.pet.asleep:
                        self.msg = "zzz... asleep"
                        return None
                    if getattr(self.pet, "away", False):
                        # transports leave from HOME (the structural doctrine,
                        # transport audit 2026-07-06) -- a mid-adventure ride
                        # would corrupt the adv_loc mailbox (road-keys 2026-07-07)
                        self.msg = "Transports leave from home."
                        return None
                    return ("done", ("transport", e["key"]))
                if (e.get("action") or "") == "Inherit":
                    mem0 = dict(getattr(self.pet, "digimemory", {}) or {})
                    self.msg = self.pet.use_item(e["key"])
                    if mem0 and not self.pet.digimemory:   # redeemed -> the ceremony
                        return ("done", ("inherit", mem0))
                    return None                            # refused / blank: stay in the bag
                num0 = self.pet.num
                self.msg = self.pet.use_item(e["key"])
                if (e.get("unlocks_food") or e.get("unlocks_item")) and "got a" in self.msg:
                    self.sfx = "mischief"      # soundConfig unlockConsumable -> mischief.wav
                if self.pet.num != num0:
                    # an ItemEvol (Digimental) carries its key: the app plays
                    # the item-evolve parade plays before the strobe
                    ik = e["key"] if (e.get("action") or "") == "ItemEvol" else None
                    return ("done", ("evolve", num0, ik))
                if self.pet.anim == "toilet":
                    # a manual toilet visit: the app plays poopToilet
                    return ("done", ("toilet", e["key"]))
                if e["key"].startswith("f:") and self.pet.anim == "eat":
                    return ("done", ("eat", e["key"]))
                if (data.shop_category(dict(e)) == "toy"
                        and self.pet.anim == "happy"):
                    # each toy plays ITS OWN script from the itemfx table:
                    # Jump keeps the trampoline hop; Idling (the Futon) plays
                    # nothing beyond its care effect; the rest run their own fx
                    from . import itemfx
                    act = (e.get("action") or "").strip()
                    if act in itemfx.SCRIPTS:
                        return ("done", ("item_use", e["key"], act))
                    if act == "Jump":
                        return ("done", ("play", e["key"]))
                    return None if act in itemfx.NO_FX else ("done", ("play", e["key"]))
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
        if not self.pet.spend_bits(price):
            return "Not enough bits."
        persistence.egg_own(idx)
        return "Unlocked %s! Hatch it next egg." % e["name"]

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
        tw = W - IC_W - 2
        if sel:
            if sel.get("egg_idx") is not None:
                info = [sel["name"][:tw], "%db" % sel["price"], "permanent egg",
                        "hatch it next egg"]
            elif self.mode == "shop":
                info = shop.slot_info(self.pet, sel, tw)
            else:
                info = shop.sell_info(self.pet, sel, tw)
            menu.icon_info(out, menu.item_icon(sel), info)
        elif self._shelves_closed():
            # a clean shuttered plate drawn in the icon cell -- the old sprite
            # smeared into noise at 10x4, so tuipet draws its own sign
            o0, c0 = shop.HOME_HOURS
            plate = ["\u256d" + "\u2500" * (IC_W - 2) + "\u256e",
                     "\u2502 CLOSED \u2502",
                     "\u2502 \u2500\u2500\u2500\u2500\u2500\u2500 \u2502",
                     "\u2570" + "\u2500" * (IC_W - 2) + "\u256f"]
            menu.icon_info(out, plate,
                           ["Shop's closed", "for the night", "",
                            "Open %d:00\u2013%d:00" % (o0, c0)])
        else:
            # nothing selected == the tab is empty; the list below already prints the
            # context-aware empty label, so the icon panel stays quiet (one message, not two)
            out.append_text(menu.blanks(IC_ROWS))

        # item list for this tab
        if self._shelves_closed():
            empty = "(the shutters are down)"
        elif self._tabs()[self.tab] == "egg":
            empty = "(no eggs to buy \u2014 P for a password)"
        else:
            empty = "(shelves empty \u2014 try tomorrow)" if self.mode == "shop" else "(none owned)"

        def fmt(e, i):
            if self.mode == "shop":
                return shop.slot_label(e)
            return "x%-2d %-26s" % (self.pet.inventory.get(e["key"], 0), e["name"][:26])

        self.cursor = menu.list_window(out, rows, self.cursor, 3, fmt, empty=empty)
        out.append_text(menu.note(self.msg))
        if self.mode == "shop":
            foot = "←→ tab ↑↓ ENTER buy P password TAB bag" if tabs[self.tab] == "egg" \
                else "←→ category ↑↓ pick ENTER buy TAB bag"
            out.append_text(menu.footer(foot))
        else:
            out.append_text(menu.footer("←→ category ENTER use R sell TAB shop"))
        return out
