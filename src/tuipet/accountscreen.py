"""The name+password login card (split out of the lobby; modularize 2026-07-17).
(Round 35: the split's stranded boilerplate -- dead imports and the unused
MAX_PVP_* clamp constants (_clamp_card in lobbybout owns the real bounds) --
was cut; the cell-width law finally reached the name field.)"""
from __future__ import annotations

from .sfx import CueQueue
from rich.cells import cell_len
from rich.text import Text

from . import menu
from .theme import INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)

_NAME_MAX = 24                  # the server's MAX_NAME: what you SEE is what
#                                 logs in (round 35: the buffer held 64 and
#                                 the confirm silently trimmed)
_PW_MAX = 64
_FIELD_W = 26                   # input cells shown (38 - the 12-col label)


def _tail(s, w):
    """The LAST w CELLS of s -- an emoji/CJK glyph is two cells, and the old
    character slice let a wide name overrun the 40-col box (the CELL-WIDTH
    LAW, finally applied here -- round 35)."""
    while cell_len(s) > w:
        s = s[1:]
    return s


class AccountPanel(CueQueue):
    """Name + password entry. Tab/Up/Down switch fields; Enter on the password
    confirms when both are filled. Returns ("done", (name, password)), or
    ("done", None) on Esc. Used at first launch and to recover a failed login."""

    def __init__(self, name="", note="Name + password — the name is yours."):
        self.name_buf = name[:_NAME_MAX]
        self.pw_buf = ""
        self.field = "pw" if name else "name"
        self.note = note
        self.sfx = None
        self.frame_i = 0                # the note's marquee clock
        self.captures_text = True       # typing a name/password — never treat q as quit

    def anim(self):
        self.frame_i += 1

    def strip(self):
        # "field", the grammar sweep's verb -- the lobby's login strip and
        # this one said different words for the same key (round 35)
        return menu.hints(("TAB", "field"), ("ENTER", "continue"), ("ESC", "back"))

    def key(self, k):
        if k == "escape":
            return ("done", None)
        if k in ("tab", "up", "down"):
            self.field = "pw" if self.field == "name" else "name"
            return None
        if k == "enter":
            if self.field == "name":
                self.field = "pw"
                return None
            name = self.name_buf.strip()
            if name and not any(c.isalnum() for c in name):
                # a lone "-" became a real account (2026-10-16: the phone key
                # bar's "-" sits beside ESC); the server refuses new ones too
                self.note = "Names need a letter or number."
                self.sfx = "error"
                return None
            if name and self.pw_buf:
                return ("done", (name, self.pw_buf))
            # a missing field used to fail SILENTLY (round 35)
            self.note = "Name and password both, please."
            self.sfx = "error"
            return None
        attr = "name_buf" if self.field == "name" else "pw_buf"
        cur = getattr(self, attr)
        if k == "backspace":
            cur = cur[:-1]
        elif k == "space":
            cur = cur + " "
        elif len(k) == 1 and k.isprintable():
            cur = cur + k
        setattr(self, attr, cur[:_NAME_MAX if attr == "name_buf" else _PW_MAX])
        return None

    def text(self):
        t = Text()
        t.append("  TUIPET ACCOUNT\n\n", style=INK_B)
        # tail-window long input BY CELLS so a line never overruns the 40-col
        # LCD (the box CLIPS overflow live -- lobby audit 2026-07-04; the
        # password renders as 1-cell stars, so its char slice is safe)
        nm = _tail(self.name_buf + ("_" if self.field == "name" else ""), _FIELD_W)
        # the LAST typed character shows in plain while the field is active
        # (the phone-keyboard pattern): the first login CREATES the account,
        # so an unverifiable typo became the permanent sync password
        # (QOL sweep 2026-07-23).  Leaving the field stars it fully.
        stars = ("*" * (len(self.pw_buf) - 1) + self.pw_buf[-1]
                 if self.field == "pw" and self.pw_buf else "*" * len(self.pw_buf))
        pw = (stars + ("_" if self.field == "pw" else ""))[-_FIELD_W:]
        t.append("  name:     ", style=DIM)
        t.append(nm + "\n", style=INK_B if self.field == "name" else INK)
        t.append("  password: ", style=DIM)
        t.append(pw + "\n\n", style=INK_B if self.field == "pw" else INK)
        # keys ride the strip (round 35: the in-LCD hint line doubled it)
        # the note WRAPS, never scrolls (menus call #14 = A, 2026-10-15): a
        # server's words are the ones you must read -- the old marquee made
        # you wait for the actionable tail of a long rejection
        import textwrap
        lines = textwrap.wrap(self.note, menu.W - 2) or [""]
        t.append("\n".join("  " + ln for ln in lines[:6]), style=DIM)
        return t


FIRST_RUN_NOTE = "New? Choose a name and password to create an account. Returning? Use your account. ESC: play locally."


class CloudWaitPanel(CueQueue):
    """The few seconds the first-run sign-in spends asking the cloud: a card
    that holds the screen (no pet ticks underneath, no second Enter fires a
    second sign-in) until the app closes it with the verdict."""

    def __init__(self, name):
        self.name = name
        self.sfx = None
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        return "[dim]checking the cloud…[/]"

    def key(self, k):
        return None

    def text(self):
        t = Text()
        t.append("  TUIPET ACCOUNT\n\n", style=INK_B)
        t.append("  " + _tail(self.name, _FIELD_W) + "\n\n", style=INK)
        t.append("  checking the cloud" + "." * (1 + (self.frame_i // 4) % 3), style=DIM)
        return t
