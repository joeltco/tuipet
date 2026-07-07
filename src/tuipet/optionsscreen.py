"""OPTIONS — one home for the app-level switches (Joel 2026-07-04: "put all
options related shit in there" and give the action bar its keys back).

Rows: Theme (hosts the live-preview ThemePanel as a sub), Sound on/off (the
value names the detected backend so silent-sound mysteries self-explain),
Account (hosts the lobby AccountPanel to switch who's signed in — the current
pet parks with the old account in the cloud), Update (on-demand PyPI check via
update.py, threaded so the UI never blocks), Keys (a scrollable page of every
home-screen binding), a New egg hand-off, and Erase all data (typed-YES
confirm; wipes the local save dir -- the cloud copy stays with the account).
"""
from __future__ import annotations
import threading

from . import menu, persistence, sound, theme
from . import update as update_check
from .themescreen import ThemePanel

_ROWS = ("theme", "sound", "account", "update", "keys", "new", "erase")
_LABEL = {"theme": "Theme", "sound": "Sound", "account": "Account",
          "update": "Update", "keys": "Keys", "new": "New egg",
          "erase": "Erase all data"}


class KeysPanel:
    """Every home-screen binding on one scrollable page (no cursor — there is
    nothing to pick, ↑↓ just slide the window)."""

    VISIBLE = 8

    def __init__(self, bindings):
        self.rows = [f"{k:<6} {label}" for k, _action, label in bindings]
        self.top = 0

    def key(self, k):
        last = max(0, len(self.rows) - self.VISIBLE)
        if k in ("up", "k"):
            self.top = max(0, self.top - 1)
        elif k in ("down", "j"):
            self.top = min(last, self.top + 1)
        elif k in ("escape", "enter", "space", "g"):
            return ("done", None)
        return None

    def text(self):
        n = len(self.rows)
        lo, hi = self.top + 1, min(self.top + self.VISIBLE, n)
        out = menu.header("KEYS", f"{lo}-{hi}/{n}")
        shown = self.rows[self.top:self.top + self.VISIBLE]
        for r in shown:
            out.append_text(menu.row(r))
        out.append_text(menu.blanks(self.VISIBLE - len(shown) + 1))
        out.append_text(menu.footer("↑↓ scroll  ESC back"))
        return out


class OptionsPanel(menu.SubHost):
    def __init__(self, pet, sound_get, sound_toggle, on_theme_change=None,
                 bindings=(), update_hint=None):
        self.pet = pet
        self.sound_get = sound_get
        self.sound_toggle = sound_toggle
        self.on_theme_change = on_theme_change
        self.bindings = tuple(bindings)
        self.update_hint = update_hint
        self.cursor = 0
        self.sub = None                # the hosted Theme/Account/Keys panel
        self._sub_row = None           # which row opened it (routes the done)
        self._done = None              # a sub verdict that must close options
        self.frame_i = 0
        self._upd = None               # None idle | "…" checking | "" none | "x.y.z"
        self.confirm = False           # typed-YES gate for the erase
        self.buf = ""
        self.msg = "the dials behind the game"
        self.sfx = None

    @property
    def captures_text(self):
        # typing YES — or a name/password in the hosted AccountPanel — q is a
        # letter here, never quit
        return self.confirm or bool(
            self.sub is not None and getattr(self.sub, "captures_text", False))

    def anim(self):
        self.frame_i += 1
        if self.sub is not None and getattr(self.sub, "sfx", None):
            self.sfx = self.sub.sfx
            self.sub.sfx = None

    # ---- the update check (threaded: latest_if_newer blocks up to 4s) ----
    def _check_updates(self):
        if self._upd == "…":
            return                      # one probe at a time
        self._upd = "…"
        self.msg = "checking PyPI…"

        def run():
            latest = update_check.latest_if_newer()
            self._upd = latest or ""
            self.msg = (f"tuipet {latest} is out — pip install -U tuipet"
                        if latest else "no newer release found.")
        threading.Thread(target=run, daemon=True).start()

    def _sub_done(self, r):
        row, self._sub_row = self._sub_row, None
        if row == "theme":
            self.msg = f"theme: {theme.current()}"
        elif row == "account":
            if r:
                self._done = ("account",) + tuple(r)   # app does the heavy lifting
            else:
                self.msg = "kept your account."

    def key(self, k):
        if self.sub_key(k, self._sub_done):
            if self._done is not None:
                r, self._done = self._done, None
                return ("done", r)
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
                self._sub_row = row
                self.sub = ThemePanel(on_change=self.on_theme_change)
            elif row == "sound":
                self.sound_toggle()
                self.msg = f"sound: {self._value('sound')}"
                self.sfx = "confirm" if self.sound_get() else None
            elif row == "account":
                from .lobbyscreen import AccountPanel
                self._sub_row = row
                self.sub = AccountPanel(
                    note="Switch: the pet parks with this login.")
            elif row == "update":
                self._check_updates()
            elif row == "keys":
                self._sub_row = row
                self.sub = KeysPanel(self.bindings)
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
            if not self.sound_get():
                return "off"
            b = sound.backend()
            # first token only: "termux-media-player" clipped mid-word on the
            # 18-char value column (Joel's live screen, 2026-07-07)
            return f"on · {b.split('-')[0][:13]}" if b else "on · bell only"
        if row == "account":
            return persistence.get_account()[0] or "not signed in"
        if row == "update":
            if self._upd == "…":
                return "checking…"
            if self._upd:
                return f"{self._upd} out!"
            if self._upd == "":
                return "up to date"
            if self.update_hint is not None and self.update_hint():
                return "new version out!"   # the boot check already knows
            return f"v{update_check.current_version() or 'dev'}"
        if row == "keys":
            return f"{len(self.bindings)} bindings"
        if row == "new":
            return f"gen {self.pet.generation + 1} next"
        return "everything"          # the confirm page spells out what that means

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
        out.append_text(menu.blanks(7 - len(_ROWS)))
        out.append_text(menu.note(self.msg, tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
