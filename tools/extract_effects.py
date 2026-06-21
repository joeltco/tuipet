#!/usr/bin/env python3
"""Extract DVPet's auxiliary effect sprites (poop, Zzz, frozen, wash, emotes)
into a 1-bit halfblock atlas: src/tuipet/data/effects.json.gz.

These are small status/emote overlays drawn on the LCD on top of the creature.
Most are authored at 3x like the creatures; we downsample to native and mask on
"opaque and not the cyan LCD background"."""
import json, gzip, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
OUT = os.path.join(ROOT, "src/tuipet/data")
F = 3
CYAN = (153, 217, 234)


def native_mask(fn):
    a = np.array(Image.open(os.path.join(RES, fn)).convert("RGBA"))
    H, W, _ = a.shape
    rgb = a[:, :, :3].astype(int); al = a[:, :, 3]
    nc = (np.abs(rgb[:, :, 0]-CYAN[0]) + np.abs(rgb[:, :, 1]-CYAN[1]) + np.abs(rgb[:, :, 2]-CYAN[2])) > 60
    on = ((al > 60) & nc).astype(float)
    h, w = H // F, W // F
    return on[:h*F, :w*F].reshape(h, F, w, F).mean(axis=(1, 3)) > 0.4


def crop(m):
    ys, xs = np.where(m)
    if len(ys) == 0:
        return None
    return m[ys.min():ys.max()+1, xs.min():xs.max()+1]


def to_rows(m):
    return ["".join("1" if v else "0" for v in r) for r in m]


def split_vertical(m):
    """Split a vertical animation strip into frames on fully-blank native rows."""
    frames, run = [], []
    for r in m:
        if r.any():
            run.append(r)
        elif run:
            frames.append(np.array(run)); run = []
    if run:
        frames.append(np.array(run))
    return frames


effects = {}

# single-frame overlays
for name, fn in {"frozen": "frozen.png", "attention": "attention.png",
                 "call": "callLabel.png", "praise": "praise.png",
                 "scold": "scold.png", "wash": "wash.png"}.items():
    c = crop(native_mask(fn))
    if c is not None:
        effects[name] = [to_rows(c)]

# two-frame emotes (base + "2" variant)
for name, files in {"happy": ("happy.png", "happy2.png"),
                    "unhappy": ("unhappy.png", "unhappy2.png"),
                    "depressed": ("depressed.png", "depressed2.png")}.items():
    fr = [to_rows(crop(native_mask(f))) for f in files if crop(native_mask(f)) is not None]
    if fr:
        effects[name] = fr

# Zzz: a sleep-Z that rises and fades -- FIXED-height frames (6 native rows).
# Do NOT split on blank rows or the vertical motion is destroyed.
_zm = native_mask("sleep.png")
_ZF = 6
zframes = []
for _y in range(0, (len(_zm) // _ZF) * _ZF, _ZF):
    _ch = _zm[_y:_y + _ZF]
    _cols = [x for x in range(_ch.shape[1]) if _ch[:, x].any()]
    _sub = _ch[:, min(_cols):max(_cols) + 1] if _cols else _ch
    zframes.append(to_rows(_sub))
if zframes:
    effects["zzz"] = zframes

# poop: crop a single mound out of filth.png (a real DVPet sprite -- the sheet
# is a packed field, so we take one clean mound from it)
_fil = native_mask("filth.png")
_p = crop(_fil[6:10, 2:8])
if _p is not None:
    effects["poop"] = [to_rows(_p)]

# copymon: DVPet's real stand-in creature, used as the placeholder sprite
_cm = split_vertical(native_mask("copymon.png"))
if _cm:
    _big = crop(max(_cm, key=lambda f: int(f.sum())))
    if _big is not None:
        effects["copymon"] = [to_rows(_big)]

# real overlays that were previously hand-drawn in app.py
for name, fn in {"grave": "death.png", "sun": "noon.png", "moon": "night.png"}.items():
    c = crop(native_mask(fn))
    if c is not None:
        effects[name] = [to_rows(c)]

# attack projectile (first orb of attackSprites) + impact burst (core of attackHit)
ap = split_vertical(native_mask("attackSprites.png"))
if ap:
    orb = crop(ap[0][:, :9])
    if orb is not None:
        effects["attack"] = [to_rows(orb)]
hb = native_mask("attackHit.png")
burst = crop(hb[5:15, 12:22])
if burst is not None:
    effects["hit"] = [to_rows(burst)]

# ---- preview ----
for name, frames in effects.items():
    print(f"\n===== {name}  ({len(frames)} frame(s)) =====")
    for fi, fr in enumerate(frames[:3]):
        print(f"  frame {fi}: {len(fr[0])}x{len(fr)}")
        for r in fr:
            print("   " + "".join("#" if c == "1" else "." for c in r))

path = os.path.join(OUT, "effects.json.gz")
with gzip.open(path, "wt") as fh:
    json.dump(effects, fh, separators=(",", ":"))
print(f"\nwrote {path}: {list(effects)}")
