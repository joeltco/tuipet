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
                 "scold": "scold.png", "wash": "wash.png",
                 "shopClosed": "shopClosed.png"}.items():   # drawShop's closed sign
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

# a NAP has its own indicator (DVPet getLightsSprites: napLights/napLights2);
# canon's nap-deepening flash (napToSleepPercent) has no tuipet state to key
# on -- naps never convert here -- so only the static variant is ported
nframes = [to_rows(crop(native_mask(f))) for f in ("napLights.png", "napLights2.png")
           if crop(native_mask(f)) is not None]
if nframes:
    effects["zzz_nap"] = nframes

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

# evol: the evolution strobe mask (SpriteAnim evolveAnim alternates roomEffect
# "lightsOff" <-> "evol").  evol.png is a 50% dither -- a 1px checkerboard at the
# 3x art scale; /3 recovers the native pattern, which the evolve fx TILES over
# the room so it flickers half-dark between the full-black beats.
_ev = native_mask("evol.png")
effects["evol"] = [to_rows(_ev)]

# dnaWash: the full-screen DNA-absorb wave that sweeps DOWN over the pet during
# dnaCharge (SpriteAnim 12860: roomEffect "dnaWash" 105x120, moveDown 9/tick).
# /3 block-mean gives a ~35x40 overlay for the 40x24 LCD sweep.
_dw = crop(native_mask("dnaWash.png"))
if _dw is not None:
    effects["dna_wash"] = [to_rows(_dw)]

# field badges: fields.png is the vertical badge sheet indexed by SpriteAnim
# checkField -- 0 VirusBuster, 1 MetalEmpire, 2 DragonsRoar, 3 JungleTrooper,
# 4 DeepSaver, 5 NightmareSoldier, 6 WindGuardian, 7 NatureSpirit, 8 DarkArea,
# 9 None (== data.DNA_FIELDS order).  Used by the dnaCharge drop-in animation.
_fb = split_vertical(native_mask("fields.png"))
_FIELD_ORDER = ("VirusBuster", "MetalEmpire", "DragonsRoar", "JungleTrooper",
                "DeepSaver", "NightmareSoldier", "WindGuardian", "NatureSpirit",
                "DarkArea", "None")
for _i, _fr in enumerate(_fb):
    if _i < len(_FIELD_ORDER):
        _c = crop(_fr)
        if _c is not None:
            effects["field_" + _FIELD_ORDER[_i]] = [to_rows(_c)]

# Digicore badges (SpriteAnim setupDigicore): the special cores from
# digicoreMenuConfig.csv plus the X-antibody state badges (the default face of
# the core button).  28x28 colored-on-transparent -> /3 block-mean ~9px icons.
for _fn, _key in (("burstCore.png", "core_burst"), ("twelveCore.png", "core_twelve"),
                  ("twoCore.png", "core_two"), ("darkcore.png", "core_dark"),
                  ("xAntibodyReq.png", "core_xreq"), ("xAntibodyTemp.png", "core_xtemp"),
                  ("xAntibodyNoReq.png", "core_xnone")):
    _p = os.path.join(RES, _fn)
    if os.path.exists(_p):
        _a = np.array(Image.open(_p).convert("RGBA"))
        _m = _a[:, :, 3] > 60
        _h, _w = _m.shape[0] // F, _m.shape[1] // F
        _c = crop(_m[:_h * F, :_w * F].reshape(_h, F, _w, F).mean(axis=(1, 3)) > 0.4)
        if _c is not None:
            effects["core_" + _key.split("_", 1)[1]] = [to_rows(_c)]

# filth sizes: filth.png is DVPet's pile sheet -- 30x27 cells (gutter 2), 4 sizes
# x 2 anim frames.  SpriteObj sheets index COLUMN-major (proven by battleBags:
# getBattleBagSprite 0/2/4 = the three top-row bags), so drawFilthLevel's pairs
# (0,1)/(2,3)/(4,5)/(6,7) = column N's two rows = size N's two anim frames.
# /3 block-mean -> up to 10x9 native.  Each size pair is cropped with a SHARED
# bbox so its two frames stay registered when animated.
_fs = np.array(Image.open(os.path.join(RES, "filth.png")).convert("RGBA"))
_frgb = _fs[:, :, :3].astype(int); _fal = _fs[:, :, 3]
_fon = ((_fal > 60) & ((np.abs(_frgb[:, :, 0]-CYAN[0]) + np.abs(_frgb[:, :, 1]-CYAN[1])
                        + np.abs(_frgb[:, :, 2]-CYAN[2])) > 60))
def _filth_cell(col, row):
    m = _fon[2 + 29*row:2 + 29*row + 27, 2 + 32*col:2 + 32*col + 30]
    h, w = m.shape[0] // F, m.shape[1] // F
    return m[:h*F, :w*F].reshape(h, F, w, F).mean(axis=(1, 3)) > 0.4
for _size in range(4):
    _a1 = _filth_cell(_size, 0)
    _b1 = _filth_cell(_size, 1)
    _u = _a1 | _b1
    ys, xs = np.where(_u)
    if len(ys):
        sl = (slice(ys.min(), ys.max()+1), slice(xs.min(), xs.max()+1))
        effects[f"poop_s{_size + 1}"] = [to_rows(_a1[sl]), to_rows(_b1[sl])]

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
