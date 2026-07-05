"""OPTIONS — one home for the app-level switches (Joel 2026-07-04: "put all
options related shit in there" and give the action bar its keys back).

Rows: Theme (hosts the live-preview ThemePanel as a sub), Sound on/off, a New
egg hand-off, and Erase all data (typed-YES confirm; wipes the local save dir
-- the cloud copy stays with the account).  Replaces the g/m/n bindings with
one `g options`.
"""
from __future__ import annotations
from . import menu, persistence, theme
from .themescreen import ThemePanel

_ROWS = ("theme", "sound", "new", "erase")
_LABEL = {"theme": "Theme", "sound": "Sound", "new": "New egg",
          "erase": "Erase all data"}


class OptionsPanel(menu.SubHost):
    def __init__(self, pet, sound_get, sound_toggle, on_theme_change=None):
        self.pet = pet
        self.sound_get = sound_get
        self.sound_toggle = sound_toggle
        self.on_theme_change = on_theme_change
        self.cursor = 0
        self.sub = None                # the hosted ThemePanel
        self.confirm = False           # typed-YES gate for the erase
        self.buf = ""
        self.msg = "the dials behind the game"
        self.sfx = None

    @property
    def captures_text(self):
        return self.confirm            # typing YES -- q is a letter here

    def key(self, k):
        if self.sub is not None:
            r = self.sub.key(k)
            if r is not None and r[0] == "done":
                self.sub = None
                self.msg = f"theme: {theme.current()}"
            return None
        if self.confirm:
            if k == "escape":
                self.confirm, self.buf = False, ""
                self.msg = "kept everything."
            elif k == "enter":
                if self.buf.strip().upper() == "YES":
                    return ("done", ("erase",))
                self.confirm, self.buf = False, ""
                self.msg = "that wasn't YES — kept everything."
                self.sfx = "error"
            elif k == "backspace":
                self.buf = self.buf[:-1]
            elif len(k) == 1 and k.isprintable():
                self.buf = (self.buf + k)[:8]
            return None
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(_ROWS)
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(_ROWS)
        elif k in ("enter", "space"):
            row = _ROWS[self.cursor]
            if row == "theme":
                self.sub = ThemePanel(on_change=self.on_theme_change)
            elif row == "sound":
                self.sound_toggle()
                self.msg = f"sound: {'on' if self.sound_get() else 'off'}"
                self.sfx = "confirm" if self.sound_get() else None
            elif row == "new":
                return ("done", ("new",))
            elif row == "erase":
                self.confirm, self.buf = True, ""
                self.msg = "erase EVERYTHING? type YES + Enter"
        elif k in ("escape", "g"):     # g opened it; g also closes (nav-quit rule)
            return ("done", None)
        return None

    def _value(self, row):
        if row == "theme":
            return theme.current()
        if row == "sound":
            return "on" if self.sound_get() else "off"
        if row == "new":
            return f"gen {self.pet.generation + 1} next"
        return "save + progress + account"

    def text(self):
        if self.sub is not None:
            return self.sub.text()
        out = menu.header("OPTIONS", persistence.get_account()[0] or "")
        if self.confirm:
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("This erases the pet, progress,"))
            out.append_text(menu.note("eggs and your login — for keeps."))
            out.append_text(menu.blanks(1))
            out.append_text(menu.row(f"type YES:  {self.buf}_", True))
            out.append_text(menu.blanks(2))
            out.append_text(menu.footer("ENTER confirm   ESC keep everything"))
            return out
        for i, row in enumerate(_ROWS):
            out.append_text(menu.row(f"{_LABEL[row]:<16} {self._value(row)[:18]}",
                                     i == self.cursor))
        out.append_text(menu.blanks(4 - len(_ROWS) + 3))
        out.append_text(menu.note(self.msg))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
