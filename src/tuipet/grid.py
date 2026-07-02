"""The ONE creature grid every screen sits on -- the single source of truth for the
LCD's usable real estate, so battle / training / jogress / tournament / evolution /
adventure / the main roaming view all share ONE geometry (no per-screen drift).

The LCD is 40x24px.  Sprites live in a 32x16 window centred in it:

    x in [X0, X1)   ==  [4, 36)      (4px margin each side)
    y in [TOP, FLOOR) == [6, 22)     (a 16px-tall band)
    every sprite BASELINES on the floor -> its bottom pixel lands at y21,
    which is 2px above the y23 bottom border.

Rules enforced by the helpers below:
  - in-grid : no sprite pixel escapes x[4,36) / y[6,22)
  - grounded: content bottoms at y21 (render_scene already baselines there)
  - no overlap: face-off placements are pulled to opposite edges with a centre gap
"""
from __future__ import annotations

COLS = 40
ROWS = 12
PXH = ROWS * 2            # 24

X0 = 4                    # left edge of the grid
W = 32                    # grid width
X1 = X0 + W               # 36: right edge (exclusive)
CELL = 16                 # one creature cell (two cells side by side == the 32 grid)
TOP = PXH - 18            # 6: top of the 16px band
FLOOR = PXH - 2           # 22: the floor -- baseline, 2px above the bottom border
BAND = FLOOR - TOP        # 16


def _crop(sprite):
    """Trim a sprite to its lit content (creatures carry transparent padding)."""
    if not sprite:
        return sprite
    w = max(len(r) for r in sprite)
    rows = [r.ljust(w, "0") for r in sprite]
    ys = [y for y, r in enumerate(rows) if "1" in r]
    xs = [x for x in range(w) if any(r[x] == "1" for r in rows)]
    if not ys or not xs:
        return sprite
    return [rows[y][xs[0]:xs[-1] + 1] for y in range(ys[0], ys[-1] + 1)]


def band_h(ph=PXH):
    """Tallest a sprite may be to sit inside the band AND ground 2px above the bottom.
    24px arena -> 16 (the classic creature band, top at y6); a shorter embedded strip
    (e.g. the 14px jogress/tournament/adventure box) -> ph-2, filling it grounded."""
    return min(CELL, ph - 2)


def fit_band(sprite, ph=PXH):
    """Box-downscale a sprite's HEIGHT to <= band_h(ph) so it never overflows the box."""
    if not sprite:
        return sprite
    target = band_h(ph)
    h = len(sprite)
    if h <= target:
        return sprite
    w = max(len(r) for r in sprite)
    rows = [r.ljust(w, "0") for r in sprite]
    sc = h / target
    out = []
    for y in range(target):
        y0, y1 = int(y * sc), max(int(y * sc) + 1, int((y + 1) * sc))
        out.append("".join("1" if sum(rows[yy][x] == "1" for yy in range(y0, y1)) * 2 >= (y1 - y0)
                           else "0" for x in range(w)))
    return out


def fit_w(sprite, target):
    """Box-downscale a sprite's WIDTH to <= target."""
    if not sprite:
        return sprite
    w = max(len(r) for r in sprite)
    if w <= target:
        return sprite
    rows = [r.ljust(w, "0") for r in sprite]
    sc = w / target
    out = []
    for r in rows:
        out.append("".join("1" if sum(r[xx] == "1" for xx in range(int(x * sc), max(int(x * sc) + 1, int((x + 1) * sc)))) * 2
                           >= (max(int(x * sc) + 1, int((x + 1) * sc)) - int(x * sc)) else "0"
                           for x in range(target)))
    return out


def fit(sprite, ph=PXH):
    """Cap a sprite to one grid cell: <= band_h(ph) tall AND <= CELL wide."""
    return fit_w(fit_band(sprite, ph), CELL)


def width(sprite):
    return max((len(r) for r in sprite), default=0)


def prep(sprite, ph=PXH):
    """Fit-to-cell + crop-to-content -- the grid-ready form the placement helpers use
    (handy for custom slide animations that need the fitted sprite + its width)."""
    return _crop(fit(sprite, ph))


def left(sprite, mirror=False, ph=PXH):
    """(sprite, x, mirror) hugging the grid's LEFT edge (x == X0), fitted + cropped."""
    s = _crop(fit(sprite, ph))
    return (s, X0, mirror)


def right(sprite, mirror=True, ph=PXH):
    """(sprite, x, mirror) hugging the grid's RIGHT edge (right pixel at X1-1)."""
    s = _crop(fit(sprite, ph))
    return (s, X1 - width(s), mirror)


def center(sprite, mirror=False, ph=PXH):
    """(sprite, x, mirror) centred in the 32 grid, fitted + cropped."""
    s = _crop(fit(sprite, ph))
    return (s, X0 + (W - width(s)) // 2, mirror)


def cell(sprite, side, mirror=False, ph=PXH):
    """(sprite, x, mirror) centred in cell 0 (left) or 1 (right) of the 32x16 grid."""
    s = _crop(fit(sprite, ph))
    return (s, X0 + side * CELL + (CELL - width(s)) // 2, mirror)


def faceoff(left_sprite, right_sprite, left_mirror=False, right_mirror=True, ph=PXH):
    """Two creatures facing off: left hugs X0, right hugs X1, each fitted to a cell so a
    centre GAP always remains (no overlap).  Returns [left_placement, right_placement].
    If cropped widths would still collide, both are width-fit to CELL first (they can't
    exceed 16 each -> 32 total == the grid, worst case touching, normally a gap)."""
    ls = _crop(fit(left_sprite, ph)) if left_sprite else None
    rs = _crop(fit(right_sprite, ph)) if right_sprite else None
    lw = width(ls) if ls else 0
    rw = width(rs) if rs else 0
    if lw + rw > W:                        # would collide -> squeeze both into their cells
        ls = fit_w(ls, CELL) if ls else ls
        rs = fit_w(rs, CELL) if rs else rs
        lw, rw = width(ls) if ls else 0, width(rs) if rs else 0
    out = []
    if ls:
        out.append((ls, X0, left_mirror))
    if rs:
        out.append((rs, X1 - rw, right_mirror))
    return out


def roam_bounds(sprite_w=CELL):
    """(left_bound, right_bound) for a roaming/walking pet so it stays inside the grid:
    x in [X0, X1 - sprite_w].  Feed to anim.Roamer.step(left_bound, right_bound)."""
    return X0, X1 - sprite_w
