"""The permanent egg TEMPLATE (Joel 2026-10-15: "Just make a permanent template
lol").  Give it ONE approved still design (egg_a, 16x16 '0'/'1' rows on the
shared egg grid) and the dex the egg hatches; it builds the other two frames by
fixed rules, so no egg can drift off the grid again:

  egg_b (wobble)  egg_a squashed into the outline the original eggs share:
                  rows 6..15, each row resampled (nearest neighbour) from a
                  fixed source row onto the shared span, edges inked.
  hatch           the hatch of the ORIGINAL egg that hatches the same baby,
                  with egg_a's shell shown only where that original's shell is
                  untouched (donor_hatch); a baby no original hatches is seated
                  from its own frame 0 on egg_a's shell (seated_hatch).

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


def template_shape(k):
    """The SHAPE the original eggs share for frame k (Joel: "Theres perfectly
    built eggs already fucking made ... Use those as template shapes"): the
    cells inked in EVERY original on the shared outline, and the cells blank in
    every one.  Measured from the bank, never typed in."""
    target = STILL if k == 0 else WOBBLE
    originals = [e for e in _bank()
                 if not (e.get("hatch_line") or "").isalpha()
                 and on_grid(e["frames"][k], target)]
    ink = {(y, x) for y in range(16) for x in range(16)
           if all(e["frames"][k][y][x] == "1" for e in originals)}
    blank = {(y, x) for y in range(16) for x in range(16)
             if all(e["frames"][k][y][x] == "0" for e in originals)}
    return ink, blank


def stamp(frame, k):
    """Press a frame onto the originals' shared shape."""
    ink, blank = template_shape(k)
    rows = [list(r) for r in frame]
    for y, x in ink:
        rows[y][x] = "1"
    for y, x in blank:
        rows[y][x] = "0"
    return ["".join(r) for r in rows]


def squash(still):
    """egg_a -> egg_b: the motif resampled onto the wobble rows, then pressed
    onto the shape every original wobble shares."""
    rows = [["0"] * 16 for _ in range(16)]
    for y, src_y in SQUASH_FROM.items():
        sl, sr = STILL[src_y]
        tl, tr = WOBBLE[y]
        for x in range(tl, tr + 1):
            sx = sl + round((x - tl) * (sr - sl) / max(1, tr - tl))
            rows[y][x] = still[src_y][sx]
    return stamp(["".join(r) for r in rows], 1)


def donor_egg(dex):
    """The ORIGINAL egg (not a card egg) that hatches the same baby, or None."""
    root, _ = lines.canonical_root(dex)
    root = dex if root is None else root
    for e in _bank():
        if root in (e.get("hatch") or []) and not (e.get("hatch_line") or "").isalpha():
            return e
    return None


def donor_hatch(still, donor):
    """The original egg's hatch frame used as the template (Joel 2026-10-15,
    "Good enough"): rows 0-10 exactly as the original breaks out; rows 11-15
    keep every pixel the original's hatch CHANGED from its still (the cracks,
    the baby's feet) and show OUR shell only where the original's shell is
    untouched."""
    ds, dh = donor["frames"][0], donor["frames"][2]
    bottom = ["".join(still[y][x] if dh[y][x] == ds[y][x] else dh[y][x] for x in range(16))
              for y in range(11, 16)]
    return dh[:11] + bottom


# the originals' own numbers (measured over the 46 eggs, 2026-10-15): the
# breakout most often shows the baby's frame 5, at FULL size, its feet on row 12
# -- two rows down inside the shell, which is drawn in FRONT of it
SEAT_FRAME = 5
SEAT_FEET_ROW = 12
# ...and 29 of the 46 draw the broken shell's RIM as a line right across the egg
# at row 10/11, in front of the baby (Joel: "You guys cut off the top line of
# the bottom half shell") -- the originals' own row-10 rim
SEAT_RIM = (10, "0010111111111010")


def seated_hatch(dex, still):
    """No original hatches this baby: do what the originals do -- the baby's
    own full-size frame 5 (frame 0 if it has none), feet on row 12, the egg's
    shell (still rows 11-15) in front of its lower body, the shell rim and the
    Godzilla egg's shard spray kept clear of it.  A baby too tall for that sits
    with its head on row 0 and sinks deeper -- never clipped at the top."""
    _, by_num = data.load_sprites()
    frames = by_num[dex]["frames"]
    baby = frames[SEAT_FRAME] if len(frames) > SEAT_FRAME and any("1" in r for r in frames[SEAT_FRAME]) \
        else frames[0]
    ink = [y for y, r in enumerate(baby) if "1" in r]
    height = ink[-1] - ink[0] + 1
    feet = max(SEAT_FEET_ROW, height - 1)
    lift = ink[-1] - feet
    g = [["0"] * 16 for _ in range(11)] + [list(r) for r in still[11:]]
    body = set()
    for y in ink:
        if y - lift > 10:                          # behind the shell's front
            continue
        for x, c in enumerate(baby[y]):
            if c == "1":
                g[y - lift][x] = "1"
                body.add((y - lift, x))
    rim_y, rim = SEAT_RIM                          # the shell's broken top, in FRONT
    g[rim_y] = list(rim)
    g[rim_y - 1][2] = g[rim_y - 1][13] = "1"       # the walls rise one more row at the sides
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
    still = stamp(still, 0)
    wobble = squash(still)
    donor = donor_egg(dex)
    hatch = donor_hatch(still, donor) if donor else seated_hatch(dex, still)
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
