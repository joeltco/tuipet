#!/usr/bin/env python3
"""Extract DVPet's auxiliary effect sprites (Zzz, wash, emotes, grave, sun/moon)
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

# single-frame overlays (authentic DM20 status set only)
for name, fn in {"attention": "attention.png", "wash": "wash.png"}.items():
    c = crop(native_mask(fn))
    if c is not None:
        effects[name] = [to_rows(c)]

# two-frame emotes (base + "2" variant)
for name, files in {"happy": ("happy.png", "happy2.png"),
                    "unhappy": ("unhappy.png", "unhappy2.png")}.items():
    fr = [to_rows(crop(native_mask(f))) for f in files if crop(native_mask(f)) is not None]
    if fr:
        effects[name] = fr

# Zzz: DVPet sleepLights ("Zz") + sleepLights2 ("Z") -- two clean blinking glyphs
zframes = [to_rows(crop(native_mask(f))) for f in ("sleepLights.png", "sleepLights2.png")
           if crop(native_mask(f)) is not None]
if zframes:
    effects["zzz"] = zframes

# poop: NOT generated here.  The authentic poop is the MultiVPet spr_poop_vpet
# sprite, curated directly into effects.json.gz (commit 7ec383f) -- the old
# filth.png crop was a crude stand-in.  The merge-on-write below preserves the
# curated version so a regen never clobbers it.

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

# NOTE: the DVPet training-drill dummies (punching bag / green target / shield), the
# per-attribute attack projectiles, and the attack/hit/flash bursts are NOT generated
# here anymore.  DM20 solo training is wall-mash (no drill opponents) and mono battle
# uses the generic attribute orbs (orbs.json.gz), so those glyphs were orphaned art.

# ---- preview ----
for name, frames in effects.items():
    print(f"\n===== {name}  ({len(frames)} frame(s)) =====")
    for fi, fr in enumerate(frames[:3]):
        print(f"  frame {fi}: {len(fr[0])}x{len(fr)}")
        for r in fr:
            print("   " + "".join("#" if c == "1" else "." for c in r))

path = os.path.join(OUT, "effects.json.gz")
# MERGE, don't clobber: several sprites are curated directly in effects.json.gz
# (the MultiVPet poop, the hand-tuned unhappy drip, the st_* status icons, the
# dying emote) and are NOT reproducible from this script.  Existing keys win, so
# a regen only ADDS new keys (e.g. the training opponents) and never overwrites
# curated art.  To force-update a sprite from here, delete its key from the file
# first.  (This is the bug that wiped poop + the status icons in v0.2.0-0.2.1.)
if os.path.exists(path):
    with gzip.open(path, "rt") as fh:
        existing = json.load(fh)
    effects = {**effects, **existing}
with gzip.open(path, "wt") as fh:
    json.dump(effects, fh, separators=(",", ":"))
print(f"\nwrote {path}: {list(effects)}")
