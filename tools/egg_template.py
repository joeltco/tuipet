"""The permanent egg TEMPLATE (Joel 2026-10-15: "Just make a permanent template
lol").  Give it ONE approved still design (egg_a, 16x16 '0'/'1' rows on the
shared egg grid) and the dex the egg hatches; it builds the other two frames by
fixed rules, so no egg can drift off the grid again:

  egg_b (wobble)  egg_a squashed into the outline the original eggs share:
                  rows 6..15, each row resampled (nearest neighbour) from a
                  fixed source row onto the shared span, edges inked.
  hatch           the hatch of the ORIGINAL egg that hatches the same baby,
                  with egg_a's shell shown where that original's shell is
                  untouched and its cracks flipped onto it (donor_hatch); a
                  baby no original hatches -- or one whose original breaks out
                  in a dot scatter -- is seated from its own frame 5 on egg_a's
                  shell behind the originals' rim and flying shell pieces
                  (seated_hatch).  Rules v2, Joel 2026-10-15.

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


def _isolated(frame, rows):
    """Ink cells with no inked 8-neighbour -- loose dots."""
    return sum(1 for y in rows for x in range(16) if frame[y][x] == "1"
               and not any(0 <= y + dy < 16 and 0 <= x + dx < 16 and (dy or dx)
                           and frame[y + dy][x + dx] == "1"
                           for dy in (-1, 0, 1) for dx in (-1, 0, 1)))


# a donor whose breakout is a dot scatter cannot be the template (Joel 2026-10-15,
# rules v2): measured over the 46 originals' hatch rows 0-10, loose dots run
# 0:16  1:13  2:2  3:4  4:2  5:5  7:4 -- 42 of 46 have five or fewer; the four
# at seven are the Meicoo snow egg and the Petitmon/Slayerdra/Draco triplet.
# Past that the baby is seated on our shell instead.
SCATTER_MAX = 5


def donor_scattered(donor):
    return _isolated(donor["frames"][2], range(11)) > SCATTER_MAX


def donor_hatch(still, donor):
    """The original egg's hatch frame used as the template (Joel 2026-10-15,
    "Good enough"): rows 0-10 exactly as the original breaks out; rows 11-15
    show OUR shell where the original's shell is untouched, a HOLE (shell the
    original removed: the baby's feet, a gap) stays blank, and a MARK (ink the
    original added: a crack, a foot) flips our pixel -- ink on a blank shell as
    before, blank on an ink shell, so a dark egg's cracks show too (rules v2:
    the originals' stills are blank under every one of their marks; ours are
    not, and an ink mark on an ink shell vanished).  Measured on the 46
    originals: marks per hatch 0 / 3 / 26 (min / median / max), holes 0 / 0 / 12."""
    ds, dh = donor["frames"][0], donor["frames"][2]
    bottom = []
    for y in range(11, 16):
        row = ""
        for x in range(16):
            if dh[y][x] == ds[y][x]:
                row += still[y][x]                      # untouched: our shell
            elif dh[y][x] == "0":
                row += "0"                              # hole
            else:
                row += "0" if still[y][x] == "1" else "1"   # mark, visible either way
        bottom.append(row)
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
# ...and the flying shell: every one of the 46 draws shell pieces beside the
# baby in rows 0-6 (46/46 have ink in cols 0-1 or 14-15 there), and the cells
# inked in half or more of them -- (1,2) (2,2) (3,0) (3,1) (6,2) left, (1,14)
# (3,13) (5,14) right -- trace the starter breakout's cap arc and right-hand
# bits.  That breakout is Botamon's (the Godzilla egg carries the same rows);
# rules v2 (Joel 2026-10-15) uses its debris WHOLE: the 30 cells of its hatch
# rows 0-6 that are not its own seated body.  The old rule kept only the
# outer two columns of it, which chopped the arc into loose dots.
SHARD_EGG = "Botamon"
SHARD_ROWS = 7


def _seat(dex):
    """The baby's breakout pose and the lift that puts its feet on row 12."""
    _, by_num = data.load_sprites()
    frames = by_num[dex]["frames"]
    baby = frames[SEAT_FRAME] if len(frames) > SEAT_FRAME and any("1" in r for r in frames[SEAT_FRAME]) \
        else frames[0]
    ink = [y for y, r in enumerate(baby) if "1" in r]
    height = ink[-1] - ink[0] + 1
    feet = max(SEAT_FEET_ROW, height - 1)
    return baby, ink, ink[-1] - feet


def _near(body):
    return lambda y, x: any((y + dy, x + dx) in body for dy in (-1, 0, 1) for dx in (-1, 0, 1))


def shards():
    """The shell pieces the starter breakout throws: its hatch rows 0-6 minus
    its own seated body."""
    e = next(e for e in _bank() if e.get("hatch_name") == SHARD_EGG)
    baby, ink, lift = _seat(e["hatch"][0])
    body = {(y - lift, x) for y in ink for x, c in enumerate(baby[y]) if c == "1"}
    near = _near(body)
    h = e["frames"][2]
    return {(y, x) for y in range(SHARD_ROWS) for x in range(16)
            if h[y][x] == "1" and not near(y, x)}


def seated_hatch(dex, still):
    """No original hatches this baby: do what the originals do -- the baby's
    own full-size frame 5 (frame 0 if it has none), feet on row 12, the egg's
    shell (still rows 11-15) in front of its lower body, the shell rim and the
    flying shell pieces kept clear of it.  A baby too tall for that sits with
    its head on row 0 and sinks deeper -- never clipped at the top."""
    baby, ink, lift = _seat(dex)
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
    near = _near(body)
    for y, x in shards():
        if not near(y, x):
            g[y][x] = "1"
    return ["".join(r) for r in g]


def build(still, dex):
    if not on_grid(still, STILL):
        raise SystemExit("egg_a is off the shared egg grid: " + repr(outline(still)))
    still = stamp(still, 0)
    wobble = squash(still)
    donor = donor_egg(dex)
    if donor and donor_scattered(donor):           # a dot-scatter breakout is no template
        donor = None
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
