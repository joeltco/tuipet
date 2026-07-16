#!/usr/bin/env python3
"""Extract DVPet attack-ORB projectile sprites -> src/tuipet/data/orbs.json.gz.

DVPet checkAttackSprite (SpriteAnim.java:14809): an attack orb is either
  - GENERIC: attackSprites.png, 3 columns (Vaccine/Data/Virus) x 25 power tiers,
    chosen by attribute + floor(power/25); OR
  - SPECIAL (per-Digimon): attackSpritesSpecial.png cell, indexed directly by
    digimon.csv col 55 'vaccineNum:dataNum:virusNum' (94 of 100 cells used).
Cells are 24x24 with a 3px gutter, sliced column-major. Downsampled /3 to ~8px 1-bit
(half the body sprite, matching DVPet's 24px-orb vs 48px-body proportion)."""
import json, gzip, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
OUT = os.path.join(ROOT, "src/tuipet/data")
F, W, H, GUT = 3, 24, 24, 3


def load(fn):
    return np.array(Image.open(os.path.join(RES, fn)).convert("RGBA"))


def cell(arr, idx, nrows):
    col, row = idx // nrows, idx % nrows                # column-major (divideSpriteSheet)
    x = GUT * (col + 1) + W * col
    y = GUT * (row + 1) + H * row
    al = arr[y:y + H, x:x + W, 3]
    on = (al > 60).astype(float)
    h, w = H // F, W // F
    return on[:h * F, :w * F].reshape(h, F, w, F).mean(axis=(1, 3)) > 0.4


def crop(m):
    ys, xs = np.where(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else None


def to_rows(m):
    return ["".join("1" if v else "0" for v in r) for r in m]


gen = load("attackSprites.png")          # 84x678 -> 3 cols x 25 rows
spc = load("attackSpritesSpecial.png")   # 273x273 -> 10 x 10
orbs = {"generic": {"Vaccine": [], "Data": [], "Virus": []}, "special": {}}
# the "device" bank (MultiVPet real-hardware attacks, deviceAttacks.csv) is
# authored separately -- MERGE it through a rebuild, never drop it
_prev = os.path.join(OUT, "orbs.json.gz")
if os.path.exists(_prev):
    with gzip.open(_prev, "rt") as fh:
        orbs["device"] = json.load(fh).get("device", {})

for attr, base in (("Vaccine", 0), ("Data", 25), ("Virus", 50)):
    for tier in range(25):
        c = crop(cell(gen, base + tier, 25))
        orbs["generic"][attr].append(to_rows(c) if c is not None else None)

for idx in range(100):                   # 10x10 special sheet
    c = crop(cell(spc, idx, 10))
    if c is not None:
        orbs["special"][str(idx)] = to_rows(c)

# preview
print("generic tier-2 orbs (the common low-power tier):")
for attr in ("Vaccine", "Data", "Virus"):
    fr = orbs["generic"][attr][2]
    print(f"  {attr} {len(fr[0])}x{len(fr)}:")
    for r in fr:
        print("    " + "".join("#" if c == "1" else "." for c in r))
print(f"special orbs extracted: {len(orbs['special'])} (idx 0..99)")
for i in (0, 22, 96):
    fr = orbs["special"].get(str(i))
    if fr:
        print(f"  special[{i}] {len(fr[0])}x{len(fr)}:")
        for r in fr:
            print("    " + "".join("#" if c == "1" else "." for c in r))

path = os.path.join(OUT, "orbs.json.gz")
with gzip.open(path, "wt") as fh:
    json.dump(orbs, fh, separators=(",", ":"))
print(f"\nwrote {path}")
