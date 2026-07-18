"""Item-use animations — DVPet's per-AnimationType scripts (item-anim audit
2026-07-07: EVERY toy funneled into jumping(), canon's script for the
Trampoline alone — "balloons and futons have broken in game animations").

Each items.csv AnimationType is an Enum.State the device dispatches to its
own SpriteAnim method (playing / bouncing / riding / studying / lifting /
bathing / showering / interactingSound + the four Interact variants /
angrySurprise).  They share one stage: the ITEM at the left floor animating
its own icon frames, the PET at the right posing along, sounds on canon
beats (View/soundConfig.csv wav names, verbatim), and almost all of them
chain into cheer() at the end — angrySurprise chains into jeer().
PlayAngry/InteractAngry are dead canon (never queued by the model).

Scripts are TABLES, not code: `rows` fire once at their beat (canon's
`_frame == _interval * N` branches, 0.1s ticks 1:1), `every` applies per-beat
deltas over a range (the bounce arc, the ride-off).  Canon's 105px stage maps
onto the 40px arena at ~0.4 (moves of 6px -> 2, 3px -> 1); canon item frames
are 1-based over 8 -> ours cycle the 4 extracted frames ((n-1) % 4).
"""
from __future__ import annotations

from . import grid

COLS, SPRITE_W = 40, 16
# The stage lives INSIDE the 32x16 window (bug report 2026-07-13, "balloon
# sprite is broken and off screen": these spots predated the window law --
# ITEM_X=1 hung the toy past the left wall so its first columns clipped, and
# PET_X=23 pushed the pet's right edge past x=36).
PET_X = grid.X1 - SPRITE_W           # the right wall, flush inside the window
ITEM_X = grid.X0                     # the left wall (canon setLoc(3, floor))

# canon frame n (1-based, up to 8) -> our extracted-strip index
def _fr(n):
    return (n - 1) % 4


def _interact(snds):
    """cycleItemFrames(rate=6): item frames 1..8 at 6-beat steps, the pet
    watching (pose 0 arrival, pose 1 after), end beat 48 -> cheer."""
    rows = {0: {"i": _fr(1), "p": 0}}
    for k in range(1, 8):
        rows[6 * k] = {"i": _fr(k + 1), "p": 1}
    return {"steps": 49, "end": "cheer", "snds": snds, "layout": "floor", "rows": rows}


SCRIPTS = {
    # playing(Cheering): the pet hops between neutral and excited while the
    # toy runs its frames; playingInteract (wash) at each excited beat
    "Play": {"steps": 37, "end": "cheer", "layout": "floor",
             "snds": {6: "wash", 18: "wash", 30: "wash"},
             "rows": {0: {"i": _fr(1), "p": 1}, 6: {"i": _fr(2), "p": 5},
                      12: {"i": _fr(3), "p": 1}, 18: {"i": _fr(2), "p": 5},
                      24: {"i": _fr(3), "p": 1}, 30: {"i": _fr(2), "p": 5}}},
    # angrySurprise(Jeering): the capsule opens on the pet -- interact clicks
    # turn into refuses, the pet ends ANGRY and the fx chains into jeer
    "AngrySurprise": {"steps": 49, "end": "jeer", "layout": "floor",
                      "snds": {6: "click", 12: "click", 18: "click",
                               24: "click", 30: "refuse", 42: "refuse"},
                      "rows": {0: {"i": _fr(1), "p": 1}, 6: {"i": _fr(2), "p": 5},
                               12: {"i": _fr(3), "p": 1}, 18: {"i": _fr(4), "p": 5},
                               24: {"i": _fr(5), "p": 1}, 30: {"i": _fr(6), "p": 4},
                               36: {"i": _fr(7), "p": 1}, 42: {"i": _fr(8), "p": 4}}},
    # interactingSound(Cheering): generic Interact -- clicks on every step
    # except the first and last (canon's two exclusions)
    "Interact": _interact({12: "click", 18: "click", 24: "click",
                           30: "click", 36: "click", 42: "click"}),
    # xylophone / xylophone2 accents on canon's 4th/5th steps
    "InteractXylophone": _interact({6: "select", 12: "select", 18: "select",
                                    24: "click", 30: "click",
                                    36: "select", 42: "select"}),
    # tvStatic (wash) at 1/2/7, monitorBeep (refuse) at 3..6
    "InteractTelevision": _interact({6: "wash", 12: "wash", 18: "refuse",
                                     24: "refuse", 30: "refuse", 36: "refuse",
                                     42: "wash"}),
    # monitorBeep at 1/2/3/7, computerFlash (strongAttack) at 4/5, static at 6
    "InteractComputer": _interact({6: "refuse", 12: "refuse", 18: "refuse",
                                   24: "strongAttack", 30: "strongAttack",
                                   36: "wash", 42: "refuse"}),
    # pour at 1, ovenSet at 3/4, ovenFinish (alarm) at 6
    "InteractToyOven": _interact({6: "wash", 18: "click", 24: "click",
                                  36: "alarm"}),
    # studying(): the book pages through while the pet reads; studyStart
    # (wash) then studyProgress clicks; ends into cheer at 32
    "Study": {"steps": 33, "end": "cheer", "layout": "floor",
              "snds": {3: "wash", 17: "click", 22: "click", 27: "click"},
              "rows": {0: {"i": _fr(1), "p": 0}, 3: {"i": _fr(2), "p": 1},
                       6: {"i": _fr(3), "p": 1}, 9: {"i": _fr(4), "p": 1},
                       12: {"i": _fr(5), "p": 1}, 17: {"i": _fr(6), "p": 1},
                       22: {"i": _fr(7), "p": 1}, 27: {"i": _fr(8), "p": 1}}},
    # lifting(): the dumbbell rises off the floor on the strain pose and
    # drops back, twice (canon 16px -> our 6)
    "Lift": {"steps": 31, "end": "cheer", "layout": "floor",
             "snds": {6: "wash", 18: "wash"},
             "rows": {0: {"i": 0, "p": 1}, 6: {"i": 0, "p": 8, "iy": -6},
                      12: {"i": 0, "p": 1, "iy": 0}, 18: {"i": 0, "p": 8, "iy": -6},
                      24: {"i": 0, "p": 1, "iy": 0}}},
    # bathing(): the tub sits at the pet's feet, the pet scrubs 9<->10;
    # bathing (wash) on each scrub beat
    "Bathe": {"steps": 37, "end": "cheer", "layout": "feet",
              "snds": {6: "wash", 18: "wash", 30: "wash"},
              "rows": {0: {"i": 0, "p": 9}, 6: {"i": 1, "p": 10},
                       12: {"i": 0, "p": 9}, 18: {"i": 1, "p": 10},
                       24: {"i": 0, "p": 9}, 30: {"i": 1, "p": 10}}},
    # showering(): the shower head beside the pet runs its frames while the
    # pet shivers under it (pose 9, a 1px jiggle); showerOn -> washes ->
    # showerEnd (error) with the shake-off pose
    "Shower": {"steps": 41, "end": "cheer", "layout": "beside",
               "snds": {4: "refuse", 8: "wash", 12: "wash", 16: "wash",
                        24: "wash", 36: "error"},
               "rows": {0: {"i": _fr(1), "p": 9}, 4: {"i": _fr(2), "pdx": 1},
                        8: {"i": _fr(3), "pdx": -1}, 12: {"i": _fr(4), "pdx": 1},
                        16: {"i": _fr(5), "pdx": -1}, 20: {"i": _fr(6), "pdx": 1},
                        24: {"i": _fr(7), "pdx": -1}, 28: {"i": _fr(8), "pdx": 1},
                        36: {"i": _fr(1), "p": 4, "pdx": 1}}},
    # riding(): the pet hops ONTO the board (up-left arc), then both slide
    # LEFT off the arena, the board's wheels flipping frames; a happy sting
    # mid-ride (canon beat 20), cheer at the end
    "Ride": {"steps": 36, "end": "cheer", "layout": "near",
             "snds": {6: "wash", 20: "happy"},
             "rows": {0: {"i": 0, "p": 1}, 6: {"p": 0}, 14: {"p": 1},
                      20: {"p": 5}, 26: {"p": 1}},
             "every": {(6, 9): {"pdy": -1, "pdx": -1},
                       (10, 11): {"pdx": -1},
                       (12, 13): {"pdy": 1, "pdx": -1},
                       (15, 29): {"pdx": -2, "idx": -2, "icyc": 1}}},
    # bouncing(): the ball drops in from above, caroms off the pet
    # (hitBall -> click, the pet lights up), arcs up-left, drifts left and
    # settles down-left off the arena; cheer at the end
    "Bounce": {"steps": 32, "end": "cheer", "layout": "drop",
               "snds": {14: "click"},
               "rows": {0: {"i": _fr(2), "p": 1}, 14: {"p": 5}, 26: {"p": 1}},
               "every": {(6, 13): {"idy": 2, "icyc": 1},
                         (14, 18): {"idy": -1, "idx": -2, "icyc": 1},
                         (19, 20): {"idx": -2, "icyc": 1},
                         (21, 30): {"idy": 1, "idx": -1, "icyc": 1}}},
}

# AnimationTypes that deliberately have NO item fx: Idling (canon plays
# nothing), plus every system with its own door (transports / ItemEvol /
# Inherit / Recover / Bandaging ride their existing flows).  Jump keeps the
# ported jumping() hop.  (The Futon/toilet mentions left with the staple
# props: strict-DSprite items, 2026-07-17.)
NO_FX = {"Idling"}


def state(action, step, iw, ih, px_h):
    """Replay a script to `step`: (item_frame, pet_pose, item_x, item_y,
    pet_dx, pet_dy).  Geometry: item icon iw x ih on a COLS x px_h arena."""
    sc = SCRIPTS[action]
    floor = px_h - ih - 2            # grounded 2px above the border, like the pet
    lay = sc["layout"]
    if lay == "floor":
        ix, iy = ITEM_X, floor
    elif lay == "feet":
        ix, iy = PET_X + (SPRITE_W - iw) // 2, floor
    elif lay == "beside":
        # clamped at the window wall: a 16-wide icon beside the pet sits
        # flush (item 4..20, pet 20..36), never past the law's left edge
        ix, iy = max(grid.X0, PET_X - iw - 1), max(0, px_h - ih - 3)
    elif lay == "near":                      # the board, just left of the pet
        ix, iy = max(grid.X0, PET_X - iw - 2), floor   # never past the wall
    else:                                    # "drop": above the arena
        ix, iy = 13, -ih
    frame, pose, pdx, pdy, cyc = 0, 1, 0, 0, 0
    for b in range(step + 1):
        row = sc.get("rows", {}).get(b)
        if row:
            frame = row.get("i", frame)
            pose = row.get("p", pose)
            ix += row.get("idx", 0)
            iy = row["iy"] + floor if "iy" in row else iy
            pdx += row.get("pdx", 0)
            pdy += row.get("pdy", 0)
        for (lo, hi), d in sc.get("every", {}).items():
            if lo <= b <= hi:
                ix += d.get("idx", 0)
                iy += d.get("idy", 0)
                pdx += d.get("pdx", 0)
                pdy += d.get("pdy", 0)
                cyc += d.get("icyc", 0)
    if cyc:
        frame = (frame + cyc) % 4
    iy = min(iy, floor)                      # the ball never sinks through the floor
    return frame, pose, ix, iy, pdx, pdy
