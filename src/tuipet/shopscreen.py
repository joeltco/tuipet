"""Shop — spend bits on foods/items and use them from the bag. Renders inside the
main display box (no pop-up screen)."""
from __future__ import annotations
from rich.text import Text
from . import data

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
SEL = f"bold #9bbc0f on {LCD_ON}"
DIM = f"#5a7a1a on {LCD_BG}"
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
                    self.msg = self.pet.use_item(e["key"])
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
        out = Text()
        head = "SHOP" if self.mode == "shop" else "BAG"
        out.append(f"{head}   Bits: {self.pet.bits}\n", style=INK_B)
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
        out.append("-" * W + "\n", style=DIM)
        if not rows:
            out.append("  (empty)\n", style=DIM)
            empties = 5
        else:
            self.cursor = min(self.cursor, len(rows) - 1)
            vis = 5
            lo = max(0, min(self.cursor - vis // 2, len(rows) - vis))
            shown = 0
            for i in range(lo, min(lo + vis, len(rows))):
                e = rows[i]
                sel_row = i == self.cursor
                mark = ">" if sel_row else " "
                if self.mode == "shop":
                    line = f"{mark}{e['price']:>5}b {e['name'][:20]}"
                else:
                    line = f"{mark} x{self.pet.inventory.get(e['key'],0)} {e['name'][:22]}"
                out.append(line[:W] + "\n", style=SEL if sel_row else INK)
                shown += 1
            empties = vis - shown
        for _ in range(empties):
            out.append("\n", style=INK)
        out.append(f"{self.msg[:W]}\n", style=INK_B)
        verb = "buy" if self.mode == "shop" else "use"
        other = "bag" if self.mode == "shop" else "shop"
        out.append(f"ENTER {verb}  TAB {other}  ESC out", style=DIM)
        return out
