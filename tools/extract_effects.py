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

# training opponents: the punching bag (vaccine/virus/hp drills) + its broken form,
# and the green pop-up target (data drill).  DVPet vaccinePrePrep/dataPrePrep opponents
# -- the thing the pet actually fires its attack at during a drill's strike sequence.
# All authored at 3x like the creatures (trainGreen 32x28 / trainShield 16x18 are clean
# 3x3-block art); native_mask's /3 block-mean recovers the true crisp dot-matrix sprite.
# (A non-integer "arena scale" resize antialiased these into mush -- v0.2.27 regression.)
for name, fn in {"punching_bag": "punchingBag.png", "punching_bag_broken": "punchingBagBroken.png",
                 "train_green": "trainGreen.png", "train_green_up": "trainGreenUp.png",
                 "train_shield": "trainShield.png"}.items():       # data-drill cannon + shield
    c = crop(native_mask(fn))
    if c is not None:
        effects[name] = [to_rows(c)]

# HP-drill opponent: one dummy from the battleBags.png sheet (3x2 grid; top-left cell)
_bb = np.array(Image.open(os.path.join(RES, "battleBags.png")).convert("RGBA"))[0:72, 0:40]
_bbon = ((_bb[:, :, 3] > 60) & (np.abs(_bb[:, :, :3].astype(int) - np.array(CYAN)).sum(axis=2) > 60))
_h, _w = _bbon.shape[0] // F, _bbon.shape[1] // F
_bbc = crop(_bbon[:_h * F, :_w * F].reshape(_h, F, _w, F).mean(axis=(1, 3)) > 0.4)
if _bbc is not None:
    effects["battle_bag"] = [to_rows(_bbc)]

# per-attribute projectiles: DVPet's real attack sprites (proven via SpriteAnim
# initAttackButtons: Vaccine=red.png, Data=green.png, Virus=yellow.png -- distinct
# black silhouettes: an orb, a block, and a dart. Downsampled /2 to ~7px.
for _fn, _key in (("red.png", "atk_vaccine"), ("green.png", "atk_data"), ("yellow.png", "atk_virus")):
    _a = np.array(Image.open(os.path.join(RES, _fn)).convert("RGBA"))
    _m = _a[:, :, 3] > 120
    _h, _w = _m.shape
    _m2 = _m[:_h // 2 * 2, :_w // 2 * 2].reshape(_h // 2, 2, _w // 2, 2).mean(axis=(1, 3)) > 0.4
    _c = crop(_m2)
    if _c is not None:
        effects[_key] = [to_rows(_c)]

# attack projectile: the leading orb, animated across several attackSprites frames
ap = split_vertical(native_mask("attackSprites.png"))
if ap:
    fr = []
    for i in (0, 6, 12, 18):
        if i < len(ap):
            orb = crop(ap[i][:, :9])
            if orb is not None:
                fr.append(to_rows(orb))
    if fr:
        effects["attack"] = fr
# impact: small burst core of attackHit, plus the bright attackHitFlash burst
hb = native_mask("attackHit.png")
burst = crop(hb[5:15, 12:22])
if burst is not None:
    effects["hit"] = [to_rows(burst)]
hf = native_mask("attackHitFlash.png")
flash = crop(hf[3:17, 9:25])
if flash is not None:
    effects["flash"] = [to_rows(flash)]

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
