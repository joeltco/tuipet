"""Stand-in sprite for any creature whose art is unfinished. In the current data
set this never triggers (all 1525 creatures have real, extracted art); if a future
build ever has an unfinished cell it renders blank rather than a drawn-in glyph --
we never invent art."""
from __future__ import annotations
from . import data


def _frames():
    cm = data.load_effects().get("copymon")
    return cm if cm else [["0000000000000000"]]


FRAMES = _frames()
W = max(len(r) for r in FRAMES[0])
H = len(FRAMES[0])


def record(num, name, stage, attribute):
    return {"num": num, "name": name, "stage": stage, "attribute": attribute,
            "field": "None", "element": "None", "spriteSet": 0, "spriteNum": 0,
            "w": W, "h": H, "frames": FRAMES, "_placeholder": True}
