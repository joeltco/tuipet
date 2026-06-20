"""Shop screen — spend bits on foods/items, and use them from the bag."""
from __future__ import annotations
from rich.text import Text
from textual.screen import ModalScreen
from textual.widgets import Static

from . import data

LCD_ON, LCD_BG = "#0b3d0b", "#9bbc0f"
INK = f"{LCD_ON} on {LCD_BG}"
INK_B = f"bold {LCD_ON} on {LCD_BG}"
SEL = f"bold #9bbc0f on {LCD_ON}"
DIM = f"#5a7a1a on {LCD_BG}"
VISIBLE = 8


def effect_summary(e):
    parts = []
    for k, lbl in (("hunger", "food"), ("mood", "mood"), ("weight", "wt"),
                   ("energy", "en"), ("strength", "eff"), ("obedience", "obed"),
                   ("vaccine", "Va"), ("data", "Da"), ("virus", "Vi")):
        if e.get(k):
            parts.append(f"{lbl}{e[k]:+d}")
    if e.get("cured"):
        parts.append("cure")
    if e.get("healed"):
        parts.append("heal")
    return " ".join(parts) or "—"


class ShopScreen(ModalScreen):
    CSS = """
    ShopScreen { align: center middle; }
    #shop { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 50; height: 16; }
    """
    BINDINGS = [
        ("up", "move(-1)", "Up"), ("k", "move(-1)", "Up"),
        ("down", "move(1)", "Down"), ("j", "move(1)", "Down"),
        ("enter", "act", "Buy/Use"), ("space", "act", "Buy/Use"),
        ("tab", "toggle", "Bag/Shop"), ("escape", "leave", "Leave"),
    ]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.mode = "shop"
        self.cursor = 0
        self.msg = "Welcome! Spend your bits."

    def compose(self):
        yield Static(id="shop")

    def on_mount(self):
        self.view = self.query_one("#shop", Static)
        self.render_view()

    def _rows(self):
        if self.mode == "shop":
            return data.load_shop()
        return [data.consumable_by_key(k) for k in self.pet.inventory]

    def action_move(self, d):
        rows = self._rows()
        if rows:
            self.cursor = (self.cursor + d) % len(rows)
        self.render_view()

    def action_toggle(self):
        self.mode = "bag" if self.mode == "shop" else "shop"
        self.cursor = 0
        self.msg = "Your bag." if self.mode == "bag" else "Spend your bits."
        self.render_view()

    def action_act(self):
        rows = self._rows()
        if not rows:
            self.render_view(); return
        e = rows[self.cursor]
        if self.mode == "shop":
            self.msg = self.pet.buy(e)
        else:
            self.msg = self.pet.use_item(e["key"])
            if self.cursor >= len(self.pet.inventory):
                self.cursor = max(0, len(self.pet.inventory) - 1)
        self.render_view()

    def action_leave(self):
        self.dismiss(self.msg)

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

    def render_view(self):
        rows = self._rows()
        vis = 5
        out = Text()
        head = "SHOP" if self.mode == "shop" else "BAG"
        out.append(f"{head}    Bits: {self.pet.bits}\n", style=INK_B)
        sel_e = rows[min(self.cursor, len(rows) - 1)] if rows else None
        # selected item: icon (left) beside its name/price/effect (right)
        icon = self._icon_lines(sel_e)
        info = []
        if sel_e:
            info = [sel_e["name"][:22],
                    (f"{sel_e['price']} bits" if self.mode == "shop"
                     else f"x{self.pet.inventory.get(sel_e['key'], 0)} owned"),
                    effect_summary(sel_e)[:22]]
        for r in range(4):
            ic = icon[r] if r < len(icon) else ""
            tx = info[r - 0] if 0 <= r < len(info) else ""
            out.append(f" {ic:<10} ", style=INK)
            out.append(f"{tx}\n", style=INK_B if r == 0 else INK)
        out.append("─" * 46 + "\n", style=DIM)
        if not rows:
            out.append("  (empty)\n", style=DIM)
        else:
            self.cursor = min(self.cursor, len(rows) - 1)
            lo = max(0, min(self.cursor - vis // 2, len(rows) - vis))
            for i in range(lo, min(lo + vis, len(rows))):
                e = rows[i]
                sel = i == self.cursor
                mark = ">" if sel else " "
                if self.mode == "shop":
                    line = f"{mark}{e['price']:>5}b {e['name'][:16]:16}"
                else:
                    line = f"{mark} x{self.pet.inventory.get(e['key'],0)} {e['name'][:18]:18}"
                out.append(line[:46] + "\n", style=SEL if sel else INK)
        for _ in range(vis - (min(len(rows), vis) if rows else 1)):
            out.append("\n", style=INK)
        out.append(f"{self.msg}\n", style=INK_B)
        verb = "buy" if self.mode == "shop" else "use"
        other = "bag" if self.mode == "shop" else "shop"
        out.append(f"↑↓ ENTER {verb}  TAB {other}  ESC leave", style=DIM)
        self.view.update(out)
