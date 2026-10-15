"""The permanent egg TEMPLATE (Joel 2026-10-15: "Just make a permanent template
lol").  Give it ONE approved still design (egg_a, 16x16 '0'/'1' rows on the
shared egg grid) and the dex the egg hatches; it builds the other two frames by
fixed rules, so no egg can drift off the grid again:

  egg_b (wobble)  egg_a squashed into the outline the original eggs share:
                  rows 6..15, each row resampled (nearest neighbour) from a
                  fixed source row onto the shared span, edges inked.
  hatch           rows 0-10: the breakout of an EXISTING egg that hatches the
                  same baby (canonical twin) when there is one; otherwise the
                  baby's own frame 0 seated so its feet rest on row 10, with the
                  shell rim and the Godzilla egg's shard spray kept clear of it.
                  rows 11-15: egg_a's own shell.

  python3 tools/egg_template.py EGG_A.json DEX OUT.json [OUT.png]
      EGG_A.json: {"frames": [egg_a, ...]} or a bare list of 16 rows.
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from tuipet import data, egg as egg_mod, lines  # noqa: E402

# the outlines the original eggs share: row -> (first ink col, last ink col)
STILL = {4: (6, 9), 5: (5, 10), 6: (4, 11), 7: (3, 12), 8: (3, 12), 9: (2, 13),
         10: (2, 13), 11: (2, 13), 12: (2, 13), 13: (3, 12), 14: (4, 11), 15: (5, 10)}
WOBBLE = {6: (6, 9), 7: (4, 11), 8: (3, 12), 9: (2, 13), 10: (2, 13),
          11: (1, 14), 12: (1, 14), 13: (1, 14), 14: (2, 13), 15: (3, 12)}
# wobble row <- still row: the squash drops two of the twelve rows
SQUASH_FROM = {6: 4, 7: 5, 8: 7, 9: 8, 10: 9, 11: 10, 12: 11, 13: 13, 14: 14, 15: 15}
GODZILLA_EGG = "Godzilla Egg"


def outline(frame):
    out = {}
    for y, row in enumerate(frame):
        ink = [x for x, c in enumerate(row) if c == "1"]
        if ink:
            out[y] = (ink[0], ink[-1])
    return out


def on_grid(frame, shape):
    return outline(frame) == shape


def _bank():
    path = os.path.join(os.path.dirname(egg_mod.__file__), "data", "eggs.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def squash(still):
    """egg_a -> egg_b on the shared wobble outline."""
    rows = [["0"] * 16 for _ in range(16)]
    for y, src_y in SQUASH_FROM.items():
        sl, sr = STILL[src_y]
        tl, tr = WOBBLE[y]
        for x in range(tl, tr + 1):
            sx = sl + round((x - tl) * (sr - sl) / max(1, tr - tl))
            rows[y][x] = still[src_y][sx]
        rows[y][tl] = rows[y][tr] = "1"            # the shell edge is always inked
    return ["".join(r) for r in rows]


def donor_hatch(dex):
    """rows 0-10 of an existing egg's hatch that breaks out the same baby."""
    root, _ = lines.canonical_root(dex)
    root = dex if root is None else root
    for e in _bank():
        if root in (e.get("hatch") or []) and not (e.get("hatch_line") or "").isalpha():
            return e["frames"][2][:11]
    for e in _bank():
        if root in (e.get("hatch") or []):
            return e["frames"][2][:11]
    return None


def seated_hatch(dex):
    """rows 0-10 from the baby's own frame 0, feet on row 10, nothing clipped."""
    _, by_num = data.load_sprites()
    baby = by_num[dex]["frames"][0]
    ink = [y for y, r in enumerate(baby) if "1" in r]
    if ink[-1] - ink[0] > 10:
        raise SystemExit(f"#{dex} is {ink[-1] - ink[0] + 1} rows tall -- taller than the 11-row breakout")
    lift = ink[-1] - 10
    g = [["0"] * 16 for _ in range(11)]
    body = set()
    for y in ink:
        for x, c in enumerate(baby[y]):
            if c == "1":
                g[y - lift][x] = "1"
                body.add((y - lift, x))
    for y in (9, 10):                              # the shell rim rising at the sides
        for x in (2, 13):
            if (y, x) not in body:
                g[y][x] = "1"
    shards = next(e for e in _bank() if e.get("hatch_name") == GODZILLA_EGG)["frames"][2]
    near = lambda y, x: any((y + dy, x + dx) in body for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    for y in range(7):
        for x in range(16):
            if shards[y][x] == "1" and (x <= 1 or x >= 13) and not near(y, x):
                g[y][x] = "1"
    return ["".join(r) for r in g]


def build(still, dex):
    if not on_grid(still, STILL):
        raise SystemExit("egg_a is off the shared egg grid: " + repr(outline(still)))
    wobble = squash(still)
    top = donor_hatch(dex) or seated_hatch(dex)
    hatch = top + still[11:]
    assert on_grid(wobble, WOBBLE)
    return [still, wobble, hatch]


def preview(frames, path):
    from PIL import Image, ImageDraw
    s = 10
    im = Image.new("RGB", (3 * (16 * s + 20) + 20, 16 * s + 20), "white")
    d = ImageDraw.Draw(im)
    for i, f in enumerate(frames):
        x0 = 10 + i * (16 * s + 20)
        d.rectangle([x0 - 1, 9, x0 + 16 * s, 10 + 16 * s], outline=(200, 200, 200))
        for y, row in enumerate(f):
            for x, c in enumerate(row):
                if c == "1":
                    d.rectangle([x0 + x * s, 10 + y * s, x0 + x * s + s - 1, 10 + y * s + s - 1],
                                fill="black")
    im.save(path)


def main():
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as fh:
        src = json.load(fh)
    still = src["frames"][0] if isinstance(src, dict) else src
    frames = build(still, int(sys.argv[2]))
    with open(sys.argv[3], "w", encoding="utf-8") as fh:
        json.dump({"frames": frames}, fh)
    if len(sys.argv) > 4:
        preview(frames, sys.argv[4])
    print("ok: still + wobble on the shared grid; hatch shell = still rows 11-15")


if __name__ == "__main__":
    main()
