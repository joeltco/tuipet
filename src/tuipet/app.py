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
from . import eggselectscreen
from . import persistence
from . import jogressscreen
from . import jogress
from . import net
from . import lobbyscreen
from . import titlescreen
from . import themescreen
from . import deathscreen
from . import sound
from . import update as update_check
from . import cloudsync
from .pet import Pet, POOP_MAX_PILES
from .render import render_screen
import os

from . import theme
from .theme import LCD_ON, LCD_BG, PHASE_PALETTE, SIL_DAY, SIL_NIGHT
SCREEN_COLS, SCREEN_ROWS = 40, 12
SPRITE_W = 16                                   # native creature sprite width
# Authentic 32×16 play window, anchored (not clipped) inside the unchanged 40×24 LCD:
# centred horizontally, floor 2px from the border (render_screen's baseline already does the
# vertical). The roamer paces within [PLAY_X0, PLAY_RIGHT]; render.PLAY_COLS clamps the rest.
PLAY_COLS = 32
PLAY_X0 = (SCREEN_COLS - PLAY_COLS) // 2        # 4: left edge of the centred play window
PLAY_R = PLAY_X0 + PLAY_COLS                     # 36: right edge of the play window (HUD icons stay inside)
PLAY_RIGHT = PLAY_X0 + PLAY_COLS - SPRITE_W     # 20: rightmost sprite-x that fits in the window
# The authentic DM20 dot-matrix is 16 dots tall. The LCD canvas is taller (24px) so a
# background can show in the margins, but every game pixel lives inside this 16-dot band:
BAND_BOT = SCREEN_ROWS * 2 - 2                   # 22: floor, 2px above the border
BAND_TOP = BAND_BOT - 16                         # 6:  ceiling (16-dot screen)
PLAY_BAND = (BAND_TOP, BAND_BOT)

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


# One source of truth for the Stats-box furniture: the 26-col divider (the inner box
# is 26 wide), the compact age readout, and the one-line mode header.  Every status
# readout builds from these so they stay visually identical and markup-valid.
STAT_DIV = "[dim]" + "─" * 26 + "[/]"


def _age_str(seconds):
    """Compact age: 'Hh Mm' once past an hour (a pet lives for hours), else 'Mm Ss'."""
    s = max(0, int(seconds))
    if s >= 3600:
        h, rem = divmod(s, 3600)
        return f"{h}h{rem // 60:02d}m"
    m, sec = divmod(s, 60)
    return f"{m}m{sec:02d}s"


def _stat_head(name, tag):
    """The one-line header shared by the mode readouts: bold name + a dim mode tag."""
    return f"[b]{name[:14]}[/] [dim]· {tag}[/]"


# DM20 attribute badge: each type gets a distinct glyph + palette colour (matching the
# old triple-power glyphs so the association stays familiar). The status box shows the
# pet's ONE attribute here, DM20-style, not three separate power counters.
_ATTR_GLYPH = {"Vaccine": ("●", "POS"), "Data": ("■", "ENERGY"),
               "Virus": ("▲", "ACCENT"), "Free": ("◆", "MID")}


def _attr_badge(attribute):
    glyph, cname = _ATTR_GLYPH.get(attribute, ("·", "MID"))
    return f"[{getattr(theme, cname)}]{glyph}[/] {attribute or '—'}"


_FX = data.load_effects()
GRAVESTONE = _FX.get("grave", [None])[0]      # real DVPet death.png

def _sky_icon(pet):
    """A sun by day, a moon by night, for the status line. Returns (glyph, colour)."""
    return (chr(0x2600), theme.COIN) if pet.is_daytime else (chr(0x263E), "blue")


_K = "b cyan"
KEYS = (
    f"[{_K}]f[/] feed  [{_K}]t[/] train  [{_K}]c[/] clean  [{_K}]h[/] heal  [{_K}]s[/] lights\n"
    f"[{_K}]b[/] battle  [{_K}]j[/] jogress  [{_K}]l[/] lobby\n"
    f"[{_K}]g[/] theme  [{_K}]m[/] sound  [{_K}]n[/] new  [{_K}]q[/] quit"
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


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


COND_W = COND_H = 7                                # state.png cell size (DVPet 7x7 cells)
POOP_W = 8                                         # poop sprite width
STATUS_LANE = 8                                    # right-edge lane reserved for the injury skull
# HARD RULE ([[feedback_tuipet_sprites_never_overlap]]): NOTHING overlaps the creature.
# Poop gets a LEFT lane, the injury skull gets a RIGHT lane, and the creature is bounded to
# the clear zone between them.  wayland (source of truth) renders no poop and no Zzz sprite
# -- it shows SLEEP as the pose -- so there is no Zzz bubble, and DM20's care alert is a beep,
# not a floating '!'.


def _status_active(pet):
    """Is the right-lane status marker showing?  DM20's only floating marker is the injury
    skull ("it will have a skull floating next to it").  A care need (hungry / needs cleaning)
    is signalled by a beep + the shell's call icon on the real device, NOT a floating '!' over
    the pet -- so it does not reserve a play-field lane."""
    return bool(pet.is_injured())


def _care_zones(pet):
    """Reserved-lane bounds so the creature never overlaps the poop (left) or the status
    marker (right).  Returns (left_bound, right_bound) as the creature's sprite-x roam
    limits, plus (poop_cols, status_active) for the overlay layout."""
    if pet.dead or pet.num == -1:
        return PLAY_X0, PLAY_RIGHT, 0, False
    status_active = _status_active(pet)
    status_left = PLAY_R - (STATUS_LANE if status_active else 0)
    poop_cols = 0
    if pet.poop:
        room = (status_left - PLAY_X0) - SPRITE_W          # px left for poop after the creature
        poop_cols = max(0, min((min(pet.poop, POOP_MAX_PILES) + 1) // 2, room // POOP_W))
    left_bound = PLAY_X0 + poop_cols * POOP_W
    right_bound = max(left_bound, status_left - SPRITE_W)
    return left_bound, right_bound, poop_cols, status_active


def _effect_overlay(pet, frame_i, cols, px_h, tick=0):
    """Care overlays, laid out so NOTHING overlaps the creature (hard rule): droppings in
    a bottom-LEFT lane, the injury skull in a RIGHT lane, and the creature bounded to the
    clear zone between them (see _care_zones).  No sleep Zzz and no care-call '!' -- wayland
    (the source of truth) shows sleep as the POSE, and DM20's care alert is a beep + the
    shell call icon, not a floating bubble."""
    E = data.load_effects()
    front = []
    if pet.dead:
        return front
    band_top = max(0, px_h - 2 - 16)                      # 16-dot screen band, 2px floor (=6 on 24px canvas)
    band_bot = px_h - 2                                    # =22
    _lb, _rb, poop_cols, _sa = _care_zones(pet)
    # --- droppings: a left lane, piles stacked (2 per column); the creature stays clear ---
    poopfr = E.get("poop") or []
    if pet.poop and poopfr and poop_cols:
        pm = poopfr[(tick // (10 if pet.asleep else 7)) % len(poopfr)]   # DVPet animFilth swap
        pw, ph_ = len(pm[0]), len(pm)
        cap, n = min(pet.poop, POOP_MAX_PILES), 0
        for c in range(poop_cols):
            for r in range(2):                            # bottom pile, then one stacked above
                if n >= cap:
                    break
                front += _blit(pm, PLAY_X0 + c * pw, (band_bot - ph_) - r * ph_)
                n += 1
    if pet.num == -1:
        return front
    # --- right lane: the injury skull (DM20's only floating-beside-the-pet marker) ---
    sx = PLAY_R - STATUS_LANE
    if pet.is_injured() and E.get("st_injury"):
        front += _blit(E["st_injury"][(tick // 7) % 2], sx, band_top)
    return front


class Screen(Static):
    """The animated LCD screen."""
    def on_mount(self):
        self.frame_i = 0      # interval counter (10 Hz; 1 tick == 0.1s == one DVPet _interval)
        self.anim_key = None  # last anim state, so cadences restart on a state change
        self.roamer = anim.Roamer(int(SCREEN_COLS * 0.28), SCREEN_COLS, SPRITE_W)  # left-of-centre anchor
        self.fx = None        # active care-action animation
        self._idle_expr = None    # DVPet stepFrame care-state pose held for the current idle step (None = walk toggle)

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
        wf = self.frame_i // 4                  # effect overlay keeps its ~0.4s cadence
        if pet.dead:                           # a grave marker
            self.update(render_screen(GRAVESTONE, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                      bgimg=bgimg, band=PLAY_BAND))
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
        hold = (anim.idle_hold(0) if pet.anim in ("idle", "walk")
                else anim.SLEEP_BEAT if pet.anim == "sleep" else 6)
        idx = frames[(self.frame_i // hold) % len(frames)]
        rows = (_fr[idx] if idx < len(_fr) else None) or first
        xshift, mirror = 0, False
        if pet.anim in ("idle", "walk") and pet.is_injured() and pet.num != -1:
            si, dx = anim.sick_frame(self.frame_i)               # DVPet idleUnwell: collapse(10), weary(9) flash
            rows = (_fr[si] if si < len(_fr) else None) or first
            xshift = dx
        elif pet.anim in ("idle", "walk") and pet.num != -1:
            # full-width roam (DVPet idleWalk); pose follows the roamer's step, and a
            # filth pile is a left wall it turns at (filthLabel walk bound).  On some
            # steps DVPet's stepFrame shows a care-state pose instead of the walk toggle.
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
        # HARD RULE: keep the creature inside its clear zone so it never overlaps the poop
        # (left lane) or the injury/call marker (right lane).
        if pet.num != -1 and not (pet.num == -1 and pet.hatching):
            lb, rb, _, _ = _care_zones(pet)
            base = (SCREEN_COLS - SPRITE_W) // 2
            xshift = max(lb - base, min(xshift, rb - base))
        overlay = _effect_overlay(pet, wf, SCREEN_COLS, SCREEN_ROWS * 2, tick=self.frame_i)
        if not pet.lights:                 # lights off: DVPet's lightsOff is a fully-opaque black
            rows, xshift, mirror = [], 0, False   # cover -> the pet is hidden; only black shows
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  mirror=mirror, xshift=xshift, overlay=overlay,
                                  bgimg=bgimg, band=PLAY_BAND))

    def _background(self, pet):
        return pet.background()

    def advance(self, pet=None):
        if pet is not None and pet.anim != self.anim_key:
            self.anim_key = pet.anim            # new state -> restart its cadence at beat 0
            self.frame_i = -1
        self.frame_i += 1
        if pet is not None and pet.anim in ("idle", "walk") and pet.num != -1 and not pet.is_injured():
            prev_pose = self.roamer.pose
            # the Digimon paces only its CLEAR zone -- it turns at the poop lane (left) and
            # the injury/call lane (right) so it never overlaps them.
            lb, rb, _, _ = _care_zones(pet)
            self.roamer.step(left_bound=lb, right_bound=rb)
            if self.roamer.pose != prev_pose:                    # a fresh step landed (DVPet stepFrame):
                self._idle_expr = (anim.care_pose(pet)           # sometimes show a care-state pose instead of
                                   if random.random() < anim.IDLE_EXPR_CHANCE else None)  # the plain walk toggle
        else:
            self._idle_expr = None                               # any non-idle state clears the held expression

    # ---- care-action animations (DVPet SpriteAnim eat/clean/cheer) -----------
    def start_fx(self, kind, icon=None, poop=0, old_num=None):
        steps = {"eat": 35, "cheer": 31, "clean": 22, "spit": 11, "evolve": 18, "dying": 18}.get(kind, 12)
        self.fx = {"kind": kind, "step": 0, "steps": steps, "icon": icon, "poop": poop, "old_num": old_num}
        if kind == "eat":
            # DVPet eat(): 24px food descends (beats 0/2/4/6), then a chew triad alternates
            # open-mouth(+8)/chew(+7) at beats 10/14/18/22/26/30 while the food is eaten; ends ~34.
            beats = (10, 14, 18, 22, 26, 30)
            self.fx["chew"] = {b: (8 if i % 2 == 0 else 7) for i, b in enumerate(beats)}
            fb = (beats[1], beats[3], beats[5])
            self.fx["food_beats"] = fb
            # DVPet eat(): _eat on the first two bites, _lastBite on the third (the chew beats).
            self.fx["bite_snds"] = {fb[0]: "eat", fb[1]: "eat", fb[2]: "lastBite"}

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
        overlay = []
        xshift = 0
        yshift = 0
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
            push = max(0, base + SPRITE_W - wx)                # wash shove, measured from the pet's RIGHT edge
            xshift = -push                                     # pet slides left as the wash reaches it
            if push > 0:
                rows = self._pose_rows_idx(pet, 4)             # DVPet clean-done(4): pleased while washed
            pm = E.get("poop", [None])[0]
            if pm and fx.get("poop"):
                pw, ph_ = len(pm[0]), len(pm)
                for i in range(min(fx["poop"], POOP_MAX_PILES)):   # the floor row slides off with the pet
                    x = min(PLAY_X0 + i * pw, PLAY_R - pw) - push
                    overlay += _blit(pm, x, px_h - 2 - ph_)
            if wash:
                overlay += _blit(wash, wx, max(0, (px_h - len(wash)) // 2))
        elif fx["kind"] == "cheer":
            # a happy bounce: the pose alternates up(+5)/down(+7) every 6 intervals.  (The
            # DVPet sparkle emote bubble on the up-beats was stripped -- DM20 emotes by pose.)
            up = (step // 6) % 2 == 0
            rows = self._pose_rows_idx(pet, 5 if up else 7)   # cheer up(5) <-> down(7) bounce
        elif fx["kind"] == "spit":
            # DVPet refuse(): the pet stays CENTRED and shakes its head; the rejected
            # food drops away from its mouth (on its left) rather than off to one side.
            xshift = 0
            food = self._food_frames(fx.get("icon") or "f:0")
            if food:
                fw = len(food[0][0]) if (food[0] and food[0][0]) else 8
                # abut the pet's LEFT edge (same offer side as eat) so it falls clear of
                # the body instead of dropping straight through the silhouette
                fxx = max(PLAY_X0, (SCREEN_COLS - SPRITE_W) // 2 - fw)
                overlay += _blit(food[0], fxx, 5 + step * 2)
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
        elif fx["kind"] == "dying":
            # DVPet dying() (SpriteAnim 13179): the collapsed pet sways gently (+/-1)
            # while the 'dying' emote (dying/dying2) pulses at its right edge, tracking
            # it -- frame swap and sway in lockstep, just before the memorial.
            xshift = 1 if (step // 5) % 2 == 0 else -1
            dye = data.load_effects().get("dying")
            if dye:
                df = dye[(step // 5) % len(dye)]
                overlay += _blit(df, (SCREEN_COLS - SPRITE_W) // 2 + SPRITE_W + xshift, 1)
        # every care-action fx lives inside the 32-wide window: the window edge is the
        # screen edge (clip, not anchor), so clean's wash can shove the pet clear off it.
        self.update(render_screen(rows, SCREEN_COLS, SCREEN_ROWS, on, bg,
                                  xshift=xshift, yshift=yshift, overlay=overlay, bgimg=bgimg,
                                  mirror=(fx["kind"] == "dying"), clip=(PLAY_X0, PLAY_R), band=PLAY_BAND))


def _status_line(status, deco, width=26):
    """Assemble the status word + deco glyphs, bounded to `width` visible cols
    so the Stats box never wraps past its 16-row height. Drops the lowest-priority
    deco that would overflow (rare: only when asleep+injured+poop+effect pile up)."""
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
        div = STAT_DIV
        word = pet.status_word()
        deco = []
        if pet.asleep and word != "asleep": deco.append("[blue]Zzz[/]")
        if pet.is_injured() and word != "injured": deco.append(f"[{T.NEG}]+hurt[/]")
        if pet.poop and word != "needs cleaning": deco.append(f"[{T.COIN}]~poop x{pet.poop}[/]")
        sky, skycol = _sky_icon(pet)
        lifepct = max(0, int((pet.lifespan - pet.age_seconds) / max(1, pet.lifespan) * 100))
        lifecol = T.NEG if pet.is_geriatric else T.LIFE
        self.border_subtitle = f"gen {pet.generation}"
        lines = [
            f"[b]{pet.name[:22]}[/]",
            f"[dim]{pet.stage}[/]",
            div,
            f"Hunger  {hearts(pet.hunger)}",
            f"Effort  {hearts(pet.strength)}",
            f"DP      {bar(pet.dp_pct(), 12, T.ENERGY)}",
            div,
            f"Attrib  {_attr_badge(pet.attribute)}",
            f"Power   {pet.power}",
            f"Weight  {pet.weight}g",
            f"Battle  {pet.wins}W/{pet.battles}",
            f"[{skycol}]{sky}[/] [dim]{_age_str(pet.age_seconds)}[/]",
            f"Life    {bar(lifepct, 12, lifecol)}",
            _status_line(word, deco),
        ]
        self.update("\n".join(lines))

    def _paint_egg(self, pet):
        self.border_subtitle = f"gen {pet.generation}"
        div = STAT_DIV
        lines = [
            "[b]Digitama[/] [dim]· egg[/]",
            div,
            "[dim]a new life is warming[/]",
            "",
            "Destined to hatch",
            f"  [b]{egg_mod.hatch_name(pet.egg_type)}[/]",
            div,
            f"Age     {_age_str(pet.age_seconds)}",
            "",
            "[dim]keep it cosy — it[/]",
            "[dim]hatches on its own[/]",
        ]
        self.update("\n".join(lines))

    def _paint_grave(self, pet):
        self.border_subtitle = f"gen {pet.generation}"
        div = STAT_DIV
        lines = [
            f"[b]{pet.name[:16]}[/] [dim]· rest[/]",
            div,
            "[dim]a life remembered[/]",
            "",
            f"Lived    {_age_str(pet.age_seconds)}",
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
        ("c", "clean", "Clean"), ("h", "heal", "Heal"),
        ("j", "jogress", "Jogress"),
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
        self._sound_warned = False   # one-time "no audio backend" hint shown once in the main view
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
        self._push_cloud()              # mirror the autosave up to the cloud

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
        if self.mode is not None:
            event.stop()
            event.prevent_default()      # a panel owns the keyboard: don't fire global BINDINGS
            result = self.mode.key(event.key)
            snd = getattr(self.mode, "sfx", None)
            if snd:
                self.beep(snd, bell=False)
                self.mode.sfx = None
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
        if self.sound and not sound.available():
            # turning sound on with no backend stays silent -- say why instead of nothing
            self.flash("Sound on — install the Termux:API app for audio")
        else:
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
            self._status_card("New Egg", [f"[dim]{m.i + 1} of {m.n} versions[/]", "",
                                          "Destined to hatch",
                                          f"  [b]{egg_mod.hatch_name(m.i)}[/]",
                                          "  [dim]ready[/]", "", "",
                                          "[dim]←→ browse  ENTER pick[/]"])
        elif isinstance(self.mode, training.TrainingPanel):
            self._status_training()
        elif isinstance(self.mode, battlescreen.BattlePanel):
            self._status_battle()
        else:
            # data/digicore browses in the LCD; keep live vitals on the right
            self.stats_w.paint(self.pet)

    def _status_card(self, title, lines):
        self.stats_w.border_subtitle = ""
        body = [f"[b]{title}[/]", STAT_DIV] + lines
        self.stats_w.update("\n".join(body))

    def _status_training(self):
        from .training import MASH_TARGET, MASH_WINDOW
        p, tp, T = self.pet, self.mode, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = STAT_DIV
        head = _stat_head(p.name, "train")
        eff = hearts(p.strength)
        dp = bar(p.dp_pct(), 11, T.ENERGY)
        if tp.phase == "done":
            verdict = (f"[{T.POS}]wall smashed![/]" if tp.full
                       else (f"[{T.COIN}]some hits landed[/]" if tp.success else f"[{T.NEG}]too slow[/]"))
            lines = [head, div,
                     "[b]Wall Drill[/]", "", verdict, "",
                     f"Effort   {eff}", f"DP       {dp}", div,
                     f"[dim]{(tp.result or '')[:24]}[/]"]
        else:
            hitbar = bar(min(tp.taps, MASH_TARGET) / MASH_TARGET * 100, 11, T.POS)
            timebar = bar(max(0, tp.timer) / MASH_WINDOW * 100, 11, T.COIN)
            lines = [head, div,
                     "[b]Wall Drill[/]",
                     f"Hits     {tp.taps} / {MASH_TARGET}", f"Wall     {hitbar}",
                     f"Time     {timebar}", div,
                     f"Effort   {eff}", f"DP       {dp}", div,
                     "[dim]MASH to smash it![/]"]
        self.stats_w.update("\n".join(lines))

    def _status_battle(self):
        p, m, T = self.pet, self.mode, theme
        b = m.battle
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = STAT_DIV
        php = getattr(m, "hud_php", b.pet_hp)
        fhp = getattr(m, "hud_fhp", b.enemy_hp)
        pp = int(100 * php / b.pet_max) if b.pet_max else 0
        fp = int(100 * fhp / b.enemy_max) if b.enemy_max else 0
        tag = f" [{T.NEG}]BOSS[/]" if b.enemy.get("boss") else ""
        lines = [
            _stat_head(p.name, "battle"), div,
            f"vs [b]{b.enemy['name'][:14]}[/]{tag}", "",
            f"You  {bar(pp, 11, T.POS)} {php}/{b.pet_max}",
            f"Foe  {bar(fp, 11, T.NEG)} {fhp}/{b.enemy_max}",
            div,
        ]
        if m.done_anim:
            res = f"[{T.POS}]VICTORY![/]" if m.won else f"[{T.NEG}]DEFEAT[/]"
            lines += [res, f"[dim]{(b.reward or '')[:24]}[/]", "", "[dim]SPACE  continue[/]"]
        elif getattr(m, "phase", "") == "minigame":
            # attack-order minigame: a marker sweeps a track; land it in the zone to strike first
            pos, lo, hi = m.minigame_cells(14)
            cells = []
            for i in range(14):
                if i == pos:
                    cells.append(f"[{T.HEART}]◆[/]")
                elif lo <= i <= hi:
                    cells.append(f"[{T.POS}]▬[/]")
                else:
                    cells.append("[dim]─[/]")
            lines += ["[b]Attack order[/]", "", "".join(cells), "",
                      "[dim]SPACE strike  ESC flee[/]"]
        else:
            lines += [f"[dim]{(m.hud_note or '')[:24]}[/]", "", "[dim]SPACE  skip[/]"]
        self.stats_w.update("\n".join(lines))

    def _status_eat(self):
        """DM20 feeding readout: the hunger + effort hearts and DP, shown live while the
        eat animation plays."""
        p, T = self.pet, theme
        self.stats_w.border_subtitle = f"gen {p.generation}"
        div = STAT_DIV
        lines = [
            _stat_head(p.name, "feeding"), div,
            f"Hunger   {hearts(p.hunger)}",
            f"Effort   {hearts(p.strength)}",
            f"DP       {bar(p.dp_pct(), 12, T.ENERGY)}",
            div,
            f"Weight   {p.weight}g",
            f"Power    {p.power}",
            "",
            "[dim]Meat fills hunger; protein[/]",
            "[dim]builds strength + DP.[/]",
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
                if isinstance(self.mode, training.TrainingPanel):
                    self._status_training()
                elif isinstance(self.mode, battlescreen.BattlePanel):
                    self._status_battle()
            return
        sc = self.screen_w
        if sc.fx:
            sc.advance_fx()
            sc.paint(self.pet)
            if sc.fx:
                if sc.fx["kind"] == "eat":     # live feeding readout (hunger/effort/DP)
                    snd = sc.fx.get("bite_snds", {}).get(sc.fx["step"])
                    if snd:                    # _eat on bites 1-2, _lastBite on the final chew
                        self.beep(snd, bell=False)
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
        if (not self._sound_warned and self.sound and not sound.available()
                and self._flash_t <= 0):       # once the welcome flash clears, say why it's silent
            self._sound_warned = True
            self.flash("No audio — install the Termux:API app for sound")
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
            # DVPet playPoopSound is size-keyed: small / normal / large.  Map the new
            # pile count -> first drop is small, a big backup (>=3) is large.
            poop_snd = "smallPoop" if p.poop == 1 else ("largePoop" if p.poop >= 3 else "poop")
            self.beep(poop_snd, bell=False)
        # care-need call (classic V-pet nag): alert on onset, then every ~90s
        needs = (not p.dead and p.stage != "Egg" and not p.asleep
                 and (p.hunger == 0 or p.is_injured() or p.poop >= 3))
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
        if p.is_injured():  msg = f"{name} is hurt!"
        elif p.hunger == 0: msg = f"{name} is hungry!"
        elif p.poop >= 3:   msg = f"{name} needs cleaning!"
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
            self.screen_w.start_fx("eat", "f:0")   # SFX now fires per-bite in the fx loop
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
            self.flash(battle.reward)
            self.beep("win") if battle.won else self.beep("lose", bell=False)
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
