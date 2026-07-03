"""DVPet TUI — a terminal virtual pet rendered with halfblock sprites."""
from __future__ import annotations
# Force 24-bit color BEFORE importing Textual: SSH sessions usually do not carry
# COLORTERM, so Textual would auto-downgrade to xterm-256 and the muted background
# palette (e.g. the teal night hills #507070/#406060) all round to the same gray
# cube-color #5f5f5f -- flattening the ground into a featureless gray block. Modern
# terminals (Termux, etc.) support truecolor; advertise it unless the user set otherwise.
import os as _os
import random
if not _os.environ.get("COLORTERM"):
    _os.environ["COLORTERM"] = "truecolor"
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

from . import data
from . import anim
from . import egg as egg_mod
from . import training
from . import battlescreen
from . import dnascreen
from . import transportscreen
from . import adventurescreen
from . import shopscreen
from . import habitatscreen
from . import assistscreen
from . import feedscreen
from . import digicorescreen
from . import eggselectscreen
from . import persistence
from . import jogressscreen
from . import jogress
from . import net
from . import lobbyscreen
from . import tournament
from . import tournamentscreen
from . import titlescreen
from . import themescreen
from . import deathscreen
from . import sound
from . import update as update_check
from . import cloudsync
from .pet import Pet, POOP_MAX_PILES
from .render import render_screen
from . import grid
import os

from . import theme
from .theme import LCD_ON, LCD_BG, PHASE_PALETTE, SIL_DAY, SIL_NIGHT
SCREEN_COLS, SCREEN_ROWS = 40, 12
SPRITE_W = 16                                   # native creature sprite width
PET_BASE_X = (SCREEN_COLS - SPRITE_W) // 2      # the fx painter's centred-pet origin


class _FxCtx:
    """Mutable per-frame paint context shared by the _fxk_* painters."""
    __slots__ = ("rows", "overlay", "xshift", "yshift", "bg", "bgimg", "px_h")

import re as _re
# navigation keys: pressing one in a sub-screen plays the scroll blip (unless the
# screen sets its own sfx) — every list cursor-move beeps, V-Pet style
_NAV_KEYS = frozenset({"up", "down", "left", "right", "j", "k", "h", "l", "tab"})

HUD_W = 40              # message-box content width (CSS #msg: 44 - 2 border - 2 padding)
HUD_GAP = "      "      # blank run between marquee wraps so the looped text reads cleanly
HUD_STEP = 2            # advance the marquee every N frames (10 Hz clock -> ~0.2 s/char)
HUD_HOLD = 8            # marquee steps to hold on the message head before scrolling (~1.6 s)
_HUD_MARKUP = _re.compile(r"\[/?[^\]]*\]")
def _hud_plain(t):
    """Visible text of a Rich-markup string (tags stripped) for width measurement."""
    return _HUD_MARKUP.sub("", t)
def _hud_esc(t):
    """Escape '[' so a plain marquee window is never parsed as Rich markup."""
    return t.replace("[", "\\[")


def hearts(n, total=4, color=None):
    color = color or theme.HEART
    return f"[{color}]" + "●" * n + "[/][dim]" + "○" * (total - n) + "[/dim]"


def bar(v, width=12, color=None):
    color = color or theme.LIFE
    fill = max(0, min(width, round(v / 100 * width)))   # clamp: never overrun the track
    return f"[{color}]" + "█" * fill + "[/][dim]" + "─" * (width - fill) + "[/dim]"


_FX = data.load_effects()
GRAVESTONE = _FX.get("grave", [None])[0]      # real DVPet death.png

# The filth block is ONE CREATURE CELL: 8x8 slots in a 2x2 grid, so the max 4
# piles span exactly 16x16 -- the same footprint as a 16x16 creature, filling
# the band (y6..22) with no clamp.  (DVPet's raw 30x27+pad slots would scale to
# a 22x18 block -- wider than a cell, taller than the band, and with 3-4 piles
# it left no room for the pet to stand clear inside the 32 grid.  Joel's rule:
# 4 poops == 16x16, and the mon NEVER walks over them.)  The extracted pile
# sizes 1-3 (7x7 / 8x7 / 8x8 -- all _poop_size produces) fit the slot natively.
POOP_W = 8
POOP_PAD = 0

WEATHER_GLYPH = {
    "Clear": "", "Cloudy": chr(0x2601), "Drizzling": chr(0x2602),
    "Raining": chr(0x2602), "HeavyRain": chr(0x2614),
    "LightSnow": chr(0x2744), "Snowing": chr(0x2744), "HeavySnow": chr(0x2744),
}
def _sky_icon(pet):
    """One time+weather glyph for the status line: a sun only in clear daytime, a
    moon in clear night, otherwise the cloud/rain/snow symbol -- never a sun behind
    rain.  Returns (glyph, colour)."""
    if pet.weather == "Clear":
        return (chr(0x2600), theme.COIN) if pet.is_daytime else (chr(0x263E), "blue")
    g = WEATHER_GLYPH.get(pet.weather) or chr(0x2601)
    col = "cyan" if pet.weather in _SNOW else ("blue" if pet.weather in _RAIN else "white")
    return g, col


_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}
_PRECIP_N = {"Drizzling": 5, "LightSnow": 6, "Raining": 11, "Snowing": 10,
             "HeavyRain": 18, "HeavySnow": 16}
_K = "b cyan"
KEYS = (
    f"[{_K}]f[/] feed  [{_K}]p[/] play  [{_K}]c[/] clean  [{_K}]h[/] heal  [{_K}]r[/] praise  [{_K}]k[/] scold  [{_K}]s[/] lights  [{_K}]v[/] assist\n"
    f"[{_K}]t[/] train  [{_K}]b[/] battle  [{_K}]a[/] adventure  [{_K}]u[/] cup  [{_K}]j[/] jogress  [{_K}]l[/] lobby  [{_K}]x[/] DNA\n"
    f"[{_K}]o[/] shop  [{_K}]i[/] bag  [{_K}]e[/] habitat  [{_K}]d[/] data  [{_K}]g[/] theme  [{_K}]m[/] sound  [{_K}]n[/] new  [{_K}]q[/] quit"
)


def _sound_path():
    return os.path.join(persistence.SAVE_DIR, "sound.txt")


def _load_sound():
    try:
        return open(_sound_path()).read().strip() != "off"
    except OSError:
        return True


def _save_sound(on):
    try:
        os.makedirs(persistence.SAVE_DIR, exist_ok=True)
        with open(_sound_path(), "w") as fh:
            fh.write("on" if on else "off")
    except OSError:
        pass


def _scale_hex(hexcol, f):
    h = hexcol.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    cl = lambda v: max(0, min(255, int(v * f)))
    return "#%02x%02x%02x" % (cl(r), cl(g), cl(b))


def _weather_overlay(weather, frame_i, cols, px_h):
    # no cloud sprites -- the backgrounds carry the cloudy/overcast look; this
    # overlay only adds falling rain/snow particles.
    pts = []
    n = _PRECIP_N.get(weather, 0)
    if n:
        snow = weather in _SNOW
        heavy = weather in ("HeavyRain", "HeavySnow")
        for i in range(n):
            # scatter each particle to a pseudo-random spot (Knuth multiplicative
            # hash) instead of a linear comb, so they fill the whole sky -- random
            # columns and heights, landing near the bottom as readily as the top
            seed = (i * 2654435761) & 0xFFFFFFFF
            x0 = seed % cols
            base = (seed >> 10) % px_h
            if snow:
                # gentle drift with parallax -- ~1/3 of the flakes fall at half
                # speed so the snow has depth instead of a rigid descending grid;
                # each flake sways on its own phase
                far = i % 3 == 0
                y = (base + ((frame_i + 1) // 2 if far else frame_i)) % px_h
                x = (x0 + (-1, 0, 1, 0)[(frame_i // 2 + i) % 4]) % cols
                pts.append((x, y))
            else:
                # a straight vertical streak falling straight down; it tiles its
                # own length each frame for a smooth descent (no sky wrap), and
                # heavier rain draws a longer streak
                length = 3 if heavy else 2
                y = (base + frame_i * length) % px_h
                for d in range(length):
                    yy = y - d
                    if yy >= 0:                              # don't wrap a streak across the sky
                        pts.append((x0, yy))
    return pts


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _filth_right(count):
    """Right edge x of the filth block: fixed POOP_W columns like DVPet's 30px slots."""
    n = min(count or 0, POOP_MAX_PILES)
    if n <= 0:
        return grid.X0
    return grid.X0 + ((n + 1) // 2 - 1) * (POOP_W + POOP_PAD) + POOP_W


def _filth_pts(pet, tick, count=None, sizes=None, push=0, px_h=None):
    """DVPet drawFilthLevel + animFilth: per-pile SIZED sprites (the real filth.png
    sizes 1-4, two anim frames each, from pet.poop_sizes) laid in fixed 2-high
    columns stepping right from the grid's left edge; the frame swaps every
    7 ticks awake / 10 asleep."""
    E = data.load_effects()
    n = min((pet.poop if count is None else count) or 0, POOP_MAX_PILES)
    if n <= 0:
        return []
    if px_h is None:
        px_h = SCREEN_ROWS * 2
    sz = list(pet.poop_sizes if sizes is None else (sizes or []))
    fi = (tick // (10 if getattr(pet, "asleep", False) else 7)) % 2
    pts = []
    for i in range(n):
        s = max(1, min(4, sz[i] if i < len(sz) else 2))
        frames = E.get("poop_s%d" % s) or E.get("poop") or []
        if not frames:
            continue
        pm = frames[fi % len(frames)]
        if len(pm[0]) > POOP_W:                     # safety: only the unused size-4 art exceeds the slot
            pm = grid.fit_w(pm, POOP_W)
        if len(pm) > POOP_W:
            pm = grid.fit_band(pm, (POOP_W + 2) * 2)
        ph_ = len(pm)
        col, up = i // 2, i % 2
        x = grid.X0 + col * (POOP_W + POOP_PAD) - push
        if up:      # top slot sits on the 8-tall bottom slot -> the 2x2 block tops out at the band (y6)
            y = px_h - 2 - POOP_W - ph_
        else:       # bottom slot grounds 2px above the border
            y = px_h - 2 - ph_
        pts += _blit(pm, x, y)
    return pts


COND_W = COND_H = 7                                # state.png cell size (DVPet 7x7 cells)
PLAY_HOP = 14                                      # DVPet jumping(): 6 up + 6 down + rest per hop
PLAY_HOP_H = 6                                     # apex height in px (LCD is 24px tall)
# DVPet gifting(): amble off LEFT until half off-screen (firstGoal -20/104), amble
# back RIGHT to just past centre (secondGoal 39/104 ~ x15/40), gift pops in beside
# the pet (it rides hidden until arrival in DVPet too), pose 5 hold -> giftEnd.
# 3 logical px per 2-interval beat scales to ~1px/beat here (same ~4s legs).
GIFT_OUT = 40                                      # beats*2 ticks: centre x12 -> x-8 (20px)
GIFT_BACK = 46                                     # x-8 -> x15 (23px)
GIFT_HOLD = 18                                     # the % (interval*45) settle before giftEnd
COND_PITCH = COND_H + 1
# Status sprites disabled for now (Joel): the post-cure medicine badge and the
# misbehave/discipline "light bulb". Cosmetic-only; remove from this set to re-enable.
_HIDDEN_STATUS_ICONS = {"st_medicine", "st_teach"}
# DVPet draws the condition icons as a fixed VERTICAL COLUMN down the right edge of
# the LCD (setLocX ~120), one fixed row each, every active one shown AT ONCE -- not a
# single cycling slot.  Vertical order is DVPet's setLocY (top->bottom): sick(55),
# medicine(64), injury(73), bandage(83), vitamin(93), fatigue(103).  teach is NOT in
# the column -- DVPet gives it setDynamicComponentLocation, so it tracks the creature.


def _effect_overlay(pet, frame_i, cols, px_h, tick=0, pet_right=None):
    """Status sprites overlaid on the LCD, laid out like the DM20 hardware: poop
    bottom-left, the sleep Zzz top-right, a fixed condition column down the right
    edge (all active conditions at once), and a creature-tracking emote/'!'/teach
    bubble -- each in its own zone so nothing overlaps."""
    E = data.load_effects()
    pts = []
    if pet.dead:
        return pts
    if pet.poop:                                          # sized piles in the DVPet slot grid
        pts += _filth_pts(pet, tick, px_h=px_h)
    if pet.num == -1:
        return pts
    asleep = bool(getattr(pet, "asleep", False))
    # --- sleep Zzz (DVPet idleSleep, frame swap on the 10-tick sleep beat) ---
    # lights ON: the Zzz is the EMOTION label -- it rides the pet's right edge
    # (o = _emotionLabel; adjustEmotionLabel = char right edge + 3).
    # lights OFF: the Zzz is punched out of sleepLightsOff.png at (77..100, 12..29)
    # of 104x60 -> upper-right, a step below the border on our 40x24 grid.
    zz_bot = 0
    if asleep and E.get("zzz"):
        z = E["zzz"][(tick // 10) % len(E["zzz"])]
        zw, zh = len(z[0]), len(z)
        if pet.lights:
            pr = pet_right if pet_right is not None else (cols - 16) // 2 + 16
            pts += _blit(z, max(grid.X0, min(pr + 1, grid.X1 - zw)), 1)
        else:
            pts += _blit(z, grid.X1 - zw, 4)
            zz_bot = 4 + zh
    # --- condition column: fixed right edge, every active condition stacked + blinking ---
    # DVPet stateNumTic blink: 7 ticks awake / 10 asleep, faster (7) when unwell.
    unwell = pet.sick or pet.is_injured() or pet.is_fatigued()
    sf = (tick // (7 if unwell else (10 if asleep else 7))) % 2
    col_x = grid.X1 - COND_W                               # condition column hugs the grid's right edge (x29)
    col_y0 = (zz_bot + 1) if zz_bot else 0                 # below the lights-off Zzz when it holds the corner
    column = (("st_sick", pet.sick), ("st_medicine", pet.has_medicine()),
              ("st_injury", pet.is_injured()), ("st_bandage", pet.has_bandage()),
              ("st_vitamin", pet.has_vitamin()), ("st_fatigue", pet.is_fatigued()))
    k = 0
    col_active = False
    for key, active in column:
        if not active or not E.get(key) or key in _HIDDEN_STATUS_ICONS:
            continue
        col_active = True
        y = col_y0 + k * COND_PITCH
        if y + COND_H > px_h:                             # out of vertical room (rare: 3+ at once)
            break
        pts += _blit(E[key][sf], col_x, y)
        k += 1
    # --- creature-tracking bubble: emote / care-call '!' / teach (awake only) ---
    # DVPet's emotionLabel + teachState both ride the creature (adjustEmotionLabel /
    # setDynamicComponentLocation); reactions don't fire while it sleeps, so this slot
    # is awake-only and is clamped to stay left of the condition column.
    if not asleep:
        emo = ("happy" if pet.anim == "happy" else
               "unhappy" if pet.anim in ("sad", "refuse", "angry", "tantrum") else None)
        bubble = []
        if emo and E.get(emo):                            # cheer -> happy, jeer -> unhappy (DVPet)
            bubble.append(E[emo][frame_i % len(E[emo])])
        elif (pet.anim in ("idle", "walk") and E.get("attention")
              and pet.needs_attention()):
            # design call (polish 2026-07): the '!' bubble and the HUD alarm now
            # share ONE predicate -- a sick or misbehaving pet flags on-LCD too
            bubble.append(E["attention"][0])             # care-call '!'
        teach = ((getattr(pet, "praise_flag", False) or getattr(pet, "scold_flag", False))
                 and pet.lights)
        if teach and E.get("st_teach") and "st_teach" not in _HIDDEN_STATUS_ICONS:
            bubble.append(E["st_teach"][sf])
        if bubble:
            bm = bubble[(tick // 5) % len(bubble)]        # if both present, take turns (rare)
            w = len(bm[0])
            pr = pet_right if pet_right is not None else grid.X1 - 1
            right_limit = (col_x - 1 - w) if col_active else (grid.X1 - w)
            x = max(grid.X0, min(pr + 1, right_limit))
            pts += _blit(bm, x, 1)
    return pts


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0      # interval counter (10 Hz; 1 tick == 0.1s == one DVPet _interval)
        self.anim_key = None  # last anim state, so cadences restart on a state change
        self.roamer = anim.Roamer(int(SCREEN_COLS * 0.28), SCREEN_COLS, SPRITE_W)  # left-of-centre anchor
        self.fx = None        # active care-action animation
        self._idle_expr = None    # DVPet stepFrame mood-pose held for the current idle step (None = walk toggle)

    def paint(self, pet: Pet):
        if self.fx:
            return self._paint_fx(pet)
        phase = pet.day_phase
        on, bg = PHASE_PALETTE.get(phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        if not pet.lights:                 # lights off (the 's' lights button): dark room (+ Zzz if asleep)
            bgimg, bg, on = None, "#000000", SIL_NIGHT   # DVPet lightsOff.png is pure (0,0,0)
        elif bgimg:
            on = SIL_DAY   # dark silhouette day OR night -- the pet is never white;
            #                white (SIL_NIGHT) is reserved for the lights-out Zzz below
        else:
            w = pet.weather
            if w in _RAIN:
                bg = _scale_hex(bg, 0.78)
            elif w in _SNOW:
                bg = _scale_hex(bg, 0.85)
            elif w == "Cloudy":
                bg = _scale_hex(bg, 0.9)
        wf = self.frame_i // 4                  # weather/effect overlays keep their ~0.4s cadence
        if pet.dead:                           # a grave marker (the live path builds its own overlay below)
            overlay = (_weather_overlay(pet.weather, wf, SCREEN_COLS, SCREEN_ROWS * 2)
                       + _effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i))
            self.update(render_screen(GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg, overlay=overlay, bgimg=bgimg))
            return
        if pet.num == -1:                      # egg
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            _, by_num = data.load_sprites()
            rec = by_num[pet.num]
            roles = data.ROLES
        _fr = rec["frames"]
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        frames = roles.get(pet.anim, [0])
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
            xshift = dx
        elif pet.anim in ("idle", "walk") and pet.num != -1:
            # full-width roam (DVPet idleWalk); pose follows the roamer's step, and a
            # filth pile is a left wall it turns at (filthLabel walk bound).  On some
            # steps DVPet's stepFrame shows a mood pose instead of the walk toggle.
            expr = self._idle_expr if pet.anim == "idle" else None
            idx = expr if expr is not None else frames[self.roamer.pose % len(frames)]
            rows = (_fr[idx] if idx < len(_fr) else None) or first
            xshift, mirror = self.roamer.xshift, self.roamer.mirror
        else:
            mirror = pet.anim in data.MIRROR_ROLES and (self.frame_i // 6) % 2 == 1
        if pet.num == -1 and pet.hatching:
            # DVPet hatch() (SpriteAnim 11556), driven by elapsed hatch time (1 interval==0.1s):
            # the egg rocks (moveRight/Left 3) over intervals 4..15, then CRACKS -- drawNum(1)
            # at interval 16, drawNum(2) at interval 19 -- revealing the baby before the Fresh.
            n = int((3.0 - getattr(pet, "_hatch_t", 3.0)) / 0.1)
            pos = 0
            for k in range(4, min(n, 15) + 1):             # +3,+3 then -3,-3, repeating
                pos += 3 if ((k - 4) // 2) % 2 == 0 else -3
            xshift = pos
            fi = 0 if n < 16 else (1 if n < 19 else 2)      # egg -> crack -> baby emerging
            rows = (_fr[fi] if fi < len(_fr) and _fr[fi] else first)
            mirror = False
        # NOTE: DVPet's frozen.png (the ice encasement) is its GAME-PAUSED indicator
        # (setFrozenIcon only fires when !isPlaying), not a cold-weather state -- so cold
        # shows the huddle pose above, not a full ice block over the pet.
        if pet.poop:                       # keep the pet clear of the filth row in EVERY state
            poop_edge = _filth_right(pet.poop)            # x just past the rightmost pile slot (sleep/sick
            #                                               bypass the roamer bound and would
            base = PET_BASE_X
            lo = poop_edge - base                         # min shift to clear the piles (REAL edge, not padded)
            cap = (grid.X1 - SPRITE_W) - base             # stay inside the grid's right edge
            xshift = min(max(xshift, lo), max(cap, 0))    # clear poop on the left; emote follows the pet
        # DVPet adjustEmotionLabel: emote/'!' track the pet's final x, so rebuild the overlay now
        overlay = (_weather_overlay(pet.weather, wf, SCREEN_COLS, SCREEN_ROWS * 2)
                   + _effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i,
                                     pet_right=PET_BASE_X + xshift + SPRITE_W))
        if not pet.lights:                 # lights off: DVPet's lightsOff is a fully-opaque black
            rows, xshift, mirror = [], 0, False   # cover -> the pet is hidden; only black (+ Zzz) shows
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, overlay=overlay, bgimg=bgimg))

    def _background(self, pet):
        return pet.background()

    def advance(self, pet=None):
        if pet is not None and pet.anim != self.anim_key:
            self.anim_key = pet.anim            # new state -> restart its cadence at beat 0
            self.frame_i = -1
        self.frame_i += 1
        if pet is not None and pet.anim in ("idle", "walk") and pet.num != -1 and not pet.sick:
            poop_right = _filth_right(pet.poop) if pet.poop else grid.X0
            cond = (pet.is_injured() or pet.is_fatigued() or pet.has_vitamin()
                    or pet.has_medicine() or pet.has_bandage())
            # keep the pet inside the grid: left of the condition column when it's up, else the grid's right edge
            right_bound = (grid.X1 - COND_W - SPRITE_W) if cond else (grid.X1 - SPRITE_W)
            prev_pose = self.roamer.pose
            self.roamer.step(left_bound=poop_right, right_bound=right_bound)
            if self.roamer.pose != prev_pose:                    # a fresh step landed (DVPet stepFrame):
                self._idle_expr = (anim.mood_pose(pet)           # sometimes show a mood pose instead of
                                   if random.random() < anim.IDLE_EXPR_CHANCE else None)  # the plain walk toggle
        else:
            self._idle_expr = None                               # any non-idle state clears the held expression

    # ---- care-action animations (DVPet SpriteAnim eat/clean/cheer) -----------
    def start_fx(self, kind, icon=None, poop=0, old_num=None, pet=None, starving=False):
        steps = {"eat": 35, "cheer": 31, "jeer": 31, "clean": 22, "spit": 25, "evolve": 37, "dying": 50, "dna_charge": 44, "play": 37, "heal": 24, "poop": 25,
                 "gift": GIFT_OUT + GIFT_BACK + GIFT_HOLD, "assist": 28, "inherit": 50}.get(kind, 12)
        self.fx = {"kind": kind, "step": 0, "steps": steps, "icon": icon, "poop": poop, "old_num": old_num}
        if kind == "eat":
            # DVPet eat(): each chew beat is scaled by pow(N, mod) -- a starving pet or
            # a glutton wolfs food down (mod 0.9, ends ~beat 23), a picky eater dawdles
            # (mod 1.1, ~48); food descent (beats 0/2/4/6) is NOT scaled.  Disliked
            # food -> +9 grimace.  A heavy species (baseWeight>=40) skips a chew cycle
            # (DVPet's frame jump 18->26): two bites instead of three, ends ~beat 26.
            glut = getattr(pet, "glutton", 0) if pet else 0
            mod = 0.9 if (glut > 0 or starving) else (1.1 if glut < 0 else 1.0)
            bite = 9 if (pet is not None and getattr(pet, "_last_meal_disliked", False)) else 7
            heavy = pet is not None and pet.num != -1 and pet._base_weight() >= 40
            if heavy:
                beats = [int(b ** mod) for b in (10, 14, 18, 22)]
                self.fx["chew"] = {beats[0]: 8, beats[1]: bite, beats[2]: 8, beats[3]: bite}
                fb = (beats[1], beats[3], beats[3])         # food frames 0 -> 1 -> 3 (skips 2)
                self.fx["bite_snds"] = {beats[1]: "eat", beats[3]: "lastBite"}
                self.fx["steps"] = int(26 ** mod) + 1
            else:
                beats = [int(b ** mod) for b in (10, 14, 18, 22, 26, 30)]
                self.fx["chew"] = {b: (8 if i % 2 == 0 else bite) for i, b in enumerate(beats)}
                fb = (beats[1], beats[3], beats[5])
                # DVPet eat(): _eat on the first two bites, _lastBite on the third.
                self.fx["bite_snds"] = {fb[0]: "eat", fb[1]: "eat", fb[2]: "lastBite"}
                self.fx["steps"] = int(34 ** mod) + 1
            self.fx["food_beats"] = fb
        elif kind == "spit":
            # DVPet refuse(): _refuse fires on EVERY head-shake flip (t0/6/12/18).
            # (t0 sounds key as 1 -- the drain runs after the first advance.)
            self.fx["snds"] = {1: "refuse", 6: "refuse", 12: "refuse", 18: "refuse"}
        elif kind == "cheer":
            # DVPet cheer(): its sound (praise/_happy) plays at the anim's t0 --
            # keyed here so chained cheers (wash/evolve/heal tails) sound too.
            self.fx["snds"] = {1: "happy"}
        elif kind == "jeer":
            # DVPet jeer(): the sound fires at the first UP beat (t6).
            self.fx["snds"] = {6: "angry"}
        elif kind == "heal":
            # DVPet bandage(): _useBandage on each application, _lastBandage on the
            # final one (no ripped bandage cues -- click/confirm are the substitutes).
            self.fx["snds"] = {8: "click", 13: "click", 18: "confirm"}
        elif kind == "evolve":
            # DVPet evolveAnim(): _evolve sounds at the first burst beat (t5).
            self.fx["snds"] = {5: "evolve"}
        elif kind == "inherit":
            # DVPet inheriting(): chip-shrink t11 / parent-grow t17 / parent-shrink
            # t37 all key the attackHit cue; the flight home pips inheritMove
            # (=alarm) every 4; the collide lands inheritCollide (=strongHit)
            self.fx["snds"] = {10: "attackHit", 14: "attackHit", 32: "attackHit",
                               36: "alarm", 40: "alarm", 44: "alarm", 46: "strongHit"}
        elif kind == "dna_charge":
            # dnaCharge(): _dnaWash as the sweep enters (t21).
            self.fx["snds"] = {21: "wash"}

    def advance_fx(self):
        if not self.fx:
            return False
        self.frame_i += 1        # weather/filth keep animating through an fx (audit 2026-07)
        self.fx["step"] += 1
        if self.fx["step"] < self.fx["steps"]:
            return True
        kind = self.fx["kind"]
        had_filth = self.fx.get("poop", 0) > 0
        self.fx = None
        if kind == "clean" and had_filth:
            # DVPet clean(): the cheer chains ONLY when filth was actually washed
            # (an empty-room wash just ends -- no celebration).
            self.start_fx("cheer")
        elif kind == "evolve":
            # DVPet evolFinish(true): every evolution ends in cheer(true, _happy).
            self.start_fx("cheer")
        elif kind == "heal":
            # DVPet bandage() beat 23 -> Cheering: treatment ends in the praise bounce.
            self.start_fx("cheer")
        elif kind == "gift":
            # ClockTic.giftEnd: the handover ends in State.Cheering.
            self.start_fx("cheer")
        elif kind == "inherit":
            # inheriting() tail: the strobe resolves into the celebration poses.
            self.start_fx("cheer")
        return self.fx is not None

    def _pose_rows(self, pet, role, phase):
        if pet.num == -1:
            rec = egg_mod.record(pet.egg_type)
            roles = egg_mod.ROLES
        else:
            _, by_num = data.load_sprites()
            rec = by_num[pet.num]
            roles = data.ROLES
        frames = roles.get(role, [0])
        first = next((f for f in rec["frames"] if f), rec["frames"][0])
        return rec["frames"][frames[phase % len(frames)]] or first

    def _pose_rows_idx(self, pet, i):
        """A single creature frame by raw sprite index (for beat-scripted fx poses)."""
        if pet.num == -1:
            rec = egg_mod.record(pet.egg_type)
        else:
            _, by_num = data.load_sprites()
            rec = by_num[pet.num]
        fr = rec["frames"]
        first = next((f for f in fr if f), fr[0])
        return (fr[i] if i < len(fr) and fr[i] else None) or first

    def _food_frames(self, key, px=8):
        raw = data.load_icons().get(key)
        if not raw:
            return None
        from .render import downsample
        f = max(1, 24 // px)
        return [downsample(fr, f) for fr in raw]           # 24px source -> ~px tall on the LCD

    def _fx_filth(self, pet, tick, count=None):
        """DVPet checkFilth: the care anims (eat/cheer/jeer/refuse/poop) keep the
        filth piles on screen and stand the pet clear of them
        (adjustCharacterForFilth).  Returns (overlay_pts, clear_xshift)."""
        n = min((getattr(pet, "poop", 0) or 0) if count is None else count, POOP_MAX_PILES)
        if not n:
            return [], 0
        pts = _filth_pts(pet, tick, count=n)
        base = PET_BASE_X
        cap = max(0, grid.X1 - SPRITE_W - base)             # stay inside the grid's right edge
        return pts, min(max(0, _filth_right(n) - base), cap)

    def _paint_fx(self, pet):
        """The care-fx painter, decomposed (audit 2026-07): a shared context is
        pre-loaded (default pose, weather overlay, the cross-kind FILTH prelude),
        then the kind's own painter (_fxk_<kind>) mutates it.  Bodies verbatim
        from the old 210-line chain; behavior pinned by the fx golden."""
        fx = self.fx
        on, bg = PHASE_PALETTE.get(pet.day_phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        if bgimg:
            on = SIL_NIGHT if pet.day_phase == "night" else SIL_DAY
        step = fx["step"]
        # an Assistant_Lights visit is the one anim that CAUSES the darkness: the
        # room stays lit until the helper reaches the switch (DVPet toggles at the
        # anim's final beat), then the dark-room rule below takes over
        lit_visit = fx["kind"] == "assist" and fx.get("act") == "lights" and step < 18
        if not pet.lights and fx["kind"] != "evolve" and not lit_visit:
            # design call (polish 2026-07): the dark room stays dark through a
            # care fx -- lights-off is room STATE (DVPet's lightsOff roomEffect),
            # not a backdrop an anim may replace; evolve owns its own darkness
            bgimg, bg, on = None, "#000000", SIL_NIGHT
        c = _FxCtx()
        c.px_h = SCREEN_ROWS * 2
        c.bg, c.bgimg = bg, bgimg
        # only clean/dying rely on this default pose; the kind painters override
        # `rows` unconditionally otherwise
        pose = {"clean": "idle", "dying": "exhausted"}.get(fx["kind"], "idle")
        c.rows = self._pose_rows(pet, pose, step // 2)
        c.overlay = _weather_overlay(pet.weather, self.frame_i // 4, SCREEN_COLS, c.px_h)   # paint()'s 0.4s cadence
        c.xshift = 0
        c.yshift = 0
        if fx["kind"] in ("eat", "cheer", "jeer", "spit"):
            # DVPet checkFilth runs inside these anims: piles stay visible and the
            # pet (and its food) stands clear of them.
            filth_pts, filth_clear = self._fx_filth(pet, self.frame_i)
            c.overlay += filth_pts
            c.xshift = filth_clear
        elif fx["kind"] == "poop":
            # DVPet poop(): squat (+4, MIRRORED) clear of the old piles, net-zero
            # sway every 3 ticks; the new pile lands at t18 with the size-keyed
            # sound (fx snds) and the relieved pose (+5); ends 24.
            new = fx["step"] >= 18
            filth_pts, filth_clear = self._fx_filth(pet, self.frame_i,
                                                    count=fx.get("poop", 0) + (1 if new else 0))
            c.overlay += filth_pts
            sway = -1 if (3 <= step < 18 and (step // 3) % 2 == 1) else 0
            c.xshift = filth_clear + sway
            c.rows = self._pose_rows_idx(pet, 5 if new else 4)
        painter = getattr(self, "_fxk_" + fx["kind"], None)
        if painter is not None:
            painter(pet, fx, step, c)
        mirror = (fx["kind"] in ("dying", "poop")
                  or (fx["kind"] == "gift" and GIFT_OUT <= step < GIFT_OUT + GIFT_BACK)  # facing right, ambling back
                  or (fx["kind"] == "spit" and (step // 6) % 2 == 0))   # refuse(): head-shake flips
        self.update(render_screen(c.rows, SCREEN_COLS, SCREEN_ROWS, on, c.bg,
                                  xshift=c.xshift, yshift=c.yshift, overlay=c.overlay,
                                  bgimg=c.bgimg, mirror=mirror))

    def _fxk_eat(self, pet, fx, step, c):
        # DVPet eat(): 24px food descends in 4 stages (beats 0/2/4/6) toward the
        # mouth, then a chew triad alternates open-mouth(+8)/chew(+7) at beats
        # 10/14/18/22/26/30 while the food is consumed frame-by-frame; ends ~34.
        if c.xshift == 0:
            c.xshift = -1                                  # no filth: DVPet char x29 of 104 (~28%)
        chew = fx.get("chew") or {10: 8, 14: 7, 18: 8, 22: 7, 26: 8, 30: 7}
        pose_i = 0
        for b in sorted(chew):
            if step >= b:
                pose_i = chew[b]
        c.rows = self._pose_rows_idx(pet, pose_i)
        food = self._food_frames(fx.get("icon") or "f:0")
        if food:
            fw = len(food[0][0]) if (food[0] and food[0][0]) else 8
            if c.xshift > 0:                               # filth on screen: DVPet pads BOTH the food and
                c.xshift += fw                             # the char right of it (foodLabel x31+pad), so the
            #                                                food descends beside the piles, never onto them
            # DVPet: the food's RIGHT edge meets the pet's LEFT edge (foodLabel x31+24 == char x55),
            # so it descends right into the mouth -- abut it instead of stranding it on the far left.
            fx_x = max(0, PET_BASE_X + c.xshift - fw)
            stage = 0 if step < 2 else 1 if step < 4 else 2 if step < 6 else 3
            fy = (0, 4, 9, 13)[stage]                      # DVPet descent y 0/11/22/33 of 60 -> *(24/60)
            fb = fx.get("food_beats") or (14, 22, 30)
            fi = 0 if step < fb[0] else 1 if step < fb[1] else 2 if step < fb[2] else 3
            c.overlay += _blit(food[min(fi, len(food) - 1)], fx_x, fy)

    def _fxk_clean(self, pet, fx, step, c):
        # DVPet clean(): the wash enters from the right and, once it reaches the pet,
        # shoves the pet AND the filth left together until they slide off-screen (pet
        # in its clean pose, frame 4); the chained cheer then brings the pet back.
        E = data.load_effects()
        wash = E.get("wash", [None])[0]
        wx = SCREEN_COLS - step * 3                        # wash front: enters right, exits left
        base = PET_BASE_X
        clear = (_filth_right(fx.get("poop", 0)) - base) if fx.get("poop") else 0
        push = max(0, base + clear + SPRITE_W - wx)        # wash shove, measured from the pet's RIGHT edge
        c.xshift = clear - push                            # pet starts cleared of the filth, then both
        if push > 0:                                       # slide left in lockstep (gap preserved, no mash)
            c.rows = self._pose_rows_idx(pet, 4)           # DVPet drawNum(4) while being washed
        if fx.get("poop"):                                 # the sized piles slide off with the pet
            c.overlay += _filth_pts(pet, self.frame_i, count=fx["poop"],
                                    sizes=fx.get("sizes"), push=push, px_h=c.px_h)
        if wash:
            c.overlay += _blit(wash, wx, max(0, (c.px_h - len(wash)) // 2))

    def _fxk_assist(self, pet, fx, step, c):
        # DVPet assistantClean/assistantFeed/assistantLights: the hired helper
        # descends from the top on the LEFT (locX 6, icon flipped to face the
        # pet), does its round, and rises away (moveUp beats 18/19).  Mapped to
        # 28 steps: descend 0-7, act 8-19 (with the wiggle), leave 20+.  During
        # a clean the piles sweep RIGHT off-screen (filthLabel.moveRight(4) each
        # descent beat) -- the OPPOSITE of your wash, which shoves them left.
        act = fx.get("act")
        # the pet gives ground as the helper arrives (DVPet assistantLights
        # moveRight(2) per descent beat) and drifts back as it leaves --
        # 4+16 | 20+16 fills the grid band x[4,36) with both sprites abutted
        if step < 8:
            c.xshift = min(8, step * 2)
        elif step < 20:
            c.xshift = 8
        else:
            c.xshift = max(0, 8 - (step - 19) * 2)
        if act in ("feed", "strength") and 8 <= step < 20:
            # Assistant_Feed shares eatAnim: open-mouth(+8)/chew(+7) alternation
            c.rows = self._pose_rows_idx(pet, 8 if (step // 3) % 2 == 0 else 7)
        elif pet.asleep:
            c.rows = self._pose_rows(pet, "sleep", step // 2)
        if act == "clean" and fx.get("poop"):
            c.overlay += _filth_pts(pet, self.frame_i, count=fx["poop"],
                                    sizes=fx.get("sizes"), push=-step * 3, px_h=c.px_h)
        if act in ("feed", "strength") and step >= 4:
            food = self._food_frames(fx.get("icon") or "f:44")
            if food:
                fw = len(food[0][0]) if (food[0] and food[0][0]) else 8
                fb = fx.get("food_beats") or (12, 16, 20)
                fi = 0 if step < fb[0] else 1 if step < fb[1] else 2 if step < fb[2] else 3
                fr_ = food[min(fi, len(food) - 1)]
                if fr_:                                    # a consumed-away frame may be empty
                    # handed straight to the mouth -- no descent; it appears held out
                    c.overlay += _blit(fr_, max(0, PET_BASE_X + c.xshift - fw),
                                       c.px_h - 2 - 8 - 4)
        _, by_num = data.load_sprites()
        rec = by_num.get(fx.get("helper", -1))
        fr = rec["frames"] if rec else None
        hf = (fr[0] if fr and fr[0] else next((f for f in fr if f), None)) if fr else None
        if hf:
            hf = [row[::-1] for row in hf]                 # flipped to face the pet
            hh = len(hf)
            ground = c.px_h - hh - 2
            if step < 8:
                hy = -hh + (step + 1) * (ground + hh) // 8   # moveDown beats
            elif step < 20:
                hy = ground
            else:
                hy = ground - (step - 19) * 6              # moveUp(24) x2: off the top
            hx = 4 + (0 if not (16 <= step < 20) else (-1 if step % 2 == 0 else 1))   # the wiggle
            if hy > -hh:
                c.overlay += _blit(hf, hx, hy)

    def _fxk_cheer(self, pet, fx, step, c):
        # DVPet cheer(): pose alternates up(+5)/down(+7) every 6 intervals with a
        # "happy" emote bubble pulsing on the up-beats; ends ~beat 30.
        up = (step // 6) % 2 == 0
        c.rows = self._pose_rows_idx(pet, 5 if up else 7)
        if up:
            hap = data.load_effects().get("happy")
            if hap:
                hf = hap[(step // 6) % len(hap)]
                # DVPet cheer(): the pet stays CENTRED and the emote rides its right
                # edge (adjustEmotionLabel) -- not pinned to the far corner.
                c.overlay += _blit(hf, PET_BASE_X + c.xshift + SPRITE_W, 1)

    def _fxk_gift(self, pet, fx, step, c):
        # DVPet gifting(): walk-toggle poses (spriteNum/spriteNum+1) per beat;
        # facing follows the leg (drawNumMirror false left / true right).  The
        # present is only revealed on arrival, beside the pet (locX gap 4/104
        # ~ 1px), vertically centred -- then pose 5 faces it for the hold.
        base = PET_BASE_X
        if step < GIFT_OUT:
            c.xshift = -(step // 2)                        # off to fetch it
            c.rows = self._pose_rows(pet, "walk", step // 2)
        elif step < GIFT_OUT + GIFT_BACK:
            c.xshift = -(GIFT_OUT // 2) + (step - GIFT_OUT) // 2   # ambling back
            c.rows = self._pose_rows(pet, "walk", step // 2)
        else:
            c.xshift = -(GIFT_OUT // 2) + (GIFT_BACK - 1) // 2   # exactly where the walk ended
            c.rows = self._pose_rows_idx(pet, 5)           # ta-dah beside the present
            gf = self._food_frames(fx.get("icon") or "f:0")
            if gf:
                g0 = gf[0]
                gw = max((len(r) for r in g0), default=8)
                gh = len(g0)
                gx = base + c.xshift - gw - 1
                c.overlay += _blit(g0, gx, (c.px_h - gh) // 2)

    def _fxk_play(self, pet, fx, step, c):
        # DVPet jumping() (SpriteAnim 17308): the pet bounces with joy -- hops UP on
        # the excited pose (5) and lands on the neutral pose (1), a happy chirp at the
        # top of each hop.  Distinct from cheer (which bounces in place on 5/7 with an
        # emote bubble) -- here the body actually leaves the ground.
        ph = step % PLAY_HOP
        up = ph < PLAY_HOP // 2
        c.rows = self._pose_rows_idx(pet, 5 if up else 1)
        c.yshift = int(PLAY_HOP_H * (1 - abs(ph / (PLAY_HOP / 2) - 1)))   # triangle: 0 -> apex -> 0

    def _fxk_jeer(self, pet, fx, step, c):
        # DVPet jeer(goodScold): the SCOLD reaction -- pose alternates down(+4)/up(+6)
        # every 6 intervals, leading DOWN, with the "unhappy" emote riding the pet;
        # ends ~beat 30.  (Poses 9/10 belong to badHealthJeer, the dying variant.)
        down = (step // 6) % 2 == 0
        c.rows = self._pose_rows_idx(pet, 4 if down else 6)
        un = data.load_effects().get("unhappy")
        if un:
            uf = un[(step // 6) % len(un)]
            # DVPet jeer(): centred pet, emote at its right edge (not the corner).
            c.overlay += _blit(uf, PET_BASE_X + c.xshift + SPRITE_W, 1)

    def _fxk_spit(self, pet, fx, step, c):
        # DVPet refuse(): pose 4 (9 while Depressed) held the whole beat while the
        # head SHAKES via mirror flips T/F/T/F at 0/6/12/18 (_refuse on each flip,
        # wired in start_fx); ends at 24.  No food drops -- the meal never appears.
        sprite = 9 if pet.current_mood() == "Depressed" else 4
        c.rows = self._pose_rows_idx(pet, sprite)

    def _fxk_evolve(self, pet, fx, step, c):
        # DVPet evolveAnim(): the room plunges DARK (lightsOff, fully opaque -- the
        # pet vanishes) and the bright "evol" burst strobes over it at beats
        # 5/12/19/25/29/34 (each icon holds until the next beat); changeSprite()
        # swaps in the evolved form at beat 21 UNDER darkness, so it emerges on the
        # next burst.  _evolve sounds at the first burst (start_fx snds).  The
        # chained cheer(true) afterwards is DVPet evolFinish.
        old = fx.get("old_num")
        if step < 21 and old not in (None, -1):            # old form until the covered swap
            rec = data.load_sprites()[1].get(old)
            if rec and rec["frames"][0]:
                c.rows = rec["frames"][0]
        burst = any(a <= step < b for a, b in
                    ((5, 10), (12, 14), (19, 21), (25, 27), (29, 32), (34, 99)))
        if burst:
            # "evol" burst: the room shows through DVPet's 50% dither mask --
            # tile the extracted checkerboard over the whole LCD in ink.
            ev = (data.load_effects().get("evol") or [None])[0]
            if ev:
                mh, mw = len(ev), len(ev[0])
                c.overlay += [(x, y) for y in range(c.px_h) for x in range(SCREEN_COLS)
                              if ev[y % mh][x % mw] == "1"]
        else:                                              # lightsOff beats: pure black, pet hidden
            c.rows, c.bgimg, c.bg = [], None, "#000000"

    def _fxk_inherit(self, pet, fx, step, c):
        # DVPet inheriting(): the pet stands RIGHT (locX width-3-size); the chip
        # descends on its left (t1-10), shrinks to a point (t11, chipShrink), the
        # DEPARTED ancestor rises from it (t17, parentGrow) and greets on poses
        # 6/1 (t24-33), fades (t37, parentShrink), then the chip reappears and
        # wobbles home into the pet (t42-64, inheritMove pips) and collides
        # (t65) into an evol-dither strobe.  Mapped to 50 steps; the sprite
        # scaling beats become appear/disappear (16px art does not scale).
        c.xshift = 8                                       # the pet gives the seance room
        chip = data.load_icons().get("i:32")               # raw: the 8x7 chip art is already
        cf = chip[0] if chip and chip[0] else None         # LCD-scale (_food_frames' /3 is for 24px food)
        cw = len(cf[0]) if cf and cf[0] else 8
        cx = 8
        _, by_num = data.load_sprites()
        anc = by_num.get(fx.get("ancestor", -1))
        if step < 10:                                      # the chip descends
            if cf:
                c.overlay += _blit(cf, cx, -8 + step * 2)
        elif step < 14:                                    # ...and shrinks to a point
            cy = c.px_h // 2 + 4
            c.overlay += [(cx + cw // 2 + dx, cy + dy) for dx in (0, 1) for dy in (0, 1)]
        elif step < 32 and anc:                            # the ancestor's visit
            fr = anc["frames"]
            pose = 6 if ((step - 14) // 4) % 2 == 0 else 1
            af = (fr[pose] if pose < len(fr) and fr[pose] else fr[0]) or next((f for f in fr if f), None)
            if af:
                c.overlay += _blit(af, cx - 2, c.px_h - len(af) - 2)
        elif step < 46:                                    # the chip flies home
            if cf:
                wob = -1 if (step % 4) < 2 else 1
                c.overlay += _blit(cf, cx + (step - 34) * 2, c.px_h // 2 + wob)
        else:                                              # the collide strobe
            ev = (data.load_effects().get("evol") or [None])[0]
            if ev and (step % 2 == 0):
                mh, mw = len(ev), len(ev[0])
                c.overlay += [(x, y) for y in range(c.px_h) for x in range(SCREEN_COLS)
                              if ev[y % mh][x % mw] == "1"]

    def _fxk_dna_charge(self, pet, fx, step, c):
        # DVPet dnaCharge() (SpriteAnim 12860): the FIELD badge drops in beside the
        # pet (t1-7), wobbles (9/11/13), inserts (t16), then the full-screen dnaWash
        # wave sweeps DOWN over everything (t21+, ~9px/tick of 120) while the pet
        # strains (pose 9 from the collide at t27); the badge sinks away at the tail
        # (t37+).  Pet nudged 1 right (setLocX 3+x), pose 0 until the collide.
        E = data.load_effects()
        c.rows = self._pose_rows_idx(pet, 9 if step >= 27 else 0)
        c.xshift = 1
        badge = (E.get("field_" + str(fx.get("icon") or "")) or E.get("field_None") or [None])[0]
        if badge:
            bw, bh = len(badge[0]), len(badge)
            base = PET_BASE_X + c.xshift
            bx = max(0, base - 2 - bw) + ({9: -1, 10: -1, 11: 1, 12: 1}.get(step, 0))
            rest = 8                                       # DVPet rest y21 of 60 -> ~8 of 24
            if step < 8:
                by = -bh + int((rest + bh) * step / 7)     # moveDown 6/tick descent
            else:
                by = rest + (1 if step >= 16 else 0) + max(0, step - 36)   # insert nudge + sink tail
            c.overlay += _blit(badge, bx, by)
        wash = (E.get("dna_wash") or [None])[0]
        if wash and step >= 21:
            wy = -len(wash) + (step - 21) * 4              # 9px/tick of 120 -> ~4px/tick of 48
            c.overlay += _blit(wash, max(0, (SCREEN_COLS - len(wash[0])) // 2), wy)

    def _fxk_heal(self, pet, fx, step, c):
        # DVPet bandage(): the item drops in on the pet's LEFT (x31 vs char x55,
        # like the food) and steps through its 4-frame application strip at beats
        # 0/8/13/18 while the pet holds the HURT pose (+9, being treated); ends 23
        # and chains into cheer(true).
        c.rows = self._pose_rows_idx(pet, 9)
        item = data.load_icons().get(fx.get("icon") or "i:80")
        if item:
            fi = 0 if step < 8 else 1 if step < 13 else 2 if step < 18 else 3
            bm = item[min(fi, len(item) - 1)]
            bw = len(bm[0])
            ix = max(0, PET_BASE_X - bw)
            iy = 0 if step < 4 else 4                      # setLocY 53 -> 64 at beat 4
            c.overlay += _blit(bm, ix, iy)

    def _fxk_dying(self, pet, fx, step, c):
        # DVPet dying() (SpriteAnim 13179): the collapsed pet (pose 10, mirrored)
        # sways +/-1 as the 'dying' emote (dying/dying2) swaps at its right edge,
        # BOTH on a 10-tick beat (frame % (10*interval)), just before the memorial.
        c.xshift = 1 if (step // 10) % 2 == 0 else -1
        dye = data.load_effects().get("dying")
        if dye:
            df = dye[(step // 10) % len(dye)]
            c.overlay += _blit(df, PET_BASE_X + SPRITE_W + c.xshift, 1)



def _status_line(status, deco, width=26):
    """Assemble the status word + deco glyphs, bounded to `width` visible cols
    so the Stats box never wraps past its 16-row height. Drops the lowest-priority
    deco that would overflow (rare: only when asleep+sick+poop+effect pile up)."""
    from rich.text import Text
    used = len(status) + 3                      # the status word + 3 spaces
    shown = []
    for d in deco:
        vis = len(Text.from_markup(d).plain)
        add = vis + (2 if shown else 0)         # 2-space separator between glyphs
        if used + add <= width:
            shown.append(d)
            used += add
    return f"[b]{status}[/]   " + "  ".join(shown)


class Stats(Static):
    def paint(self, pet: Pet):
        if pet.dead:
            return self._paint_grave(pet)
        if pet.num == -1 or pet.stage == "Egg":
            return self._paint_egg(pet)
        T = theme
        div = f"[dim]{'─' * 26}[/]"
        word = pet.status_word()
        deco = []
        if pet.asleep and word != "asleep": deco.append("[blue]Zzz[/]")
        if pet.sick and word != "sick": deco.append(f"[{T.NEG}]+sick[/]")
        if pet.is_fatigued() and word != "fatigued": deco.append(f"[{T.NEG}]+tired[/]")
        if pet.is_injured() and word != "injured": deco.append(f"[{T.NEG}]+hurt[/]")
        if pet.is_freezing() and word != "freezing": deco.append("[blue]+cold[/]")
        if pet.is_overheating() and word != "overheating": deco.append(f"[{T.NEG}]+hot[/]")
        if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
        if getattr(pet, "effect_id", -1) >= 0: deco.append(f"[{T.POS}]\u2726{pet.effect_name()}[/]")
        mins, secs = divmod(int(pet.age_seconds), 60)
        sky, skycol = _sky_icon(pet)
        aff = pet._affinity()
        amark = (f"[{T.POS}]" + chr(0x2665) + "[/]" if aff > 0
                 else (f"[{T.NEG}]" + chr(0x2716) + "[/]" if aff < 0 else "[dim]·[/dim]"))
        xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
        lifepct = max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100))
        lifecol = T.NEG if pet.is_geriatric else T.LIFE
        self.border_subtitle = f"gen {pet.generation}"
        lines = [
            f"[b]{pet.name[:22]}[/]{xm}",
            f"[dim]{pet.stage}{(' · ' + pet.attribute) if pet.attribute else ''}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy_pct(), 12, T.ENERGY)}",
            f"Mood    {bar(pet.mood_pct(), 12, T.MOOD)}",
            div,
            f"Power   [{T.POS}]●{pet.vaccine}[/] [{T.ENERGY}]■{pet.data_power}[/] [{T.MOOD}]▲{pet.virus}[/]",
            f"HP {pet.full_health}/{pet.max_health()}  Wt {pet.weight}g  [{T.COIN}]{pet.bits}b[/]",
            f"Battle  {pet.wins}W/{pet.battles}   [{T.COIN}]\u2605{pet.trophies}[/]",
            f"@{pet.habitat_obj()['name'][:14]} {amark} [dim]{pet.season}[/]",
            f"[{skycol}]{sky}[/] [dim]{pet.weather} {int(pet.temp)}\u00b0[/] [dim]{mins}m{secs:02d}s[/]",
            f"Life    {bar(lifepct, 12, lifecol)}",
            _status_line(word, deco),
        ]
        self.update("\n".join(lines))

    def _paint_egg(self, pet):
        mins, secs = divmod(int(pet.age_seconds), 60)
        self.border_subtitle = f"gen {pet.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            "[b]Digitama[/] [dim]· egg[/]",
            div,
            "[dim]a new life is warming[/]",
            "",
            "Destined to hatch",
            f"  [b]{egg_mod.hatch_name(pet.egg_type)}[/]",
            div,
            f"Age     {mins}m{secs:02d}s",
            "",
            "[dim]keep it cosy — it[/]",
            "[dim]hatches on its own[/]",
        ]
        self.update("\n".join(lines))

    def _paint_grave(self, pet):
        mins = int(pet.age_seconds) // 60
        self.border_subtitle = f"gen {pet.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lines = [
            f"[b]{pet.name[:16]}[/] [dim]· rest[/]",
            div,
            "[dim]a life remembered[/]",
            "",
            f"Lived    {mins}m",
            f"Reached  {pet.stage}",
            f"Attrib   {pet.attribute}",
            f"Record   {pet.wins}W / {pet.battles}",
            div,
            "[dim]gone, but not[/]",
            "[dim]forgotten.[/]",
            "",
            "[dim]press N for a new egg[/]",
        ]
        self.update("\n".join(lines))


class TuiPetApp(App):
    CSS = """
    Screen { align: center middle; }
    #wrap { width: auto; height: auto; }
    #top { width: auto; height: auto; }
    #left { width: 44; height: auto; }
    #lcd { border: thick #7a7e78; padding: 0 1; background: #c6c9cc; width: 44; height: 14; }
    #msg {
        border: round #7a7e78; padding: 0 1; width: 44; height: 3; margin-top: 1;
        color: #7d8186; content-align: left middle;
    }
    #stats { border: round #7a7e78; padding: 0 1; width: 30; height: 18; margin-left: 1; }
    #keys {
        border: round #7a7e78; padding: 0 1; width: 75; height: 5; margin-top: 1; color: #7d8186;
    }
    """
    BINDINGS = [
        ("f", "feed", "Feed"), ("t", "train", "Train"), ("b", "battle", "Battle"),
        ("p", "play", "Play"), ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("r", "praise", "Praise"), ("k", "scold", "Scold"),
        ("a", "adventure", "Adventure"), ("o", "shop", "Shop"), ("i", "inventory", "Inventory"), ("e", "habitat", "Habitat"),
        ("d", "digicore", "DigiCore"),
        ("j", "jogress", "Jogress"), ("u", "tournament", "Cup"), ("x", "dna", "DNA"),
        ("l", "lobby", "Lobby"),
        ("s", "sleep", "Lights"), ("v", "assist", "Assistant"), ("g", "theme", "Theme"), ("m", "sound", "Sound"), ("n", "new", "New pet"), ("q", "quit", "Quit"),
        ("enter", "gift", "Accept gift"),
    ]

    def __init__(self, pet: Pet | None = None):
        super().__init__()
        self._welcome = "Welcome! Raise your pet."
        self._new_game = False
        if pet is None:
            loaded, msg = persistence.load()
            if loaded is not None:
                pet, self._welcome = loaded, (msg or "Welcome back!")
            else:
                self._new_game = True
        self.pet = pet or Pet.new_egg()
        self.mode = None            # active in-display panel (no pop-up screens)
        self._dying_fx = False      # playing the death animation before the memorial
        self._mode_close = None
        self.sound = _load_sound()
        self._needs = False
        self._flash_t = 0           # ticks an action flash holds before a care-need re-asserts
        self._showing_need = False
        self._update_msg = None     # set by the background PyPI check when a newer release exists
        self._showing_update = False
        self._sync = None           # background cloud-save push client (net.SyncClient), or None
        self._hud_scroll = None     # plain text being marquee-scrolled, or None when it fits
        self._hud_off = 0           # marquee window offset
        self._hud_hold = 0          # steps left to hold on the head before scrolling
        self._hud_tick = 0          # frame counter for the marquee throttle

    def compose(self) -> ComposeResult:
        with Vertical(id="wrap"):
            with Horizontal(id="top"):
                with Vertical(id="left"):
                    yield Screen(id="lcd")
                    yield Static("Welcome! Raise your pet.", id="msg")
                yield Stats(id="stats")
            yield Static(KEYS, id="keys")

    def on_mount(self):
        self.screen_w = self.query_one("#lcd", Screen)
        self.stats_w = self.query_one("#stats", Stats)
        self.msg_w = self.query_one("#msg", Static)
        self.keys_w = self.query_one("#keys", Static)
        self.screen_w.border_title = "TUIPET"
        self.stats_w.border_title = "STATUS"
        self.keys_w.border_title = "ACTIONS"
        self.screen_w.border_subtitle = "● on"
        self._hud(self._welcome)
        theme.apply(theme.load_choice())
        self._restyle()
        self.repaint()
        self._open_mode(titlescreen.TitlePanel(), self._after_title)
        self._hud("[b]▸ PRESS ENTER ◂[/b]")
        self.set_interval(0.1, self.on_frame)    # single DVPet interval clock: 1 tick == 0.1s (main view AND sub-screens)
        self.set_interval(1.0, self.on_tick)
        self.set_interval(10.0, self.autosave)
        self.run_worker(self._check_update(), name="update", exclusive=False)
        self._start_sync()

    def _start_sync(self):
        """Spin up the background cloud-save push client once an account exists
        (idempotent). The startup pull already ran in main(); this handles pushes."""
        if self._sync is not None:
            return
        name, pw = persistence.get_account()
        if not name:
            return                       # no account yet (first launch) — started after account setup
        self._sync = net.SyncClient(_lobby_uri(), name, pw)
        self.run_worker(self._sync.run(), name="sync", exclusive=False)

    def _push_cloud(self):
        """Queue the current pet's save for upload (no-op until the account/sync exists)."""
        if self._sync is not None and self.pet is not None:
            self._sync.push_save(persistence.to_save_dict(self.pet))

    async def _check_update(self):
        """Background: ask PyPI once per launch if a newer tuipet exists, then let
        the idle HUD nudge the player (see on_tick).  Fail-soft, never blocks."""
        import asyncio
        latest = await asyncio.to_thread(update_check.latest_if_newer)
        if latest:
            self._update_msg = f"⬆ tuipet {latest} out — pip install -U tuipet"

    def _after_title(self, _=None):
        if not persistence.get_account()[0]:     # first launch: create your lobby account
            self._open_mode(lobbyscreen.AccountPanel(), self._after_account)
            return
        self._post_title()

    def _after_account(self, result):
        if result:
            persistence.set_account(*result)
        self._start_sync()              # account now exists -> begin cloud-save sync
        self._post_title()

    def _post_title(self):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet), self._after_egg_pick)
        else:
            self._hud(self._welcome)
            self.repaint()

    def _grant_digimemory(self, pet):
        """Hand the banked inheritance data to the next generation: the payload
        rides the pet's save; item 32 appears in its bag (DVPet items persist
        across resetToEgg -- tuipet's generations carry only this one)."""
        mem = persistence.take_digimemory()
        if mem:
            pet.digimemory = dict(mem)
            pet.add_item("i:32")

    def _after_death(self, result):
        if result == "new":
            self.action_new()
        else:
            self.repaint()

    def _after_egg_pick(self, egg_type):
        if egg_type is None:                       # backed out -> return to the title
            self._open_mode(titlescreen.TitlePanel(), self._after_title)
            return
        self.pet = Pet.new_egg(egg_type=egg_type)
        self._grant_digimemory(self.pet)
        self.flash("Take good care of your egg!")
        self.repaint()

    def autosave(self):
        persistence.save(self.pet)
        self._note_progress()
        self._push_cloud()              # mirror the autosave up to the cloud

    def _note_progress(self):
        """Record cross-generation egg-unlock milestones from the live pet."""
        p = self.pet
        if p is None or p.stage in ("", "Egg"):
            return
        persistence.note_generation(p.generation)
        if p.stage in data.STAGE_ORDER:
            persistence.note_stage_index(data.STAGE_ORDER.index(p.stage))
        if getattr(p, "x_antibody", "None") != "None":
            persistence.note_xanti()

    def on_unmount(self):
        persistence.save(self.pet)
        self._flush_cloud_on_quit()     # capture the final state cloud-side on any exit

    def _flush_cloud_on_quit(self):
        """Best-effort blocking push so the final state is captured cloud-side."""
        if self._sync is None:
            return
        try:
            name, pw = persistence.get_account()
            cloudsync.push_save(_lobby_uri(), name, pw,
                                persistence.to_save_dict(self.pet), timeout=2.0)
        except Exception:
            pass

    def on_key(self, event):
        fx = getattr(getattr(self, "screen_w", None), "fx", None)
        if fx is not None and fx.get("kind") == "dying":
            # dying(): the pet is a BUTTON -- frantic taps can save it
            # (numHits > HitsToSave x (savedFromDeath + 1))
            self._revive_hits = getattr(self, "_revive_hits", 0) + 1
            self.beep("click", bell=False)
            event.stop()
            event.prevent_default()
            return
        if self.mode is not None:
            event.stop()
            event.prevent_default()      # a panel owns the keyboard: don't fire global BINDINGS
            result = self.mode.key(event.key)
            snd = getattr(self.mode, "sfx", None)
            if snd:
                self.beep(snd, bell=False)
                self.mode.sfx = None
            elif getattr(self.mode, "captures_text", False):
                pass                                # typing: no nav/confirm blips (audit 2026-07)
            elif event.key in _NAV_KEYS:
                self.beep("scroll", bell=False)     # cursor-move blip for every list screen
            elif event.key == "enter":
                self.beep("confirm", bell=False)    # menu confirm (a screen's own sfx wins above)
            elif event.key == "escape":
                self.beep("cancel", bell=False)     # back/cancel
            if result is not None and result[0] == "done":
                self._close_mode(result[1])
            elif result is not None and result[0] == "quit":
                self.action_quit()                  # a screen asked to quit the app (e.g. q on the title)
            elif event.key == "q" and not getattr(self.mode, "captures_text", False):
                self.action_quit()                  # QoL: q quits from any non-text screen, not just the main view
            else:
                self.repaint()

    def _open_mode(self, panel, on_close=None):
        self.mode = panel
        self._mode_close = on_close
        # clear the message strip so a screen never shows the PREVIOUS screen's
        # farewell flash; each sub-screen carries its own note inside the LCD
        if getattr(self, "msg_w", None) is not None:
            self._hud("")
        self.repaint()

    def _close_mode(self, result):
        cb = self._mode_close
        self.mode = None
        self._mode_close = None
        if cb:
            cb(result)
        else:
            self.repaint()

    # ---- multiplayer lobby ----------------------------------------------
    def action_lobby(self):
        if self.mode is not None:
            return
        name, pw = persistence.get_account()
        self._open_mode(lobbyscreen.LobbyPanel(self.pet, self._lobby_connect,
                        name=name, pw=pw),
                        self._after_lobby)

    def _lobby_connect(self, name, pw, card):
        """Create + start the WebSocket client; the app owns its worker lifecycle."""
        persistence.set_account(name, pw)
        uri = _lobby_uri()
        client = net.LobbyClient(uri, name, pw, card)
        self._lobby_worker = self.run_worker(client.run(), name="lobby", exclusive=False)
        return client

    def _after_lobby(self, result=None):
        # The lobby panel applies its own jogress/battle results in-place (you stay
        # in the lobby between sessions), so here we just tear down the connection.
        w = getattr(self, "_lobby_worker", None)
        if w is not None:
            w.cancel()
            self._lobby_worker = None
        self.repaint()

    def action_quit(self):
        persistence.save(self.pet)
        self.exit()

    def beep(self, name=None, bell=True):
        if not self.sound:
            return
        if name and sound.play(name):
            return
        if bell:
            self.bell()

    def action_sound(self):
        self.sound = not self.sound
        _save_sound(self.sound)
        self.flash(f"Sound: {'on' if self.sound else 'off'}")
        if self.sound:
            self.bell()

    def _restyle(self):
        try:
            for w in (self.screen_w, self.stats_w, self.msg_w, self.keys_w):
                w.styles.border = ("round", theme.BORDER)
                w.styles.border_title_color = theme.MID
            self.screen_w.styles.border = ("thick", theme.BORDER)
            self.screen_w.styles.border_subtitle_color = theme.ACCENT
            self.screen_w.styles.background = theme.LCD_BG
            self.msg_w.styles.color = theme.MID
            self.keys_w.styles.color = theme.MID
        except Exception:
            pass

    def action_theme(self):
        self._open_mode(themescreen.ThemePanel(on_change=self._restyle), self._after_theme)

    def _after_theme(self, _=None):
        self._restyle()
        self.flash(f"Theme: {theme.current()}")
        self.repaint()

    def _center(self, text):
        from rich.text import Text
        n = text.plain.count("\n") + 1
        pad = max(0, (SCREEN_ROWS - n) // 2)
        if not pad:
            return text
        out = Text("\n" * pad)
        out.append_text(text)
        return out

    def repaint(self):
        if self.mode is not None:
            self.screen_w.update(self._center(self.mode.text()))
        else:
            self.screen_w.paint(self.pet)
        if isinstance(self.mode, titlescreen.TitlePanel):
            self._status_card("TUIPET", ["[dim]a terminal v-pet[/]", "", "",
                                         "[dim]a creature awaits[/]", "",
                                         "[dim]press ENTER[/]", "[dim]to begin[/]"])
        elif isinstance(self.mode, eggselectscreen.EggSelectPanel):
            m = self.mode
            idx = m.unlocked[m.i] if m.unlocked else 0
            state = m.states.get(idx, ("owned", 0))[0]
            badge = {"temp": "[dim]this gen only[/]"}.get(state, "[dim]ready[/]")
            self._status_card("New Egg", [f"[dim]{m.i + 1} of {m.n} available[/]",
                                          f"[dim]{m.locked} still locked[/]", "",
                                          "Destined to hatch", f"  [b]{egg_mod.hatch_name(idx)}[/]",
                                          f"  {badge}", "",
                                          "[dim]←→ browse  ENTER pick[/]"])
        elif (painter := self._status_painter()) is not None:
            painter()
        else:
            # data/digicore browses in the LCD; keep live vitals on the right
            self.stats_w.paint(self.pet)

    def _status_painter(self):
        """The mode's live status-panel painter (one table for repaint AND
        on_frame -- the two hand-rolled dispatches drifted; audit 2026-07)."""
        table = ((adventurescreen.AdventurePanel, self._status_adventure),
                 (tournamentscreen.TournamentPanel, self._status_tournament),
                 (training.TrainingPanel, self._status_training),
                 (battlescreen.BattlePanel, self._status_battle),
                 (dnascreen.DNAPanel, self._status_dna))
        for cls, painter in table:
            if isinstance(self.mode, cls):
                return painter
        return None

    def _status_card(self, title, lines):
        self.stats_w.border_subtitle = ""
        body = [f"[b]{title}[/]", f"[dim]{'─' * 26}[/]"] + lines
        self.stats_w.update("\n".join(body))

    def _status_tournament(self):
        p, t, T = self.pet, self.mode.tourney, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        if t is None:                      # cup-select phase (no bout yet)
            self._status_card("Cup", [f"[dim]{p.season} season[/]", "", "Pick a cup", "to enter."])
            return
        div = f"[dim]{'─' * 26}[/]"
        if t.over and t.champion:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.POS}]\u2605 CHAMPION \u2605[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                     f"Reward   [{T.COIN}]+{t.reward_bits}b[/]", div,
                     "[dim]you took the cup![/]"]
        elif t.over:
            lines = [f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                     f"[b]{t.name[:24]}[/]", "",
                     f"[{T.NEG}]eliminated[/]",
                     f"[dim]in the {t.round_name}[/]", "",
                     f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]", div,
                     "[dim]train up, try again[/]"]
        else:
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· cup[/]", div,
                f"[b]{t.name[:24]}[/]",
                f"Match    {t.round + 1} / 3",
                f"Trophy   [{T.COIN}]\u2605{p.trophies}[/]",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    [{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]",
                div,
                "[dim]fight for the cup[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def _status_training(self):
        from .training import GAMES, VACCINE_WINDOW, HP_ROUNDS, VIRUS_BAR_MIN
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'-' * 26}[/]".replace("-", "\u2500")
        eff = hearts(p.strength)
        energy = bar(p.energy_pct(), 11, T.ENERGY)
        power = f"[{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]"
        label = GAMES[tp.gi][1]
        gk = tp.gkey
        if tp.phase == "menu":
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     "[b]choose a drill[/]", "",
                     f"Effort   {eff}", f"Power    {power}", f"Energy   {energy}",
                     div, "[dim]pick what to build[/]"]
        elif tp.phase == "done":
            verdict = f"[{T.POS}]drill complete[/]" if tp.success else f"[{T.NEG}]needs work[/]"
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", "", verdict, "",
                     f"Effort   {eff}", f"Energy   {energy}", div,
                     f"[dim]{(tp.result or '')[:24]}[/]"]
        else:
            if gk == "hp":
                dots = "\u25cf" * tp.rounds_won + "\u25cb" * (HP_ROUNDS - tp.rep) + "\u00b7" * (tp.rep - tp.rounds_won)
                prog, prog2 = f"Round    {min(tp.rep + 1, HP_ROUNDS)} / {HP_ROUNDS}", f"Won      {dots}"
                target, flav = f"Effort   {eff}", "build your effort"
            elif gk == "vaccine":
                tpct = max(0, tp.timer) / VACCINE_WINDOW * 100
                prog, prog2 = f"Hits     {tp.taps} / {tp.vaccine_target}", f"Time     {bar(tpct, 11, T.MOOD)}"
                target, flav = f"Vaccine  [{T.POS}]{p.vaccine}[/]", "mash it up!"
            elif gk == "data":
                atk = ("HIGH" if tp.tgt_up else "LOW") if tp.locked else "feint\u2026"
                prog, prog2 = f"Attack   {atk}", f"Shield   {'UP' if tp.shield_up else 'DOWN'}"
                target, flav = f"Data     [{T.ENERGY}]{p.data_power}[/]", "block high or low"
            else:
                prog, prog2 = f"Power    {int(tp.pos)}", f"Need     {VIRUS_BAR_MIN}"
                target, flav = f"Virus    [{T.MOOD}]{p.virus}[/]", "stop it high"
            lines = [f"[b]{p.name[:14]}[/] [dim]\u00b7 train[/]", div,
                     f"[b]{label}[/]", prog, prog2, div,
                     target, f"Energy   {energy}", div, f"[dim]{flav}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_battle(self):
        p, m, T = self.pet, self.mode, theme
        b = m.battle
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'─' * 26}[/]"
        php = getattr(m, "hud_php", b.pet_hp)
        fhp = getattr(m, "hud_fhp", b.enemy_hp)
        pp = int(100 * php / b.pet_max) if b.pet_max else 0
        fp = int(100 * fhp / b.enemy_max) if b.enemy_max else 0
        tag = f" [{T.NEG}]BOSS[/]" if b.enemy.get("boss") else ""
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· battle[/]", div,
            f"vs [b]{b.enemy['name'][:14]}[/]{tag}", "",
            f"You  {bar(pp, 11, T.POS)} {php}/{b.pet_max}",
            f"Foe  {bar(fp, 11, T.NEG)} {fhp}/{b.enemy_max}",
            div,
        ]
        if m.done_anim:
            res = f"[{T.POS}]VICTORY![/]" if m.won else f"[{T.NEG}]DEFEAT[/]"
            lines += [res, f"[dim]{(b.reward or '')[:24]}[/]", "", "[dim]SPACE  continue[/]"]
        else:
            hint = "↑↓ ENTER pick" if getattr(m, "phase", "") == "menu" else "SPACE  skip"
            lines += [f"[dim]{(m.hud_note or '')[:24]}[/]", "", f"[dim]{hint}[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_eat(self):
        """DVPet feeding readout: the calorie (hunger) buffer plus the protein/mineral/
        vitamin macros, shown live while the eat animation plays."""
        from .pet import CALORIE_LIMIT, MAX_MACRO, GOOD_NUTRITION_MIN
        p, T = self.pet, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = "[dim]" + chr(0x2500) * 26 + "[/]"   # no backslash inside an f-string (SyntaxError on py3.10/3.11)
        def mbar(v, col):
            return bar(min(100, v * 100 // MAX_MACRO), 11, col)
        well = (p.nutr_protein >= GOOD_NUTRITION_MIN and p.nutr_mineral >= GOOD_NUTRITION_MIN
                and p.nutr_vitamin >= GOOD_NUTRITION_MIN)
        lines = [
            f"[b]{p.name[:14]}[/] [dim]\u00b7 feeding[/]", div,
            f"Calorie  {hearts(p.hunger)}",
            f"Fuel     {bar(p.calories * 100 // CALORIE_LIMIT, 12, T.COIN)}",
            div,
            f"Protein  {mbar(p.nutr_protein, T.POS)}",
            f"Mineral  {mbar(p.nutr_mineral, T.ENERGY)}",
            f"Vitamin  {mbar(p.nutr_vitamin, T.MOOD)}",
            div,
            f"Weight {p.weight}g",
            (f"[{T.POS}]well nourished[/]" if well else "[dim]a varied diet helps[/]"),
        ]
        self.stats_w.update("\n".join(lines))

    def _status_dna(self):
        p, m, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'─' * 26}[/]"
        f = m.field
        same = f == p.field
        own, chg = p.dna_owned.get(f, 0), p.dna_applied.get(f, 0)
        cost = "spirit -3/ea  mood+" if same else "spirit -6/ea  mood-  ill?"
        from . import data, evolution
        reqs = data.load_requirements()
        dna_t = [t for t in data.load_evolutions().get(p.num, [])
                 if reqs.get(t) and any(g[0] != "None" for g in reqs[t]["dna"].values())]
        unlocked = sum(1 for t in dna_t if evolution._dna_ok(p, reqs[t]))
        screen = {"home": "menu", "charge": "charge", "stats": "stats",
                  "reqs": "requirements", "bet": "generate", "mash": "generate",
                  "result": "generate"}.get(m.phase, "menu")
        lines = [
            f"[b]{p.name[:14]}[/] [dim]· DNA · {screen}[/]", div,
            f"Bits     [{T.COIN}]{p.bits}[/]",
            f"Field    {data.pretty_field(f)}" + ("  [dim](own)[/]" if same else ""),
            f"Banked   {own}     Charged {chg}",
            f"Share    {p.dna_percent(f)}%    [dim]x{m.amount}[/]",
            f"Unlocks  [b]{unlocked}[/]/{len(dna_t)} form(s)",
            div,
            f"[dim]{cost}[/]",
            f"[dim]{(m.last or '')[:24]}[/]",
            "",
            "[dim]own Field * = cheaper charge[/]",
            "[dim]ESC steps back out[/]",
        ]
        self.stats_w.update("\n".join(lines))

    def _status_adventure(self):
        p, a, T = self.pet, self.mode.adv, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'─' * 26}[/]"
        lives = "♥" * a.lives + "[dim]·[/]" * (3 - a.lives)
        power = f"[{T.POS}]●{p.vaccine}[/] [{T.ENERGY}]■{p.data_power}[/] [{T.MOOD}]▲{p.virus}[/]"
        if self.mode.sub is not None:                       # mid-encounter battle
            e = self.mode.sub.battle.enemy
            tag = f" [{T.NEG}]BOSS[/]" if e.get("boss") else ""
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· battle[/]",
                div,
                f"vs [b]{e['name'][:14]}[/]{tag}",
                f"Lives    {lives}",
                div,
                f"Effort   {hearts(p.strength)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    {power}",
                div,
                "[dim]a wild foe blocks[/]",
                "[dim]the path — fight![/]",
            ]
        else:                                               # travelling
            lines = [
                f"[b]{p.name[:14]}[/] [dim]· away[/]",
                div,
                f"Map      {a.mi + 1}-{a.zi + 1}",
                f"Lives    {lives}",
                f"Progress {a.pct}%",
                f"Bag      {sum(p.inventory.values())}   [{T.COIN}]{p.bits}b[/]",
                div,
                f"Hunger   {hearts(p.hunger)}",
                f"Energy   {bar(p.energy_pct(), 11, T.ENERGY)}",
                f"Power    {power}",
                div,
                "[dim]out exploring —[/]",
                "[dim]survive the zone[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def on_frame(self):                        # single DVPet interval clock (10 Hz, 0.1s): main view AND sub-screens
        self._hud_marquee()                    # scroll any over-long HUD message (independent of the LCD)
        if self.mode is not None:
            if hasattr(self.mode, "anim"):
                self.mode.anim()
                snd = getattr(self.mode, "sfx", None)   # drain anim-driven sfx (battle hits, lobby) — on_key only covers keypress
                if snd:
                    self.beep(snd, bell=False)
                    self.mode.sfx = None
                self.screen_w.update(self._center(self.mode.text()))
                painter = self._status_painter()
                if painter is not None:
                    painter()
            return
        sc = self.screen_w
        if sc.fx:
            sc.advance_fx()
            sc.paint(self.pet)
            if sc.fx:
                # beat-scripted fx sounds: eat's per-bite map + the generic snds map
                # (refuse head-shakes, the evolve burst, the dnaWash entry, ...)
                snd = (sc.fx.get("bite_snds", {}).get(sc.fx["step"])
                       or sc.fx.get("snds", {}).get(sc.fx["step"]))
                if snd:
                    self.beep(snd, bell=False)
                if sc.fx["kind"] == "eat":     # live DVPet feeding readout (calorie + P/M/V)
                    self._status_eat()
                elif sc.fx["kind"] == "play" and sc.fx["step"] % PLAY_HOP == 1:
                    self.beep("happy", bell=False)   # DVPet jumping(): a chirp at each hop's launch
            elif getattr(self, "_pending_evolve", None) is not None and self.screen_w.fx is None:
                old_num, self._pending_evolve = self._pending_evolve, None
                self.screen_w.start_fx("evolve", old_num=old_num)
            elif self._dying_fx:               # dying beat finished: saved, or the memorial
                self._dying_fx = False
                hits = getattr(self, "_revive_hits", 0)
                self._revive_hits = 0
                from .pet import HITS_TO_SAVE
                if hits > HITS_TO_SAVE * (self.pet.saved_from_death + 1):
                    old_num = self.pet.save_from_death()
                    if old_num is not None:            # the dark rebirth
                        self.flash(f"[b]{self.pet.name}![/] It came back... changed.")
                        self.screen_w.start_fx("evolve", old_num=old_num)
                    else:
                        self.flash(f"[b]{self.pet.name}[/] clings to life!")
                        self.screen_w.start_fx("cheer")
                    persistence.save(self.pet)
                else:
                    # UnlockInheritance (onDie with _bonus > 0): the departed etches
                    # its Digimemory; a second memory raises DVPet's only-one prompt
                    new_mem = self.pet.make_digimemory()
                    old_mem = persistence.peek_digimemory()
                    if new_mem and not old_mem:
                        persistence.bank_digimemory(new_mem)
                    persistence.save(self.pet)             # the spent bonus sticks
                    self._open_mode(deathscreen.DeathPanel(self.pet, new_mem=new_mem,
                                                           old_mem=old_mem), self._after_death)
            else:                              # any other fx just finished -> restore the HUD
                self.repaint()
        else:
            if self.pet.hatching:
                ht0 = getattr(self.pet, "_hatch_t", 3.0)
                done = self.pet.advance_hatch(0.1)
                # DVPet hatch(): _hatch sounds at t0.6 of the rock (interval 6), not at
                # the reveal -- fire as the timer crosses that beat (3.0s total - 0.6).
                if ht0 > 2.4 >= getattr(self.pet, "_hatch_t", 0.0):
                    self.beep("hatch")
                if done:
                    p = self.pet
                    self.flash(f"[b]{p.name}[/] hatched!")
            sc.advance(self.pet)
            sc.paint(self.pet)

    def on_tick(self):
        if self.mode is not None:
            return  # a sub-screen is open -> pause the life-sim (resumes in the main view)
        prev = (self.pet.num, self.pet.stage)
        was_dead = self.pet.dead
        poop0 = self.pet.poop
        self.pet.tick(1.0)
        p = self.pet
        if p.dead and not was_dead:
            self.beep("death")            # death.wav, like DVPet's dying() sound
            self.flash("")
            self.screen_w.start_fx("dying")   # exhausted pose beat, then the memorial
            self._dying_fx = True
            self._revive_hits = 0
        elif (p.num, p.stage) != prev:
            if prev[1] == "Egg":
                self.beep("hatch")
                self.flash(f"[b]{p.name}[/] hatched!")
                # hatch has NO evolve dither -- the egg already shook; the Fresh just appears
            else:
                # _evolve sounds INSIDE the strobe (fx snds beat 5), like DVPet evolveAnim.
                # design call (polish 2026-07): an evolution landing mid-fx WAITS for
                # the current animation instead of truncating it (death still overrides)
                self.flash(f"[b]{p.name}![/] evolved to {p.stage}!")
                if self.screen_w.fx is None:
                    self.screen_w.start_fx("evolve", old_num=prev[0])
                else:
                    self._pending_evolve = prev[0]
        elif p.poop > poop0:
            # DVPet playPoopSound is size-keyed: small / normal / large.  Map the new
            # pile count -> first drop is small, a big backup (>=3) is large.
            poop_snd = "smallPoop" if p.poop == 1 else ("largePoop" if p.poop >= 3 else "poop")
            if self.screen_w.fx is None:
                # DVPet poop(): squat/sway then the pile lands at t18 with its sound
                self.screen_w.start_fx("poop", poop=poop0)
                self.screen_w.fx["snds"] = {18: poop_snd}
            else:
                self.beep(poop_snd, bell=False)
        # AI Assistant rounds (checkAutoCare): play the visit, flash the quit notes
        ev = getattr(p, "assist_event", None)
        if ev and self.screen_w.fx is None:
            p.assist_event = None
            act, piles, sizes = ev
            self.screen_w.start_fx("assist", pet=p, poop=piles,
                                   icon="f:44" if act == "feed" else ("f:43" if act == "strength" else None))
            self.screen_w.fx["act"] = act
            self.screen_w.fx["sizes"] = sizes
            self.screen_w.fx["helper"] = p.assistant_num
            if act in ("feed", "strength"):
                # Assistant_Feed shares eatAnim's sounds: _eat per bite, _lastBite last
                self.screen_w.fx["snds"] = {12: "eat", 16: "eat", 20: "lastBite"}
        note = getattr(p, "assist_note", "")
        if note:
            self.flash(note)
            p.assist_note = ""
        # birthday (setTimeToAge age-up): announce the day's verdict
        if p.birthday_note:
            self.flash(p.birthday_note)
            self.beep("reward" if "Cupcake" in p.birthday_note or "Cookie" in p.birthday_note else "lose", bell=False)
            p.birthday_note = ""
        # tournament alarm (TournamentAlert): the alarmed cup's hour arrived --
        # onset ring, then the same attention bounce as the gift call
        if p.tourney_alert and not getattr(self, "_cup_alert_seen", False):
            self.beep("alarm")
        self._cup_alert_seen = p.tourney_alert
        if p.tourney_alert and p.anim == "idle" and self.screen_w.fx is None:
            p._set_anim("happy", 1.2)
        # gift call (DVPet GiftCall): onset chime, then the attention bounce
        # (poses 5/7, like DVPet attention(5,7)) until the present is claimed
        if p.gift and not getattr(self, "_gift_seen", False):
            self.beep("reward", bell=False)
        self._gift_seen = bool(p.gift)
        if p.gift and p.anim == "idle" and self.screen_w.fx is None:
            p._set_anim("happy", 1.2)
        # care-need call (classic V-pet nag): alert on onset, then every ~90s
        needs = p.needs_attention()
        if needs and not self._needs:
            self.beep("alarm")
            self._nag_t = 0.0
        elif needs:
            self._nag_t = getattr(self, "_nag_t", 0.0) + 1.0
            if self._nag_t >= 90:
                self._nag_t = 0.0
                self.beep("alarm")
        self._needs = needs
        # the alarm's on-screen half: announce the active care need in the HUD box,
        # yielding to a fresh action flash and clearing once the need is met
        if self._flash_t > 0:
            self._flash_t -= 1
            self._showing_update = False
        elif needs:
            self._hud(self._need_message(p))
            self._showing_need = True
            self._showing_update = False
        elif p.tourney_alert:
            self._hud("ALERT — Tournament open! [b]U[/] to enter")
            self._showing_need = True           # reuse the clear-on-resolve flag
            self._showing_update = False
        elif p.gift:
            self._hud(f"[b]{p.name}[/] has a present for you! ENTER to accept")
            self._showing_need = True           # reuse the clear-on-resolve flag
            self._showing_update = False
        elif self._showing_need:
            self._hud("")
            self._showing_need = False
        elif self._update_msg and not self._showing_update:
            self._hud(self._update_msg)     # gentle update nudge when idle (set once so the marquee can scroll)
            self._showing_update = True
        if self.screen_w.fx is None:   # during a care fx on_frame owns the paint; repainting here flashes the status box
            self.repaint()

    FLASH_HOLD = 4                  # seconds an action result holds before the care-need shows

    def _hud(self, markup):
        """Single entry point for the message box.  Any message wider than the box
        is marquee-scrolled (see _hud_marquee) so it is never clipped; messages that
        fit render as-is with their Rich markup.  Re-sending the SAME text is a
        no-op: on_tick re-asserts persistent messages every second, and resetting
        the hold each time froze the marquee on its first window (audit 2026-07)."""
        if markup == getattr(self, "_hud_text", None):
            return
        self._hud_text = markup
        if len(_hud_plain(markup)) <= HUD_W:
            self._hud_scroll = None
            self.msg_w.update(markup)
        else:
            self._hud_scroll = _hud_plain(markup)   # scroll plain text (overflow msgs carry no markup)
            self._hud_off = 0
            self._hud_hold = HUD_HOLD
            self._hud_tick = 0
            self.msg_w.update(_hud_esc(self._hud_scroll[:HUD_W]))

    def _hud_marquee(self):
        """Advance the message marquee one step.  Called from the 10 Hz frame clock;
        a no-op unless the current message overflows the box."""
        if self._hud_scroll is None:
            return
        self._hud_tick = (self._hud_tick + 1) % HUD_STEP
        if self._hud_tick:
            return                                  # throttle: scroll once per HUD_STEP frames
        if self._hud_hold > 0:
            self._hud_hold -= 1
            return                                  # pause on the head (and at each wrap)
        loop = self._hud_scroll + HUD_GAP
        self.msg_w.update(_hud_esc((loop + loop)[self._hud_off:self._hud_off + HUD_W]))
        self._hud_off += 1
        if self._hud_off >= len(loop):
            self._hud_off = 0
            self._hud_hold = HUD_HOLD               # hold again when it loops back to the head

    def flash(self, text):
        self._hud(text)
        self._flash_t = self.FLASH_HOLD

    def _need_message(self, p):
        """HUD announcement for the pet's most urgent unmet care need (or '')."""
        name = p.name or "Your pet"
        if p.sick:          msg = f"{name} is sick!"
        elif p.hunger == 0: msg = f"{name} is hungry!"
        elif p.poop >= 3:   msg = f"{name} needs cleaning!"
        elif p.energy <= 0: msg = f"{name} is exhausted!"
        elif p.scold_flag:  msg = f"{name} is misbehaving!"
        else:               return ""
        return f"[{theme.NEG}]\u26a0 {msg}[/]"

    def _do(self, result):
        self.flash(result)
        self.repaint()

    def action_feed(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        reason = self.pet.can_feed()            # egg/asleep/dead -> flash the reason, no menu
        if reason:
            self._do(reason); return
        self._open_mode(feedscreen.FeedPanel(self.pet), self._after_feed)

    def _after_feed(self, result):
        # result: ("fed"|"full"|"refused", food, msg); None on cancel.  A refusal
        # plays no food fx -- the refuse pose (State.Refusing) is already on the pet
        if not result:
            self.repaint(); return
        outcome, food, msg = result
        icon = food.get("key", "f:0")               # the food's REAL icon rides the eat fx
        # eat(): the wolf-down modifier is decided BEFORE the meal (a starving
        # pet that just ate has hunger>0 -- reading it here was always False)
        starving = getattr(self.pet, "_last_meal_starving", False)
        if outcome == "fed" and self.pet.anim == "eat":
            self.screen_w.start_fx("eat", icon, pet=self.pet, starving=starving)   # SFX per-bite in the fx loop
        elif outcome == "full":
            self.screen_w.start_fx("spit", icon)  # _refuse fires on each head-shake (fx snds)
        self._do(msg)
    def action_train(self):
        reason = self.pet.can_train()
        if reason:
            self._do(reason); return
        self._open_mode(training.TrainingPanel(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
        # DVPet onExerciseFinish: success -> setPraise(true) -> the cheer(true) fx;
        # anything less -> State.Jeering -> jeer(true, _angry).  apply_training left
        # the verdict in pet.anim (happy/sad; the sim is paused while the drill is
        # open, so it's still fresh here).
        if self.pet.anim == "happy":
            self.screen_w.start_fx("cheer")
        elif self.pet.anim == "sad":
            self.screen_w.start_fx("jeer")
        self.repaint()

    def action_battle(self):
        reason = self.pet.can_battle()
        if reason:
            self._do(reason); return
        self._open_mode(battlescreen.BattlePanel(self.pet), self._after_battle)

    def _after_battle(self, battle):
        if battle is not None:
            if battle.won:
                persistence.wins_add(1)        # lifetime wins gate the mystery eggs
            self.flash(battle.reward)
            self.beep("win") if battle.won else self.beep("lose", bell=False)
        self.repaint()

    def action_praise(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.praise()
        if self.pet.anim == "happy":                # the praise lands -> DVPet cheer()
            self.screen_w.start_fx("cheer")         # (its _happy sound is fx-scripted)
        self._do(msg)

    def action_scold(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.scold()
        if self.pet.anim == "angry":                # the scold lands -> DVPet jeer()
            self.screen_w.start_fx("jeer")          # (its _angry sound is fx-scripted)
        self._do(msg)

    def action_tournament(self):
        err = tournament.can_enter(self.pet)   # single source of entry gating (young/asleep/no-cup)
        if err:
            self._do(err); return
        self.pet.tourney_alert = False         # answering the call silences it
        self._open_mode(tournamentscreen.TournamentPanel(self.pet), self._after_cup)

    def _after_cup(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def action_jogress(self):
        reason = jogress.can_jogress(self.pet)
        if reason:
            self._do(reason); return
        self._open_mode(jogressscreen.JogressPanel(self.pet), self._after_jogress)

    def _after_jogress(self, msg):
        if msg:
            self.flash(msg)
            self.beep("jogress")
        self.repaint()

    def action_dna(self):
        reason = self.pet.can_charge_dna()
        if reason:
            self._do(reason); return
        self._open_mode(dnascreen.DNAPanel(self.pet), self._after_dna)

    def _after_dna(self, result=None):
        self.autosave()
        if isinstance(result, tuple) and result and result[0] == "charged":
            _, field, amount = result          # DVPet applyDNA -> DNA_Feeding -> main view
            self.screen_w.start_fx("dna_charge", icon=field, pet=self.pet)
            self.beep("compatible", bell=False)   # the DNA charge/absorb beep (no dedicated dna rip)
            self.flash("%s absorbed %d %s DNA" % (self.pet.name, amount, data.pretty_field(field)))
        else:
            self.repaint()

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)
    def action_inventory(self):
        self._open_mode(shopscreen.ShopPanel(self.pet, start_mode="bag"), self._after_shop)

    def action_habitat(self):
        self._open_mode(habitatscreen.HabitatPanel(self.pet), self._after_habitat)

    def action_assist(self):
        self._open_mode(assistscreen.AssistPanel(self.pet), lambda _=None: self.repaint())

    def action_digicore(self):
        self._open_mode(digicorescreen.DigiCorePanel(self.pet), self._after_digicore)

    def _after_digicore(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "evolve":
            # modeChange -> State.Evolving: the same strobe as any evolution
            self.flash(f"[b]{msg[2] if len(msg) > 2 else 'MODE CHANGE!'}[/]")
            self.screen_w.start_fx("evolve", old_num=msg[1])
        self.repaint()

    def _after_habitat(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def _after_shop(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "eat":
            self.screen_w.start_fx("eat", msg[1], pet=self.pet,
                                   starving=getattr(self.pet, "_last_meal_starving", False))
        elif isinstance(msg, tuple) and msg and msg[0] == "evolve":
            # _evolve sounds INSIDE the strobe (fx snds beat 5), like DVPet evolveAnim
            self.flash(f"[b]{self.pet.name}![/] evolved to {self.pet.stage}!")
            self.screen_w.start_fx("evolve", old_num=msg[1])
        elif isinstance(msg, tuple) and msg and msg[0] == "inherit":
            mem = msg[1]
            self.flash(f"[b]{mem.get('name', '?')}[/]'s power lives on!  "
                       f"Va+{mem.get('vaccine', 0)} D+{mem.get('data', 0)} Vi+{mem.get('virus', 0)}")
            self.screen_w.start_fx("inherit", pet=self.pet)
            self.screen_w.fx["ancestor"] = mem.get("num", -1)
        elif isinstance(msg, tuple) and msg and msg[0] == "transport":
            self._open_mode(transportscreen.TransportPanel(self.pet, msg[1]), self._after_transport)
            return
        elif msg:
            self.flash(msg)
        self.repaint()

    def _after_transport(self, msg):
        if msg:
            self.flash(msg)
        self.autosave()
        self.repaint()

    def action_adventure(self):
        if self.pet.stage in ("Egg", "Fresh"):
            self._do("Too young to adventure."); return
        if self.pet.asleep:
            self._do("zzz... asleep"); return
        refused = self.pet.check_refused()          # canTravel: checkRefused ...
        self.pet.check_compliant()                  # ... ; checkCompliant
        if refused:
            self._do(f"{self.pet.name} refuses to go!"); return
        self._open_mode(adventurescreen.AdventurePanel(self.pet), lambda _=None: self.repaint())

    def action_gift(self):
        if self.mode is not None or self.screen_w.fx is not None or not self.pet.gift:
            return
        key = self.pet.gift
        msg = self.pet.claim_gift()
        if msg:
            self.screen_w.start_fx("gift", icon=key)   # gifting() amble, chains to cheer (giftEnd)
            self._do(msg)

    def action_play(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.play()
        if self.pet.anim == "play":
            self.screen_w.start_fx("play")       # the DVPet jumping() hop; SFX fires per-hop in the fx loop
        self._do(msg)
    def action_clean(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        poop = self.pet.poop
        sizes0 = list(self.pet.poop_sizes)      # clean() wipes them; the fx still shows the piles
        msg = self.pet.clean()
        if self.pet.anim == "wash":
            self.screen_w.start_fx("clean", poop=poop)
            self.screen_w.fx["sizes"] = sizes0
            self.beep("wash", bell=False)
        self._do(msg)
    def action_heal(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.heal()
        if self.pet.anim == "heal":
            # DVPet bandage(): the treatment anim (item strip on the hurt pose),
            # which chains into cheer(true, _happy) at its beat 23.
            self.screen_w.start_fx("heal", icon="i:80")
        self._do(msg)
    def action_sleep(self):                                     # the "s" key is the LIGHTS toggle
        self.beep("confirm", bell=False)                        # a button blip on the lights on/off press
        self._do(self.pet.toggle_lights())
    def action_new(self):
        persistence.snapshot_prev_gen(self.pet)   # previous-generation egg gates
        gen = self.pet.generation + 1
        self._open_mode(eggselectscreen.EggSelectPanel(self.pet),
                        lambda et: self._hatch_new(et, gen))

    def _hatch_new(self, egg_type, gen):
        if egg_type is None:                        # cancelled -> keep the current pet
            self._do("Kept your current partner.")
            return
        self.pet = Pet.new_egg(generation=gen, egg_type=egg_type)
        self._grant_digimemory(self.pet)
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")


def _lobby_uri():
    return os.environ.get("TUIPET_LOBBY_URL", "wss://ff3mmo.com/tuipet/")  # live lobby (TLS); override for local dev


def main():
    # Cross-device: pull a newer cloud save down BEFORE the app loads the pet, so
    # the normal load path picks it up (no mid-session swapping). Fail-soft.
    if not _os.environ.get("TUIPET_NO_SYNC"):
        try:
            name, pw = persistence.get_account()
            cloudsync.sync_down_at_startup(_lobby_uri(), name, pw)
        except Exception:
            pass
    TuiPetApp().run()


if __name__ == "__main__":
    main()
