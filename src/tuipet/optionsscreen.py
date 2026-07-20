"""OPTIONS — one home for the app-level switches (Joel 2026-07-04: "put all
options related shit in there" and give the action bar its keys back).

Rows: Theme (hosts the live-preview ThemePanel as a sub), Sound (hosts the
SoundPanel sub: the on/off switch + the volume bar; the value still names the
detected backend so silent-sound mysteries self-explain), Account (hosts the
lobby AccountPanel to switch who's signed in — the current pet parks with the
old account in the cloud), Cloud sync (the cloud-save + offline-mail toggle;
TUIPET_NO_SYNC outranks it), Update (on-demand PyPI check via update.py,
threaded so the UI never blocks), Keys (a scrollable page of every
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
         "sound": "the DVPet chirps — switch + volume",
         "account": "switch login — the pet parks in the cloud",
         "cloud": "cloud saves + offline mail — on or off",
         "update": "ENTER checks + installs · A flips launch auto-install",
         "keys": "every binding on one page",
         "new": "retire the pet, hatch the heir",
         "erase": "wipe save, progress and login — for keeps"}


def _sound_value(on, with_volume=False):
    """The sound state + WHICH backend carries it, so a silent install
    self-explains (the Termux no-player mystery).  First token only and capped
    so nothing clips mid-word in the 18-char value column; the volume rides
    along on the OPTIONS row when a real player exists (the bell has none)."""
    if not on:
        return "off"
    b = sound.backend()
    if b:
        name = b.split("-")[0][:13]
        return f"on · {name[:6]} · {sound.volume()}%" if with_volume else f"on · {name}"
    from . import hostinfo
    return "on · bell (iOS)" if hostinfo.is_ios() else "on · bell only"


class SoundPanel:
    """The sound page: the on/off switch and a volume bar (Joel 2026-07-15:
    the full-scale chirps were piercing — "chop that sound volume in half").
    ←→ steps the volume by 10 and chirps at the NEW level so you hear what you
    picked.  A bell-only host is told the truth — the terminal bell has no
    volume, so the bar never pretends to slide it."""

    _ROWS = ("sound", "volume")
    _DESC = {"sound": "the DVPet chirps — on or off",
             "volume": "←→ set it — every step chirps"}

    def __init__(self, sound_get, sound_toggle):
        self.sound_get = sound_get
        self.sound_toggle = sound_toggle
        self.cursor = 0
        self.frame_i = 0
        self.msg = ""                  # action feedback; empty -> the row's _DESC
        self.sfx = None

    def anim(self):
        self.frame_i += 1              # heartbeat: over-wide notes marquee

    def strip(self):
        if self._ROWS[self.cursor] == "volume" and sound.available():
            return menu.hints(("←→", "volume"), ("ENTER", "hear it"),
                              ("ESC", "back"))
        return menu.hints(("↑↓", "pick"), ("ENTER", "toggle"), ("ESC", "back"))

    def key(self, k):
        row = self._ROWS[self.cursor]
        if k in ("up", "k"):
            self.cursor = (self.cursor - 1) % len(self._ROWS)
            self.msg = ""
        elif k in ("down", "j"):
            self.cursor = (self.cursor + 1) % len(self._ROWS)
            self.msg = ""
        elif row == "volume" and k in ("left", "right", "h", "l"):
            if not sound.available():
                self.msg = "the terminal bell has no volume"
                return None
            v = sound.set_volume(sound.volume()
                                 + (10 if k in ("right", "l") else -10))
            self.msg = f"volume: {v}%"
            if self.sound_get():
                self.sfx = "confirm"   # hear the NEW level right away
        elif k in ("enter", "space"):
            if row == "sound":
                self.sound_toggle()
                self.msg = f"sound: {_sound_value(self.sound_get())}"
                self.sfx = "confirm" if self.sound_get() else None
            elif not sound.available():
                self.msg = "the terminal bell has no volume"
            elif not self.sound_get():
                self.msg = "sound is off — nothing to hear"
            else:
                self.msg = f"volume: {sound.volume()}%"
                self.sfx = "confirm"
        elif k in ("escape", "g"):
            return ("done", None)
        return None

    def text(self):
        out = menu.header("SOUND", sound.backend() or "bell")
        vol = sound.volume()
        if sound.available():
            vbar = "█" * (vol // 10) + "░" * (10 - vol // 10) + f" {vol}%"
        else:
            vbar = "bell — n/a"        # no player: nothing a slider could touch
        rows = (("Sound", _sound_value(self.sound_get())), ("Volume", vbar))
        for i, (label, val) in enumerate(rows):
            out.append_text(menu.row(f"{label:<16} {val[:18]}", i == self.cursor))
        out.append_text(menu.blanks(5))
        out.append_text(menu.note(self.msg or self._DESC[self._ROWS[self.cursor]],
                                  tick=self.frame_i))
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC back"))
        return out


class KeysPanel:
    """Every home-screen binding on one scrollable page (no cursor — there is
    nothing to pick, ↑↓ just slide the window)."""

    VISIBLE = 8

    def anim(self):
        pass          # frame heartbeat: over-wide notes marquee (sweep 2026-07-15)

    def __init__(self, bindings):
        # Textual binds a couple of keys by identifier, not glyph -- show the
        # glyph so the page reads "?  Help" / "Enter  Accept gift" instead of
        # leaking "question_mark" (which also overran the 6-col key column).
        keyname = {"question_mark": "?", "enter": "ENTER"}
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
        elif k == "pageup":                  # page jumps, lobby-chat style
            self.top = max(0, self.top - (self.VISIBLE - 1))
        elif k == "pagedown":
            self.top = min(last, self.top + (self.VISIBLE - 1))
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
                 bindings=(), update_hint=None, verdict=None):
        self.pet = pet
        self.sound_get = sound_get
        self.sound_toggle = sound_toggle
        self.on_theme_change = on_theme_change
        self.bindings = tuple(bindings)
        self.update_hint = update_hint
        self.verdict = verdict or (lambda m: None)   # the app's async-verdict
        #                                              channel (rounds 19/21/22)
        self.cursor = 0
        self.sub = None                # the hosted Theme/Account/Keys panel
        self._sub_row = None           # which row opened it (routes the done)
        self._done = None              # a sub verdict that must close options
        self.frame_i = 0
        self._upd = None               # None idle | "…" checking | "" none | "x.y.z"
        self._installing = False       # a pip run is in flight
        self._updated = False          # installed: the NEW code needs a restart
        self.confirm = False           # typed-YES gate for the erase
        self.confirm_restart = False   # update installed: offer the relaunch
        self.confirm_new = False       # one-ENTER gate before retiring a LIVING pet
        self.buf = ""
        self.msg = ""                  # action feedback; empty -> the row's _DESC
        self.sfx = None

    @property
    def captures_text(self):
        # typing YES — or a name/password in the hosted AccountPanel — q is a
        # letter here, never quit
        return self.confirm or self.confirm_new or self.confirm_restart or bool(
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
        if self.confirm_restart:
            return menu.hints(("ENTER", "restart now"), ("ESC", "later"))
        if self.confirm_new:
            return menu.hints(("ENTER", "retire"), ("ESC", "keep"))
        return menu.hints(("↑↓", "pick"), ("ENTER", "go"), ("ESC", "out"))

    # ---- the update check (threaded: latest_if_newer blocks up to 4s) ----
    def _check_updates(self):
        if self._upd == "…":
            return                      # one probe at a time
        self._upd = "…"
        self.msg = "checking PyPI…"

        def run():
            latest = update_check.latest_if_newer()
            self._upd = latest or ""
            self.msg = (f"tuipet {latest} is out — ENTER installs it"
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
                # the restart OFFER (Joel 2026-07-18: "make it so the update
                # option asks to restart after update"): ENTER relaunches
                self.confirm_restart = True
                self.msg = "Updated! Restart now?  ENTER restarts · ESC later"
            # the completion ALSO rides the app's verdict channel (options
            # audit 2026-07-19, swallow class #4): pip takes seconds -- if
            # the player closed options meanwhile, the offer above lands on
            # a dead panel and they learn nothing.  The parked verdict
            # flashes wherever they are next home; a redundant note beside
            # the live offer is honest, a swallowed one is not.
            self.verdict("tuipet updated — restart to play the new version."
                         if ok else f"update: {msg}")
        threading.Thread(target=run, daemon=True).start()

    def _sub_done(self, r):
        row, self._sub_row = self._sub_row, None
        if row == "theme":
            self.msg = f"theme: {theme.current()}"
        elif row == "sound":
            self.msg = f"sound: {self._value('sound')}"
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
        if self.confirm_restart:
            if k in ("enter", "space"):
                return ("done", ("restart",))
            if k == "escape":
                self.confirm_restart = False
                self.msg = "later — the update applies on your next launch"
            return None
        if self.confirm_new:
            if k in ("enter", "space"):    # SPACE = ENTER like the restart
                return ("done", ("new",))  # confirm right above (parity 07-18)
            if k == "escape":
                self.confirm_new = False
                self.msg = f"kept {self.pet.name}."
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
                self._sub_row = row
                self.sub = SoundPanel(self.sound_get, self.sound_toggle)
            elif row == "account":
                from .accountscreen import AccountPanel
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
                hint = self.update_hint() if self.update_hint is not None else ""
                if self._updated or "installed" in (hint or ""):
                    # a launch (or earlier) auto-update ALREADY wrote the new
                    # version to disk -- but this process is still running the
                    # OLD code it imported at startup, so there is nothing left
                    # to install: ENTER RESTARTS to apply it.  Without this the
                    # row read "restart to apply" (see _value) yet ENTER
                    # re-checked and said "up to date" -- current_version() reads
                    # the freshly-upgraded disk -- stranding the player on the
                    # old code with no way to relaunch from Options (Joel
                    # 2026-07-20: "the first reset should update the game").
                    return ("done", ("restart",))
                if self._upd and self._upd != "…":
                    self._install_update()
                else:
                    self._check_updates()
            elif row == "keys":
                self._sub_row = row
                self.sub = KeysPanel(self.bindings)
            elif row == "new":
                # a LIVING pet gets a confirm: "New egg" replaced it instantly
                # while Erase demanded a typed YES (sweep 2026-07-14).  A dead
                # pet or an unhatched egg hands off without ceremony.
                if getattr(self.pet, "dead", False) or self.pet.stage == "Egg":
                    return ("done", ("new",))
                self.confirm_new = True
                self.msg = f"retire {self.pet.name} (gen {self.pet.generation}) for a new egg?"
            elif row == "erase":
                self.confirm, self.buf = True, ""
                self.msg = "erase EVERYTHING? type YES + ENTER"
        elif k in ("escape", "g"):     # g opened it; g also closes (nav-quit rule)
            return ("done", None)
        return None

    def _value(self, row):
        if row == "theme":
            return theme.current()
        if row == "sound":
            return _sound_value(self.sound_get(), with_volume=True)
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
            if self.confirm_restart:
                return "restart now? ENTER"
            hint = self.update_hint() if self.update_hint is not None else ""
            if self._updated or "installed" in (hint or ""):
                # (was getattr(self.pet, "_updated_to") -- a DEAD read: the
                # launch installer sets the flag on the APP, never the pet;
                # the update_hint lambda carries the app's message.  Bug-
                # report sweep 2026-07-19.)
                return "restart to apply"
            if not persistence.get_auto_update():
                return f"v{update_check.current_version() or 'dev'} · auto off"
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
        if self.confirm_restart:
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("Update installed."))
            out.append_text(menu.note("Restart into the new version now?"))
            out.append_text(menu.blanks(1))
            out.append_text(menu.note("Your save is already written."))
            out.append_text(menu.blanks(2))
            out.append_text(menu.footer("ENTER restart now   ESC later"))
            return out
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
        out.append_text(menu.footer("↑↓ pick  ENTER go  ESC out"))
        return out
