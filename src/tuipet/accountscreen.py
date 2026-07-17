"""The name+password login card (split out of the lobby; modularize 2026-07-17)."""
from __future__ import annotations

import hashlib
import random

from rich.cells import cell_len, chop_cells, set_cell_size  # noqa: F401
from rich.text import Text  # noqa: F401

from . import data  # noqa: F401
from . import jogress  # noqa: F401
from . import battle  # noqa: F401
from . import battlescreen  # noqa: F401
from . import jogressscreen  # noqa: F401
from . import menu  # noqa: F401
from . import persistence  # noqa: F401
from .net import ANNOUNCE, CHAT_CAP  # noqa: F401
from .render import marquee  # noqa: F401
from .theme import INK, INK_B, DIM, SEL  # noqa: F401  (theme.apply propagation)


class AccountPanel:
    """Name + password entry. Tab/Up/Down switch fields; Enter on the password
    confirms when both are filled. Returns ("done", (name, password)), or
    ("done", None) on Esc. Used at first launch and to recover a failed login."""

    def __init__(self, name="", note="Name + password — the name is yours."):
        self.name_buf = name
        self.pw_buf = ""
        self.field = "pw" if name else "name"
        self.note = note
        self.sfx = None
        self.captures_text = True       # typing a name/password — never treat q as quit

    def strip(self):
        return menu.hints(("TAB", "switch"), ("ENTER", "go"), ("ESC", "back"))

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
            name = self.name_buf.strip()[:24]
            if name and self.pw_buf:
                return ("done", (name, self.pw_buf))
            return None
        attr = "name_buf" if self.field == "name" else "pw_buf"
        cur = getattr(self, attr)
        if k == "backspace":
            cur = cur[:-1]
        elif k == "space":
            cur = cur + " "
        elif len(k) == 1 and k.isprintable():
            cur = cur + k
        setattr(self, attr, cur[:64])
        return None

    def text(self):
        t = Text()
        t.append("  TUIPET ACCOUNT\n\n", style=INK_B)
        # tail-window long input so a line never overruns the 40-col LCD
        # (the box CLIPS overflow live -- lobby audit 2026-07-04)
        nm = (self.name_buf + ("_" if self.field == "name" else ""))[-26:]
        pw = ("*" * len(self.pw_buf) + ("_" if self.field == "pw" else ""))[-26:]
        t.append("  name:     ", style=DIM)
        t.append(nm + "\n", style=INK_B if self.field == "name" else INK)
        t.append("  password: ", style=DIM)
        t.append(pw + "\n\n", style=INK_B if self.field == "pw" else INK)
        t.append(f"  {self.note[:38]}\n", style=DIM)
        t.append("  TAB switch   ENTER go   ESC back", style=DIM)
        return t


# PvP wire bounds (multiplayer audit 2026-07-13): the relay is peer-to-peer,
# so an opponent card is UNTRUSTED input.  HP ceiling = the oldest trained cap
# (pet.HEALTH_CAP_LADDER tops out at 30); power ceiling sits above the
# strongest enemy in the shipped data (virus 650) with headroom for a fully
# trained Mega.  A peer claiming more is clamped, not kicked.
MAX_PVP_HP = 30
MAX_PVP_POWER = 999
