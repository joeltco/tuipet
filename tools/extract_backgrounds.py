#!/usr/bin/env python3
"""Extract DVPet habitat backgrounds into a colour atlas for the LCD.

Each background sheet stacks 5 time/weather frames (DVPet BackgroundAnim
getBackgroundIndex): 0=morning 1=noon/day 2=sunset 3=night 4=precipitation,
each 104x101 with a 2px gap. We crop each and downsample to the LCD pixel grid
(40x28) as RGB, so the pet view can show a colour scene that follows the
day/night clock."""
import json, gzip, os, csv
from PIL import Image, ImageEnhance, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "raw_resources")
OUT = os.path.join(ROOT, "src/tuipet/data")
MODEL = os.path.join(ROOT, "raw_model")
FW, FH, GAP = 104, 101, 2
COLS, PXH = 40, 24


def frames_for(fn):
    p = os.path.join(RES, fn + ".png")
    if not os.path.exists(p):
        return None
    im = Image.open(p).convert("RGB")
    W, H = im.size
    n = max(1, (H + GAP) // (FH + GAP))
    out = []
    for i in range(n):
        y = i * (FH + GAP)
        TOP_BAR, BOT_BAR = 20, 21   # exact DVPet _mainDisplay window (104x60); strips the icon-overlay sky/ground bands
        y0 = y + TOP_BAR
        y1 = min(y + FH - BOT_BAR, H)
        fr = im.crop((0, y0, FW, y1)).resize((COLS, PXH), Image.BOX)
        fr = ImageEnhance.Color(fr).enhance(1.85)    # punch up colour (terminal/JPEG mute it)
        fr = ImageEnhance.Contrast(fr).enhance(1.3)
        fr = ImageOps.posterize(fr, 4)               # flat colour bands -> clean pixel-art
        px = fr.load()
        out.append(["".join("%02x%02x%02x" % px[x, yy] for x in range(COLS)) for yy in range(PXH)])
    return out


def main():
    files = set()
    for r in csv.DictReader(open(os.path.join(MODEL, "habitats.csv"))):
        f = (r.get("File Name (png)") or "").strip()
        if f:
            files.add(f)
    bgs = {}
    for fn in sorted(files):
        fr = frames_for(fn)
        if fr:
            bgs[fn] = fr
    path = os.path.join(OUT, "backgrounds.json.gz")
    with gzip.open(path, "wt") as fh:
        json.dump(bgs, fh, separators=(",", ":"))
    sz = os.path.getsize(path)
    print(f"extracted {len(bgs)} backgrounds ({sum(len(v) for v in bgs.values())} frames) -> {path} ({sz//1024} KB)")


if __name__ == "__main__":
    main()
