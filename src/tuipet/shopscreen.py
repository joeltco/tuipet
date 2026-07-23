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
substitute lookalike art.  The crest eggs show the small Digimental
item glyphs DVPet ITSELF draws (drawEvolutionInventory's Items-sheet
icon, via the Pet._CREST_IDS identity the item flow uses) -- Joel
2026-07-18: "8x8 item icons, like how the rest of the shop is"; the
armorEggs.png ghost-egg scene was tried and REMOVED same day (fan-
authored, unused even by DVPet).  The Honors crest is the drawn text
plate (allowed: a plate, not art -- the CLOSED-sign precedent).

Info rows are a LIVE dossier -- price with held count / shortfall,
effect, and a crest egg names the form that would answer it RIGHT NOW
(the same evolution.check the item runs).  Buy/sell verdicts flash in
the footer (they were beep-only before -- self.msg was never rendered);
the sealed Digimental waves tease there on the egg-carousel cadence.
"""
from __future__ import annotations
import textwrap

from rich.text import Text

from . import data
from . import shop
from . import persistence

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)
from . import menu

# the classic tab grammar (v0.5.0): the DSprite categories fold into the
# four tabs the shop always had.  Honors is shop-only (titles never bag).
GROUPS = (("Food", ("Food", "Fruit")),
          ("Items", ("Care", "Evolution", "Medical", "Toy", "Adventure")),
          ("Eggs", (shop.ARMOR_CATEGORY,)),
          ("Honors", None))

# the honors crest: a drawn text plate, like the old CLOSED sign -- a
# title has no item sprite and hand-drawing ART is banned; a plate isn't
_HONOR_PLATE = ["╭" + "─" * (menu.IC_W - 2) + "╮",
                "│ HONORS │",
                "│ ✦✦✦✦✦✦ │",
                "╰" + "─" * (menu.IC_W - 2) + "╯"]


# where you left off, per session: the HOME shop/bag reopen on the last
# (tab, cursor) instead of Food/row 0 every restock run (QOL 2026-07-23).
# Session-only by design -- a fresh launch starts fresh.
_LAST_POS = {}


class ShopPanel:
    def __init__(self, pet, start_mode="shop", bag_only=False, town_id=None,
                 start_tab=None):
        self.pet = pet
        self.mode = start_mode
        self.bag_only = bag_only        # road bag: use/sell only
        self.town = town_id             # a TOWN counter: authored stock, local
        #                                 prices, the day's deal, demand resale
        #                                 (shops arc 2026-07-21); None = home
        self.tab = 0
        if start_tab is not None:       # e.g. the town hub's Eggs door
            tabs = self._tabs()
            if start_tab in tabs:
                self.tab = tabs.index(start_tab)
        self.cursor = 0
        # per-tab cursor memory for this visit: tabbing away and back no
        # longer dumps you at row 0 (QOL 2026-07-23)
        self._tab_pos = {}
        self._mode_pos = {}             # (tab, cursor) per shop/bag side
        if town_id is None and start_tab is None and not bag_only:
            self.tab, self.cursor = _LAST_POS.get(start_mode, (0, 0))
        self._retarget = False          # the stack under the cursor just
        #                                 emptied: eat ONE act-press so a
        #                                 mash can't hit the neighbor
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
        """Verdict flash > the sealed-wave tease > mode-true hints -- the
        egg-carousel grammar (round 31: the old in-LCD footer doubled the
        keys the strip carried and squeezed the shelf; its row feeds the
        list now).  The #msg hud marquees any over-wide tease."""
        if self.msg_t > 0:
            return self.msg
        if (self.mode == "shop" and self.sealed
                and (self.frame_i // 40) % 2 == 1):
            return self.wave_hint
        if self.mode == "shop":
            tabs = self._tabs()
            act = "wear" if tabs[self.tab % len(tabs)] == "Honors" else "buy"
            return menu.hints(("←→", "tab"), ("ENTER", act),
                              ("TAB", "bag"), ("ESC", "out"))
        if self.bag_only:
            return menu.hints(("ENTER", "use"), ("R", "sell"), ("ESC", "out"))
        return menu.hints(("ENTER", "use"), ("R", "sell"),
                          ("TAB", "shop"), ("ESC", "out"))

    # ---- data ----
    def _tabs(self):
        """Shop: the classic four; a TOWN counter carries its two authored
        shelves + the digitama band as an EGGS tab (shops-look-the-same
        2026-07-22: the market rode a separate one-off grid screen while
        the home shop had a tab -- one shop family now; honors stay a home
        prestige).  Bag: the goods tabs over what you own."""
        if self.mode == "shop":
            if self.town is not None:
                return ["Food", "Items", "Eggs"]
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
            if self.town is not None:      # the town counter: authored stock
                if name == "Eggs":         # the digitama band, shop-row shape
                    return shop.town_egg_rows(self.town)
                return [e for e in shop.town_stock(self.town, pet=self.pet)
                        if e["category"] in cats]
            return [e for e in shop.catalog() if e["category"] in cats]
        out = []
        for k, n in self.pet.inventory.items():
            e = shop.entry(k)
            if e and e["category"] in cats:
                e = dict(e, count=n)
                if self.town is not None:  # local demand: the town's OWN offer
                    e["sell_price"] = shop.town_sell_price(k, self.town)
                out.append(e)
        out.sort(key=lambda e: e["name"])      # by the name you SEE, not the key
        return out

    # ---- keys ----
    def _buy_title(self, e):
        """Buy an honor once, then ENTER toggles wearing it.  Purely cosmetic:
        the worn title rides the STATUS panel border and the lobby card.
        Returns (msg, sfx) like shop.buy -- the old flat confirm played the
        happy chirp on "Not enough bits." too (round 31)."""
        tid, price = e["title_id"], e["price"]
        if tid in persistence.get_titles_owned():
            if persistence.get_title_worn() == tid:
                persistence.set_title_worn(-1)
                return "Put the %s title away." % e["name"], "confirm"
            persistence.set_title_worn(tid)
            return "Wearing: %s." % e["name"], "confirm"
        if not self.pet.spend_bits(price):
            return "Not enough bits.", "error"
        persistence.title_own(tid)
        persistence.set_title_worn(tid)
        return "Earned the honor: %s!" % e["name"], "confirm"

    def _use(self, e):
        p = self.pet
        old = p.num
        key = e["key"]
        # the chip clears its payload on success; the inherit fx needs it
        mem = dict(p.digimemory) if key == "digimemory" else None
        out = p.use_item(key)
        if p.num != old:                        # a crest egg fired the armor jump
            return ("done", ("evolve", old))
        if out is None:
            self._flash("You don't have that.")
            self.sfx = "error"
            return None
        if out == "":
            self._flash(f"{e['name']} does nothing here.")
            return None
        from .petbase import _Refused
        refused = isinstance(out, _Refused)      # kept the item: no show plays
        if not refused and key in shop.FOOD_KEYS:
            # the bag CLOSES and the meal plays on the LCD through its own
            # DVPet strip -- the eat fx the feed menu rides (TUIPET catalog
            # 2026-07-18; the _after_shop route was waiting for this)
            return ("done", ("eat", shop.ICON_KEYS.get(key, "f:0"), out))
        if not refused and key in shop.TOY_SCRIPTS:
            # the toy's SHOW: its canon itemfx script on the main LCD
            return ("done", ("item_use", shop.ICON_KEYS[key],
                             shop.TOY_SCRIPTS[key], out))
        if not refused and key == "digimemory" and mem:
            # the heir redeems the ancestor: the bag closes and the canon
            # inherit fx plays on the LCD (_after_shop's waiting route)
            return ("done", ("inherit", mem))
        self._flash(out)
        self.sfx = "error" if refused else "confirm"   # a kept item is a NO
        return None

    def _remember_pos(self):
        """Session memory: the HOME shop/bag reopen where you left off."""
        if self.town is None and not self.bag_only:
            _LAST_POS[self.mode] = (self.tab, self.cursor)

    def _check_retarget(self, e):
        """After a bag use/sell: if that emptied the stack, the list shifts
        under the cursor -- arm the one-press guard so a mashed R/ENTER
        can't silently hit the neighbor (QOL 2026-07-23)."""
        key = e.get("key")
        if key is not None and all(r.get("key") != key for r in self._rows()):
            self._retarget = True

    def key(self, k):
        rows = self._rows()
        n = len(rows)
        tabs = self._tabs()
        if k in ("left", "h", "right", "l", "up", "k", "down", "j",
                 "pageup", "pagedown", "tab"):
            self._retarget = False           # the player re-aimed on purpose
        if k == "tab" and not self.bag_only:
            self._tab_pos[(self.mode, self.tab)] = self.cursor
            self._mode_pos[self.mode] = (self.tab, self.cursor)
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.tab, self.cursor = self._mode_pos.get(self.mode, (0, 0))
            self._flash("Your bag." if self.mode == "bag" else "Welcome back!")
            return None
        if k in ("left", "h"):
            self._tab_pos[(self.mode, self.tab)] = self.cursor
            self.tab = (self.tab - 1) % len(tabs)
            self.cursor = self._tab_pos.get((self.mode, self.tab), 0)
        elif k in ("right", "l"):
            self._tab_pos[(self.mode, self.tab)] = self.cursor
            self.tab = (self.tab + 1) % len(tabs)
            self.cursor = self._tab_pos.get((self.mode, self.tab), 0)
        elif k in ("up", "k") and n:
            self.cursor = (self.cursor - 1) % n
        elif k in ("down", "j") and n:
            self.cursor = (self.cursor + 1) % n
        elif k in ("pageup", "pagedown"):     # the shelf/bag leap (help audit 2026-07-21)
            self.cursor = menu.page_step(self.cursor, n, 5, k)
        elif k in ("enter", "space") and n:
            e = rows[self.cursor % n]
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    msg, self.sfx = self._buy_title(e)
                    self._flash(msg)
                elif e.get("egg_idx") is not None:
                    msg, self.sfx = shop.town_egg_buy(self.pet, e["egg_idx"])
                    self._flash(msg)
                elif self.town is not None:
                    msg, self.sfx = shop.town_buy(self.pet, e)
                    self._flash(msg)
                else:
                    msg, self.sfx = shop.buy(self.pet, e)
                    self._flash(msg)
            else:
                if self._retarget:
                    self._retarget = False
                    self._flash(f"now on {e['name']} — press again")
                    self.sfx = "cancel"
                    return None
                r = self._use(e)
                if r is not None:
                    self._remember_pos()   # a toy/inherit exit closes the bag
                    return r
                self._check_retarget(e)
        elif k == "r" and self.mode == "bag" and n:
            e = rows[self.cursor % n]
            if self._retarget:
                self._retarget = False
                self._flash(f"now on {e['name']} — press again")
                self.sfx = "cancel"
                return None
            msg, self.sfx = shop.sell(self.pet, e)
            self._flash(msg)
            self._check_retarget(e)
        elif k in ("escape", "o", "i"):
            # carry a still-live verdict home (round 31: keying on self.sfx
            # was dead -- the app consumes sfx every frame, so buy-then-
            # leave never showed its verdict)
            self._remember_pos()
            return ("done", self.msg if self.msg_t > 0 else None)
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
        """The icon cell: honors wear the plate; a crest egg shows the crest
        GLYPH DVPet itself draws for the Digimental (drawEvolutionInventory's
        Items-sheet icon, via the _CREST_IDS identity the item flow uses);
        DSprite consumables have no rips -> the cell stays quiet.  (The
        armorEggs.png ghost eggs were tried and REMOVED 2026-07-18 -- fan-
        authored, unused even by DVPet, and Joel wasn't digging them: "too
        complicated for a basic vpet".  Canon display only now.)"""
        if sel.get("title_id") is not None:
            return _HONOR_PLATE
        key = str(sel.get("key", ""))
        if key.startswith("egg_of_"):
            iid = self.pet._CREST_IDS.get(key, -1)
            fr = data.load_icons().get("i:%d" % iid) if iid >= 0 else None
            if fr:
                return menu.icon_cell(fr[0])
        ak = shop.ICON_KEYS.get(key)
        if ak:
            fr = data.load_icons().get(ak)
            if fr:
                return menu.icon_cell(fr[0])
        return menu.item_icon(sel)

    def _info(self, sel, tw):
        """The four info rows beside the icon -- the LIVE dossier."""
        if sel.get("title_id") is not None:
            state = ("worn now" if sel.get("worn")
                     else "owned" if sel.get("owned") else "%db" % sel["price"])
            desc = textwrap.wrap(sel.get("desc") or "a tamer honor", tw)[:2]
            return [sel["name"][:tw], state] + desc + [""] * (2 - len(desc))
        if sel.get("egg_idx") is not None:     # the town digitama band
            state = "owned" if sel.get("owned") else "%db" % sel["price"]
            return [sel["name"][:tw], state,
                    "a digitama, bought outright"[:tw],
                    "joins your hatch carousel"[:tw]]
        key = str(sel["key"])
        if self.mode == "shop":
            held = self.pet.inventory.get(key, 0)
            short = sel["price"] - self.pet.bits
            price = "%db" % sel["price"]
            if self.town is not None and sel.get("left", 1) <= 0:
                price += " · sold out today"
            elif sel.get("deal"):
                price += " · DEAL! (was %db)" % sel.get("base_price", 0)
            elif held:
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

    def _bar_text(self, tabs):
        bar = ""
        for i, t in enumerate(tabs):
            bar += ("[%s]" % t) if i == (self.tab % len(tabs)) else (" %s " % t)
        return bar[:menu.W].ljust(menu.W) + "\n"

    def text(self):
        p = self.pet
        tabs = self._tabs()
        rows = self._rows()
        self.cursor = min(self.cursor, max(0, len(rows) - 1))
        if self.mode == "shop":
            out = menu.header("SHOP", f"{p.bits}b")
        else:
            # count what the shelves can SHOW: a key the catalog doesn't know
            # (a newer build's item riding cloud sync past the bag heal) used
            # to count in the header while appearing on NO tab -- "8 items"
            # over 5 visible (deep-state sweep 2026-07-22)
            held = sum(v for k, v in p.inventory.items() if k in shop.CATALOG)
            out = menu.header("BAG", f"{held} items · {p.bits}b")
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
        def dim_if_short(label, e, i):
            """Affordability at a GLANCE: an unaffordable row renders dim
            across the whole shelf, not just as the selected row's "short
            Xb" dossier tail (QOL 2026-07-23).  The selected row keeps the
            ▸ inversion -- its dossier already spells out the shortfall."""
            if i != self.cursor and e.get("price", 0) > self.pet.bits:
                return Text(("  " + label)[:menu.W].ljust(menu.W) + "\n",
                            style=DIM)
            return label

        def fmt(e, i):
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    # blank mark column so the price column holds still when
                    # tabbing Food/Items/Eggs <-> Honors (menu polish 2026-07-21)
                    if e.get("worn"):
                        return "%-18s %3s %7s" % (("★ " + e["name"])[:18], "", "worn")
                    if e.get("owned"):
                        return "%-18s %3s %7s" % (e["name"][:18], "", "owned")
                    return dim_if_short(
                        "%-18s %3s %6db" % (e["name"][:18], "", e["price"]), e, i)
                if e.get("egg_idx") is not None:     # digitama: owned/price
                    if e.get("owned"):
                        return "%-18s %3s %7s" % (e["name"][:18], "", "owned")
                    return dim_if_short(
                        "%-18s %3s %7s" % (e["name"][:18], "",
                                           ("%6db" % e["price"]).strip()), e, i)
                held = self.pet.inventory.get(e["key"], 0)
                mark = ("x%d" % held) if held else ""
                nm = ("▾" + e["name"][:17]) if e.get("deal") else e["name"][:18]
                if self.town is not None and e.get("left", 1) <= 0:
                    return "%-18s %3s %6s" % (nm, mark, "out")
                return dim_if_short(
                    "%-18s %3s %6db" % (nm, mark, e["price"]), e, i)
            return "%-18s x%-3d %5db" % (e["name"][:18], e.get("count", 1),
                                         shop.resell_price(e))

        # 5 shelf rows: the old footer's row (round 31) -- header 2 + tab
        # bar 1 + dossier 4 + list 5 = the 12-row LCD exactly
        self.cursor = menu.list_window(out, rows, self.cursor, 5, fmt,
                                       empty=empty)
        out.right_crop(1)          # the last row sheds its newline (the
        #                            footer convention: 12 rows, no 13th
        #                            empty split element)
        return out
