"""The shop + bag screen (the DSprite item system, cloned from the v0.4.x
rebuild -- BASIC VPET 2026-07-16; polish pass 2026-07-17).

LAYOUT (the classic v0.5.0 grammar, restored on Joel's call 2026-07-17
"where are the tabs you had like before?"): a visible TAB BAR under the
header ([Food] Items  Eggs  Honors, active bracketed), then the selected
entry's ICON + four info rows (menu.icon_info -- the one layout every
icon view shares), then the list, then the footer.  The DSprite catalog
groups into the classic four tabs; the bag keeps its own bar (Food /
Items / Eggs over what you own).  ENTER buys / uses (a crest egg fires
the classic armor evolution), R sells back half, TAB flips shop<->bag.

Art law: consumables have NO DSprite icon rips (vitems carries only
id/name/price/category), so their icon cell stays quiet -- never
substitute lookalike art.  The crest eggs DO show their real ripped
DVPet Digimental icons via the same Pet._CREST_IDS identity the item
flow uses; the Honors crest is the drawn text plate (allowed: a plate,
not art -- the CLOSED-sign precedent).

Info rows are a LIVE dossier -- price with held count / shortfall,
effect, and a crest egg names the form that would answer it RIGHT NOW
(the same evolution.check the item runs).  Buy/sell verdicts flash in
the footer (they were beep-only before -- self.msg was never rendered);
the sealed Digimental waves tease there on the egg-carousel cadence.
"""
from __future__ import annotations
import textwrap

from . import data
from . import shop
from . import persistence

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)
from . import menu

# the classic tab grammar (v0.5.0): the DSprite categories fold into the
# four tabs the shop always had.  Honors is shop-only (titles never bag).
GROUPS = (("Food", ("Food", "Fruit")),
          ("Items", ("Care", "Evolution", "Medical")),
          ("Eggs", (shop.ARMOR_CATEGORY,)),
          ("Honors", None))

# the honors crest: a drawn text plate, like the old CLOSED sign -- a
# title has no item sprite and hand-drawing ART is banned; a plate isn't
_HONOR_PLATE = ["╭" + "─" * (menu.IC_W - 2) + "╮",
                "│ HONORS │",
                "│ ✦✦✦✦✦✦ │",
                "╰" + "─" * (menu.IC_W - 2) + "╯"]


class ShopPanel:
    def __init__(self, pet, start_mode="shop", bag_only=False):
        self.pet = pet
        self.mode = start_mode
        self.bag_only = bag_only        # road bag: use/sell only
        self.tab = 0
        self.cursor = 0
        self.frame_i = 0
        self.sfx = None
        self.msg = ""                   # transient footer flash (last verdict)
        self.msg_t = 0
        self.sealed, self.wave_hint = shop.wave_status()
        self._answers = {}              # (num, key) -> crest_answer cache
        self._flash("Your bag." if start_mode == "bag"
                    else "Welcome! Spend your bits.")

    def anim(self):
        self.frame_i += 1
        if self.msg_t > 0:
            self.msg_t -= 1

    def _flash(self, text):
        if text:
            self.msg, self.msg_t = text, 26

    def strip(self):
        if self.mode == "shop":
            return menu.hints(("←→", "tab"), ("ENTER", "confirm"), ("TAB", "bag"))
        if self.bag_only:
            return menu.hints(("ENTER", "use"), ("R", "sell"), ("ESC", "out"))
        return menu.hints(("ENTER", "use"), ("R", "sell"), ("TAB", "shop"))

    # ---- data ----
    def _tabs(self):
        """Shop: the classic four.  Bag: the goods tabs over what you own."""
        if self.mode == "shop":
            return [g for g, _ in GROUPS]
        return [g for g, cats in GROUPS if cats is not None]

    def _rows(self):
        tabs = self._tabs()
        name = tabs[self.tab % len(tabs)]
        cats = dict(GROUPS)[name]
        if self.mode == "shop":
            if cats is None:            # the HONORS board (prestige sink)
                owned = persistence.get_titles_owned()
                worn = persistence.get_title_worn()
                return [dict(t, title_id=t["id"], owned=t["id"] in owned,
                             worn=t["id"] == worn)
                        for t in data.load_titles()]
            return [e for e in shop.catalog() if e["category"] in cats]
        out = []
        for k, n in self.pet.inventory.items():
            e = shop.entry(k)
            if e and e["category"] in cats:
                out.append(dict(e, count=n))
        out.sort(key=lambda e: e["name"])      # by the name you SEE, not the key
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
            self._flash("You don't have that.")
            self.sfx = "error"
        elif out == "":
            self._flash(f"{e['name']} does nothing here.")
        else:
            self._flash(out)
            self.sfx = "confirm"
        return None

    def key(self, k):
        rows = self._rows()
        n = len(rows)
        tabs = self._tabs()
        if k == "tab" and not self.bag_only:
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.tab, self.cursor = 0, 0
            self._flash("Your bag." if self.mode == "bag" else "Welcome back!")
            return None
        if k in ("left", "h"):
            self.tab = (self.tab - 1) % len(tabs)
            self.cursor = 0
        elif k in ("right", "l"):
            self.tab = (self.tab + 1) % len(tabs)
            self.cursor = 0
        elif k in ("up", "k") and n:
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j") and n:
            self.cursor = (self.cursor + 1) % n
        elif k in ("enter", "space") and n:
            e = rows[self.cursor % n]
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    self._flash(self._buy_title(e))
                    self.sfx = "confirm"
                else:
                    msg, self.sfx = shop.buy(self.pet, e)
                    self._flash(msg)
            else:
                return self._use(e)
        elif k == "r" and self.mode == "bag" and n:
            e = rows[self.cursor % n]
            msg, self.sfx = shop.sell(self.pet, e)
            self._flash(msg)
        elif k in ("escape", "o", "i"):
            return ("done", self.msg if self.sfx else None)
        return None

    # ---- render ----
    def _crest_answer(self, key):
        """The crest egg's LIVE answer for this pet (cached per form+key --
        evolution.check walks the gate table)."""
        ck = (self.pet.num, key)
        if ck not in self._answers:
            self._answers[ck] = shop.crest_answer(self.pet, key)
        return self._answers[ck]

    def _icon(self, sel):
        """The icon cell: honors wear the plate; DSprite consumables have no
        rips -> the cell stays quiet.  (The Eggs tab never comes here: it
        renders the REAL armor-egg sprite full-size in its own scene --
        shrinking the 15x17 linework into the 10x8 cell reduced all eleven
        eggs to one identical blob, tried both thresholds 2026-07-17.)"""
        if sel.get("title_id") is not None:
            return _HONOR_PLATE
        return menu.item_icon(sel)

    def _armor_egg(self, key):
        """The crest egg's REAL ripped sprite (armorEggs.png, indexed by the
        _CREST_IDS identity the item flow uses), or None."""
        iid = self.pet._CREST_IDS.get(str(key), -1)
        bank = data.load_armor_eggs()
        if 0 <= iid - 15 < len(bank):
            return bank[iid - 15]
        return None

    def _info(self, sel, tw):
        """The four info rows beside the icon -- the LIVE dossier."""
        if sel.get("title_id") is not None:
            state = ("worn now" if sel.get("worn")
                     else "owned" if sel.get("owned") else "%db" % sel["price"])
            desc = textwrap.wrap(sel.get("desc") or "a tamer honor", tw)[:2]
            return [sel["name"][:tw], state] + desc + [""] * (2 - len(desc))
        key = str(sel["key"])
        if self.mode == "shop":
            held = self.pet.inventory.get(key, 0)
            short = sel["price"] - self.pet.bits
            price = "%db" % sel["price"]
            if held:
                price += " · hold x%d" % held
            elif short > 0:
                price += " · short %db" % short
        else:
            price = "x%d · sells %db" % (sel.get("count", 1),
                                         shop.resell_price(sel))
        if key.startswith("egg_of_"):
            names = self._crest_answer(key)
            tail = (("→ " + " / ".join(names))[:tw] if names
                    else "nothing answers yet")
            return [sel["name"][:tw], price[:tw], "armor evolution", tail]
        eff = textwrap.wrap(shop.effect_line(sel), tw)[:2]
        return [sel["name"][:tw], price[:tw]] + eff + [""] * (2 - len(eff))

    def _footer(self):
        """Priority: the verdict flash > the sealed-wave tease (alternating,
        the egg-carousel cadence) > controls."""
        if self.msg_t > 0:
            return self.msg
        if (self.mode == "shop" and self.sealed
                and (self.frame_i // 40) % 2 == 1):
            return self.wave_hint
        if self.mode == "shop":
            return "←→ tab  ENTER buy  TAB bag  ESC out"
        if self.bag_only:
            return "ENTER use  R sell  ESC out"
        return "ENTER use  R sell  TAB shop  ESC out"

    def _bar_text(self, tabs):
        bar = ""
        for i, t in enumerate(tabs):
            bar += ("[%s]" % t) if i == (self.tab % len(tabs)) else (" %s " % t)
        return bar[:menu.W].ljust(menu.W) + "\n"

    def _eggs_text(self, rows):
        """The Eggs tab: the REAL armor-egg sprite FULL-SIZE in an egg-select
        style scene (Joel 2026-07-17: real egg sprites -- the 10x8 icon cell
        blobbed them, so they show whole instead).  ↑↓ browses, the marquee
        note carries the dossier."""
        p = self.pet
        from . import grid
        from .render import render_scene
        title = "SHOP" if self.mode == "shop" else "BAG"
        right = (f"{p.bits}b" if self.mode == "shop"
                 else f"{sum(p.inventory.values())} items · {p.bits}b")
        out = menu.bar(title, right)          # 1-line header: the scene needs the row
        out.append(self._bar_text(self._tabs()), style=INK_B)
        cols, rows_n = 40, 8
        if not rows:
            out.append_text(menu.blanks(rows_n // 2))
            out.append_text(menu.note("no relics here — earn them out there"
                                      if self.mode == "shop" else "(none owned)"))
            out.append_text(menu.blanks(rows_n - rows_n // 2))
            out.append_text(menu.footer(self._footer()))
            return out
        sel = rows[self.cursor]
        egg = self._armor_egg(sel["key"])
        placements = []
        if egg:
            egg = grid.fit_band(egg, rows_n * 2)
            w = max(len(r) for r in egg)
            placements.append((egg, (cols - w) // 2, False))
        scene = render_scene(placements, cols, rows_n,
                             menu.scene_ink(None), LCD_BG)
        out.append_text(scene)
        out.append("\n")
        pos = f"{self.cursor + 1}/{len(rows)}"
        info = self._info(sel, 99)
        note = " · ".join([f"{sel['name']} {pos}"] + [x for x in info[1:] if x])
        out.append_text(menu.note(note, tick=self.frame_i))
        out.append_text(menu.footer(self._footer()))
        return out

    def text(self):
        p = self.pet
        tabs = self._tabs()
        rows = self._rows()
        self.cursor = min(self.cursor, max(0, len(rows) - 1))
        if tabs[self.tab % len(tabs)] == "Eggs":
            return self._eggs_text(rows)
        if self.mode == "shop":
            out = menu.header("SHOP", f"{p.bits}b")
        else:
            out = menu.header("BAG", f"{sum(p.inventory.values())} items · {p.bits}b")
        # the classic tab bar: active bracketed, the rest breathing
        out.append(self._bar_text(tabs), style=INK_B)

        tw = menu.W - menu.IC_W - 2
        if rows:
            sel = rows[self.cursor]
            menu.icon_info(out, self._icon(sel), self._info(sel, tw))
        else:
            out.append_text(menu.blanks(menu.IC_ROWS))

        empty = ("(shelves empty)" if self.mode == "shop"
                 else "(none of these owned)")
        def fmt(e, i):
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    if e.get("worn"):
                        return "%-18s %7s" % (("★ " + e["name"])[:18], "worn")
                    if e.get("owned"):
                        return "%-18s %7s" % (e["name"][:18], "owned")
                    return "%-18s %6db" % (e["name"][:18], e["price"])
                held = self.pet.inventory.get(e["key"], 0)
                mark = ("x%d" % held) if held else ""
                return "%-18s %3s %6db" % (e["name"][:18], mark, e["price"])
            return "%-18s x%-3d %5db" % (e["name"][:18], e.get("count", 1),
                                         shop.resell_price(e))

        self.cursor = menu.list_window(out, rows, self.cursor, 4, fmt,
                                       empty=empty)
        out.append_text(menu.footer(self._footer()))
        return out
