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
        # the CLONE stage vocabulary (Joel 2026-07-15: "title screen is
        # missing mons") -- the old dub names matched NOTHING in the new
        # atlas, so every launch fell back to num 0
        pool = [n for n, r in by.items()
                if r["stage"] in ("Child", "Adult", "Perfect",
                                  "Ultimate-Super Ultimate")
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
        from .grid import lit
        for y, line in enumerate(mascot):
            for x, ch in enumerate(line):
                # clone frames are COLOUR cells -- the old `ch == "1"` test
                # lit ZERO pixels and the mascot vanished (audit 2026-07-15)
                if lit(ch) and 0 <= oy + y < PXH and 0 <= ox + x < COLS:
                    buf[oy + y][ox + x] = 1 if ch == "1" else ch
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
        def _col(v):                   # 1 = ink (wordmark/boot), str = sprite colour
            return LCD_ON if v == 1 else (v if v else LCD_BG)
        t = Text()
        for cy in range(PXH // 2):
            ty, byy = cy * 2, cy * 2 + 1
            for cx in range(COLS):
                t.append("▀", style=f"{_col(buf[ty][cx])} on {_col(buf[byy][cx])}")
            if cy != PXH // 2 - 1:
                t.append("\n")
        return t


