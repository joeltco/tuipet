#!/usr/bin/env python3
"""Extract DVPet 1-bit creature sprites from the game atlases.

Layout (verified): creature stages live in sprites{Stage}{Set}.png, each 672x672,
an 11x11 grid. Each Digimon = one row (NewSpriteNum // 11), its 11 animation/expression
frames = columns 0..10. Background is cyan (153,217,234); creature is black.
We threshold dark pixels -> 1-bit bitmaps, crop to the union bbox of a Digimon's
non-empty frames (stable alignment), and emit a compact JSON dataset.
"""
import csv, json, os, sys, gzip
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
MODEL = os.path.join(ROOT, "raw_model")
OUT = os.path.join(ROOT, "src/tuipet/data")
GRID = 11
STAGES = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]

_cache = {}
def get_sheet(stage, s):
    key = f"sprites{stage}{s}"
    if key not in _cache:
        p = os.path.join(RES, key + ".png")
        if os.path.exists(p):
            img = Image.open(p)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            _cache[key] = np.array(img)
        else:
            _cache[key] = None
    return _cache[key]

F = 3        # creatures are authored at 3x; native cell is ~20px
NATIVE = 20  # native cell size after downsample (60 = 20*3)

_CYAN = (153, 217, 234)

def dark_mask_native(cell60):
    # cell60: HxWx4 RGBA slice (60x60). A pixel belongs to the sprite if it is
    # OPAQUE and NOT the cyan LCD background (works for both opaque-cyan-bg sheets
    # and transparent-bg sheets). Box-downsample by 3 and threshold -> native
    # sprite, dropping 1px column labels.
    rgb = cell60[:, :, :3].astype(int)
    a = cell60[:, :, 3]
    notcyan = (np.abs(rgb[:, :, 0] - _CYAN[0]) + np.abs(rgb[:, :, 1] - _CYAN[1])
               + np.abs(rgb[:, :, 2] - _CYAN[2])) > 60
    on = ((a > 128) & notcyan).astype(float)
    m = on[:NATIVE*F, :NATIVE*F].reshape(NATIVE, F, NATIVE, F).mean(axis=(1, 3))
    return m > 0.5


def content_fill(frame):
    """Fill ratio within a frame's tight content bbox. Solid placeholder squares
    (no finished art in this test build) come out ~1.0; real silhouettes ~0.3-0.6."""
    rows = [r for r in frame if "1" in r]
    if not rows:
        return 0.0
    left = min(r.find("1") for r in rows)
    right = max(r.rfind("1") for r in rows)
    w = right - left + 1
    ones = sum(r[left:right + 1].count("1") for r in rows)
    return ones / (w * len(rows))

def extract_digimon(stage, S, N):
    sheet = get_sheet(stage, S)
    if sheet is None:
        return None
    H, W, _ = sheet.shape
    ch, cw = H / GRID, W / GRID
    col = N // GRID  # creatures are laid out per COLUMN; 11 frames run down the rows
    if col >= GRID:
        return None
    masks = []
    x0 = round(col * cw)
    for f in range(GRID):
        y0 = round(f * ch)
        masks.append(dark_mask_native(sheet[y0:y0 + NATIVE*F, x0:x0 + NATIVE*F]))
    # union bbox over non-empty frames
    nonempty = [m for m in masks if m.any()]
    if not nonempty:
        return None
    union = np.zeros_like(masks[0])
    for m in nonempty:
        union |= m
    ys, xs = np.where(union)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    frames = []
    for m in masks:
        crop = m[y0:y1, x0:x1]
        if not crop.any():
            frames.append(None)
        else:
            frames.append(["".join("1" if v else "0" for v in r) for r in crop])
    return {"w": int(x1 - x0), "h": int(y1 - y0), "frames": frames}



def extract_eggs():
    """Extract the 11 egg sprites from armorEggs.png (1-bit black-on-cyan)."""
    import numpy as np
    from PIL import Image
    im = np.array(Image.open(os.path.join(RES, "armorEggs.png")).convert("RGB"))
    H, W, _ = im.shape
    dark = im.sum(axis=2) < 200
    colhas = dark.any(axis=0)
    eggs, x = [], 0
    while x < W:
        if colhas[x]:
            j = x
            while j < W and colhas[j]:
                j += 1
            band = dark[:, x:j]
            ys = np.where(band.any(axis=1))[0]
            if len(ys):
                crop = band[ys.min():ys.max() + 1]
                eggs.append(["".join("1" if v else "0" for v in r) for r in crop])
            x = j
        else:
            x += 1
    path = os.path.join(OUT, "eggs.json.gz")
    with gzip.open(path, "wt") as fh:
        json.dump(eggs, fh)
    print(f"extracted {len(eggs)} egg sprites -> {path}")

def main():
    os.makedirs(OUT, exist_ok=True)
    rows = list(csv.DictReader(open(os.path.join(MODEL, "digimon.csv"))))
    out = []
    skipped = 0
    for r in rows:
        stage = r["NewStage"]
        if stage not in STAGES:
            skipped += 1
            continue
        S, N = int(r["NewSpriteSet"]), int(r["NewSpriteNum"])
        spr = extract_digimon(stage, S, N)
        if spr is None:
            skipped += 1
            continue
        out.append({
            "num": int(r["DigimonNum"]),
            "name": r["Name"],
            "stage": stage,
            "attribute": r["NewAttribute"],
            "field": r["NewField"],
            "element": r["Element"],
            "spriteSet": S, "spriteNum": N,
            **spr,
        })
    path = os.path.join(OUT, "sprites.json.gz")
    with gzip.open(path, "wt", compresslevel=9) as fh:
        json.dump(out, fh, separators=(",", ":"))
    sz = os.path.getsize(path)
    nonemptyframes = sum(1 for d in out for f in d["frames"] if f)
    print(f"extracted {len(out)} digimon, {nonemptyframes} non-empty frames, skipped {skipped}")
    print(f"wrote {path} ({sz/1024:.0f} KB)")
    extract_eggs()
    import extract_icons as _ic
    _ic.run()
    # sample frame-occupancy: how many digimon have each frame index non-empty
    occ = [0]*GRID
    for d in out:
        for i, f in enumerate(d["frames"]):
            if f: occ[i] += 1
    print("frame index non-empty counts:", occ)

if __name__ == "__main__":
    main()
