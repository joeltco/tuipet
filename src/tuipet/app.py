"""DVPet TUI — a terminal virtual pet rendered with halfblock sprites."""
from __future__ import annotations
# Force 24-bit color BEFORE importing Textual: SSH sessions usually do not carry
# COLORTERM, so Textual would auto-downgrade to xterm-256 and the muted background
# palette (e.g. the teal night hills #507070/#406060) all round to the same gray
# cube-color #5f5f5f -- flattening the ground into a featureless gray block. Modern
# terminals (Termux, etc.) support truecolor; advertise it unless the user set otherwise.
import os as _os
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
from .pet import Pet, POOP_MAX_PILES
from .render import render_screen
import os

from . import theme
from .theme import LCD_ON, LCD_BG, PHASE_PALETTE, SIL_DAY, SIL_NIGHT
SCREEN_COLS, SCREEN_ROWS = 40, 12
SPRITE_W = 16                                   # native creature sprite width

import re as _re
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
SUN = _FX.get("sun", [None])[0]               # real DVPet noon.png
MOON = _FX.get("moon", [None])[0]             # real DVPet night.png

_POOP_FR = (_FX.get("poop") or [None])[0]
POOP_W = len(_POOP_FR[0]) if _POOP_FR else 5
POOP_PAD = max(1, round(POOP_W * 6 / 30))   # DVPet drawFilthLevel column gap (pad 6 on a 30px cell)
_FROZEN_FR = (_FX.get("frozen") or [None])[0]

WEATHER_GLYPH = {
    "Clear": "", "Cloudy": chr(0x2601), "Drizzling": chr(0x2602),
    "Raining": chr(0x2602), "HeavyRain": chr(0x2614),
    "LightSnow": chr(0x2744), "Snowing": chr(0x2744), "HeavySnow": chr(0x2744),
}
_RAIN = {"Drizzling", "Raining", "HeavyRain"}
_SNOW = {"LightSnow", "Snowing", "HeavySnow"}
_PRECIP = _RAIN | _SNOW
_PRECIP_N = {"Drizzling": 5, "LightSnow": 6, "Raining": 11, "Snowing": 10,
             "HeavyRain": 18, "HeavySnow": 16}
CLOUD = ["0011100", "0111111", "1111111"]

_K = "b cyan"
KEYS = (
    f"[{_K}]f[/] feed  [{_K}]p[/] play  [{_K}]c[/] clean  [{_K}]h[/] heal  [{_K}]r[/] praise  [{_K}]k[/] scold  [{_K}]s[/] lights\n"
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
    pts = []
    if weather == "Cloudy" or weather in _RAIN or weather in _SNOW:
        for y, line in enumerate(CLOUD):          # a cloud bank, top-left
            for x, ch in enumerate(line):
                if ch == "1":
                    pts.append((1 + x, 1 + y))
    n = _PRECIP_N.get(weather, 0)
    if n:
        snow = weather in _SNOW
        for i in range(n):
            x0 = (i * 7 + 3) % cols
            base = (i * 5) % px_h
            if snow:
                y = (base + frame_i) % px_h                  # slow, drifting
                x = (x0 + ((frame_i // 2 + i) % 3 - 1)) % cols
                pts.append((x, y))
            else:
                y = (base + frame_i * 2) % px_h              # fast, slanted streaks
                x = (x0 + y // 2) % cols
                pts.append((x, y))
                pts.append((x, (y - 1) % px_h))
    return pts


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


COND_W = COND_H = 7                                # state.png cell size (DVPet 7x7 cells)
COND_PITCH = COND_H + 1
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
    poopfr = E.get("poop") or []
    if pet.poop and poopfr:                               # piles stack in a 2-wide grid (DVPet filth)
        pm = poopfr[(tick // (10 if pet.asleep else 7)) % len(poopfr)]   # DVPet animFilth swap
        pw, ph_ = len(pm[0]), len(pm)
        for i in range(min(pet.poop, POOP_MAX_PILES)):                  # DVPet drawFilthLevel: 3 columns x 2 rows,
            col, up = i // 2, i % 2                         # column-major (bottom pile, then one stacked
            x = 2 + col * (pw + POOP_PAD)                   # directly above it), each column steps right
            y = (px_h - 2 - ph_) - up * ph_
            pts += _blit(pm, x, y)
    if pet.num == -1:
        return pts
    asleep = bool(getattr(pet, "asleep", False))
    # --- sleep Zzz: fixed TOP-RIGHT corner (DVPet sleepLabel: width - w - 8, y1) ---
    zz_h = 0
    if asleep and E.get("zzz"):
        z = E["zzz"][(frame_i // 2) % len(E["zzz"])]
        zw, zz_h = len(z[0]), len(z)
        pts += _blit(z, cols - zw - 1, 0)
    # --- condition column: fixed right edge, every active condition stacked + blinking ---
    # DVPet stateNumTic blink: 7 ticks awake / 10 asleep, faster (7) when unwell.
    unwell = pet.sick or pet.is_injured() or pet.is_fatigued()
    sf = (tick // (7 if unwell else (10 if asleep else 7))) % 2
    col_x = cols - COND_W - 1                              # 1px off the right bezel (DVPet leaves ~2px)
    col_y0 = (zz_h + 1) if (asleep and zz_h) else 0        # even y -> crisp half-block alignment; below Zzz when asleep
    column = (("st_sick", pet.sick), ("st_medicine", pet.has_medicine()),
              ("st_injury", pet.is_injured()), ("st_bandage", pet.has_bandage()),
              ("st_vitamin", pet.has_vitamin()), ("st_fatigue", pet.is_fatigued()))
    k = 0
    col_active = False
    for key, active in column:
        if not active or not E.get(key):
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
              and (pet.hunger == 0 or pet.poop >= 3 or pet.energy <= 0)):
            bubble.append(E["attention"][0])             # care-call '!'
        teach = ((getattr(pet, "praise_flag", False) or getattr(pet, "scold_flag", False))
                 and pet.lights)
        if teach and E.get("st_teach"):
            bubble.append(E["st_teach"][sf])
        if bubble:
            bm = bubble[(tick // 5) % len(bubble)]        # if both present, take turns (rare)
            w = len(bm[0])
            pr = pet_right if pet_right is not None else cols - 1
            right_limit = (col_x - 1 - w) if col_active else (cols - w - 1)
            x = max(0, min(pr + 1, right_limit))
            pts += _blit(bm, x, 1)
    return pts


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0      # interval counter (10 Hz; 1 tick == 0.1s == one DVPet _interval)
        self.anim_key = None  # last anim state, so cadences restart on a state change
        self.roamer = anim.Roamer(int(SCREEN_COLS * 0.28), SCREEN_COLS, SPRITE_W)  # left-of-centre anchor
        self.fx = None        # active care-action animation

    def paint(self, pet: Pet):
        if self.fx:
            return self._paint_fx(pet)
        phase = pet.day_phase
        on, bg = PHASE_PALETTE.get(phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        corner = None                      # DVPet shows time via bg frame + palette, no corner icon
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
        overlay = (_weather_overlay(pet.weather, wf, SCREEN_COLS, SCREEN_ROWS * 2)
                   + _effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i))
        if pet.dead:                           # a grave marker
            self.update(render_screen(GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                      corner=corner, overlay=overlay, bgimg=bgimg))
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
            # full-width roam with edge-wrap (DVPet idleWalk); pose follows the roamer's
            # step and a filth pile is a left wall it turns at (filthLabel walk bound).
            idx = frames[self.roamer.pose % len(frames)]
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
            pcols = (min(pet.poop, POOP_MAX_PILES) + 1) // 2          # (sleep/sick bypass the roamer bound and would
            poop_edge = 2 + (pcols - 1) * (POOP_W + POOP_PAD) + POOP_W  # x just past the rightmost pile
            base = (SCREEN_COLS - SPRITE_W) // 2
            lo = poop_edge - base                         # min shift to clear the piles (REAL edge, not padded)
            cap = (SCREEN_COLS - SPRITE_W) - base         # don't push the pet off the right edge
            xshift = min(max(xshift, lo), max(cap, 0))    # clear poop on the left; emote follows the pet
        # DVPet adjustEmotionLabel: emote/'!' track the pet's final x, so rebuild the overlay now
        overlay = (_weather_overlay(pet.weather, wf, SCREEN_COLS, SCREEN_ROWS * 2)
                   + _effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i,
                                     pet_right=(SCREEN_COLS - SPRITE_W) // 2 + xshift + SPRITE_W))
        if not pet.lights:                 # lights off: DVPet's lightsOff is a fully-opaque black
            rows, xshift, mirror = [], 0, False   # cover -> the pet is hidden; only black (+ Zzz) shows
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, corner=corner, overlay=overlay, bgimg=bgimg))

    def _background(self, pet):
        return pet.background()

    def advance(self, pet=None):
        if pet is not None and pet.anim != self.anim_key:
            self.anim_key = pet.anim            # new state -> restart its cadence at beat 0
            self.frame_i = -1
        self.frame_i += 1
        if pet is not None and pet.anim in ("idle", "walk") and pet.num != -1 and not pet.sick:
            poop_cols = (min(pet.poop, POOP_MAX_PILES) + 1) // 2          # 3x2 grid -> ceil(piles/2) columns wide
            poop_right = (2 + poop_cols * (POOP_W + POOP_PAD) + 1) if pet.poop else 0
            cond = (pet.is_injured() or pet.is_fatigued() or pet.has_vitamin()
                    or pet.has_medicine() or pet.has_bandage())
            right_bound = (SCREEN_COLS - COND_W - 1 - SPRITE_W) if cond else None   # clear the right-edge column
            self.roamer.step(left_bound=poop_right, right_bound=right_bound)

    # ---- care-action animations (DVPet SpriteAnim eat/clean/cheer) -----------
    def start_fx(self, kind, icon=None, poop=0, old_num=None, pet=None):
        steps = {"eat": 35, "cheer": 31, "jeer": 31, "clean": 22, "spit": 11, "evolve": 18, "dying": 18, "dna_charge": 16}.get(kind, 12)
        self.fx = {"kind": kind, "step": 0, "steps": steps, "icon": icon, "poop": poop, "old_num": old_num}
        if kind == "eat":
            # DVPet eat(): each chew beat is scaled by pow(N, mod) -- a glutton wolfs
            # food down (mod 0.9, ends ~beat 23), a picky eater dawdles (mod 1.1, ~48);
            # food descent (beats 0/2/4/6) is NOT scaled.  Disliked food -> +9 grimace.
            glut = getattr(pet, "glutton", 0) if pet else 0
            mod = 0.9 if glut > 0 else (1.1 if glut < 0 else 1.0)
            bite = 9 if (pet is not None and getattr(pet, "_last_meal_disliked", False)) else 7
            beats = [int(b ** mod) for b in (10, 14, 18, 22, 26, 30)]
            self.fx["chew"] = {b: (8 if i % 2 == 0 else bite) for i, b in enumerate(beats)}
            self.fx["food_beats"] = (beats[1], beats[3], beats[5])
            self.fx["steps"] = int(34 ** mod) + 1

    def advance_fx(self):
        if not self.fx:
            return False
        self.fx["step"] += 1
        if self.fx["step"] < self.fx["steps"]:
            return True
        kind = self.fx["kind"]
        self.fx = None
        if kind == "clean":            # a good wash ends in the happy 'sunshine'
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

    def _paint_fx(self, pet):
        fx = self.fx
        on, bg = PHASE_PALETTE.get(pet.day_phase, (LCD_ON, LCD_BG))
        bgimg = self._background(pet)
        if bgimg:
            on = SIL_NIGHT if pet.day_phase == "night" else SIL_DAY
        px_h = SCREEN_ROWS * 2
        step = fx["step"]
        pose = {"eat": "eat", "clean": "idle", "cheer": "happy", "spit": "refuse", "dying": "exhausted"}.get(fx["kind"], "idle")
        rows = self._pose_rows(pet, pose, step // 2)
        overlay = _weather_overlay(pet.weather, self.frame_i, SCREEN_COLS, px_h)
        xshift = 0
        if fx["kind"] == "eat":
            # DVPet eat(): 24px food descends in 4 stages (beats 0/2/4/6) toward the
            # mouth, then a chew triad alternates open-mouth(+8)/chew(+7) at beats
            # 10/14/18/22/26/30 while the food is consumed frame-by-frame; ends ~34.
            xshift = -1                                        # DVPet centres the pet (char x29 of the 104px display)
            chew = fx.get("chew") or {10: 8, 14: 7, 18: 8, 22: 7, 26: 8, 30: 7}
            pose_i = 0
            for b in sorted(chew):
                if step >= b:
                    pose_i = chew[b]
            rows = self._pose_rows_idx(pet, pose_i)
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                fw = len(food[0][0]) if (food[0] and food[0][0]) else 8
                # DVPet: the food's RIGHT edge meets the pet's LEFT edge (foodLabel x31+24 == char x55),
                # so it descends right into the mouth -- abut it instead of stranding it on the far left.
                fx_x = max(0, (SCREEN_COLS - SPRITE_W) // 2 + xshift - fw)
                stage = 0 if step < 2 else 1 if step < 4 else 2 if step < 6 else 3
                fy = (0, 4, 9, 13)[stage]                      # DVPet descent y 0/11/22/33 of 60 -> *(24/60)
                fb = fx.get("food_beats") or (14, 22, 30)
                fi = 0 if step < fb[0] else 1 if step < fb[1] else 2 if step < fb[2] else 3
                overlay += _blit(food[min(fi, len(food) - 1)], fx_x, fy)
        elif fx["kind"] == "clean":
            # DVPet clean(): the wash enters from the right and, once it reaches the pet,
            # shoves the pet AND the filth left together until they slide off-screen (pet
            # in its clean pose, frame 4); the chained cheer then brings the pet back.
            E = data.load_effects()
            wash = E.get("wash", [None])[0]
            wx = SCREEN_COLS - step * 3                        # wash front: enters right, exits left
            base = (SCREEN_COLS - SPRITE_W) // 2
            pcols = (min(fx.get("poop", 0), 4) + 1) // 2
            clear = (2 + (pcols - 1) * (POOP_W + POOP_PAD) + POOP_W) - base if fx.get("poop") else 0
            push = max(0, base + clear + SPRITE_W - wx)        # wash shove, measured from the pet's RIGHT edge
            xshift = clear - push                              # pet starts cleared of the filth, then both
            if push > 0:                                       # slide left in lockstep (gap preserved, no mash)
                rows = self._pose_rows_idx(pet, 4)             # DVPet drawNum(4) while being washed
            pm = E.get("poop", [None])[0]
            if pm and fx.get("poop"):
                pw, ph_ = len(pm[0]), len(pm)
                for i in range(min(fx["poop"], POOP_MAX_PILES)):
                    col, up = i // 2, i % 2                     # filth slides off-screen with the pet
                    overlay += _blit(pm, 2 + col * (pw + POOP_PAD) - push,
                                     (px_h - 2 - ph_) - up * ph_)
            if wash:
                overlay += _blit(wash, wx, max(0, (px_h - len(wash)) // 2))
        elif fx["kind"] == "cheer":
            # DVPet cheer(): pose alternates up(+5)/down(+7) every 6 intervals with a
            # "happy" emote bubble pulsing on the up-beats; ends ~beat 30.
            up = (step // 6) % 2 == 0
            rows = self._pose_rows_idx(pet, 5 if up else 7)
            if up:
                hap = data.load_effects().get("happy")
                if hap:
                    hf = hap[(step // 6) % len(hap)]
                    # DVPet cheer(): the pet stays CENTRED and the emote rides its right
                    # edge (adjustEmotionLabel) -- not pinned to the far corner.
                    overlay += _blit(hf, (SCREEN_COLS - SPRITE_W) // 2 + SPRITE_W, 1)
        elif fx["kind"] == "jeer":
            # DVPet jeer(): pose alternates down(+10)/up(+9) every 6 intervals with an
            # "unhappy" emote bubble; ends ~beat 30 (the scold reaction).
            down = (step // 6) % 2 == 0
            rows = self._pose_rows_idx(pet, 10 if down else 9)
            un = data.load_effects().get("unhappy")
            if un:
                uf = un[(step // 6) % len(un)]
                # DVPet jeer(): centred pet, emote at its right edge (not the corner).
                overlay += _blit(uf, (SCREEN_COLS - SPRITE_W) // 2 + SPRITE_W, 1)
        elif fx["kind"] == "spit":
            # DVPet refuse(): the pet stays CENTRED and shakes its head; the rejected
            # food drops away from its mouth (on its left) rather than off to one side.
            xshift = 0
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                overlay += _blit(food[0], (SCREEN_COLS - SPRITE_W) // 2, 5 + step * 2)
        elif fx["kind"] == "evolve":
            # DVPet evolveAnim(): the screen strobes dark (lightsOff) <-> bright burst
            # (evol) while changeSprite() swaps the old form for the new one mid-flash --
            # the digimon flashes as a silhouette and emerges as its evolved form.
            n = fx["steps"]
            swap = n // 2                                      # changeSprite() midway
            old = fx.get("old_num")
            if step < swap and old not in (None, -1):          # old form until the swap...
                rec = data.load_sprites()[1].get(old)
                if rec and rec["frames"][0]:
                    rows = rec["frames"][0]
            # ...with bright full-screen "evol" flashes punctuating the transition
            if step < n - 3 and step % 3 == 1:
                overlay = overlay + [(x, y) for y in range(px_h) for x in range(SCREEN_COLS)]
            # the final steps drop the flash -> the evolved form is revealed
        elif fx["kind"] == "dna_charge":
            # DVPet dnaCharge(): the field drops into the pet and a "dnaWash" sweep
            # passes DOWN over it (moveDown) while the pet feeds on the DNA; bright
            # "flash" pulses mark the absorb.  Pet stays centred.  ~16 beats.
            rows = self._pose_rows_idx(pet, 0 if (step // 2) % 2 == 0 else 7)
            E = data.load_effects()
            wash = E.get("wash", [None])[0]
            if wash:
                wy = -len(wash) + step * 3                 # wash front: enters top, exits bottom
                overlay += _blit(wash, (SCREEN_COLS - SPRITE_W) // 2, wy)
            if step % 3 == 1 and step < fx["steps"] - 2:
                fl = E.get("flash")
                if fl:
                    overlay += _blit(fl[(step // 3) % len(fl)],
                                     (SCREEN_COLS - SPRITE_W) // 2 + SPRITE_W, 1)
        elif fx["kind"] == "dying":
            # DVPet dying() (SpriteAnim 13179): the collapsed pet sways gently (+/-1)
            # while the 'dying' emote (dying/dying2) pulses at its right edge, tracking
            # it -- frame swap and sway in lockstep, just before the memorial.
            xshift = 1 if (step // 5) % 2 == 0 else -1
            dye = data.load_effects().get("dying")
            if dye:
                df = dye[(step // 5) % len(dye)]
                overlay += _blit(df, (SCREEN_COLS - SPRITE_W) // 2 + SPRITE_W + xshift, 1)
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  xshift=xshift, overlay=overlay, bgimg=bgimg,
                                  mirror=(fx["kind"] == "dying")))


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
        deco = []
        if pet.asleep: deco.append("[blue]Zzz[/]")
        if pet.sick: deco.append(f"[{T.NEG}]+sick[/]")
        if pet.poop: deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
        if getattr(pet, "effect_id", -1) >= 0: deco.append(f"[{T.POS}]\u2726{pet.effect_name()}[/]")
        mins, secs = divmod(int(pet.age_seconds), 60)
        picon = chr(0x2600) if pet.is_daytime else chr(0x263E)
        wglyph = WEATHER_GLYPH.get(pet.weather, "")
        aff = pet._affinity()
        amark = (f"[{T.POS}]" + chr(0x2665) + "[/]" if aff > 0
                 else (f"[{T.NEG}]" + chr(0x2716) + "[/]" if aff < 0 else "[dim]·[/dim]"))
        xm = f" [b {T.ACCENT}]X[/]" if pet.x_antibody != "None" else ""
        lifepct = max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100))
        lifecol = T.NEG if pet.is_geriatric else T.LIFE
        self.border_subtitle = f"gen {pet.generation}"
        lines = [
            f"[b]{pet.name[:22]}[/]{xm}",
            f"[dim]{pet.stage} · {pet.attribute}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"Energy  {bar(pet.energy_pct(), 12, T.ENERGY)}",
            f"Mood    {bar(pet.mood_pct(), 12, T.MOOD)}",
            div,
            f"Power   [{T.POS}]V{pet.vaccine}[/] [{T.ENERGY}]D{pet.data_power}[/] [{T.MOOD}]Vi{pet.virus}[/]",
            f"Weight {pet.weight}g   [{T.COIN}]{pet.bits}b[/]",
            f"Battle {pet.wins}W/{pet.battles}   [{T.COIN}]\u2605{pet.trophies}[/]",
            f"@{pet.habitat_obj()['name'][:14]} {amark} [dim]{pet.season}[/]",
            f"[{T.COIN}]{picon}[/] [dim]{wglyph}{pet.weather} {int(pet.temp)}\u00b0[/] [dim]{mins}m{secs:02d}s[/]",
            f"Life    {bar(lifepct, 12, lifecol)}",
            _status_line(pet.status_word(), deco),
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
        ("s", "sleep", "Lights"), ("g", "theme", "Theme"), ("m", "sound", "Sound"), ("n", "new", "New pet"), ("q", "quit", "Quit"),
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

    def _after_title(self, _=None):
        if not persistence.get_account()[0]:     # first launch: create your lobby account
            self._open_mode(lobbyscreen.AccountPanel(), self._after_account)
            return
        self._post_title()

    def _after_account(self, result):
        if result:
            persistence.set_account(*result)
        self._post_title()

    def _post_title(self):
        if self._new_game:
            self._open_mode(eggselectscreen.EggSelectPanel(self.pet), self._after_egg_pick)
        else:
            self._hud(self._welcome)
            self.repaint()

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
        self.flash("Take good care of your egg!")
        self.repaint()

    def autosave(self):
        persistence.save(self.pet)
        self._note_progress()

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

    def on_key(self, event):
        if self.mode is not None:
            event.stop()
            event.prevent_default()      # a panel owns the keyboard: don't fire global BINDINGS
            result = self.mode.key(event.key)
            snd = getattr(self.mode, "sfx", None)
            if snd:
                self.beep(snd, bell=False)
                self.mode.sfx = None
            if result is not None and result[0] == "done":
                self._close_mode(result[1])
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
        uri = os.environ.get("TUIPET_LOBBY_URL", "wss://ff3mmo.com/tuipet/")  # live lobby (TLS); override for local dev
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
        elif isinstance(self.mode, adventurescreen.AdventurePanel):
            self._status_adventure()
        elif isinstance(self.mode, tournamentscreen.TournamentPanel):
            self._status_tournament()
        elif isinstance(self.mode, training.TrainingPanel):
            self._status_training()
        elif isinstance(self.mode, battlescreen.BattlePanel):
            self._status_battle()
        elif isinstance(self.mode, dnascreen.DNAPanel):
            self._status_dna()
        else:
            # data/digicore browses in the LCD; keep live vitals on the right
            self.stats_w.paint(self.pet)

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
                f"Power    [{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]",
                div,
                "[dim]fight for the cup[/]",
            ]
        self.stats_w.update("\n".join(lines))

    def _status_training(self):
        from .training import (GAMES, VACCINE_HITS_MIN, VACCINE_WINDOW,
                               HP_ROUNDS, DATA_REPS, VIRUS_BAR_MIN)
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = f"[dim]{'-' * 26}[/]".replace("-", "\u2500")
        eff = hearts(p.strength)
        energy = bar(p.energy_pct(), 11, T.ENERGY)
        power = f"[{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]"
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
                prog, prog2 = f"Hits     {tp.taps} / {VACCINE_HITS_MIN}", f"Time     {bar(tpct, 11, T.MOOD)}"
                target, flav = f"Vaccine  [{T.POS}]{p.vaccine}[/]", "mash it up!"
            elif gk == "data":
                dots = "\u25cf" * tp.hits + "\u25cb" * (DATA_REPS - tp.rep) + "\u00b7" * (tp.rep - tp.hits)
                prog, prog2 = f"Shot     {min(tp.rep + 1, DATA_REPS)} / {DATA_REPS}", f"Hits     {dots}"
                target, flav = f"Data     [{T.ENERGY}]{p.data_power}[/]", "shoot the frame"
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
        div = f"[dim]{'\u2500' * 26}[/]"
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
        power = f"[{T.POS}]V{p.vaccine}[/] [{T.ENERGY}]D{p.data_power}[/] [{T.MOOD}]Vi{p.virus}[/]"
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
                self.screen_w.update(self._center(self.mode.text()))
                if isinstance(self.mode, adventurescreen.AdventurePanel):
                    self._status_adventure()
                elif isinstance(self.mode, training.TrainingPanel):
                    self._status_training()
                elif isinstance(self.mode, battlescreen.BattlePanel):
                    self._status_battle()
                elif isinstance(self.mode, dnascreen.DNAPanel):
                    self._status_dna()
            return
        sc = self.screen_w
        if sc.fx:
            sc.advance_fx()
            sc.paint(self.pet)
            if sc.fx:
                if sc.fx["kind"] == "eat":     # live DVPet feeding readout (calorie + P/M/V)
                    self._status_eat()
            elif self._dying_fx:               # dying beat finished -> memorial
                self._dying_fx = False
                self._open_mode(deathscreen.DeathPanel(self.pet), self._after_death)
            else:                              # any other fx just finished -> restore the HUD
                self.repaint()
        else:
            if self.pet.hatching and self.pet.advance_hatch(0.1):
                p = self.pet
                self.beep("hatch")
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
        elif (p.num, p.stage) != prev:
            if prev[1] == "Egg":
                self.beep("hatch")
                self.flash(f"[b]{p.name}[/] hatched!")
                # hatch has NO evolve dither -- the egg already shook; the Fresh just appears
            else:
                self.beep("evolve")
                self.flash(f"[b]{p.name}![/] evolved to {p.stage}!")
                self.screen_w.start_fx("evolve", old_num=prev[0])
        elif p.poop > poop0:
            self.beep("poop", bell=False)
        # care-need call (classic V-pet nag): alert on onset, then every ~90s
        needs = (not p.dead and p.stage != "Egg" and not p.asleep and not p.call_paused()
                 and (p.hunger == 0 or p.sick or p.poop >= 3 or p.energy <= 0
                      or p.scold_flag))
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
        elif needs:
            self._hud(self._need_message(p))
            self._showing_need = True
        elif self._showing_need:
            self._hud("")
            self._showing_need = False
        if self.screen_w.fx is None:   # during a care fx on_frame owns the paint; repainting here flashes the status box
            self.repaint()

    FLASH_HOLD = 4                  # seconds an action result holds before the care-need shows

    def _hud(self, markup):
        """Single entry point for the message box.  Any message wider than the box
        is marquee-scrolled (see _hud_marquee) so it is never clipped; messages that
        fit render as-is with their Rich markup."""
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
        msg = self.pet.feed()
        if self.pet.anim == "eat":
            self.screen_w.start_fx("eat", "f:0", pet=self.pet)
            self.beep("eat", bell=False)
        elif "too full" in msg:
            self.screen_w.start_fx("spit", "f:0")
            self.beep("refuse", bell=False)
        self._do(msg)
    def action_train(self):
        reason = self.pet.can_train()
        if reason:
            self._do(reason); return
        self._open_mode(training.TrainingPanel(self.pet), self._after_train)

    def _after_train(self, msg):
        if msg:
            self.flash(msg)
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
            self.screen_w.start_fx("cheer")
            self.beep("happy", bell=False)
        self._do(msg)

    def action_scold(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.scold()
        if self.pet.anim == "angry":                # the scold lands -> DVPet jeer()
            self.screen_w.start_fx("jeer")
            self.beep("angry", bell=False)
        self._do(msg)

    def action_tournament(self):
        err = tournament.can_enter(self.pet)   # single source of entry gating (young/asleep/no-cup)
        if err:
            self._do(err); return
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
            self.flash("%s absorbed %d %s DNA" % (self.pet.name, amount, data.pretty_field(field)))
        else:
            self.repaint()

    def action_shop(self):
        self._open_mode(shopscreen.ShopPanel(self.pet), self._after_shop)
    def action_inventory(self):
        self._open_mode(shopscreen.ShopPanel(self.pet, start_mode="bag"), self._after_shop)

    def action_habitat(self):
        self._open_mode(habitatscreen.HabitatPanel(self.pet), self._after_habitat)

    def action_digicore(self):
        self._open_mode(digicorescreen.DigiCorePanel(self.pet), lambda _=None: self.repaint())

    def _after_habitat(self, msg):
        if msg:
            self.flash(msg)
        self.repaint()

    def _after_shop(self, msg):
        if isinstance(msg, tuple) and msg and msg[0] == "eat":
            self.screen_w.start_fx("eat", msg[1], pet=self.pet)        # the pet eats what you fed from the bag
        elif isinstance(msg, tuple) and msg and msg[0] == "evolve":
            self.beep("evolve")
            self.flash(f"[b]{self.pet.name}![/] evolved to {self.pet.stage}!")
            self.screen_w.start_fx("evolve", old_num=msg[1])
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
        self._open_mode(adventurescreen.AdventurePanel(self.pet), lambda _=None: self.repaint())

    def action_play(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.play()
        if self.pet.anim == "play":
            self.screen_w.start_fx("cheer")
            self.beep("happy", bell=False)
        self._do(msg)
    def action_clean(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        poop = self.pet.poop
        msg = self.pet.clean()
        if self.pet.anim == "wash":
            self.screen_w.start_fx("clean", poop=poop)
            self.beep("wash", bell=False)
        self._do(msg)
    def action_heal(self):
        if self.screen_w.fx is not None:        # let the current care animation finish before acting again
            return
        msg = self.pet.heal()
        if self.pet.anim == "heal":
            self.screen_w.start_fx("cheer")
            self.beep("happy", bell=False)
        self._do(msg)
    def action_sleep(self): self._do(self.pet.toggle_lights())   # the "s" key is the LIGHTS toggle
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
        persistence.save(self.pet)
        self._do(f"A new egg appeared! (generation {gen})")


def main():
    TuiPetApp().run()


if __name__ == "__main__":
    main()
