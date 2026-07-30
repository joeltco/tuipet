#!/usr/bin/env python3
"""Extract DVPet's JOGRESS CONNECT flash card into a 1-bit halfblock overlay:
src/tuipet/data/jogress_overlays.json.

canon SpriteAnim.jogressFlash cycles two icons while two devices handshake --
`jogressConnectStart` <-> `jogressConnectStartFlash` (the CONNECT variants are
the networked ones; the plain pair is the offline device's own animation).
tuipet's fusion is lobby-only, so the connect pair is the right rip.

Same masking rule as tools/extract_effects.py: authored at 3x, downsample to
native, keep pixels that are opaque AND not the cyan LCD background.  REAL rips
only -- nothing here is drawn.
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
OUT = os.path.join(ROOT, "src/tuipet/data/jogress_overlays.json")
F = 3
CYAN = (153, 217, 234)
FRAMES = ("jogressConnectStart", "jogressConnectStartFlash")


def native_mask(fn):
    a = np.array(Image.open(os.path.join(RES, fn)).convert("RGBA"))
    H, W, _ = a.shape
    rgb = a[:, :, :3].astype(int)
    al = a[:, :, 3]
    nc = (abs(rgb[:, :, 0] - CYAN[0]) + abs(rgb[:, :, 1] - CYAN[1])
          + abs(rgb[:, :, 2] - CYAN[2])) > 60
    on = ((al > 60) & nc).astype(float)
    h, w = H // F, W // F
    return on[:h * F, :w * F].reshape(h, F, w, F).mean(axis=(1, 3)) > 0.4


def crop_pair(masks):
    """One shared crop box for BOTH frames: cropping them apart would make the
    card jitter as it flashes."""
    any_on = np.zeros_like(masks[0])
    for m in masks:
        any_on |= m
    ys, xs = np.where(any_on)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return [m[y0:y1, x0:x1] for m in masks]


def main():
    masks = crop_pair([native_mask(f"{n}.png") for n in FRAMES])
    out = {"jogress_connect": [["".join("1" if v else "0" for v in row)
                                for row in m] for m in masks]}
    h = len(out["jogress_connect"][0])
    w = len(out["jogress_connect"][0][0])
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh)
    print(f"wrote {OUT}: {len(FRAMES)} frames, {w}x{h} native px")


if __name__ == "__main__":
    main()
