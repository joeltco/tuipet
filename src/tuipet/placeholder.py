"""Generic substitute sprite for Digimon whose art is unfinished in the test build
(their sheet cell is a solid placeholder square). Rather than show a black block,
tuipet draws this friendly "mystery monster" blob with a small idle wobble.
"""
from __future__ import annotations

W, H = 16, 15


def _blob(squash=0):
    cx, cy = (W - 1) / 2, (H - 1) / 2
    rx, ry = W / 2 - 0.5, H / 2 - 0.5 - squash
    rows = []
    for y in range(H):
        row = []
        for x in range(W):
            nx, ny = (x - cx) / rx, (y - cy) / ry
            row.append("1" if nx * nx + ny * ny <= 1.0 else "0")
        rows.append(row)
    # carve two eyes (upper third) and a small mouth
    ey = int(H * 0.38)
    for ex in (int(W * 0.32), int(W * 0.62)):
        for dy in range(2):
            for dx in range(2):
                if 0 <= ey + dy < H and 0 <= ex + dx < W:
                    rows[ey + dy][ex + dx] = "0"
    my = int(H * 0.62)
    for mx in range(int(W * 0.38), int(W * 0.62)):
        rows[my][mx] = "0"
    return ["".join(r) for r in rows]


_F0 = _blob(0)
_F1 = _blob(1)            # slightly squished -> wobble
FRAMES = [_F0, _F1] * 6   # 12 frames; any role index 0-10 lands on a blob frame


def record(num, name, stage, attribute):
    return {"num": num, "name": name, "stage": stage, "attribute": attribute,
            "field": "None", "element": "None", "spriteSet": 0, "spriteNum": 0,
            "w": W, "h": H, "frames": FRAMES, "_placeholder": True}


if __name__ == "__main__":
    for r in _F0:
        print(r.replace("0", " ").replace("1", "#"))
