"""HP-drill training dummies from battleBags.png (REAL DVPet art, EXTRACT-not-draw).

The sheet is 3 cols x 2 rows (cell 48x61), SpriteObj COLUMN-major: n = col*2 + row.
getBattleBagSprite maps Vaccine=0 / Virus=2 / Data=4 (top row, clean) and the
wrong-guess TAUNT is drawn at +1 (SpriteAnim: `drawNum(getBattleBagSprite(a) + 1)`)
-- the bottom row of the same column.  Art is authored at 3x: crop-first, then a
/3 block-mean (integer factor only; fractional resizes mush the pixels).
"""
import json
import os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEET = os.path.join(ROOT, "raw_resources", "battleBags.png")
OUT = os.path.join(ROOT, "src", "tuipet", "data", "hp_dummies.json")
CYAN = np.array((153, 217, 234))
F = 3


def cell_rows(im, col, row):
    ch, cw = im.shape[0] // 2, im.shape[1] // 3
    c = im[row * ch:(row + 1) * ch, col * cw:(col + 1) * cw]
    # the bags are WHITE-bodied with black linework on a cyan key: the LCD
    # 1-bit art is the DARK linework (mask on darkness, not on non-background)
    on = (c[:, :, 3] > 60) & (c[:, :, :3].astype(int).sum(axis=2) < 384)
    ys, xs = np.where(on)
    if not len(ys):
        return None
    on = on[ys.min():ys.max() + 1, xs.min():xs.max() + 1]   # crop FIRST (native px)
    h, w = on.shape
    H, W = -(-h // F), -(-w // F)
    pad = np.zeros((H * F, W * F), bool)
    pad[:h, :w] = on
    m = pad.reshape(H, F, W, F).mean(axis=(1, 3)) > 0.4
    ys, xs = np.where(m)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return ["".join("1" if v else "0" for v in r) for r in m]


def main():
    im = np.array(Image.open(SHEET).convert("RGBA"))
    out = {}
    for name, col in (("vaccine", 0), ("virus", 1), ("data", 2)):
        out[name] = cell_rows(im, col, 0)
        out[name + "_taunt"] = cell_rows(im, col, 1)
    with open(OUT, "w") as f:
        json.dump(out, f)
    for k, v in out.items():
        print(k, f"{len(v)}x{len(v[0])}")


if __name__ == "__main__":
    main()
