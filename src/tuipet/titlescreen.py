"""Boot/title screen shown on launch (the device powering on)."""
from __future__ import annotations
import random
from rich.text import Text
from . import data
from .theme import LCD_ON, LCD_BG

COLS, PXH = 40, 24
BOOT_BLIP = 4      # frames of all-segments-on (power-on flash)
BOOT_FADE = 8      # frames of transition from the flash into the title
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


# --- boot transitions -------------------------------------------------------
# Each takes the finished title buffer and a step in 0..BOOT_FADE-1 and lays
# lit segments over the not-yet-revealed part; every effect must reveal
# SOMETHING at step 0 (the flash has to visibly break the moment the
# transition starts) and keep moving every step.

def _fx_dissolve(buf, step):
    keep = BOOT_FADE - step                      # thinning noise as the title emerges
    for y in range(PXH):
        for x in range(COLS):
            if (x * 7 + y * 13 + step * 5) % (BOOT_FADE + 1) < keep:
                buf[y][x] = 1


def _fx_wipe(buf, step):
    edge = (step + 1) * COLS // BOOT_FADE        # curtain sweeps left to right
    for y in range(PXH):
        for x in range(edge, COLS):
            buf[y][x] = 1


def _fx_scan(buf, step):
    edge = (step + 1) * PXH // BOOT_FADE         # CRT scan, top to bottom
    for y in range(edge, PXH):
        for x in range(COLS):
            buf[y][x] = 1


def _fx_blinds(buf, step):
    slit = 1 + step * 5 // (BOOT_FADE - 1)       # venetian slats open downward
    for y in range(PXH):
        if y % 6 >= slit:
            for x in range(COLS):
                buf[y][x] = 1


def _fx_iris(buf, step):
    rx = (step + 1) * (COLS // 2) // BOOT_FADE   # box iris opens from centre
    ry = max(1, (step + 1) * (PXH // 2) // BOOT_FADE)
    cx, cy = COLS // 2, PXH // 2
    for y in range(PXH):
        for x in range(COLS):
            if abs(x - cx) > rx or abs(y - cy) > ry:
                buf[y][x] = 1


def _fx_checker(buf, step):
    for y in range(PXH):                         # 4x4 tiles flip in, staggered
        for x in range(COLS):
            if ((x // 4) * 3 + (y // 4) * 7) % BOOT_FADE > step:
                buf[y][x] = 1


BOOT_FX = (_fx_dissolve, _fx_wipe, _fx_scan, _fx_blinds, _fx_iris, _fx_checker)


class TitlePanel:
    """Shows a bobbing mascot + the TUIPET wordmark; any key starts the game (q quits)."""

    def __init__(self):
        _, by = data.load_sprites()
        pool = [n for n, r in by.items()
                if r["stage"] in ("Rookie", "Champion", "Ultimate", "Mega")
                and not data.is_placeholder(n)]
        self.num = random.choice(pool) if pool else next(iter(by))   # ONE mon per
        #                                      title (Joel 2026-07-20: no switching)
        self.fx = random.choice(BOOT_FX)     # this power-on's transition
        self.frame_i = 0
        self.sfx = "boot"                    # the power-on jingle (baked from the
        #                                      device's own beeps — tools/make_boot_jingle.py)
        #                                      rides the flash via the app's anim-sfx drain
        from . import update
        self.version = update.current_version() or ""   # blank when running from source

    def anim(self):
        self.frame_i += 1

    def strip(self):
        """The press-to-start prompt rides the #msg strip.  It used to be set
        once by the app and the v0.2.223 strip plumbing blanked it a frame
        later (title audit 2026-07-04) — panels own their strips now."""
        if self.frame_i < BOOT_BLIP + BOOT_FADE:
            return ""                            # let the power-on play in silence
        tag = f"  [dim]v{self.version}[/dim]" if self.version else ""
        # pulse bright/dim rather than blink off: same visible width both
        # phases, so the centred strip never jumps
        if self.frame_i % 12 < 8:
            return "[b]▸ PRESS ENTER ◂[/b]" + tag
        return "[dim]▸ PRESS ENTER ◂[/dim]" + tag

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
        # power-on: all segments flash black, then this boot's randomly drawn
        # transition (BOOT_FX) plays the title in
        boot = self.frame_i
        if boot < BOOT_BLIP:
            buf = [[1] * COLS for _ in range(PXH)]
        elif boot < BOOT_BLIP + BOOT_FADE:
            self.fx(buf, boot - BOOT_BLIP)
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
