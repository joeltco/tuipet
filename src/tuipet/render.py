"""Render DVPet 1-bit sprite bitmaps to the terminal.

Each character cell stacks two vertical pixels using the upper-half block (U+2580).
Top pixel -> foreground colour, bottom pixel -> background colour. "Off" pixels are
left transparent (terminal default) unless an LCD background colour is supplied.
"""
from __future__ import annotations
from rich.text import Text

def blit(bm, ox, oy):
    """Sprite bitmap -> (x,y) pixel list for render_scene/_screen's overlay.
    Tolerates None/blank frames: 28 foods ship a blank 'eaten away' last frame
    that extracts as None -- the eat fx crashed on their final bite (2026-07-04).
    Lived in three verbatim copies (app/training/strikefx; refactor 2026-07-05)."""
    if not bm:
        return []
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _stamp(buf, pts, cols, px_h):
    """Overlay pixels -> the buffer, clipped to the LCD."""
    for ox_, oy_ in pts:
        if 0 <= oy_ < px_h and 0 <= ox_ < cols:
            buf[oy_][ox_] = 1


def _paint_cells(buf, cols, rows, on, bg, bgimg):
    """The half-block compositor: a filled pixel buffer -> Rich Text.
    render_screen and render_scene carried two byte-identical copies of this
    loop, which had to be edited in lockstep (refactor 2026-07-05).  Background
    art passes through the active theme's quantizer when it declares one
    (gameboy's light DMG shades) -- this is the ONE spot every bgimg crosses,
    so weather tints, cross-fades and lightning all inherit the palette.
    Sprites stay readable by LAYERING, not outlines: a ramp theme's darkest
    ink is reserved for sprites, never handed to background art (the halo
    experiment this replaced boxed the mon -- redo 2026-07-05)."""
    if bgimg:
        from . import theme
        bgimg = theme.themed_bg(bgimg)
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


# A few palettes. "on" = creature ink, "off" = LCD background (None = transparent).
def render_screen(frame_rows, cols, rows, on="#2b2e31", bg="#c6c9cc", baseline=True, mirror=False, xshift=0, yshift=0, overlay=None, bgimg=None):
    """Compose a sprite centred on a fixed cols x rows (character) LCD screen.

    Returns a rich Text. The screen is rows*2 pixels tall; the sprite is blitted
    centred horizontally and sitting on the floor (baseline) so it doesn't bob
    off the ground between frames of different heights.
    """
    px_h = rows * 2
    buf = [[0] * cols for _ in range(px_h)]
    if frame_rows and mirror:
        frame_rows = [r[::-1] for r in frame_rows]
    if frame_rows:
        sw = max(len(r) for r in frame_rows)
        sh = len(frame_rows)
        ox = (cols - sw) // 2 + xshift
        oy = max(0, (px_h - sh - 2) if baseline else (px_h - sh) // 2) - yshift   # +yshift lifts the sprite (a hop)
        for y, line in enumerate(frame_rows):
            for x, ch in enumerate(line):
                if ch == "1":
                    py, pxx = oy + y, ox + x
                    if 0 <= py < px_h and 0 <= pxx < cols:
                        buf[py][pxx] = 1
    if overlay:                              # weather: rain/snow/cloud pixels
        _stamp(buf, overlay, cols, px_h)
    return _paint_cells(buf, cols, rows, on, bg, bgimg)


def render_scene(placements, cols, rows, on="#2b2e31", bg="#c6c9cc", overlay=None, bgimg=None):
    """Compose several sprites onto one LCD screen.

    placements: list of (frame_rows, x_left, mirror). Each sprite sits on the
    floor (baseline). Used for the battle scene (pet vs enemy facing off).
    """
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
        _stamp(buf, overlay, cols, px_h)
    return _paint_cells(buf, cols, rows, on, bg, bgimg)


UPPER, LOWER, FULL = "\u2580", "\u2584", "\u2588"   # half/full blocks (bitmap_text's pixels;
#                                                      the dead-code sweep deleted them with the
#                                                      OLD renderer while bitmap_text still reads
#                                                      them -- the v0.2.166-175 feed-screen crash)


def bitmap_text(rows, on, bg, pad_to=0):
    """1-bit rows -> half-block Rich Text lines (square pixels).  The one
    implementation behind every icon/badge mini-render (audit 2026-07: this
    lived in three drifting copies)."""
    from rich.text import Text
    if not rows:
        return []
    w = max(len(r) for r in rows)
    g = [r.ljust(w, "0") for r in rows]
    if len(g) % 2:
        g.append("0" * w)
    out = []
    for y in range(0, len(g), 2):
        t = Text()
        for x in range(w):
            top, bot = g[y][x] == "1", g[y + 1][x] == "1"
            ch = FULL if top and bot else UPPER if top else LOWER if bot else " "
            t.append(ch, style=f"{on} on {bg}")
        if pad_to and w < pad_to:
            t.append(" " * (pad_to - w))
        out.append(t)
    return out


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
