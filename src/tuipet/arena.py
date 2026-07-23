"""The animated LCD arena: the Screen widget plus its fx painters and the
filth / status-effect overlays.

Lifted out of app.py verbatim (modularization 2026-07-08) — this is the render
half of the old app module.  app.py imports the public names back
(Screen, hearts, bar, _effect_overlay, SCREEN_COLS/ROWS, ...) so
`tuipet.app.Screen` and the existing tests keep resolving.  Nothing here imports
app, so there is no cycle.

NOTE: the Screen renderer resolves `render_screen` in THIS module's namespace.
Tests that spy on it must patch `tuipet.arena.render_screen`, not `tuipet.app`.
"""
from __future__ import annotations

import random

from textual.widgets import Static

from . import data
from . import anim
from . import egg as egg_mod
from . import grid
from . import theme
from .theme import LCD_ON, LCD_BG, SIL_SCENE, SIL_LIGHTSOFF, VOID
from .pet import Pet
from .render import render_screen

# the fx engine + shared geometry live in arenafx (tier-2 split 2026-07-17);
# every old name stays importable from here (and via app.py's re-export)
from .arenafx import (  # noqa: F401,E402
    COND_H, COND_W, FxMixin, GIFT_BACK, GIFT_HOLD, GIFT_OUT, PET_BASE_X,
    PLAY_HOP, PLAY_HOP_H, PLAY_LEAD, POOP_PAD, POOP_W, SCREEN_COLS,
    SCREEN_ROWS, SICK_ZONE, SPRITE_W, _FxCtx, _WINDOW, _clip_win,
    _HIDDEN_STATUS_ICONS, _effect_overlay, _evol_strobe, _filth_pts,
    _filth_right, _sick_mark_up)


def hearts(n, total=4, color=None):
    color = color or theme.HEART
    return f"[{color}]" + "●" * n + "[/][dim]" + "○" * (total - n) + "[/dim]"


def bar(v, width=12, color=None):
    color = color or theme.LIFE
    fill = max(0, min(width, round(v / 100 * width)))   # clamp: never overrun the track
    return f"[{color}]" + "█" * fill + "[/][dim]" + "─" * (width - fill) + "[/dim]"


_FX = data.load_effects()
GRAVESTONE = _FX.get("grave", [None])[0]      # real DVPet death.png


def _flip_frames(frames, _fr, first, role=None):
    """A pose-flip needs two DIFFERENT rips (Joel 2026-07-22: "why does
    bubbmon not have a dancing animation?  theres only one frame").  Some
    sheets fill a role's slots with one identical frame -- Bubbmon's
    4/5/7 are the same rip, freezing its happy dance ([5,7]) and its
    poopdance ([4,5]) solid; a roster scan found ~35 species with SOME
    frozen flip (happy/poop/angry/tantrum/startle/wash... and sleep).
    When every slot resolves to the same bitmap, alternate with a
    DIFFERENT real frame of the same species (the bob pair first) --
    motion from the rips it actually has, nothing drawn.  SLEEP is
    exempt: a still sleeper is the correct pose, and the bob substitute
    would flash it visibly awake every beat."""
    if role == "sleep" or len(frames) < 2:
        return frames
    fs = [(_fr[i] if i < len(_fr) else None) or first for i in frames]
    if any(f != fs[0] for f in fs):
        return frames
    alt = next((j for j in (1, 0, 8, 6) if j < len(_fr) and _fr[j]
                and _fr[j] != fs[0]), None)
    return [frames[0], alt] if alt is not None else frames


#                                                     every canon sprite fits inside; things leave
#                                                     the screen only off the LEFT or RIGHT edge,
#                                                     on occasion -- never the top or bottom.)


class Screen(FxMixin, Static):
    """The animated LCD screen."""
    BG_FADE = 15              # canon animateBack: viewConfig BackgroundOpacityChange
    #                           -0.05/tick = a ~20-tick dissolve; 15 of our 10Hz
    #                           ticks = 1.5s (background audit 2026-07-15)

    def on_mount(self):
        self.frame_i = 0      # interval counter (10 Hz; 1 tick == 0.1s == one DVPet _interval)
        self.anim_key = None  # last anim state, so cadences restart on a state change
        self.roamer = anim.Roamer(int(SCREEN_COLS * 0.28), SCREEN_COLS, SPRITE_W)  # left-of-centre anchor
        self.fx = None        # active care-action animation
        self._idle_expr = None    # DVPet stepFrame mood-pose held for the current idle step (None = walk toggle)

    def paint(self, pet: Pet):
        if self.fx:
            return self._paint_fx(pet)
        # (the per-phase LCD tint left with the day/night system -- BASIC
        # VPET 2026-07-17; one palette, day and night)
        on, bg = LCD_ON, LCD_BG
        bgimg = self._background(pet)
        if not pet.lights:                 # lights off (the 's' lights button): dark room (+ Zzz if asleep)
            bgimg, bg, on = None, VOID, SIL_LIGHTSOFF   # DVPet lightsOff.png is pure (0,0,0); VOID keeps it on-palette
        elif bgimg:
            on = SIL_SCENE   # dark silhouette day OR night -- the pet is never white;
            #                white (SIL_LIGHTSOFF) is reserved for the lights-out Zzz below
        # (the storm gloom, thunder flash and precip overlays left with the
        # weather system; BASIC VPET 2026-07-16)
        wf = self.frame_i // 4                  # effect overlays keep their ~0.4s cadence
        if pet.dead:                           # a grave marker (the live path builds its own overlay below)
            self.update(render_screen(
                GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg, bgimg=bgimg,
                overlay=_clip_win(_effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i)),
                clip=_WINDOW))
            return
        if pet.num == -1:                      # egg
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            rec = data.record_for(pet.num)   # never KeyError: a cross-version
            #                                  save wears the placeholder
            roles = data.ROLES
        _fr = rec["frames"]
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        frames = _flip_frames(roles.get(pet.anim, [0]), _fr, first,
                              role=pet.anim)
        # stepFrame: a GERIATRIC pet idles on spriteNum+9 -- the aged shuffle
        # toggles the dejected/collapse frames (canon re-audit 2026-07)
        if (pet.anim in ("idle", "walk") and pet.num != -1
                and getattr(pet, "is_geriatric", False)):
            frames = [f + 9 for f in frames]
        # per-state cadence: hold each pose for its DVPet interval count rather than
        # flipping every tick (root-cause #2 -- one tick == one _interval; see anim.py).
        # idle holds 5/6/7, sleep holds its 2/3 poses for 10 each, reactions ~6.
        hold = (anim.idle_hold(pet._restless()) if pet.anim in ("idle", "walk")
                else anim.SLEEP_BEAT if pet.anim == "sleep" else 6)
        idx = frames[(self.frame_i // hold) % len(frames)]
        rows = (_fr[idx] if idx < len(_fr) else None) or first
        xshift, mirror = 0, False
        if pet.anim in ("idle", "walk") and pet.sick and pet.num != -1:
            si, dx = anim.sick_frame(self.frame_i)               # DVPet idleUnwell: collapse(10), weary(9) flash
            rows = (_fr[si] if si < len(_fr) else None) or first
            # canon idleUnwell resets Y ONLY (setSpriteCharDefaultY) and sways
            # around the pet's current X -- it collapses where it stands, not
            # at the anchor (walk-pose audit 2026-07-08)
            xshift = self.roamer.xshift + dx
        elif pet.anim in ("idle", "walk") and pet.num != -1:
            # full-width roam (DVPet idleWalk); pose follows the roamer's step, and a
            # filth pile is a left wall it turns at (filthLabel walk bound).  On some
            # steps DVPet's stepFrame shows a mood pose instead of the walk toggle.
            if self.roamer.pause:
                # device wall-pause (GML 2026-07-14): stopped at the wall on the
                # TURN pose pair -- turn(1)/idle(0) alternating -- before it
                # departs; a mood pose never overrides the turn
                idx = (1, 0)[self.roamer.pause % 2]
            else:
                expr = self._idle_expr if pet.anim == "idle" else None
                idx = expr if expr is not None else frames[self.roamer.pose % len(frames)]
            rows = (_fr[idx] if idx < len(_fr) else None) or first
            xshift, mirror = self.roamer.xshift, self.roamer.mirror
        else:
            mirror = pet.anim in data.MIRROR_ROLES and (self.frame_i // 6) % 2 == 1
            if pet.anim.startswith("startle"):
                # canon surprising() is an IDLE-family special: it jumps where
                # it stands, facing kept (drawNumMirror(.., getIsMirror())) --
                # never re-anchored (walk-pose audit 2026-07-08)
                xshift, mirror = self.roamer.xshift, self.roamer.mirror
        if pet.num == -1 and pet.hatching:
            # DVPet hatch() (SpriteAnim 11556), driven by elapsed hatch time (1 interval==0.1s):
            # the egg rocks (moveRight/Left 3) over intervals 4..15, then CRACKS -- drawNum(1)
            # at interval 16, drawNum(2) at interval 19 -- revealing the baby before the Fresh.
            # round, don't truncate: 0.4/0.1 is 3.999... in binary floats, and a
            # truncated beat makes the rock STUTTER (0,+6,+3,0,0,...) and the
            # crack land late (hatch-anim audit 2026-07-05)
            n = int(round((3.0 - getattr(pet, "_hatch_t", 3.0)) / 0.1))
            # the wobble ACCELERATES as the hatch nears (device-exact, GML
            # 2026-07-14: egg alarm 30 -> 10 for the final stretch): sways on
            # intervals 4/6/8 (0.2s beat), then EVERY interval 10..15
            beats = [4, 6, 8] + list(range(10, 16))
            moves = sum(1 for k in beats if k <= min(n, 15))
            # 0->3->6->3 rock cycle; the CRACK recentres (the accelerated cycle
            # ends mid-sway, unlike the old symmetric +-3 walk)
            xshift = 0 if n >= 16 else (0, 3, 6, 3)[moves % 4]
            fi = 0 if n < 16 else (1 if n < 19 else 2)      # egg -> crack -> baby emerging
            rows = (_fr[fi] if fi < len(_fr) and _fr[fi] else first)
            mirror = False
        # NOTE: DVPet's frozen.png (the ice encasement) is its GAME-PAUSED indicator
        # (setFrozenIcon only fires when !isPlaying), not a cold-weather state -- so cold
        # shows the huddle pose above, not a full ice block over the pet.
        # exclusive floor zones, enforced in EVERY state (Bandai-grammar sweep
        # 2026-07-11): the filth block is a hard left wall and the sick skull
        # a hard right one -- sleep/sick/startle bypass the roamer's bounds,
        # so the clamp here is what actually guarantees no overlap.
        base = PET_BASE_X
        lo = (_filth_right(pet.poop) if pet.poop else grid.X0) - base
        cap = ((grid.X1 - SICK_ZONE if _sick_mark_up(pet) else grid.X1)
               - SPRITE_W) - base
        xshift = min(max(xshift, lo), max(cap, lo))       # poop wins over the skull (it yields when crowded)
        overlay = _clip_win(_effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i))
        if not pet.lights:                 # lights off: DVPet's lightsOff is a fully-opaque black
            rows, xshift, mirror = [], 0, False   # cover -> the pet is hidden; only black (+ Zzz) shows
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, overlay=overlay,
                                  bgimg=bgimg, clip=_WINDOW))

    def _background(self, pet):
        return self._crossfade(pet.background())

    def _crossfade(self, target):
        """Canon BackgroundAnim.animateBack: a background change never snaps --
        the old frame dissolves into the new one (scene picks, egg homes).
        A None or shape change still cuts: lights-off is canon's
        checkBackNoAnim force path.  (The weather/habitat swap triggers this
        was built for left with their systems -- doc truthed 2026-07-18.)"""
        prev = getattr(self, "_bg_tgt", None)
        if target is None or not prev or not target \
                or len(prev) != len(target) or len(prev[0]) != len(target[0]):
            self._bg_tgt = self._bg_out = target
            self._bg_fade = 0
            return target
        if target != prev:
            self._bg_from = self._bg_out    # retarget from what's showing NOW,
            self._bg_tgt = target           # so a mid-fade flap never jumps
            self._bg_fade = self.BG_FADE
        if getattr(self, "_bg_fade", 0) > 0:
            self._bg_fade -= 1
            self._bg_out = theme.blend_frames(
                self._bg_from, target, 1 - self._bg_fade / self.BG_FADE)
        else:
            self._bg_out = target
        return self._bg_out

    def advance(self, pet=None):
        if pet is not None and pet.anim != self.anim_key:
            self.anim_key = pet.anim            # new state -> restart its cadence at beat 0
            self.frame_i = -1
        self.frame_i += 1
        if (pet is not None and pet.anim in ("idle", "walk") and pet.num != -1
                and not pet.sick and not self.fx):
            # not during an fx: the roamer holds position while a pose or care
            # anim plays (canon anims own LocX; the walk resumes after) -- else
            # a seeded yawn/poopdance would SLIDE as the roamer kept stepping
            poop_right = _filth_right(pet.poop) if pet.poop else grid.X0
            # keep the pet inside the grid: left of the sick skull while it
            # stands in the scene (the SAME predicate paint()'s clamp uses),
            # else the full locked 32x16 is the pet's -- nothing else on the
            # LCD may shrink its world (Bandai grammar 2026-07-11)
            right_bound = ((grid.X1 - SICK_ZONE - SPRITE_W) if _sick_mark_up(pet)
                           else (grid.X1 - SPRITE_W))
            self.roamer.step(left_bound=poop_right, right_bound=right_bound)
            if self.roamer.stepped and not self.roamer.pause:    # a fresh step landed (DVPet stepFrame):
                # keyed on the BEAT, not a pose change -- the device-exact
                # random frame pick repeats a pose ~half the time, which would
                # have silently halved the mood-pose rate (GML port 2026-07-14)
                self._idle_expr = (anim.mood_pose(pet)           # sometimes show a mood pose instead of
                                   if random.random() < anim.IDLE_EXPR_CHANCE else None)  # the plain walk toggle
        else:
            self._idle_expr = None                               # any non-idle state clears the held expression


