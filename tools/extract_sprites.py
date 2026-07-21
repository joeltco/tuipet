#!/usr/bin/env python3
"""Extract DVPet 1-bit creature sprites from the game atlases.

Layout (verified): creature stages live in sprites{Stage}{Set}.png, each 672x672,
an 11x11 grid. Each Digimon = one column (NewSpriteNum // 11), its 11 animation/expression
frames = rows 0..10 down the column. Background is cyan (153,217,234); creature is black.
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

# DVPet's divideIntoColumn geometry: a 48px sprite with a 12px gutter (pitch 60),
# authored at 3x so native is 16px. The creature's POSITION within its 48px cell
# is the animation (bob/walk/crouch), so we keep the full native cell and never
# crop -- that is exactly what the game draws.
F = 3
SIZE = 48
GUTTER = 12
PITCH = SIZE + GUTTER   # 60
NATIVE = SIZE // F       # 16
_CYAN = (153, 217, 234)


def cell_mask(sheet, col, fr):
    """16x16 native mask for one frame: OPAQUE and not the cyan LCD background."""
    y0 = GUTTER + PITCH * fr
    x0 = GUTTER + PITCH * col
    cell = sheet[y0:y0 + SIZE, x0:x0 + SIZE]
    if cell.shape[0] < SIZE or cell.shape[1] < SIZE:
        return None
    rgb = cell[:, :, :3].astype(int)
    a = cell[:, :, 3]
    notcyan = (np.abs(rgb[:, :, 0] - _CYAN[0]) + np.abs(rgb[:, :, 1] - _CYAN[1])
               + np.abs(rgb[:, :, 2] - _CYAN[2])) > 60
    on = ((a > 128) & notcyan).astype(float)
    return on.reshape(NATIVE, F, NATIVE, F).mean(axis=(1, 3)) > 0.5


def content_fill(frame):
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
    col = N // GRID
    if GUTTER + PITCH * col + SIZE > W:
        return None
    masks = [cell_mask(sheet, col, f) for f in range(GRID)]
    if not any(m is not None and m.any() for m in masks):
        return None
    frames = [None if (m is None or not m.any())
              else ["".join("1" if v else "0" for v in r) for r in m]
              for m in masks]
    return {"w": NATIVE, "h": NATIVE, "frames": frames}



def extract_eggs():
    """Real Digitama eggs from spritesEgg0.png. The egg sheet uses a 54px pitch and
    6px gutter (not the creatures' 60/12), 48px cells, 3 frames down a column. Each
    Egg-stage creature (column = NewSpriteNum // 3) hatches into one specific Fresh
    via evolutions.csv -- we keep the egg sprite AND that hatch target, so the picker
    shows egg -> Digimon and the egg hatches into the right baby.

    ⚠ The SHIPPED data/eggs.json.gz has been hand-authored past this extractor
    (display hatch_names like 'Lalamon Egg', curated hatch roots, the Digitama
    X3 pool) -- rerunning this clobbers that authoring (consistency audit
    2026-07-21).  Patch the shipped file in place instead of regenerating."""
    sheet = get_sheet("Egg", 0)
    if sheet is None:
        return
    XS, XP, YS, YP, S = 6, 54, 6, 54, 48

    def egg_cell(col, fr):
        y0 = YS + YP * fr
        x0 = XS + XP * col
        c = sheet[y0:y0 + S, x0:x0 + S]
        if c.shape[0] < S or c.shape[1] < S:
            return None
        rgb = c[:, :, :3].astype(int)
        a = c[:, :, 3]
        nc = (np.abs(rgb[:, :, 0] - _CYAN[0]) + np.abs(rgb[:, :, 1] - _CYAN[1])
              + np.abs(rgb[:, :, 2] - _CYAN[2])) > 60
        return ((a > 128) & nc).reshape(NATIVE, F, NATIVE, F).mean(axis=(1, 3)) > 0.5

    digi = {int(r["DigimonNum"]): r for r in csv.DictReader(open(os.path.join(MODEL, "digimon.csv")))
            if r.get("DigimonNum", "").strip().isdigit()}
    evo = {}
    with open(os.path.join(MODEL, "evolutions.csv")) as fh:
        rd = csv.reader(fh)
        next(rd)
        for row in rd:
            cells = [c for c in row if c.strip() != ""]
            if cells:
                evo[int(cells[0])] = [int(v) for v in cells[1:]]

    egg_creatures = sorted(((int(r["NewSpriteNum"]) // 3, n)
                            for n, r in digi.items() if r["NewStage"] == "Egg"),
                           key=lambda t: t[0])
    eggs, seen = [], set()
    for col, n in egg_creatures:
        if col in seen:
            continue
        m0 = egg_cell(col, 0)
        if m0 is None or int(m0.sum()) < 16:
            continue
        fresh = [t for t in evo.get(n, []) if digi.get(t, {}).get("NewStage") == "Fresh"]
        if not fresh:
            continue
        seen.add(col)
        frames = []
        for fr in range(3):
            m = egg_cell(col, fr)
            if m is not None and m.any():
                frames.append(["".join("1" if v else "0" for v in rr) for rr in m])
        eggs.append({"frames": frames, "hatch": fresh,
                     "hatch_name": digi[fresh[0]]["Name"] if len(fresh) == 1 else "???"})
    path = os.path.join(OUT, "eggs.json.gz")
    with gzip.open(path, "wt") as fh:
        json.dump(eggs, fh)
    print(f"extracted {len(eggs)} real eggs with hatch targets -> {path}")


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
