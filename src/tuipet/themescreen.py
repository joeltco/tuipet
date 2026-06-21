"""Theme picker panel: pick a palette from a list with live colour swatches."""
from __future__ import annotations
from rich.text import Text
from . import theme, menu
from .theme import INK, SEL


class ThemePanel:
    """Lists the themes with a swatch; navigating live-previews the whole UI."""

    def __init__(self, on_change=None):
        self.names = theme.names()
        self.cursor = self.names.index(theme.current()) if theme.current() in self.names else 0
        self.on_change = on_change

    def _apply(self):
        theme.apply(self.names[self.cursor])
        theme.save_choice(self.names[self.cursor])
        if self.on_change:
            self.on_change()

    def key(self, k):
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.names)
            self._apply()
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.names)
            self._apply()
        elif k in ("enter", "space", "escape", "g"):
            return ("done", None)
        return None

    def text(self):
        out = menu.header("THEMES", theme.current())
        out.append_text(menu.blanks(1))
        for i, name in enumerate(self.names):
            t = theme.THEMES[name]
            sel = i == self.cursor
            out.append(("▸ " if sel else "  ") + f"{name:<10}", style=SEL if sel else INK)
            sw = "".join(f"[{c}]██[/]" for c in
                         (t["on"], t["heart"], t["energy"], t["mood"], t["coin"]))
            out.append_text(Text.from_markup(sw + "\n"))
        out.append_text(menu.blanks(max(0, 4 - len(self.names))))
        out.append_text(menu.note("live preview as you move"))
        out.append_text(menu.footer("up/dn preview   ENTER ok   ESC close"))
        return out
