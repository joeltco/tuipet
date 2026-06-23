"""Shop — spend bits on foods/items and use them from the bag. Renders inside the
main display box (no pop-up screen)."""
from __future__ import annotations
from rich.text import Text
from . import data

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SEL
from . import menu
W = 38


def effect_summary(e):
    parts = []
    for k, lbl in (("hunger", "food"), ("mood", "mood"), ("weight", "wt"),
                   ("energy", "en"), ("strength", "eff"), ("vaccine", "Va"),
                   ("data", "Da"), ("virus", "Vi")):
        if e.get(k):
            parts.append(f"{lbl}{e[k]:+d}")
    if e.get("cured"):
        parts.append("cure")
    if e.get("healed"):
        parts.append("heal")
    return " ".join(parts) or "-"


class ShopPanel:
    def __init__(self, pet):
        self.pet = pet
        self.mode = "shop"
        self.cursor = 0
        self.msg = "Welcome! Spend your bits."

    def _rows(self):
        if self.mode == "shop":
            return data.load_shop()
        return [data.consumable_by_key(k) for k in self.pet.inventory]

    def key(self, k):
        rows = self._rows()
        if k in ("up", "k"):
            if rows:
                self.cursor = (self.cursor - 1) % len(rows)
        elif k in ("down", "j"):
            if rows:
                self.cursor = (self.cursor + 1) % len(rows)
        elif k == "tab":
            self.mode = "bag" if self.mode == "shop" else "shop"
            self.cursor = 0
            self.msg = "Your bag." if self.mode == "bag" else "Spend your bits."
        elif k in ("enter", "space"):
            if rows:
                e = rows[self.cursor]
                if self.mode == "shop":
                    self.msg = self.pet.buy(e)
                else:
                    if (e.get("action") or "") in data.TRANSPORT_ACTIONS:
                        return ("done", ("transport", e["key"]))   # open the warp picker
                    num0 = self.pet.num
                    self.msg = self.pet.use_item(e["key"])
                    if self.pet.num != num0:
                        return ("done", ("evolve", num0))    # item-triggered evolution
                    if e["key"].startswith("f:") and self.pet.anim == "eat":
                        return ("done", ("eat", e["key"]))   # fed a food -> watch the pet eat it
                    if self.cursor >= len(self.pet.inventory):
                        self.cursor = max(0, len(self.pet.inventory) - 1)
        elif k in ("escape", "o"):
            return ("done", self.msg)
        return None

    def _icon_lines(self, e):
        from .render import downsample
        fr = data.load_icons().get(e["key"]) if e else None
        if not fr:
            return []
        bm = downsample(fr[0], 3 if e["key"].startswith("f:") else 2)
        w = max((len(r) for r in bm), default=0)
        if not w:
            return []
        bm = [r.ljust(w, "0") for r in bm]
        if len(bm) % 2:
            bm.append("0" * w)
        lines = []
        for cy in range(0, len(bm), 2):
            top, bot = bm[cy], bm[cy + 1]
            seg = ""
            for x in range(w):
                t, b = top[x] == "1", bot[x] == "1"
                seg += "█" if (t and b) else ("▀" if t else ("▄" if b else " "))
            lines.append(seg)
        return lines

    def text(self):
        rows = self._rows()
        head = "SHOP" if self.mode == "shop" else "BAG"
        out = menu.header(head, f"{self.pet.bits}b")
        sel = rows[min(self.cursor, len(rows) - 1)] if rows else None
        icon = self._icon_lines(sel)
        info = []
        if sel:
            info = [sel["name"][:24],
                    (f"{sel['price']} bits" if self.mode == "shop"
                     else f"x{self.pet.inventory.get(sel['key'], 0)} owned"),
                    effect_summary(sel)[:24]]
        for r in range(3):
            ic = icon[r] if r < len(icon) else ""
            tx = info[r] if r < len(info) else ""
            out.append(f" {ic:<9} ", style=INK)
            out.append(f"{tx}\n", style=INK_B if r == 0 else INK)
        vis = 4
        if not rows:
            out.append_text(menu.row("(empty)"))
            shown = 1
        else:
            self.cursor = min(self.cursor, len(rows) - 1)
            lo = max(0, min(self.cursor - vis // 2, len(rows) - vis))
            shown = 0
            for i in range(lo, min(lo + vis, len(rows))):
                e = rows[i]
                if self.mode == "shop":
                    label = f"{e['price']:>4}b {e['name'][:24]}"
                else:
                    label = f"x{self.pet.inventory.get(e['key'],0)}  {e['name'][:26]}"
                out.append_text(menu.row(label, i == self.cursor))
                shown += 1
        out.append_text(menu.blanks(vis - shown))
        out.append_text(menu.note(self.msg))
        verb = "buy" if self.mode == "shop" else "use"
        other = "bag" if self.mode == "shop" else "shop"
        out.append_text(menu.footer(f"ENTER {verb}   TAB {other}   ESC out"))
        return out
