"""Town visit — DVPet's town economies, reached mid-adventure.

A town is a place, not just a rest stop: its own FOOD and ITEM shops (the home
pool re-priced/re-stocked by the town's shopConsumable.csv overrides, rolled to
the town's inventory sizes), SELL counters gated by CanSellItems/CanSellFood,
and the town TOURNAMENT (Town.getTrophies): tournament_limit slots where 0-23
are hourly cups and anything past 23 -- the ForceTrophies pins -- is always
open.  Shops and cups roll fresh per visit (DVPet resets them daily)."""
from __future__ import annotations
from . import data, menu, shop, tournament
from .tournament import Tournament
from .battlescreen import BattlePanel
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM  # noqa: F401  (theme.apply propagation)

_MENU = (("food", "Food shop"), ("items", "Item shop"), ("sell", "Sell"),
         ("cups", "Tournament"), ("leave", "Leave town"))


class TownPanel(menu.SubHost):
    def __init__(self, pet, town_id):
        self.pet = pet
        self.town = data.load_towns().get(town_id) or {"id": town_id, "items_override": [],
                                                       "foods_override": [], "food_max": 8,
                                                       "item_max": 12, "can_sell_items": True,
                                                       "can_sell_food": True,
                                                       "tournament_limit": 0, "forced_trophies": []}
        self.food_slots = shop.roll_town_shop(pet, self.town, True)
        self.item_slots = shop.roll_town_shop(pet, self.town, False)
        self.cups = tournament.town_schedule(pet, self.town)
        self.phase = "menu"
        self.cursor = 0
        self.sub = None            # a cup match (BattlePanel)
        self.tourney = None
        self.frame_i = 0
        self.msg = "Welcome to town."

    # ---- plumbing ----
    def anim(self):
        if self.sub_anim():          # SubHost: delegate + sfx bubble
            return
        self.frame_i += 1

    def _rows(self):
        if self.phase == "menu":
            return list(_MENU)
        if self.phase == "food":
            return self.food_slots
        if self.phase == "items":
            return self.item_slots
        if self.phase == "sell":
            return [k for k in self.pet.inventory]
        if self.phase == "cups":
            return self.cups
        return []

    # ---- input ----
    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.tourney.record(bool(r[1] and r[1].won))
                self.sub = None
                if self.tourney.over:
                    self.msg = self.tourney.last
                    self.sfx = "champion" if self.tourney.champion else "lose"
                    self.tourney = None
                    self.phase = "cups"
            return None
        if self.tourney is not None:            # between cup rounds
            if k in ("space", "enter") and not self.tourney.over:
                self.sub = BattlePanel(self.pet, self.tourney.current_opponent())
            elif k == "escape":
                self.tourney = None
                self.phase = "cups"
            return None
        rows = self._rows()
        n = len(rows)
        if k in ("up", "k") and n:
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j") and n:
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space"):
            return self._activate(rows)
        elif k == "escape":
            if self.phase == "menu":
                return ("done", None)
            self.phase, self.cursor = "menu", 0
            self.msg = "Welcome to town."
        return None

    def _activate(self, rows):
        p = self.pet
        if self.phase == "menu":
            key = _MENU[self.cursor][0]
            if key == "leave":
                return ("done", None)
            if key == "sell" and not (self.town["can_sell_items"] or self.town["can_sell_food"]):
                self.msg = "This town doesn't buy."
                self.sfx = "error"
                return None
            self.phase, self.cursor = key, 0
            self.msg = {"food": "The town's larder.", "items": "The town's wares.",
                        "sell": "What will you part with?", "cups": "The town's cups."}[key]
            return None
        if self.phase in ("food", "items") and rows:
            slot = rows[min(self.cursor, len(rows) - 1)]
            bits0 = p.bits
            self.msg = p.buy_slot(slot)
            self.sfx = "reward" if p.bits < bits0 else "error"
            return None
        if self.phase == "sell" and rows:
            key = rows[min(self.cursor, len(rows) - 1)]
            e = data.consumable_by_key(key)
            if not e:
                return None
            is_food = key.startswith("f:")
            if not self.town["can_sell_food" if is_food else "can_sell_items"]:
                self.msg = "They won't buy that here."
                self.sfx = "error"
                return None
            self.msg = p.sell(dict(e, key=key, **self._town_econ(e)))
            return None
        if self.phase == "cups" and rows:
            i = min(self.cursor, len(rows) - 1)
            tid = rows[i]
            tr = tournament.trophy_by_id(tid) if tid >= 0 else None
            if tr is None:
                self.msg = "An empty ring."
                return None
            if not tournament.town_slot_open(p, i):
                self.msg = "That cup is closed — its hour hasn't come."
                self.sfx = "error"
                return None
            err = tournament.eligibility(p, tr)
            if err:
                self.msg = err
                self.sfx = "error"
                return None
            self.tourney = Tournament(p, tr)
            self.msg = self.tourney.last
            return None
        return None

    def _town_econ(self, e):
        """The town's shopConsumable override econ for a consumable (else {}) --
        so the sell counter pays the TOWN's resell rate, not home's."""
        ov = data.load_shop_overrides()
        pool = self.town["foods_override" if e["key"].startswith("f:") else "items_override"]
        for sid in pool:
            o = ov.get(sid)
            if o and o["consumable_id"] == e.get("id"):
                return {"resell_factor": o["resell_factor"], "price": o["price"]}
        return {}

    # ---- render ----
    def text(self):
        p = self.pet
        if self.sub is not None:
            return self.sub.text()
        if self.tourney is not None:
            t = self.tourney
            out = menu.header("TOWN CUP", f"{t.round_name} {t.round + 1}/3")
            out.append(f"  {t.name[:30]}\n", style=INK_B)
            opp = t.current_opponent()
            out.append(f"  vs {opp['name'][:22]} [{opp['attribute'][:2]}]\n", style=INK)
            out.append_text(menu.blanks(3))
            out.append_text(menu.note(t.last))
            out.append_text(menu.footer("SPACE fight   ESC forfeit"))
            return out
        rows = self._rows()
        out = menu.header(f"TOWN {self.town['id']}", f"{p.bits}b")

        def fmt(r, i):
            if self.phase == "menu":
                return r[1]
            if self.phase in ("food", "items"):
                e = shop.entry(r["key"]) or {"name": "?"}
                price = r.get("sale") or r.get("price", 0)
                qty = "OUT" if r.get("stock", 0) <= 0 else "x%d" % r["stock"]
                return "%-18s %4s%s %5db" % (e["name"][:18], qty,
                                             "*" if r.get("sale") else " ", price)
            if self.phase == "sell":
                e = data.consumable_by_key(r) or {"name": "?"}
                val = shop.resell_price(dict(e, key=r, **self._town_econ(dict(e, key=r))))
                return "%-18s x%-2d  %4db" % (e["name"][:18], p.inventory.get(r, 0), val)
            tr = tournament.trophy_by_id(r) if r >= 0 else None      # cups
            nm = tournament.trophy_label(tr)[:20] if tr else "\u2014"
            mark = ("\u00bb OPEN" if tournament.town_slot_open(p, i) and tr else
                    ("%02dh" % i if i <= 23 else ""))
            return "%-22s %s" % (nm, mark)

        self.cursor = menu.list_window(out, rows, self.cursor, 5, fmt)
        out.append_text(menu.note(self.msg))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
