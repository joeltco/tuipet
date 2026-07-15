"""Stand-in sprite for any creature whose art is unfinished -- the classic V-pet's own
`copymon`. In the current data set this never triggers (all 1525 creatures have
real, extracted art), but if a future build has an unfinished cell we show a real
the classic V-pet sprite, never a drawn one."""
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
