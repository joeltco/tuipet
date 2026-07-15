"""Town visit — a rest stop with counters (the clone rebuild, 2026-07-15).

A town is a place: a FOOD counter and an ITEM counter (the one catalog
behind both), a SELL counter, and the road's rest.  The old town cups
retired with the tournament system.
"""
from __future__ import annotations
from . import data, grid, menu, shop, world
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY  # noqa: F401  (theme.apply propagation)

_MENU = (("food", "Food"), ("items", "Items"), ("sell", "Sell"),
         ("leave", "Leave"))


class TownPanel(menu.SubHost):
    def __init__(self, pet, town_id):
        self.pet = pet
        self.town = data.load_towns().get(town_id) or {"id": town_id}
        self.food_slots = shop.roll_town_shop(pet, self.town, True)
        self.item_slots = shop.roll_town_shop(pet, self.town, False)
        self.phase = "menu"
        self.cursor = 0
        self.sub = None
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
        if self.phase == "sell":
            return [k for k in sorted(self.pet.inventory) if shop.entry(k)]
        return []

    # ---- input ----
    def key(self, k):
        rows = self._rows()
        n = len(rows)
        if k in ("up", "k", "left", "h") and n:
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
            self.phase, self.cursor = key, 0
            self.msg = {"food": "The town's larder.",
                        "items": "The town's wares.",
                        "sell": "What will you part with?"}[key]
            return None
        if self.phase in ("food", "items") and rows:
            slot = rows[min(self.cursor, len(rows) - 1)]
            self.msg, self.sfx = shop.buy(p, slot)
            return None
        if self.phase == "sell" and rows:
            key = rows[min(self.cursor, len(rows) - 1)]
            e = shop.entry(key)
            if e:
                self.msg, self.sfx = shop.sell(p, e)
            return None
        return None

    # ---- render ----
    def _scene(self, placements):
        """A bare 12-row arena over the town's canonical backdrop."""
        from . import backgrounds as bgs
        bgimg = self.pet.background(file=bgs.TOWN) or self.pet.background()
        return menu.paint(placements, bgimg)

    def strip(self):
        if self.phase != "menu":
            verb = "sell" if self.phase == "sell" else "buy"
            return menu.hints(("↑↓", "pick"), ("ENTER", verb))
        parts = []
        for i, (key, label) in enumerate(_MENU):
            parts.append(f"[b]▸{label}[/]" if i == self.cursor
                         else f"[dim]{label}[/]")
        return " ".join(parts)

    def text(self):
        p = self.pet
        rows = self._rows()
        if self.phase == "menu":
            # the town LOBBY is a PLACE: the pet stands in the town scenery
            fr = data.bob_frame(p.num, self.frame_i)
            return self._scene([grid.center(grid.prep(fr, ph=24))])
        out = menu.header(world.town_name(self.town_id).upper(), f"{p.bits}b")
        sel = rows[min(self.cursor, len(rows) - 1)] if rows else None
        if sel is not None:
            e = sel if isinstance(sel, dict) else shop.entry(sel)
            out.append_text(menu.note(shop.effect_line(e)))
        else:
            out.append_text(menu.note("Nothing here."))

        def fmt(r, i):
            if self.phase == "sell":
                e = shop.entry(r)
                return "%-18s x%-2d  %4db" % (e["name"][:18],
                                              p.inventory.get(r, 0),
                                              shop.resell_price(e))
            return shop.slot_label(r)

        self.cursor = menu.list_window(out, rows, self.cursor, 6, fmt)
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
