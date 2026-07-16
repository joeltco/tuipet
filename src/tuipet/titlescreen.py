"""Boot/title screen shown on launch (the device powering on)."""
from __future__ import annotations
import random
from rich.text import Text
from . import data
from .theme import LCD_ON, LCD_BG

COLS, PXH = 40, 24
BOOT_BLIP = 4      # frames of all-segments-on (power-on flash)
BOOT_FADE = 5      # frames of dither dissolve into the title
# tiny 3x5 pixel font for the wordmark
_FONT = {
    "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"],
    "I": ["111", "010", "010", "010", "111"],
    "P": ["111", "101", "111", "100", "100"],
    "E": ["111", "100", "110", "100", "111"],
}


def _wordmark(s):
    rows = ["", "", "", "", ""]
    for ch in s:
        g = _FONT[ch]
        for i in range(5):
            rows[i] += g[i] + "0"
    return [r[:-1] for r in rows]


WORD = _wordmark("TUIPET")


class TitlePanel:
    """Shows a bobbing mascot + the TUIPET wordmark; any key starts the game (q quits)."""

    def __init__(self):
        _, by = data.load_sprites()
        pool = [n for n, r in by.items()
                if r["stage"] in ("Rookie", "Champion", "Ultimate", "Mega")
                and not data.is_placeholder(n)]
        self.num = random.choice(pool) if pool else next(iter(by))
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        """The press-to-start prompt rides the #msg strip.  It used to be set
        once by the app and the v0.2.223 strip plumbing blanked it a frame
        later (title audit 2026-07-04) — panels own their strips now."""
        if self.frame_i < BOOT_BLIP + BOOT_FADE:
            return ""                            # let the power-on play in silence
        return "[b]▸ PRESS ENTER ◂[/b]"

    def key(self, k):
        if k == "q":
            return ("quit", None)      # q quits the app rather than starting the game
        return ("done", None)

    def text(self):
        mascot = data.bob_frame(self.num, self.frame_i, beat=4)  # gentle bob (~0.5s), not every fast-tick
        buf = [[0] * COLS for _ in range(PXH)]
        sw = max(len(r) for r in mascot)
        sh = len(mascot)
        ww = max(len(r) for r in WORD)
        group_h = sh + 1 + len(WORD)                 # mascot + gap + wordmark, centred as a unit
        top = max(0, (PXH - group_h) // 2)
        ox = (COLS - sw) // 2
        oy = top
        for y, line in enumerate(mascot):
            for x, ch in enumerate(line):
                if ch == "1" and 0 <= oy + y < PXH and 0 <= ox + x < COLS:
                    buf[oy + y][ox + x] = 1
        wx = (COLS - ww) // 2
        wy = top + sh + 1
        for y, line in enumerate(WORD):
            for x, ch in enumerate(line):
                if ch == "1" and 0 <= wy + y < PXH and 0 <= wx + x < COLS:
                    buf[wy + y][wx + x] = 1
        # power-on: all segments flash black, then the title dissolves in from static
        boot = self.frame_i
        if boot < BOOT_BLIP:
            buf = [[1] * COLS for _ in range(PXH)]
        elif boot < BOOT_BLIP + BOOT_FADE:
            keep = BOOT_BLIP + BOOT_FADE - boot      # thinning noise as the title emerges
            for y in range(PXH):
                for x in range(COLS):
                    if (x * 7 + y * 13 + boot * 5) % (BOOT_FADE + 1) < keep:
                        buf[y][x] = 1
        t = Text()
        for cy in range(PXH // 2):
            ty, byy = cy * 2, cy * 2 + 1
            for cx in range(COLS):
                tc = LCD_ON if buf[ty][cx] else LCD_BG
                bc = LCD_ON if buf[byy][cx] else LCD_BG
                t.append("▀", style=f"{tc} on {bc}")
            if cy != PXH // 2 - 1:
                t.append("\n")
        return t


class GatePanel:
    """The UNDER-CONSTRUCTION lock (Joel 2026-07-15): the game itself needs
    the PIN while the rebuild settles; the LOBBY stays open to everyone.
    Digits type the PIN, ENTER submits, L skips straight to the lobby.
    The right PIN sticks (settings construction_ok) so it's a one-time ask
    per device."""

    def __init__(self):
        self.buf = ""
        self.msg = ""
        self.frame_i = 0

    def anim(self):
        self.frame_i += 1

    def strip(self):
        from . import menu
        return menu.hints(("0-9", "PIN"), ("ENTER", "go"), ("L", "lobby"))

    def key(self, k):
        if k == "escape":
            return ("done", None)               # back out to the title
        if k == "l":
            return ("done", "lobby")
        if k in ("enter", "space"):
            if self.buf == GATE_PIN:
                return ("done", "play")
            self.buf = ""
            self.msg = "That's not it."
            return None
        if k == "backspace":
            self.buf = self.buf[:-1]
            self.msg = ""
        elif len(k) == 1 and k.isdigit() and len(self.buf) < 8:
            self.buf += k
            self.msg = ""
        return None

    def text(self):
        from . import menu
        out = menu.header("UNDER CONSTRUCTION", "")
        out.append_text(menu.blanks(1))
        out.append_text(menu.note("tuipet is being worked on — the game"))
        out.append_text(menu.note("is PIN-locked; the lobby stays open"))
        out.append_text(menu.blanks(1))
        dots = "●" * len(self.buf) + ("_" if (self.frame_i // 4) % 2 else " ")
        out.append_text(menu.row(f"  PIN: {dots}"))
        if self.msg:
            out.append_text(menu.note(self.msg))
        else:
            out.append_text(menu.blanks(1))
        out.append_text(menu.footer("ENTER go   L lobby   ESC back"))
        return out


GATE_PIN = "2974"
