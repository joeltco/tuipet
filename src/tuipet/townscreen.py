"""Town visit — DVPet's town economies, reached mid-adventure.

A town is a place, not just a rest stop: its own FOOD and ITEM shops (the home
pool re-priced/re-stocked by the town's shopConsumable.csv overrides, rolled to
the town's inventory sizes), SELL counters gated by CanSellItems/CanSellFood,
and the town TOURNAMENT (Town.getTrophies): tournament_limit slots where 0-23
are hourly cups and anything past 23 -- the ForceTrophies pins -- is always
open.  Shops and cups roll fresh per visit (DVPet resets them daily)."""
from __future__ import annotations
from . import data, grid, menu, shop, tournament, world
from .tournament import Tournament
from .battlescreen import BattlePanel
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY  # noqa: F401  (theme.apply propagation)

# short labels: the errand strip lives in the 40-col #msg box (the old
# "Food shop   Item shop   Tournament..." row ran 58 cols and the live
# compositor clipped it mid-word -- box-clip audit 2026-07-04)
_MENU = (("food", "Food"), ("items", "Items"), ("eggs", "Eggs"), ("sell", "Sell"),
         ("cups", "Cups"), ("leave", "Leave"))


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
        from . import egg as _egg, persistence as _pst
        _prog, _owned = _pst.get_progress(), _pst.get_eggs_owned()
        self.egg_slots = [_egg.shop_egg_entry(i, pr)
                          for i, pr in _egg.eggs_for_town(town_id, _prog, _owned)]
        # the goal board: locked eggs this town would sell, with their unlock
        # hints -- shown dim after the buyable stock (egg design 2026-07-10)
        self.egg_slots += [_egg.locked_shop_entry(i, hint)
                           for i, hint in _egg.locked_town_eggs(town_id, _prog, _owned)]
        self.cups = tournament.town_schedule(pet, self.town)
        self.phase = "menu"
        self.cursor = 0
        self.sub = None            # a cup match (BattlePanel)
        self.tourney = None
        self.town_id = town_id
        self.frame_i = 0
        self.msg = world.town_greeting(town_id)

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
        if self.phase == "eggs":
            return self.egg_slots
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
                if not self.tourney.over:
                    self.tourney.record(False)      # forfeiting mid-cup is an elimination
                self.msg = self.tourney.last
                self.tourney = None
                self.phase = "cups"
            return None
        rows = self._rows()
        n = len(rows)
        if k in ("up", "k", "left", "h") and n:      # the lobby strip reads sideways
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j", "right", "l") and n:
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space"):
            return self._activate(rows)
        elif k == "escape":
            if self.phase == "menu":
                return ("done", None)
            self.phase, self.cursor = "menu", 0
            self.msg = world.town_greeting(self.town_id)
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
            if key in ("food", "items") and not shop.town_shop_open(p, self.town, key == "food"):
                self.msg = self._closed_msg(key == "food")
                self.sfx = "error"
                return None
            self.phase, self.cursor = key, 0
            self.msg = {"food": "The town's larder.", "items": "The town's wares.",
                        "eggs": world.town_known_for(self.town_id),
                        "sell": "What will you part with?",
                        "cups": "The town's cups."}[key]
            return None
        if self.phase in ("food", "items") and rows:
            slot = rows[min(self.cursor, len(rows) - 1)]
            self.msg, self.sfx = shop.buy(p, slot)
            return None
        if self.phase == "eggs" and rows:
            e = rows[min(self.cursor, len(rows) - 1)]
            self.msg, self.sfx = self._buy_egg(e)
            return None
        if self.phase == "sell" and rows:
            key = rows[min(self.cursor, len(rows) - 1)]
            if not data.consumable_by_key(key):
                return None
            is_food = key.startswith("f:")
            if not self.town["can_sell_food" if is_food else "can_sell_items"]:
                self.msg = "They won't buy that here."
                self.sfx = "error"
                return None
            self.msg = p.sell(self._sell_entry(key))
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
            self.tourney = Tournament(p, tr, field_bias=world.town_field(self.town_id))
            self.msg = self.tourney.last
            return None
        return None

    def _buy_egg(self, e):
        """Buy a themed town egg: spend bits, unlock it permanently (it appears in the
        egg select). Mirrors the home counter's buy."""
        from . import persistence
        if e.get("locked"):
            return ("Locked — %s." % e["hint"].rstrip("."), "error")
        idx, price = e["egg_idx"], e["price"]
        if idx in persistence.get_eggs_owned():
            return ("Already unlocked.", "error")
        if not self.pet.spend_bits(price):
            return ("Not enough bits.", "error")
        persistence.egg_own(idx)
        return ("Unlocked %s! Hatch it next egg." % e["name"], "reward")

    def _closed_msg(self, is_food):
        """'The food shop is shut. (opens 6:00)' -- or shut for the season when
        the span can never match an hour (the winter-market towns)."""
        name = "food shop" if is_food else "item shop"
        span = shop.town_shop_hours(self.pet, self.town, is_food)
        if span and span[0] <= 23:
            return f"The {name} is shut. (opens {span[0]}:00)"
        return f"The {name} is shut for {self.pet.season.lower()}."

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

    def _slot_entry(self, r):
        """A rolled shop slot merged over its consumable entry -- the slot's
        town-econ fields (price/sale/stock) win."""
        return dict(shop.entry(r["key"]) or {"name": "?"}, **r)

    def _sell_entry(self, key):
        """An owned consumable with the TOWN's override econ substituted."""
        e = dict(data.consumable_by_key(key) or {"name": "?"}, key=key)
        return dict(e, **self._town_econ(e))

    # ---- render ----
    def _scene(self, placements):
        """A bare 12-row arena over the town's canonical backdrop -- the WHOLE
        LCD (box-clip audit 2026-07-04: any in-LCD chrome overflowed the
        physical 12-row box; notes and errands ride the #msg strip instead)."""
        bg_h = self.town.get("bg_habitat")
        bgimg = self.pet.background(bg_h) if bg_h is not None else self.pet.background()
        return menu.paint(placements, bgimg)

    def strip(self):
        """The one-line chrome under the LCD: the errand picker in the lobby,
        the bout card between cup rounds (marquee'd by the app when long)."""
        if self.sub is not None:
            return ""
        if self.tourney is not None:
            # the bout card: round name + a marquee'd FIELD for the foe -- the
            # old free-length line always overflowed 40 cols, so the app's
            # safety-net marquee slid the key hints out of view (hint law:
            # live hints never move; ESC-forfeit rides the universal ESC)
            from .render import marquee
            t = self.tourney
            opp = t.current_opponent()
            name = marquee(opp["name"], 10, self.frame_i // 2)
            return (f"{t.round_name} vs [b]{name}[/] [dim]·[/] "
                    + menu.hints(("SPACE", "fight")))
        if self.phase != "menu":
            # the deeper pages carry in-LCD menus, but the message box still
            # pops the hint line (convention v0.2.399 -- the HOME shop's
            # identical icon view hints; the town shelves went silent)
            verb = {"food": "buy", "items": "buy", "eggs": "buy",
                    "sell": "sell", "cups": "enter"}.get(self.phase, "go")
            return menu.hints(("↑↓", "pick"), ("ENTER", verb))
        parts = []
        for i, (key, label) in enumerate(_MENU):
            shut = (key in ("food", "items")
                    and not shop.town_shop_open(self.pet, self.town, key == "food"))
            name = label + ("×" if shut else "")
            parts.append(f"[b]▸{name}[/]" if i == self.cursor else f"[dim]{name}[/]")
        return " ".join(parts)

    def text(self):
        p = self.pet
        if self.sub is not None:
            return self.sub.text()
        if self.tourney is not None:
            # the town cup interstitial: the faceoff SCENE fills the LCD; the
            # round card + controls ride the strip (they were clipped in-LCD)
            t = self.tourney
            opp = t.current_opponent()

            def fr(num):
                return data.bob_frame(num, self.frame_i)

            return self._scene(grid.faceoff(fr(p.num), fr(opp["num"]),
                                            left_mirror=True, right_mirror=False, ph=24))
        rows = self._rows()
        if self.phase == "menu":
            # the town LOBBY is a PLACE: the pet stands in the town's canonical
            # scenery (towns.csv TownBackgroundID), filling the LCD; the errand
            # strip reads below in the #msg box.
            fr = data.bob_frame(p.num, self.frame_i)
            return self._scene([grid.center(grid.prep(fr, ph=24))])
        out = menu.header(world.town_name(self.town_id).upper(), f"{p.bits}b")
        # the selected item's icon+info block -- the SAME icon view as the home
        # shop (the town shelves rendered nameplates only; refactor 2026-07-05)
        if self.phase in ("food", "items", "sell", "eggs"):
            sel = rows[min(self.cursor, len(rows) - 1)] if rows else None
            tw = menu.W - menu.IC_W - 2
            if sel is None:
                out.append_text(menu.blanks(menu.IC_ROWS))
            elif self.phase == "eggs":
                if sel.get("locked"):
                    menu.icon_info(out, menu.item_icon(sel),
                                   ["???", "locked", sel["hint"][:tw],
                                    (sel["hint"][tw:] or "")[:tw]])
                else:
                    menu.icon_info(out, menu.item_icon(sel),
                                   [sel["name"][:tw], "%db" % sel["price"],
                                    "permanent egg", "hatch it next egg"])
            elif self.phase == "sell":
                e = self._sell_entry(sel)
                menu.icon_info(out, menu.item_icon(e), shop.sell_info(p, e, tw))
            else:
                e = self._slot_entry(sel)
                menu.icon_info(out, menu.item_icon(e), shop.slot_info(p, e, tw))
            vis = 3                               # the home shop's window height
        else:
            vis = 5                               # cups: no icons, the taller list

        def fmt(r, i):
            if self.phase in ("food", "items"):
                return shop.slot_label(self._slot_entry(r))
            if self.phase == "sell":
                e = self._sell_entry(r)
                return "%-18s x%-2d  %4db" % (e["name"][:18], p.inventory.get(r, 0),
                                              shop.resell_price(e))
            if self.phase == "eggs":
                if r.get("locked"):
                    return "%-18s %7s" % ("???", "locked")
                return "%-18s %6db" % (r["name"][:18], r["price"])
            tr = tournament.trophy_by_id(r) if r >= 0 else None      # cups
            nm = tournament.trophy_label(tr)[:20] if tr else "\u2014"
            mark = ("★ OPEN" if i > 23 and tr and tr.get("field_req") else
                    ("\u00bb OPEN" if tournament.town_slot_open(p, i) and tr else
                     ("%02dh" % i if i <= 23 else "")))
            return "%-22s %s" % (nm, mark)

        self.cursor = menu.list_window(out, rows, self.cursor, vis, fmt)
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
