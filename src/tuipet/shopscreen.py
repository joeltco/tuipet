"""The shop + bag screen (the DSprite item system, cloned from the v0.4.x
rebuild -- BASIC VPET 2026-07-16; polish pass 2026-07-17).

SHOP: the fixed catalog, tabbed by PLAY order (everyday care first, the
relics last); the HONORS board rides the last tab (an economy, not an
item; the digitama-licence shelf was cut 2026-07-17 -- eggs unlock by
condition only, never by purchase).  ENTER buys.  BAG: what you own,
ENTER uses it (Pet.use_item — a crest egg triggers the classic armor
evolution), R sells it back for half.  TAB flips between the two.

Polish law (2026-07-17): the note line is a LIVE dossier -- effect, held
count, affordability shortfall, and a crest egg names the form that would
answer it RIGHT NOW (the same evolution.check the item runs).  Buy/sell
feedback flashes in the footer (it used to be beep-only -- self.msg was
never rendered anywhere); the sealed Digimental waves tease there on the
egg-carousel cadence.
"""
from __future__ import annotations

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
        for k, n in self.pet.inventory.items():
            e = shop.entry(k)
            if e:
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
        if k == "tab" and not self.bag_only:
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.cursor = 0
            self._flash("Your bag." if self.mode == "bag" else "Welcome back!")
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
    def _crest_note(self, key):
        """The crest egg's LIVE answer for this pet (cached per form+key --
        evolution.check walks the gate table)."""
        ck = (self.pet.num, key)
        if ck not in self._answers:
            self._answers[ck] = shop.crest_answer(self.pet, key)
        names = self._answers[ck]
        if not names:
            return "armor evolution · nothing answers it yet"
        return "armor evolution · answers now: " + " / ".join(names)

    def _row_note(self, sel):
        if sel.get("title_id") is not None:
            state = ("worn now" if sel.get("worn")
                     else "owned" if sel.get("owned") else "%db" % sel["price"])
            return f"{state} · {sel.get('desc') or 'a tamer honor'}"
        key = sel["key"]
        if str(key).startswith("egg_of_"):
            bits = [self._crest_note(key)]
        else:
            bits = [shop.effect_line(sel)]
        if self.mode == "shop":
            held = self.pet.inventory.get(key, 0)
            if held:
                bits.append(f"you hold {held}")
            short = sel["price"] - self.pet.bits
            if short > 0:
                bits.append(f"need {short}b more")
        else:
            bits.append(f"sells {shop.resell_price(sel)}b")
        return " · ".join(bits)

    def _footer(self):
        """Priority: the verdict flash > the sealed-wave tease (alternating,
        the egg-carousel cadence) > controls."""
        if self.msg_t > 0:
            return self.msg
        if (self.mode == "shop" and self.sealed
                and (self.frame_i // 40) % 2 == 1):
            return self.wave_hint
        if self.mode == "shop":
            return "←→ cat  ENTER buy  TAB bag  ESC out"
        if self.bag_only:
            return "ENTER use  R sell  ESC out"
        return "ENTER use  R sell  TAB shop  ESC out"

    def text(self):
        p = self.pet
        rows = self._rows()
        if self.mode == "shop":
            cat = self.tabs[self.tab % len(self.tabs)]
            pos = f"{(self.tab % len(self.tabs)) + 1}/{len(self.tabs)}"
            out = menu.header("SHOP", f"{cat} {pos} · {p.bits}b")
        else:
            out = menu.header("BAG", f"{sum(p.inventory.values())} items · {p.bits}b")
        if not rows:
            out.append_text(menu.blanks(2))
            out.append_text(menu.note("Nothing here." if self.mode == "shop"
                                      else "The bag is empty — the shop is a TAB away."))
            out.append_text(menu.blanks(3))
            out.append_text(menu.footer(self._footer()))
            return out
        self.cursor = min(self.cursor, len(rows) - 1)
        sel = rows[self.cursor]
        out.append_text(menu.note(self._row_note(sel), tick=self.frame_i))

        def fmt(e, i):
            if self.mode == "shop":
                if e.get("title_id") is not None:
                    tag = "worn" if e.get("worn") else ("owned" if e.get("owned")
                                                        else f"{e['price']}b")
                    return f"{e['name'][:22]:<22} {tag:>7}"
                held = self.pet.inventory.get(e["key"], 0)
                mark = f"x{held}" if held else ""
                return f"{e['name'][:19]:<19} {mark:>4} {e['price']:>6}b"
            return (f"{e['name'][:19]:<19} x{e.get('count', 1):<3}"
                    f" {shop.resell_price(e):>5}b")

        self.cursor = menu.list_window(out, rows, self.cursor, 6, fmt)
        out.append_text(menu.footer(self._footer()))
        return out
