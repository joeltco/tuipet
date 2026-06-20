"""Procedural digi-egg sprites for the hatch sequence.

The DVPetTest build ships only placeholder art for eggs, so tuipet draws its own
classic LCD egg: a speckled oval with an idle wobble and a crack/hatch animation.
Frames are 1-bit bitmaps (lists of '0'/'1' rows), same format as creature sprites.
"""
from __future__ import annotations

W, H = 16, 20


def _ellipse(squash=0, dx=0):
    cx, cy = (W - 1) / 2 + dx, (H - 1) / 2
    rx, ry = W / 2 - 0.5, H / 2 - 0.5 - squash
    rows = []
    for y in range(H):
        row = []
        for x in range(W):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            row.append("1" if nx * nx + ny * ny <= 1.0 else "0")
        rows.append("".join(row))
    return rows


def _band(rows, phase=0):
    """Carve the classic jagged lightning band across the egg's middle."""
    rows = [list(r) for r in rows]
    bandtop = int(H * 0.46)
    for i, y in enumerate((bandtop, bandtop + 1)):
        for x in range(W):
            if rows[y][x] == "1" and (x + phase + i) % 3 == 0:
                rows[y][x] = "0"
    return ["".join(r) for r in rows]


def _crack(rows, depth):
    """Vertical jagged crack growing from the top (depth 0..1)."""
    rows = [list(r) for r in rows]
    cx = W // 2
    n = int(depth * (H - 4))
    jag = [0, 1, -1, 1, 0, -1, 1, -1, 0, 1, -1, 0, 1, -1, 1, 0]
    for y in range(1, 1 + n):
        x = cx + jag[y % len(jag)]
        for xx in (x, x + (1 if y % 2 else -1)):
            if 0 <= xx < W and 0 <= y < H and rows[y][xx] == "1":
                rows[y][xx] = "0"
    return ["".join(r) for r in rows]


# Named animations (each a list of frames). Renderer cycles the frames.
def idle():
    return [_band(_ellipse(squash=0, dx=0), 0),
            _band(_ellipse(squash=1, dx=1), 1)]   # tiny wobble


def hatch():
    base = _ellipse()
    return [_band(base, 0),
            _crack(_band(base, 0), 0.4),
            _crack(_band(base, 1), 0.7),
            _crack(_band(base, 0), 1.0)]


FRAMES = idle() + hatch()
ROLES = {"idle": [0, 1], "egg_idle": [0, 1], "hatch": [2, 3, 4, 5]}


def record():
    """A sprite record compatible with data.load_sprites() entries."""
    return {"num": -1, "name": "Digitama", "stage": "Egg",
            "attribute": "None", "field": "None", "element": "None",
            "spriteSet": 0, "spriteNum": 0, "w": W, "h": H, "frames": FRAMES}


if __name__ == "__main__":
    for i, f in enumerate(FRAMES):
        print(f"frame {i}")
        for r in f:
            print(r.replace("0", " ").replace("1", "#"))
        print()
