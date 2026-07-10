"""Theme picker panel: preview palettes live, commit on Enter, revert on Esc.

Navigating previews a theme (applied to the live UI but NOT saved); Enter keeps
it (persists to disk); Esc cancels back to whatever theme was active on open.
"""
from __future__ import annotations
from rich.text import Text
from . import theme, menu
from .theme import INK, SEL


class ThemePanel:
    """Lists the themes with a swatch; navigating live-previews the whole UI."""

    def __init__(self, on_change=None):
        self.names = theme.names()
        self.original = theme.current()        # restore this if the user cancels
        self.cursor = self.names.index(self.original) if self.original in self.names else 0
        self.on_change = on_change

    def _preview(self):
        theme.apply(self.names[self.cursor])   # live preview only -- not persisted yet
        if self.on_change:
            self.on_change()

    def _settle(self, name):
        theme.apply(name)
        if self.on_change:
            self.on_change()

    def strip(self):
        return menu.hints(("↑↓", "preview"), ("ENTER", "keep"),
                          ("ESC", "revert"))

    def key(self, k):
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self.names)
            self._preview()
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self.names)
            self._preview()
        elif k in ("enter", "space", "g"):
            chosen = self.names[self.cursor]
            self._settle(chosen)
            theme.save_choice(chosen)          # commit the choice to disk
            return ("done", None)
        elif k == "escape":
            self._settle(self.original)        # cancel -> revert (original is the saved theme)
            return ("done", None)
        return None

    def text(self):
        out = menu.header("THEMES", theme.current())
        for i, name in enumerate(self.names):
            t = theme.THEMES[name]
            sel = i == self.cursor
            out.append(("▸ " if sel else "  ") + f"{name:<10}", style=SEL if sel else INK)
            sw = "".join(f"[{c}]██[/]" for c in
                         (t["on"], t["heart"], t["energy"], t["mood"], t["coin"]))
            out.append_text(Text.from_markup(sw + "\n"))
        out.append_text(menu.blanks(max(0, 8 - len(self.names))))
        out.append_text(menu.note("live preview as you move"))
        out.append_text(menu.footer("↑↓ preview  ENTER keep  ESC cancel"))
        return out
