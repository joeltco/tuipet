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

    def render_view(self):
        rows = self._rows()
        out = Text()
        head = "SHOP" if self.mode == "shop" else "BAG"
        out.append(f"{head}", style=INK_B)
        out.append(f"          Bits: {self.pet.bits}\n", style=INK)
        if not rows:
            out.append("\n  (empty)\n\n", style=DIM)
        else:
            self.cursor = min(self.cursor, len(rows) - 1)
            lo = max(0, min(self.cursor - VISIBLE // 2, len(rows) - VISIBLE))
            for i in range(lo, min(lo + VISIBLE, len(rows))):
                e = rows[i]
                sel = i == self.cursor
                mark = ">" if sel else " "
                if self.mode == "shop":
                    line = f"{mark}{e['price']:>5}b {e['name'][:15]:15} {effect_summary(e)[:16]}"
                else:
                    cnt = self.pet.inventory.get(e["key"], 0)
                    line = f"{mark} x{cnt} {e['name'][:16]:16} {effect_summary(e)[:16]}"
                out.append(line[:46] + "\n", style=SEL if sel else INK)
        # pad
        shown = min(len(rows), VISIBLE) if rows else 3
        for _ in range(VISIBLE - shown):
            out.append("\n", style=INK)
        out.append(f"{self.msg}\n", style=INK_B)
        verb = "buy" if self.mode == "shop" else "use"
        other = "bag" if self.mode == "shop" else "shop"
        out.append(f"↑↓ move  ENTER {verb}  TAB {other}  ESC leave", style=DIM)
        self.view.update(out)
