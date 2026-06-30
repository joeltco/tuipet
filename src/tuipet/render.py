"""Render DVPet 1-bit sprite bitmaps to the terminal.

Each character cell stacks two vertical pixels using the upper-half block (U+2580).
Top pixel -> foreground colour, bottom pixel -> background colour. "Off" pixels are
left transparent (terminal default) unless an LCD background colour is supplied.
"""
from __future__ import annotations
from rich.segment import Segment
from rich.style import Style
from rich.text import Text

# A few palettes. "on" = creature ink, "off" = LCD background (None = transparent).
PALETTES = {
    "lcd":   ("#2b2e31", "#c6c9cc"),   # grey pocket-LCD
    "vpet":  ("#1a1a1a", "#8cb89a"),   # grey-green pocket LCD
    "amber": ("#3a1f00", "#ffb000"),
    "mono":  ("#e6e6e6", None),        # white ink, transparent bg
    "ink":   ("#101010", None),        # black ink, transparent bg
}

UPPER, LOWER, FULL, EMPTY = "▀", "▄", "█", " "

# Authentic play field: 16×16 sprites live in a 32-dot-wide window. The LCD canvas itself
# stays wider (e.g. 40) and shows background in the margins; sprites ANCHOR (no clip) inside
# a centred 32-wide band. cols<=PLAY_COLS => the whole width is the play field (no clamp).
PLAY_COLS = 32


def frame_segments(rows, on="#e6e6e6", off=None):
    """Yield Rich Segments for one bitmap frame (list of '0'/'1' strings)."""
    if not rows:
        return
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, "0") for r in rows]
    if len(rows) % 2:
        rows.append("0" * w)
    for y in range(0, len(rows), 2):
        top, bot = rows[y], rows[y + 1]
        for x in range(w):
            t, b = top[x] == "1", bot[x] == "1"
            if t and b:
                yield Segment(FULL, Style(color=on))
            elif t and not b:
                yield Segment(UPPER, Style(color=on, bgcolor=off))
            elif b and not t:
                yield Segment(LOWER, Style(color=on, bgcolor=off))
            else:
                yield Segment(EMPTY if off is None else UPPER,
                              Style(bgcolor=off) if off else Style())
        yield Segment("\n")


def frame_text(rows, on="#e6e6e6", off=None) -> Text:
    """Build a Rich Text (handy inside Textual Static widgets)."""
    t = Text()
    for seg in frame_segments(rows, on, off):
        t.append(seg.text, seg.style)
    return t


if __name__ == "__main__":
    import gzip
    import json
    import os
    import sys
    here = os.path.dirname(__file__)
    data = json.load(gzip.open(os.path.join(here, "data/dm20_sprites.json.gz"), "rt"))["sprites"]
    by = {d["name"]: d for d in data}
    name = sys.argv[1] if len(sys.argv) > 1 else "Agumon"
    pal = sys.argv[2] if len(sys.argv) > 2 else "lcd"
    on, off = PALETTES.get(pal, PALETTES["lcd"])
    d = by.get(name) or data[0]
    from rich.console import Console
    c = Console()
    c.print(f"[bold]{d['name']}[/] ({d['stage']}, {d['attribute']})  {d['w']}x{d['h']}px  palette={pal}")
    for i in (0, 1, 2, 6):  # DVPet: idle, idle-b, sleep, attack
        c.print(f"frame {i}:")
        c.print(frame_text(d["frames"][i], on, off))


def render_screen(frame_rows, cols, rows, on="#2b2e31", bg="#c6c9cc", baseline=True, mirror=False, xshift=0, yshift=0, corner=None, overlay=None, bgimg=None):
    """Compose a sprite centred on a fixed cols x rows (character) LCD screen.

    Returns a rich Text. The screen is rows*2 pixels tall; the sprite is blitted
    centred horizontally and sitting on the floor (baseline) so it doesn't bob
    off the ground between frames of different heights.
    """
    from rich.text import Text
    px_h = rows * 2
    buf = [[0] * cols for _ in range(px_h)]
    if frame_rows and mirror:
        frame_rows = [r[::-1] for r in frame_rows]
    if frame_rows:
        sw = max(len(r) for r in frame_rows)
        sh = len(frame_rows)
        ox = (cols - sw) // 2 + xshift
        if cols > PLAY_COLS and sw <= PLAY_COLS:   # anchor the sprite inside the centred 32-wide play window
            px0 = (cols - PLAY_COLS) // 2
            ox = max(px0, min(ox, px0 + PLAY_COLS - sw))
        oy = max(0, (px_h - sh - 2) if baseline else (px_h - sh) // 2) - yshift   # +yshift lifts the sprite (a hop)
        for y, line in enumerate(frame_rows):
            for x, ch in enumerate(line):
                if ch == "1":
                    py, pxx = oy + y, ox + x
                    if 0 <= py < px_h and 0 <= pxx < cols:
                        buf[py][pxx] = 1
    if corner:                               # sun/moon tucked into the top-right
        cw = max(len(r) for r in corner)
        cx0 = cols - cw - 1
        for y, line in enumerate(corner):
            for x, ch in enumerate(line):
                if ch == "1":
                    py, pxx = 1 + y, cx0 + x
                    if 0 <= py < px_h and 0 <= pxx < cols:
                        buf[py][pxx] = 1
    if overlay:                              # weather: rain/snow/cloud pixels
        for ox_, oy_ in overlay:
            if 0 <= oy_ < px_h and 0 <= ox_ < cols:
                buf[oy_][ox_] = 1
    t = Text()
    for cy in range(rows):
        ty, byy = cy * 2, cy * 2 + 1
        for cx in range(cols):
            tc = on if buf[ty][cx] else ("#" + bgimg[ty][cx * 6:cx * 6 + 6] if bgimg else bg)
            bc = on if buf[byy][cx] else ("#" + bgimg[byy][cx * 6:cx * 6 + 6] if bgimg else bg)
            t.append("▀", style=f"{tc} on {bc}")
        if cy != rows - 1:
            t.append("\n")
    return t


def render_scene(placements, cols, rows, on="#2b2e31", bg="#c6c9cc", overlay=None, bgimg=None):
    """Compose several sprites onto one LCD screen.

    placements: list of (frame_rows, x_left, mirror). Each sprite sits on the
    floor (baseline). Used for the battle scene (pet vs enemy facing off).
    """
    from rich.text import Text
    px_h = rows * 2
    buf = [[0] * cols for _ in range(px_h)]
    for frame_rows, x_left, mirror in placements:
        if not frame_rows:
            continue
        src = [r[::-1] for r in frame_rows] if mirror else frame_rows
        sh = len(src)
        oy = max(0, px_h - sh - 2)
        for y, line in enumerate(src):
            for x, ch in enumerate(line):
                if ch == "1":
                    py, px = oy + y, x_left + x
                    if 0 <= py < px_h and 0 <= px < cols:
                        buf[py][px] = 1
    if overlay:                              # projectiles / impact bursts
        for ox_, oy_ in overlay:
            if 0 <= oy_ < px_h and 0 <= ox_ < cols:
                buf[oy_][ox_] = 1
    t = Text()
    for cy in range(rows):
        ty, byy = cy * 2, cy * 2 + 1
        for cx in range(cols):
            tc = on if buf[ty][cx] else ("#" + bgimg[ty][cx * 6:cx * 6 + 6] if bgimg else bg)
            bc = on if buf[byy][cx] else ("#" + bgimg[byy][cx * 6:cx * 6 + 6] if bgimg else bg)
            t.append("▀", style=f"{tc} on {bc}")
        if cy != rows - 1:
            t.append("\n")
    return t


def downsample(rows, f):
    """Box-downsample a 1-bit bitmap by integer factor f (for shrinking 3x icons)."""
    if not rows or f <= 1:
        return rows
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, "0") for r in rows]
    h = len(rows)
    out = []
    for y in range(h // f):
        line = []
        for x in range(w // f):
            c = sum(rows[y*f+dy][x*f+dx] == "1" for dy in range(f) for dx in range(f))
            line.append("1" if c * 2 >= f * f else "0")
        out.append("".join(line))
    return out
