"""Extract food + item icons from spritesFood0/spritesItems0 via the alpha channel
(transparent bg, opaque icon). Food: 24x24 cells, 6px gutters, 4 frames/col.
Items: 16x16 cells, 1px gutters, 9 frames/col. Keyed f:<foodID> / i:<itemID>."""
import csv, gzip, json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
MODEL = os.path.join(ROOT, "raw_model")
OUT = os.path.join(ROOT, "src/tuipet/data")
CY = (153, 217, 234)


def _mask(cell):
    rgb = cell[:, :, :3].astype(int); a = cell[:, :, 3]
    notcyan = (np.abs(rgb[:, :, 0]-CY[0]) + np.abs(rgb[:, :, 1]-CY[1]) + np.abs(rgb[:, :, 2]-CY[2])) > 60
    return (a > 128) & notcyan


def _icon(sheet, col, row, gut, size):
    x0 = gut + (gut + size) * col
    y0 = gut + (gut + size) * row
    m = _mask(sheet[y0:y0+size, x0:x0+size])
    if not m.any():
        return None
    ys, xs = np.where(m)
    crop = m[ys.min():ys.max()+1, xs.min():xs.max()+1]
    return ["".join("1" if v else "0" for v in r) for r in crop]


def run():
    icons = {}
    food = np.array(Image.open(os.path.join(RES, "spritesFood0.png")))   # RGBA
    for r in csv.DictReader(open(os.path.join(MODEL, "foods.csv"))):
        try:
            fid = int(r["FoodIdentificationNum"]); col = int(r["SpriteNum"]) // 4
        except (KeyError, ValueError):
            continue
        frames = [_icon(food, col, fr, 6, 24) for fr in range(4)]
        if any(frames):
            icons[f"f:{fid}"] = frames
    items = np.array(Image.open(os.path.join(RES, "spritesItems0.png")))
    for r in csv.DictReader(open(os.path.join(MODEL, "items.csv"))):
        try:
            iid = int(r["ItemIdentificationNum"]); col = int(r["SpriteNum"]) // 9
        except (KeyError, ValueError):
            continue
        ic = _icon(items, col, 0, 1, 16)
        if ic:
            icons[f"i:{iid}"] = [ic]
    with gzip.open(os.path.join(OUT, "icons.json.gz"), "wt") as fh:
        json.dump(icons, fh)
    print(f"extracted {len(icons)} icons -> icons.json.gz")
    return icons


if __name__ == "__main__":
    icons = run()
    # preview a few foods + items
    for key in ("f:0", "f:1", "f:4", "i:0", "i:3"):
        if key in icons:
            print(f"\n{key}:")
            for row in icons[key][0]:
                print("  " + row.replace("0", " ").replace("1", "#"))
