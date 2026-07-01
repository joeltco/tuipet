#!/usr/bin/env python3
"""Procedurally generate tuipet's 1-bit dot art from scratch — original shapes drawn
by code, NOT traced from the DVPet rips.  Mirrors gen_sounds.py: deterministic,
stdlib-only, re-runnable.  Replaces the ripped effects/orbs/overlays/food-icon so the
package carries no extracted DVPet PNG data.

Each frame is a list of equal-length '0'/'1' row strings (same schema the renderer
already consumes).  Sizes match the assets they replace so the LCD layout math is
untouched.  Dead glyphs (praise/scold/sun/moon/attack/hit/st_teach/train_cannon_up)
are simply not generated.

Usage:
    python3 tools/gen_art.py --preview          # ASCII preview, writes nothing
    python3 tools/gen_art.py --out src/tuipet/data   # write the .gz/.json files
"""
from __future__ import annotations
import argparse
import gzip
import json
import math
import os


# ---- tiny drawing kit ------------------------------------------------------
class C:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[0] * w for _ in range(h)]

    def px(self, x, y, v=1):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.g[int(y)][int(x)] = v

    def rect(self, x0, y0, x1, y1, fill=False):
        for x in range(x0, x1 + 1):
            self.px(x, y0); self.px(x, y1)
        for y in range(y0, y1 + 1):
            self.px(x0, y); self.px(x1, y)
        if fill:
            for y in range(y0 + 1, y1):
                for x in range(x0 + 1, x1):
                    self.px(x, y)

    def hline(self, x0, x1, y):
        for x in range(x0, x1 + 1):
            self.px(x, y)

    def vline(self, x, y0, y1):
        for y in range(y0, y1 + 1):
            self.px(x, y)

    def disc(self, cx, cy, r, fill=True):
        for y in range(self.h):
            for x in range(self.w):
                d = math.hypot(x - cx, y - cy)
                if (d <= r) if fill else (r - 0.7 <= d <= r + 0.2):
                    self.px(x, y)

    def rows(self):
        return ["".join(str(v) for v in row) for row in self.g]


def _blank(w, h):
    return C(w, h).rows()


def G(art):
    """Parse a hand-drawn glyph ('.'=off, '#'=on) into '0'/'1' rows. Original art."""
    rows = [ln for ln in art.split("\n") if ln]
    w = max(len(r) for r in rows)
    return [r.ljust(w, ".").replace(".", "0").replace("#", "1") for r in rows]


# ---- effect glyphs (original designs) --------------------------------------
def _attention():                                   # 4x8 exclamation mark
    c = C(4, 8)
    c.rect(1, 0, 2, 4, fill=True)
    c.rect(1, 6, 2, 7, fill=True)
    return [c.rows()]


def _zzz():                                         # 8x6 two blocky Z's rising right
    f0 = G("""
....####
.....##.
....##..
###.####
.##.....
###.....
""")
    f1 = G("""
...####.
....##..
...##...
.###.###
..##....
.###....
""")
    return [f0, f1]


def _happy():                                       # 8x8 twinkling gem (positive emote)
    f0 = G("""
...##...
..####..
.######.
########
########
.######.
..####..
...##...
""")
    f1 = G("""
...##...
..####..
.##..##.
##....##
##....##
.##..##.
..####..
...##...
""")
    return [f0, f1]


def _unhappy():                                     # 7x8 rain cloud (gloomy emote)
    f0 = G("""
..###..
.#####.
#######
#######
.#####.
..#.#..
.#...#.
.......
""")
    f1 = G("""
..###..
.#####.
#######
#######
.#####.
.#.#...
...#.#.
.......
""")
    return [f0, f1]


def _poop():                                        # 8x8 swirl pile, 2 frames
    def f(w):
        c = C(8, 8)
        c.hline(2, 5, 7); c.hline(1, 6, 6)           # base mound
        c.hline(2, 5, 5); c.hline(2, 4, 4)
        c.hline(3, 4, 3); c.px(3 + w, 2)             # swirl tip
        c.px(2, 5); c.px(5, 4)                       # texture
        return c.rows()
    return [f(0), f(1)]


def _dying():                                       # 7x8 bold X (crossed-out / done for)
    f0 = G("""
##...##
.##.##.
..###..
...#...
..###..
.##.##.
##...##
.......
""")
    f1 = G("""
.#...#.
##...##
.##.##.
..###..
.##.##.
##...##
.#...#.
.......
""")
    return [f0, f1]


def _grave():                                       # 12x16 tombstone with a cross
    c = C(12, 16)
    c.rect(2, 2, 9, 15)                             # arched slab
    c.hline(3, 8, 1); c.px(2, 1 + 0)
    for y in range(0, 2):
        c.px(3 + y, y); c.px(8 - y, y)
    c.vline(5, 5, 11); c.vline(6, 5, 11)            # cross
    c.hline(3, 8, 7); c.hline(3, 8, 8)
    c.hline(1, 10, 15)                              # ground line
    return [c.rows()]


def _wash():                                        # 14x21 shower spray fan
    c = C(14, 21)
    c.hline(4, 9, 0); c.hline(3, 10, 1)            # spray head
    for i, x in enumerate(range(2, 13, 2)):        # falling droplets, staggered
        y = 4 + (i % 3) * 2
        for k in range(3):
            c.px(x, y + k * 5)
            c.px(x - 1, y + 2 + k * 5)
    return [c.rows()]


# ---- 7x7 condition icons (each: [frame0, blink-frame1]) --------------------
def _two(a, b):
    return [G(a), G(b)]


_SICK = _two("""
..###..
.#####.
#.#.#.#
#.#.#.#
.#####.
..###..
..#.#..
""", """
..###..
.#####.
#.###.#
#.###.#
.#####.
..###..
..#.#..
""")                                                # skull: hollow eyes + teeth

_INJURY = _two("""
...##..
..##...
.####..
...##..
..##...
.##....
.#.....
""", """
...#...
..##...
.###...
...##..
..##...
.##....
.#.....
""")                                                # jagged crack / lightning (a wound)

_BANDAGE = _two("""
.......
.#####.
##.#.##
#.#.#.#
##.#.##
.#####.
.......
""", """
.......
.#####.
##...##
#.#.#.#
##...##
.#####.
.......
""")                                                # plaster w/ pad dots

_FATIGUE = _two("""
...#...
...#...
..###..
.#####.
.#####.
..###..
.......
""", """
...#...
..###..
.#####.
.#####.
..###..
...#...
.......
""")                                                # sweat drop

_VITAMIN = _two("""
.......
.#####.
###.###
###.###
.#####.
.......
.......
""", """
.......
.#####.
##...##
##...##
.#####.
.......
.......
""")                                                # scored tablet

_MEDICINE = _two("""
..###..
..#.#..
.#####.
.#####.
.#...#.
.#####.
.#####.
""", """
..###..
..###..
.#####.
.#####.
.#...#.
.#####.
.#####.
""")                                                # medicine bottle


def _copymon():                                     # 16x16 "?" box — unfinished-sprite fallback
    c = C(16, 16)
    c.rect(1, 1, 14, 14)                            # frame
    for gy, row in enumerate(_FONT["?"] if "?" in _FONT else ["111", "001", "011", "000", "010"]):
        for gx, v in enumerate(row):
            if v == "1":
                c.px(6 + gx, 5 + gy)
    return [c.rows()]


def build():
    effects = {
        "copymon": _copymon(),
        "attention": _attention(),
        "zzz": _zzz(),
        "happy": _happy(),
        "unhappy": _unhappy(),
        "poop": _poop(),
        "dying": _dying(),
        "grave": _grave(),
        "wash": _wash(),
        "st_sick": _SICK,
        "st_injury": _INJURY,
        "st_bandage": _BANDAGE,
        "st_fatigue": _FATIGUE,
        "st_vitamin": _VITAMIN,
        "st_medicine": _MEDICINE,
    }
    return effects


# ---- orbs (fully algorithmic: a disc that grows with power tier) -----------
def _orb(attr, tier):
    r = 2.3 + tier * 0.05                            # small (tier0) -> full (tier24)
    c = C(8, 8)
    c.disc(3.5, 3.5, min(r, 3.5))
    if attr == "Vaccine":                           # ring highlight
        c.px(3, 3, 0); c.px(4, 3, 0)
    elif attr == "Virus":                           # jagged edge
        c.px(0, 3); c.px(7, 4); c.px(3, 0); c.px(4, 7)
    # Data: plain filled disc
    return c.rows()


def build_orbs():
    gen = {a: [_orb(a, t) for t in range(25)] for a in ("Vaccine", "Data", "Virus")}
    return {"generic": gen, "special": {}}


# ---- battle overlays -------------------------------------------------------
# minimal 3x5 uppercase font for the banners (generic letterforms, not DVPet art)
_FONT = {
    "B": ["110", "101", "110", "101", "110"], "A": ["010", "101", "111", "101", "101"],
    "T": ["111", "010", "010", "010", "010"], "L": ["100", "100", "100", "100", "111"],
    "E": ["111", "100", "110", "100", "111"], "V": ["101", "101", "101", "101", "010"],
    "S": ["011", "100", "010", "001", "110"], "!": ["1", "1", "1", "0", "1"],
}


def _text(s, cw=32, ch=16, invert=False):
    c = C(cw, ch)
    glyphs = [_FONT[ch_] for ch_ in s]
    total = sum(len(g[0]) + 1 for g in glyphs) - 1
    x = (cw - total) // 2
    y = (ch - 5) // 2
    if invert:                                      # flash frame: fill, punch the text out
        c.rect(0, 0, cw - 1, ch - 1, fill=True)
    for g in glyphs:
        for gy, row in enumerate(g):
            for gx, v in enumerate(row):
                if v == "1":
                    c.px(x + gx, y + gy, 0 if invert else 1)
        x += len(g[0]) + 1
    return c.rows()


def _burst(dense):                                 # 30x18 spiky burst, 2 densities (strobe)
    c = C(30, 18)
    cx, cy = 15, 9
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        ln = (9 if ang % 60 == 0 else 6) if dense else (7 if ang % 60 == 0 else 4)
        r0 = 2 if dense else 3
        for r in range(r0, ln):
            c.px(cx + r * math.cos(a), cy + r * math.sin(a) * 0.5)
            if dense:                               # thicken the rays on the filled frame
                c.px(cx + r * math.cos(a), cy + r * math.sin(a) * 0.5 + 1)
    c.disc(cx, cy, 3.5 if dense else 2.0)
    return c.rows()


def build_overlays():
    return {
        "battle_banner": [_text("BATTLE!", 32, 16), _text("BATTLE!", 32, 16, invert=True)],
        "hit_explosion": [_burst(False), _burst(True)],
    }


# ---- food icon (24x24, 4 eaten stages) -------------------------------------
def _meat(stage):                                   # a meat-on-bone that shrinks
    c = C(24, 24)
    keep = 1.0 - stage * 0.28                        # 1.0 -> 0.16 across 4 stages
    r = 8 * keep
    if r >= 1:
        c.disc(12, 11, r)                            # the meat
        c.disc(12 - r * 0.5, 11 - r * 0.4, r * 0.35, fill=False)   # sheen
    c.vline(3, 18, 22); c.vline(4, 18, 22)          # bone stub always shows
    c.px(2, 18); c.px(5, 18); c.px(2, 22); c.px(5, 22)
    return c.rows()


def build_icons():
    return {"f:0": [_meat(s) for s in range(4)]}


# ---- output / preview ------------------------------------------------------
def _ascii(frame):
    return "\n".join(r.replace("0", "·").replace("1", "█") for r in frame)


def preview():
    eff = build()
    print("=== EFFECT GLYPHS ===")
    for k, frames in eff.items():
        print(f"\n[{k}]  {len(frames[0][0])}x{len(frames[0])}")
        print(_ascii(frames[0]))
    print("\n=== ORBS (Vaccine tiers 0 / 12 / 24) ===")
    orbs = build_orbs()["generic"]
    for t in (0, 12, 24):
        print(f"\nVaccine tier {t}")
        print(_ascii(orbs["Vaccine"][t]))
    print("\n=== BATTLE OVERLAYS ===")
    for k, fr in build_overlays().items():
        print(f"\n[{k}]")
        print(_ascii(fr))
    print("\n=== FOOD ICON (4 eaten stages) ===")
    for i, fr in enumerate(build_icons()["f:0"]):
        print(f"\nstage {i}")
        print(_ascii(fr))


def write(out):
    def wz(name, obj):
        with gzip.open(os.path.join(out, name), "wt") as fh:
            json.dump(obj, fh)
    wz("effects.json.gz", build())
    wz("orbs.json.gz", build_orbs())
    wz("icons.json.gz", build_icons())
    with open(os.path.join(out, "battle_overlays.json"), "w") as fh:
        json.dump(build_overlays(), fh)
    print(f"wrote effects/orbs/icons/battle_overlays to {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.out:
        write(a.out)
    else:
        preview()
