"""Render the classic V-pet 1-bit sprite bitmaps to the terminal.

Each character cell stacks two vertical pixels using the upper-half block (U+2580).
Top pixel -> foreground colour, bottom pixel -> background colour. "Off" pixels are
left transparent (terminal default) unless an LCD background colour is supplied.
"""
from __future__ import annotations
from rich.text import Text

def blit(bm, ox, oy, color=None):
    """Sprite bitmap -> (x,y[,color]) pixel list for render_scene/_screen's
    overlay.  `color` tints the lit pixels (the per-mon projectile tint,
    audit 2026-07-15); default stays the LCD ink.
    Tolerates None/blank frames: 28 foods ship a blank 'eaten away' last frame
    that extracts as None -- the eat fx crashed on their final bite (2026-07-04).
    Lived in three verbatim copies (app/training/strikefx; refactor 2026-07-05)."""
    if not bm:
        return []
    if color:
        return [(ox + x, oy + y, color) for y, row in enumerate(bm)
                for x, c in enumerate(row) if c == "1"]
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _stamp(buf, pts, cols, px_h, clip=None):
    """Overlay pixels -> the buffer, clipped to the LCD (and to `clip`).
    A 3-tuple pixel carries its own colour; a bare (x,y) stamps ink."""
    cx0, cx1, cy0, cy1 = clip if clip else (0, cols, 0, px_h)
    for p in pts:
        ox_, oy_ = p[0], p[1]
        if cy0 <= oy_ < cy1 and cx0 <= ox_ < cx1 and 0 <= oy_ < px_h and 0 <= ox_ < cols:
            buf[oy_][ox_] = p[2] if len(p) > 2 else 1


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
            tv, bv = buf[ty][cx], buf[byy][cx]
            # a buffer cell is 0 (bg), 1 (theme ink) or a "#rrggbb" COLOUR
            # pixel (the colour-sprite lane, 2026-07-15)
            tc = (tv if isinstance(tv, str) else on) if tv \
                else ("#" + bgimg[ty][cx * 6:cx * 6 + 6] if bgimg else bg)
            bc = (bv if isinstance(bv, str) else on) if bv \
                else ("#" + bgimg[byy][cx * 6:cx * 6 + 6] if bgimg else bg)
            t.append("▀", style=f"{tc} on {bc}")
        if cy != rows - 1:
            t.append("\n")
    return t


# A few palettes. "on" = creature ink, "off" = LCD background (None = transparent).
def render_screen(frame_rows, cols, rows, on="#2b2e31", bg="#c6c9cc", baseline=True, mirror=False, xshift=0, yshift=0, overlay=None, bgimg=None, clip=None, overlay_free=None):
    """Compose a sprite centred on a fixed cols x rows (character) LCD screen.

    Returns a rich Text. The screen is rows*2 pixels tall; the sprite is blitted
    centred horizontally and sitting on the floor (baseline) so it doesn't bob
    off the ground between frames of different heights.
    """
    buf = fill_buf(frame_rows, cols, rows * 2, baseline=baseline, mirror=mirror,
                   xshift=xshift, yshift=yshift, overlay=overlay, clip=clip,
                   overlay_free=overlay_free)
    return _paint_cells(buf, cols, rows, on, bg, bgimg)


def fill_buf(frame_rows, cols, px_h, baseline=True, mirror=False, xshift=0,
             yshift=0, overlay=None, clip=None, overlay_free=None):
    """The shared pixel-buffer builder behind render_screen.  `clip` is an
    (x0, x1, y0, y1) half-open window over sprite ink AND `overlay`: the main
    pet scene passes the locked 32x16 play window -- a real dot matrix
    physically ENDS at its edge, so off-window ink is simply not displayed
    (which is also HOW things exit: walking off the left or right edge, the
    lawful occasions -- Joel 2026-07-11).  `overlay_free` is stamped WITHOUT
    the window: weather, which may rain over the whole LCD (Joel: "rain and
    snow can cover the whole lcd").  Exposed so tests can assert the window
    invariant on this buffer, the renderer's ground truth."""
    buf = [[0] * cols for _ in range(px_h)]
    cx0, cx1, cy0, cy1 = clip if clip else (0, cols, 0, px_h)
    if frame_rows and mirror:
        frame_rows = [r[::-1] for r in frame_rows]
    if frame_rows:
        from .grid import lit
        sw = max(len(r) for r in frame_rows)
        sh = len(frame_rows)
        ox = (cols - sw) // 2 + xshift
        oy = max(0, (px_h - sh - 2) if baseline else (px_h - sh) // 2) - yshift   # +yshift lifts the sprite (a hop)
        for y, line in enumerate(frame_rows):
            for x, ch in enumerate(line):
                if lit(ch):
                    py, pxx = oy + y, ox + x
                    if cy0 <= py < cy1 and cx0 <= pxx < cx1 \
                            and 0 <= py < px_h and 0 <= pxx < cols:
                        buf[py][pxx] = 1 if ch == "1" else ch
    if overlay:                              # scene actors / fx props (window-clipped)
        _stamp(buf, overlay, cols, px_h, clip=clip)
    if overlay_free:                         # unclipped overlay: the whole LCD
        _stamp(buf, overlay_free, cols, px_h)
    return buf


def render_scene(placements, cols, rows, on="#2b2e31", bg="#c6c9cc", overlay=None, bgimg=None, clip=None, overlay_free=None):
    """Compose several sprites onto one LCD screen.

    placements: list of (frame_rows, x_left, mirror). Each sprite sits on the
    floor (baseline). Used for the battle scene (pet vs enemy facing off).
    """
    px_h = rows * 2
    buf = [[0] * cols for _ in range(px_h)]
    cx0, cx1, cy0, cy1 = clip if clip else (0, cols, 0, px_h)
    from .grid import lit
    for frame_rows, x_left, mirror in placements:
        if not frame_rows:
            continue
        src = [r[::-1] for r in frame_rows] if mirror else frame_rows
        sh = len(src)
        oy = max(0, px_h - sh - 2)
        for y, line in enumerate(src):
            for x, ch in enumerate(line):
                if lit(ch):
                    py, px = oy + y, x_left + x
                    if cy0 <= py < cy1 and cx0 <= px < cx1 \
                            and 0 <= py < px_h and 0 <= px < cols:
                        buf[py][px] = 1 if ch == "1" else ch
    if overlay:                              # projectiles / impact bursts
        _stamp(buf, overlay, cols, px_h, clip=clip)
    if overlay_free:                         # unclipped overlay: the whole LCD
        _stamp(buf, overlay_free, cols, px_h)
    return _paint_cells(buf, cols, rows, on, bg, bgimg)


UPPER, LOWER, FULL = "\u2580", "\u2584", "\u2588"   # half/full blocks (bitmap_text's pixels;
#                                                      the dead-code sweep deleted them with the
#                                                      OLD renderer while bitmap_text still reads
#                                                      them -- the v0.2.166-175 feed-screen crash)


def marquee(s, width, step, gap="   ", hold=8):
    """Universal FIELD scroll (menu-bounds audit 2026-07-07): text that fits
    its slot renders unchanged; longer text slides a width-wide window that
    holds on the head, then loops through a gap.  Panels key `step` off their
    own anim counter, so the CHROME around the field never moves -- the app's
    _hud marquee scrolls whole overflow lines as a safety net, but a strip
    that always overflowed slid its key hints out of view with it."""
    if len(s) <= width:
        return s
    loop = s + gap
    t = step % (len(loop) + hold)
    off = 0 if t < hold else t - hold
    return (loop + loop)[off:off + width]


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
