"""Adventure town hub: Shop, Eggs and Bag halfway through a run."""
from __future__ import annotations
from . import menu
from .theme import INK, INK_B, DIM, POS  # noqa: F401  (theme.apply propagation)

_MENU = (("shop", "Shop"), ("eggs", "Eggs"), ("bag", "Bag — eat, mend, sell"),
         ("leave", "Leave"))


# the session's last hub pick: a multi-town run re-entered every hub on
# "shop" (QOL sweep 2026-07-23).  Session-only, like the shop's memory.
_LAST_CURSOR = [0]


class TownPanel(menu.SubHost):
    def __init__(self, pet, town_id):
        # town_id is REQUIRED (audit 2026-07-25): None silently meant the
        # HOME counter -- full unrationed catalog, Honors tab, and town 0's
        # trophy -- in a constructor whose whole job is "this town"
        self.pet = pet
        self.town_id = town_id
        self.cursor = _LAST_CURSOR[0] % len(_MENU)
        self.sub = None
        self.frame_i = 0
        self.sfx = None
        # <= 38 cols: the hub body clips hard, no marquee (sheet audit
        # 2026-07-21 caught the old line dying mid-word at "resupply, o")
        self.msg = "A town — rest, eat, mend, shop."

    def anim(self):
        if self.sub_anim():            # the shop owns the clock
            return
        self.frame_i += 1

    # -- input ----------------------------------------------------------------
    def key(self, k):
        if self.sub_key(k, self._sub_done):
            return None
        if self.pet.dead:
            # a lethal bag item (the poison mushroom is a real road find):
            # the verdict has spoken on the strip; any key closes the hub
            # so the run can end and the memorial take over (audit 2026-07-25)
            return ("done", None)
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(_MENU)
            _LAST_CURSOR[0] = self.cursor
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(_MENU)
            _LAST_CURSOR[0] = self.cursor
        elif k in ("enter", "space"):
            key = _MENU[self.cursor][0]
            if key == "shop":
                from .shopscreen import ShopPanel
                # the real shop layout, serving THIS map's tier stock,
                # local prices, and the day's deal (shops arc 2026-07-21)
                self.sub = ShopPanel(self.pet, town_id=self.town_id)
            elif key == "eggs":
                from .shopscreen import ShopPanel
                # this town's DISTINCT egg band, on the SHOP's own Eggs tab
                # (shops-look-the-same 2026-07-22: the one-off thumbnail
                # grid made the town's egg counter a different UI from
                # every other shelf -- one shop family now, one layout)
                self.sub = ShopPanel(self.pet, town_id=self.town_id,
                                     start_tab="Eggs")
            elif key == "bag":
                from .shopscreen import ShopPanel
                # the real bag (use / sell back), same layout as home --
                # paying THIS town's rates: demand goods fetch 70%, its own
                # stock a pittance (buy-low/sell-high, shops arc 2026-07-21)
                self.sub = ShopPanel(self.pet, start_mode="bag", bag_only=True,
                                     town_id=self.town_id)
            elif key == "leave":
                return ("done", None)            # back to the road
        elif k in ("escape",):
            return ("done", None)
        return None

    def _sub_done(self, result):
        """The shop/bag closed.  The payloads _after_shop PLAYS at home (eat
        fx, evolution strobe, item scripts) have no LCD here, so the town
        SPEAKS them -- SHOW-FLOW: a show plays or speaks (audit 2026-07-25:
        a road-town poison mushroom killed with the strip reading 'Anything
        else?', and a crest egg swapped the species in silence)."""
        r = result if isinstance(result, tuple) else ()
        kind = r[0] if r else None
        if kind == "eat" and len(r) > 2 and r[2]:
            self.msg = str(r[2])
        elif kind == "item_use" and len(r) > 3 and r[3]:
            self.msg = str(r[3])
        elif kind == "evolve":
            self.msg = f"...evolved into {self.pet.name}!"
        elif kind == "inherit":
            self.msg = "The memory settles in."
        else:
            self.msg = "Anything else?"          # a plain browse -> back to the menu

    # -- render ---------------------------------------------------------------
    def strip(self):
        if self.sub is not None:
            return self.sub.strip()
        return menu.hints(("↑↓", "pick"), ("ENTER", "go"), ("ESC", "leave"))

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        out = menu.header("TOWN", "")
        menu.list_window(out, list(_MENU), self.cursor, 6, lambda row, _i: row[1])
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick   ENTER go   ESC leave"))
        return out
