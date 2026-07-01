"""DVPet ambient-animation cadence, isolated as pure helpers so the timing is
testable without Textual.

The whole engine rests on one invariant from the decompiled game: SpriteAnim
sets ``_interval = targetFPS / 10`` frames, so ``_interval`` is exactly 1/10 of
a second and every ``_frame == _interval * N`` check fires N tenths of a second
into a state.  tuipet therefore drives animation on a single 10 Hz tick where
**one tick == one interval == 0.1 s**, and each state below reproduces DVPet's
beats one-for-one in real time, independent of frame rate.

Ground truth: _audit_src/View/SpriteAnim.java
  idleNormal :11246   idleWalk :11337   idleSleep :11525   idleUnwell :11447
"""
from __future__ import annotations
import random

STEP_PX = 3        # idleWalk / stepFrame moveRight|Left(3)
TURN_CHANCE = 0.06 # stepFrame flips travelRight now and then so the pet wanders, not marches
WALK_BEAT = 5      # idleWalk advances at _frame 0 and _frame 5 -> a step every 5 intervals
SLEEP_BEAT = 10    # idleSleep: pose 2 at 0, pose 3 at 10, back at 20 (period 20)
SICK_PERIOD = 50   # idleUnwell: collapse held, tiny shuffle 30..45, weary flash at 50
IDLE_EXPR_CHANCE = 0.30   # stepFrame: a fraction of idle steps show a care-state pose, not the walk toggle


def idle_hold(restless):
    """idleNormal holds each idle pose 5/6/7 intervals (restless >0 / 0 / <0)."""
    return 5 if restless > 0 else (7 if restless < 0 else 6)


def sick_frame(frame):
    """idleUnwell: returns (sprite_index, dx_px).  Collapse pose (10) dominates the
    50-interval cycle; the weary pose (9) only flashes on the reset beat.  DVPet's
    shuffle is moveLeft1@30, moveRight1@35, moveRight1@40, moveLeft1@45 -- which is
    net-zero: the body sits 1px left over [30,35), back to centre [35,40), 1px right
    over [40,45), centre after.  (The pose offset is HELD across each range, not a
    one-frame blip.)"""
    f = frame % SICK_PERIOD
    if f == 49:
        idx = 9                            # brief weary flash before the reset
    else:
        idx = 10                           # collapsed the rest of the time
    if 30 <= f < 35:
        dx = -1
    elif 40 <= f < 45:
        dx = 1
    else:
        dx = 0
    return idx, dx


def care_pose(pet):
    """On a fraction of idle steps the pet shows an expression pose instead of the plain
    walk toggle, so a resting pet *reads* its live care state (DM20 has no mood meter --
    this is state-driven, not a stored value).  Returns a sprite index, or None to keep
    the neutral walk toggle.

    needs-care (hungry/injured/messy) -> 4/6 (sour), otherwise neutral (None -- a
    content pet just walks)."""
    if pet.needs_care():
        return random.choice((4, 6))          # sour faces (hungry / injured / messy)
    return None                               # content -> ordinary walk pose


class Roamer:
    """Full-width pacing, after SpriteAnim.idleWalk: the pet steps STEP_PX every
    WALK_BEAT intervals, toggling its two walk poses.  DVPet's idleWalk *wraps*
    around the screen edges; on tuipet's tiny LCD we instead *turn around* at the
    walls (so the pet never vanishes) and occasionally about-face mid-room
    (TURN_CHANCE) so it wanders rather than marches.  A filth pile on the floor is
    a hard left wall it turns at."""

    def __init__(self, x, cols, sprite_w, face=1):
        self.x = float(x)
        self.cols = cols
        self.sw = sprite_w
        self.face = face          # +1 moving/looking right, -1 left
        self.pose = 0             # index into the two walk frames [0, 1]
        self._t = 0

    def step(self, left_bound=0, right_bound=None):
        """Advance one interval.  Movement happens on the WALK_BEAT cadence: the pet
        paces STEP_PX at a time, turning around at the screen edges (and at a filth
        pile on the left) and occasionally reversing mid-room -- the way DVPet's
        stepFrame flips travelRight, so it wanders the full width instead of
        marching one direction forever."""
        self._t += 1
        if self._t < WALK_BEAT:
            return
        self._t = 0
        self.pose ^= 1
        self.x += self.face * STEP_PX
        right_edge = self.cols - self.sw
        if right_bound is not None:                  # a right-edge status column is a wall too
            right_edge = min(right_edge, right_bound)
        if self.x >= right_edge:                     # hit the right wall -> turn back
            self.x = float(right_edge)
            self.face = -1
        elif self.x <= left_bound:                   # hit the left wall (or filth pile) -> turn back
            self.x = float(left_bound)
            self.face = 1
        elif random.random() < TURN_CHANCE:          # otherwise wander: an occasional about-face
            self.face = -self.face

    @property
    def xshift(self):
        """Offset from screen centre that render_screen expects (it centres first)."""
        base = (self.cols - self.sw) // 2
        return int(round(self.x)) - base

    @property
    def mirror(self):
        return self.face > 0          # sprites face left by default; mirror to face right
