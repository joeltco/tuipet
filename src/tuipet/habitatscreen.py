"""Habitat screen — buy new homes with bits and move your pet between them.

Each habitat has its own seasonal climate (driving weather/temperature) and
Field/Element affinities that help or hurt the pet living there."""
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


class HabitatScreen(ModalScreen):
    CSS = """
    HabitatScreen { align: center middle; }
    #hab { border: heavy #5a7a1a; background: #9bbc0f; padding: 0 1; width: 52; height: 18; }
    """
    BINDINGS = [
        ("up", "move(-1)", "Up"), ("k", "move(-1)", "Up"),
        ("down", "move(1)", "Down"), ("j", "move(1)", "Down"),
        ("enter", "act", "Buy/Move"), ("space", "act", "Buy/Move"),
        ("escape", "leave", "Leave"),
    ]

    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.rows = sorted(data.load_habitats().values(), key=lambda h: (h["price"], h["id"]))
        self.cursor = next((i for i, h in enumerate(self.rows) if h["id"] == pet.habitat), 0)
        self.msg = "Pick a home for your pet."

    def compose(self):
        yield Static(id="hab")

    def on_mount(self):
        self.view = self.query_one("#hab", Static)
        self.render_view()

    def action_move(self, d):
        self.cursor = (self.cursor + d) % len(self.rows)
        self.render_view()

    def action_act(self):
        h = self.rows[self.cursor]
        if h["id"] == self.pet.habitat:
            self.msg = f"Already living in {h['name']}."
        elif h["id"] in self.pet.habitats:
            self.msg = self.pet.move_to(h["id"])
        else:
            self.msg = self.pet.buy_habitat(h["id"])
        self.render_view()

    def action_leave(self):
        self.dismiss(self.msg)

    def _aff(self, h):
        f, e = self.pet.field, self.pet.element
        c = (f in h["compat_fields"]) + (e in h["compat_elements"])
        i = (f in h["incompat_fields"]) + (e in h["incompat_elements"])
        return c - i

    def _aff_parts(self, h):
        """(text, style) for the affinity blurb — markup-free for Text.append."""
        a = self._aff(h)
        if a > 0:
            return (chr(0x2665) * a + " thrives here", f"bold #0b5a0b on {LCD_BG}")
        if a < 0:
            return (chr(0x2716) * -a + " suffers here", f"bold #7a1010 on {LCD_BG}")
        return ("neutral", DIM)

    def render_view(self):
        out = Text()
        out.append(f"HABITATS{' ':>6}Bits: {self.pet.bits}\n", style=INK_B)
        sel = self.rows[self.cursor]
        su, wi = sel["temps"]["Summer"], sel["temps"]["Winter"]
        climate = ("climate-controlled" if sel["weather_chance"] <= 0
                   else f"Su {su[0]}-{su[1]}°  Wi {wi[0]}-{wi[1]}°")
        out.append(f"{sel['name']}  ", style=INK_B)
        atxt, astyle = self._aff_parts(sel)
        out.append(atxt + "\n", style=astyle)
        out.append(f"  {sel['desc'][:46]}\n", style=DIM)
        out.append(f"  {climate}\n", style=INK)
        out.append("─" * 48 + "\n", style=DIM)

        vis = 7
        lo = max(0, min(self.cursor - vis // 2, len(self.rows) - vis))
        for i in range(lo, min(lo + vis, len(self.rows))):
            h = self.rows[i]
            cur = i == self.cursor
            if h["id"] == self.pet.habitat:
                tag = chr(0x25CF) + " here "          # currently living here
            elif h["id"] in self.pet.habitats:
                tag = chr(0x25CB) + " owned"
            else:
                tag = f"{h['price']:>5}b"
            a = self._aff(h)
            amark = (chr(0x2665) if a > 0 else (chr(0x2716) if a < 0 else " "))
            line = f"{'>' if cur else ' '} {h['name']:<13} {tag:>7} {amark}"
            out.append(line[:48] + "\n", style=SEL if cur else INK)
        for _ in range(vis - (min(lo + vis, len(self.rows)) - lo)):
            out.append("\n", style=INK)
        out.append(f"{self.msg}\n", style=INK_B)
        out.append("↑↓  ENTER buy/move  ESC leave", style=DIM)
        self.view.update(out)
