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

_ROWS = ("theme", "sound", "account", "cloud", "update", "keys", "new", "erase")
_LABEL = {"theme": "Theme", "sound": "Sound", "account": "Account",
          "cloud": "Cloud sync", "update": "Update", "keys": "Keys",
          "new": "New egg", "erase": "Erase all data"}
# the note line under the list describes the SELECTED row and follows the
# cursor (Joel's live review 2026-07-07: it sat frozen on the flavour line);
# action feedback (sound toggled, update verdict...) overrides it until the
# cursor moves again.  Over-wide lines marquee via menu.note(tick).
_DESC = {"theme": "recolor the whole game — live preview",
         "sound": "the DVPet chirps — on or off",
         "account": "switch login — the pet parks in the cloud",
         "cloud": "cloud saves + offline mail — on or off",
         "update": "auto-installs new releases at launch · ENTER checks now",
         "keys": "every binding on one page",
         "new": "retire the pet, hatch the heir",
         "erase": "wipe save, progress and login — for keeps"}


class KeysPanel:
    """Every home-screen binding on one scrollable page (no cursor — there is
    nothing to pick, ↑↓ just slide the window)."""

    VISIBLE = 8

    def __init__(self, bindings):
        # Textual binds a couple of keys by identifier, not glyph -- show the
        # glyph so the page reads "?  Help" / "Enter  Accept gift" instead of
        # leaking "question_mark" (which also overran the 6-col key column).
        keyname = {"question_mark": "?", "enter": "Enter"}
        self.rows = [f"{keyname.get(k, k):<6} {label}"
                     for k, _action, label in bindings]
        self.top = 0

    def strip(self):
        return menu.hints(("↑↓", "scroll"), ("ESC", "back"))

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
        self._installing = False       # a pip run is in flight
        self._updated = False          # installed: the NEW code needs a restart
        self.confirm = False           # typed-YES gate for the erase
        self.buf = ""
        self.msg = ""                  # action feedback; empty -> the row's _DESC
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

    def strip(self):
        """The message-box hint line (hint overhaul 2026-07-10)."""
        if self.sub is not None:
            return ""                  # the hosted panel owns the box (strip walker)
        if self.confirm:
            return menu.hints(("ENTER", "erase it all"), ("ESC", "keep"))
        return menu.hints(("↑↓", "pick"), ("ENTER", "go"), ("ESC", "back"))

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

    def _install_update(self):
        """Install the newer release, off the UI thread (pip takes seconds).

        The running process keeps executing the OLD code -- Python imported it
        at launch -- so a success always ends in "restart tuipet".  We never
        pretend the swap happened live.
        """
        if self._installing:
            return
        self._installing = True
        self.msg = "updating… (this takes a moment)"

        def run():
            ok, msg = update_check.run_upgrade()
            self.msg = msg
            self._installing = False
            if ok:
                self._upd = ""                # nothing left to offer
                self._updated = True
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
            self.msg = ""              # feedback yields to the new row's description
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(_ROWS)
            self.msg = ""
        elif k == "a" and _ROWS[self.cursor] == "update":
            # opt out of the launch auto-install (Joel 2026-07-14: it is ON by
            # default, but nobody should be forced to have pip run for them)
            on = persistence.set_auto_update(not persistence.get_auto_update())
            self.msg = ("auto-update on — new releases install at launch"
                        if on else "auto-update off — you'll be told, not updated")
            self.sfx = "confirm"
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
            elif row == "cloud":
                on = persistence.set_cloud_sync(not persistence.get_cloud_sync())
                self.msg = ("cloud sync on — saves follow your account"
                            if on else "cloud sync off — this device saves locally only")
                self.sfx = "confirm"
            elif row == "update":
                # first ENTER checks; with a newer release known, the second
                # ENTER actually INSTALLS it (Joel 2026-07-13: "make the update
                # option actually update the game").  The game also installs
                # new releases for itself at launch -- `a` opts out of that.
                if self._upd and self._upd != "…":
                    self._install_update()
                else:
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
            if b:
                return f"on · {b.split('-')[0][:13]}"
            # iOS sandboxes audio players outright -- name the reason so a
            # silent iPhone reads as EXPECTED, not broken (sound audit
            # 2026-07-13); everywhere else "bell only" already self-explains.
            from . import hostinfo
            return "on · bell (iOS)" if hostinfo.is_ios() else "on · bell only"
        if row == "account":
            return persistence.get_account()[0] or "not signed in"
        if row == "cloud":
            import os as _o
            if _o.environ.get("TUIPET_NO_SYNC"):
                return "off (TUIPET_NO_SYNC)"   # the env override outranks the toggle
            return "on" if persistence.get_cloud_sync() else "off"
        if row == "update":
            if self._installing:
                return "updating…"
            if self._updated or getattr(self.pet, "_updated_to", None):
                return "restart to apply"
            if not persistence.get_auto_update():
                return "auto: off"
            if self._upd == "…":
                return "checking…"
            if self._upd:
                return f"{self._upd} · ENTER installs"
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
        out.append_text(menu.note(self.msg or _DESC[_ROWS[self.cursor]],
                                  tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out
