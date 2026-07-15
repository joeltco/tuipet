"""the classic V-pet ambient-animation cadence, isolated as pure helpers so the timing is
testable without Textual.

The whole engine rests on one invariant from the decompiled game: SpriteAnim
sets ``_interval = targetFPS / 10`` frames, so ``_interval`` is exactly 1/10 of
a second and every ``_frame == _interval * N`` check fires N tenths of a second
into a state.  tuipet therefore drives animation on a single 10 Hz tick where
**one tick == one interval == 0.1 s**, and each state below reproduces the classic V-pet's
beats one-for-one in real time, independent of frame rate.

Ground truth: _audit_src/View/SpriteAnim.java
  idleNormal :11246   idleWalk :11337   idleSleep :11525   idleUnwell :11447
"""
from __future__ import annotations
import random

STEP_PX = 2        # device-exact: 2px per beat over the 16px travel range
#                    (GML decompile 2026-07-14, obj_char_vpet Alarm_2; was 3)
TURN_CHANCE = 0.30 # device: irandom(100)>70 -- ~30% of beats flip direction
WALL_PAUSE = 4     # device limit_reach: 4 beats (2.0s) STOPPED at a wall on the
#                    turn pose pair before departing the other way
WALK_BEAT = 5      # idleWalk advances at _frame 0 and _frame 5 -> a step every 5 intervals
SLEEP_BEAT = 10    # idleSleep: pose 2 at 0, pose 3 at 10, back at 20 (period 20)
SICK_PERIOD = 50   # idleUnwell: collapse held, tiny shuffle 30..45, weary flash at 50
IDLE_EXPR_CHANCE = 0.30   # stepFrame: a fraction of idle steps show a mood pose, not the walk toggle


def idle_hold(restless):
    """idleNormal holds each idle pose 5/6/7 intervals (restless >0 / 0 / <0)."""
    return 5 if restless > 0 else (7 if restless < 0 else 6)




def sick_frame(frame):
    """idleUnwell: returns (sprite_index, dx_px).  Collapse pose (10) dominates the
    50-interval cycle; the weary pose (9) only flashes on the reset beat.  the classic V-pet's
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


def mood_pose(pet):
    """the classic V-pet stepFrame substitutes a `checkMoodFrame` expression pose for the plain
    walk toggle on a fraction of idle steps, so a resting pet *reads* its state:
    weary when tired/spent, sour when unhappy, bright when content.  Returns a
    sprite index, or None to keep the neutral walk toggle.

    Mapping condensed from checkMoodFrame's offset table: tired/no-energy -> 9/10/2,
    unhappy -> 4/6, happy & spirited -> 5, otherwise neutral (None)."""
    if pet.energy <= 0:
        return random.choice((10, 9, 2))      # weary / collapsed / droop
    if pet.sick or pet.hunger == 0 or pet.strength == 0:
        return random.choice((4, 6))          # sour faces
    return None                               # neutral -> ordinary walk pose


class Roamer:
    """Full-width pacing, after SpriteAnim.idleWalk: the pet steps STEP_PX every
    WALK_BEAT intervals, toggling its two walk poses.  the classic V-pet's idleWalk *wraps*
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
        self.pause = 0            # wall-pause beats left (device limit_reach)
        self.stepped = False      # True on the interval a movement beat landed
        self._t = 0
        self._wall = 1            # departure direction once the pause ends

    def step(self, left_bound=0, right_bound=None):
        """Advance one interval.  Movement happens on the WALK_BEAT cadence,
        device-exact per the 2026-07-14 GML decompile (obj_char_vpet Alarm_2):
        each beat picks a walk frame at RANDOM (50/50, not a strict toggle),
        flips direction on ~30% of beats, and steps STEP_PX.  Hitting a wall
        (screen edge, filth pile, status column) STOPS the pet for WALL_PAUSE
        beats -- it stands on the turn pose pair -- then it departs the other
        way.  (the classic V-pet's idleWalk wrapped; the walls are tuipet's adaptation.)"""
        self.stepped = False
        self._t += 1
        if self._t < WALK_BEAT:
            return
        self._t = 0
        self.stepped = True
        if self.pause:                               # stopped at the wall, turning
            self.pause -= 1
            self.pose ^= 1                           # the turn pair alternates
            if self.pause == 0:                      # departure beat: face away and go
                self.face = self._wall
                self.x += self.face * STEP_PX
            return
        self.pose = random.getrandbits(1)            # device: 50/50 frame pick
        if random.random() < TURN_CHANCE:            # device flips BEFORE moving
            self.face = -self.face
        self.x += self.face * STEP_PX
        right_edge = self.cols - self.sw
        if right_bound is not None:                  # a right-edge status column is a wall too
            right_edge = min(right_edge, right_bound)
        if self.x >= right_edge:                     # hit the right wall -> stop and turn
            self.x = float(right_edge)
            self.pause, self._wall = WALL_PAUSE, -1
        elif self.x <= left_bound:                   # left wall / filth pile -> stop and turn
            self.x = float(left_bound)
            self.pause, self._wall = WALL_PAUSE, 1

    @property
    def xshift(self):
        """Offset from screen centre that render_screen expects (it centres first)."""
        base = (self.cols - self.sw) // 2
        return int(round(self.x)) - base

    @property
    def mirror(self):
        return self.face > 0          # sprites face left by default; mirror to face right
