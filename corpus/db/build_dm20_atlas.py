#!/usr/bin/env python3
"""Extract the DM20 sprite atlas from wayland (+ dvpet fallback) PNGs.

Wayland sheets are 1-bit dot art upscaled x4 (alpha = ink), multi-frame horizontal,
in a FIXED native frame order (include/graphics/sprite_sheet.h):

  0 idle_1  1 idle_2  2 angry  3 down   4 happy   5 eat_1  6 sleep  7 refuse
  8 sad     9 lose_1  10 eat_2 11 lose_2 12 attack_1 13 movement_1 14 movement_2 15 attack_2

We keep frames in this NATIVE order; render.ROLES (wayland convention) indexes into it.
dvpet-fallback PNGs are single 64x64 idle frames (only frame 0 available).

Output: src/tuipet/data/dm20_sprites.json.gz  (list of {num,id,name,stage,attribute,w,h,frames,source})
Run: python3 corpus/db/build_dm20_atlas.py
"""
import gzip
import json
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(CORPUS, ".."))
DB = os.path.join(CORPUS, "db", "dm20.json")
OUT = os.path.join(REPO, "src", "tuipet", "data", "dm20_sprites.json.gz")

THRESH = 0.3   # ink coverage to light a 16x16 dot (BOX area-downscale; Agumon eyeball test)

# Native wayland frame names, by index — recorded in the atlas meta for reference.
FRAME_NAMES = ["idle_1", "idle_2", "angry", "down", "happy", "eat_1", "sleep",
               "refuse", "sad", "lose_1", "eat_2", "lose_2", "attack_1",
               "movement_1", "movement_2", "attack_2"]


def _alpha(im):
    if im.mode == "LA":
        return np.array(im)[..., 1]
    if im.mode == "RGBA":
        return np.array(im)[..., 3]
    return np.array(im.convert("LA"))[..., 1]


def _to16(blk):
    """bool HxW ink mask -> list of 16 '0'/'1' strings.

    The wayland art is hand-drawn at ~3px stroke pitch on a 64px canvas (NOT a clean
    16x16 upscaled x4), so a fixed reshape mis-samples the dot grid and shreds it.
    A BOX (area-average) resize integrates the ink coverage of each 16x16 cell, which
    preserves the silhouette; THRESH lights a dot once it's that fraction inked."""
    img = Image.fromarray((blk * 255).astype("uint8"))
    small = np.asarray(img.resize((16, 16), Image.BOX), dtype=float) / 255.0
    return ["".join("1" if v >= THRESH else "0" for v in row) for row in small]


def extract(path):
    A = _alpha(Image.open(path)) > 127
    h, w = A.shape
    n = max(1, round(w / h))
    out = []
    for i in range(n):
        x0, x1 = round(i * w / n), round((i + 1) * w / n)
        out.append(_to16(A[:, x0:x1]))
    return out


def main():
    db = json.load(open(DB))
    recs = []
    miss = []
    for i, r in enumerate(db["digimon"]):
        sp = r.get("sprite")
        path = os.path.join(CORPUS, sp) if sp else None
        if not path or not os.path.exists(path):
            miss.append(r["name"])
            frames = []
        else:
            frames = extract(path)
        recs.append({
            "num": i, "id": r["id"], "name": r["name"], "stage": r["stage"],
            "attribute": r.get("attribute"), "w": 16, "h": 16,
            "frames": frames, "source": r.get("sprite_source"),
        })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh:
        json.dump({"_meta": {"device": "dm20", "count": len(recs),
                             "frame_names": FRAME_NAMES, "thresh": THRESH,
                             "missing": miss}, "sprites": recs}, fh, ensure_ascii=False)
    fc = {}
    for r in recs:
        fc[len(r["frames"])] = fc.get(len(r["frames"]), 0) + 1
    print(f"wrote {OUT}: {len(recs)} sprites")
    print(f"frame-count histogram: {dict(sorted(fc.items()))}")
    print(f"missing PNGs: {miss or 'none'}")


if __name__ == "__main__":
    main()
