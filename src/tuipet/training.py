"""Training — DVPet's four drills, faithful to the SpriteAnim training states
(Vaccine_Training / Data_Training / Virus_Training / HP_Training -> Attacking ->
Attack_Contact -> Attack_Aftermath).

Every drill is fought against an on-screen OPPONENT that is present the whole time
-- the punching bag (HP / Vaccine / Virus) or the green pop-up target (Data) -- and
the skill phase flows straight into the strike -> impact -> aftermath, exactly like
the hardware (no abstract gauge with the opponent conjured up only at the end):

  HP    — the round's target attribute shows LEFT (big icon), 3 pickable option
          icons MIDDLE, pet RIGHT: read the symbol, pick the match, best of 3
          (drawHPTraining, first to 2 wins); builds Effort.
  Vaccine — pet HIDDEN, bag on screen: mash the hit button (drawVaccinePre);
          builds Vaccine power.  Pet appears for the strike.
  Data  — pet LEFT, green target RIGHT (drawDataPre): the attack feints, then
          COMMITS high or low; raise your shield to the matching side to BLOCK it
          (controller checkSuccess: success = shieldTop == isUp).  Fires RIGHT.
  Virus — pet HIDDEN, bag on screen: stop the sweeping power bar high
          (drawVirusPre); builds Virus power.

The stat outcome stays in Pet.apply_training; this module is the presentation.
"""
from __future__ import annotations
import json
import os
import random
from rich.text import Text
from . import data
from . import grid
from .render import render_scene
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, MID, ACCENT, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
# the post-drill strike CLONES the battle screen's alternating-view volley (one combatant
# on screen at a time: pet rears back & fires the real orb off the near edge -> view switches
# to the TARGET as the orb arrives -> fullscreen explosion -> break).  Reuse the battle's
# pose ids + beat timings + column-bounds helper so the two stay in lockstep.
from .battlescreen import (IDLE, TURN, ATTACK, CHARGE, COLLAPSE,  # noqa: F401
                           WINDUP_T, FIRE_T, EXPLODE_FRAMES, EXPLODE_HOLD, FLINCH_T,
                           _cbounds, _clamp_grid)

# the full-screen spiky hit burst (attackHit/attackHitFlash), shared with the battle
# screen -- strobes outline<->filled to flash the LCD on impact (DVPet hitAnim).
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _EXPLODE = json.load(_f)["hit_explosion"]

# DVPet config (config.csv).  tuipet ticks at 0.1s == one DVPet _interval (6 frames @60fps),
# so frame-unit constants are converted to per-tick.  Each attribute drill's difficulty steps
# up by RANK = attributePower // 75 (AttributeTrainDifficultyChange) -> 0 Easy / 1 Normal / 2 Hard.
ATTR_TRAIN_DIFFICULTY = 75
# Vaccine: MASH to a hit threshold (VaccineGameHitsMin{Easy,,Hard}).
VACCINE_HITS = (16, 20, 24)
VACCINE_WINDOW = 41           # drawVaccinePre = _interval*41 = 246 frames @60fps ~= 4.1s
# Virus: a power bar FILLS 0->maxBar and loops; stop it in the zone (>= VirusGameBarMin).
VIRUS_BAR_MIN = 86            # VirusGameBarMin
VIRUS_MAX = 94               # DVPet maxBar (bar pixel width) -> the zone 86..94 is the top ~8%
VIRUS_SPEEDS = (4.8, 6.0, 8.0)  # per-tick fill = DVPet +4 per VirusGameBarSpeed{5,4,3} frames (48/60/80 px/s / 10Hz)
# Data is a SHIELD BLOCK (checkSuccess: success = shieldTop == isUp): the green target feints,
# then COMMITS its attack high or low; raise your shield to the matching side before the window closes.
DATA_BOB = 3                  # ticks per feint up/down toggle during the telegraph
DATA_TELEGRAPH = (21, 17, 15)  # feint window before commit (DVPet frame*8+pad*8 frames, /6 -> ticks)
DATA_WINDOW = (10, 7, 5)      # reaction window after commit (DataTrainShootFrame{10,7,5}; 6*frame/6 -> ticks)
DATA_MARGIN = 4               # the data stage's side margin == GRID_X0: cannon anchors on the grid's left edge
DATA_FLY = 3                  # DVPet attackGreen: the shot moves over 3 intervals (locX 55->61->67)
#  collision = the battle's exact beats: EXPLODE_FRAMES strobe (hitAnim) + FLINCH_T pose (aftermathGreen)
HP_ROUNDS = 3                 # DVPet _hpTrainingRounds
HP_ROUNDS_WON = 2             # DVPet _hpTrainingRoundsWon (first to 2 wins the drill)
HP_TRAIN_DIFFICULTY = 11      # DVPet _hpTrainDifficultyChange: rank = fullHealthPoints // 11
HP_ROUND_LEN = (30, 20, 10)   # ticks/round by rank (Easy/Normal/Hard) -- DVPet _hpTrainingRoundLength{Easy,,Hard};
                              # the timer SHRINKS as battle HP grows (the drill gets harder)
VBAR_W = 24

COLS = 40
ARENA_ROWS = 12               # the app's ONE locked LCD area (== app SCREEN_ROWS / battle ROWS).
                              # DVPet's native LCD is 105x60px; tuipet shows it at 40x24 everywhere.
PXH = ARENA_ROWS * 2          # 24px tall

# The ONE creature grid every drill sits on -- shared with every other screen via grid.py
# (two 16x16 cells side by side == 32x16, centred in the 40-wide LCD, floor 2px above bottom).
CELL = grid.CELL                  # 16
GRID_W = grid.W                   # 32
GRID_X0 = grid.X0                 # 4: left margin (32 grid centred in 40)
BAND_TOP = grid.TOP               # 6: top of the 16px band
BASE_Y = grid.FLOOR               # 22: the floor -- every sprite baselines here, 2px above bottom

# strike sequence: a battle-style volley (windup -> fire_out -> fire_in -> hit -> break),
# beats imported from the battle screen so they march at the same pace.  The orb rides the
# lower 16px creature band -- the SAME band the drill sprites stand in.
STRIKE_BAND_TOP = BAND_TOP
STRIKE_BAND_BOT = BASE_Y


# drill sprite helpers -- thin aliases over the shared grid module (single source of truth)
def _fit_cell(sprite):
    """Cap a sprite to the 16px band height so it fits the grid like the 16x16 creatures."""
    return grid.fit_band(sprite)


def _cell(sprite, cell):
    """(sprite, x_left, mirror) placement in cell 0 (left) or 1 (right) of the 32x16 grid."""
    return grid.cell(sprite, cell)


def _fit_width(sprite, target_w):
    """Box-downscale a sprite horizontally to <= target_w so a wide gauge fits the 32-grid."""
    return grid.fit_w(sprite, target_w)


def _blit(bm, ox, oy):
    """Sprite bitmap -> (x,y) pixel list for render_scene's overlay (projectile / flash)."""
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


# The REAL DVPet HP training dummy -- the bird "battle bag" (battleBags.png top row, the clean
# frames DVPet's getBattleBagSprite maps as Vaccine=circle / Virus=triangle / Data=square).
# The target attribute shows as a cutout symbol on the bird's belly; the player reads it and
# picks the matching attribute.  1-bit, cropped-to-content, downscaled to fit the LCD.  From source art.
with open(os.path.join(os.path.dirname(__file__), "data", "hp_dummies.json")) as _f:
    _HP_DUMMIES = json.load(_f)         # {'vaccine','virus','data'} -> 1-bit bird w/ belly symbol


GAMES = [
    ("hp",      "HP Drill", "Effort",  "guess the bag — best of 3"),
    ("vaccine", "Vaccine",  "Vaccine", "mash the bag — fast!"),
    ("data",    "Data",     "Data",    "block the attack — high or low"),
    ("virus",   "Virus",    "Virus",   f"stop the bar over {VIRUS_BAR_MIN}"),
]


class TrainingPanel:
    def __init__(self, pet):
        self.pet = pet
        self.phase = "menu"          # menu | play | strike | done
        self.gi = 0
        self.frame_i = 0
        self.flash = "Pick a drill."
        self.result = None
        self.success = False
        self._reset()

    def _reset(self):
        self.pos = 0.0
        self.dir = 1
        self.rep = 0
        self.hits = 0
        self.power = 0
        self.taps = 0
        self.timer = VACCINE_WINDOW
        self.vaccine_target = VACCINE_HITS[1]   # rank-based, set per drill start (below)
        self.virus_speed = VIRUS_SPEEDS[1]      # rank-based bar fill speed
        self.data_telegraph = DATA_TELEGRAPH[1]  # rank-based feint window
        self.data_window = DATA_WINDOW[1]       # rank-based reaction window
        self.round_len = HP_ROUND_LEN[1]
        self.round_t = self.round_len
        self.rounds_won = 0
        self.hp_target = 0           # hidden attribute the bag "is" (0/1/2)
        self.hp_pick = 0             # the player's cursor over the 3 guess buttons
        # data shield-block state
        self.data_t = 0
        self.feint_up = False        # green's current feint position during the telegraph
        self.locked = False          # has the attack committed (revealed high/low)?
        self.tgt_up = False          # the committed attack direction (only once locked)
        self.shield_up = True        # the player's shield: up (True) or down (False)
        self.blocked = False
        self.fired = False           # DVPet onPreFinish: success is LOCKED; the shot now fires (cosmetic)
        self.fly_t = 0               # DVPet attackGreen countdown: the committed shot flies to the target
        self.strobe_t = 0            # DVPet hitAnim: the centred fullscreen collision flash strobes
        self.flinch_t = 0            # DVPet aftermathGreen: the pet's pose is held after the impact
        self._impact_args = None     # the staged _finish() call, fired when the flinch ends
        self._strike_pose = None     # transient hit(6)/miss(9) pose during a drill
        self._strike_t = 0
        self.strike_tl = []          # the post-drill strike timeline (battle-style volley)
        self.si = 0                  # index into strike_tl
        self.strike_attr = None      # the orb's attribute ("Vaccine"/"Data"/"Virus")
        self._last_sm = None         # last strike marker, for one-shot sfx at beat edges
        self._strong = False         # a full-success drill -> strong attack/hit

    @property
    def gkey(self):
        return GAMES[self.gi][0]

    @property
    def _is_data(self):
        return self.gkey == "data"

    def _attr_rank(self, power):
        """DVPet difficulty rank for an attribute drill: power // 75 -> 0 Easy/1 Normal/2 Hard."""
        return min(power // ATTR_TRAIN_DIFFICULTY, 2)

    def _vaccine_threshold(self):
        """DVPet checkSuccess(Vaccine): hits needed scales with vaccine rank."""
        return VACCINE_HITS[self._attr_rank(self.pet.vaccine)]

    # ---- lifecycle ----
    def _start_game(self):
        self.phase = "play"
        self._reset()
        gk = self.gkey
        if gk == "hp":
            self._new_hp_round()
        elif gk == "vaccine":
            self.vaccine_target = self._vaccine_threshold()
            self.flash = "MASH the bag!"
        elif gk == "data":
            r = self._attr_rank(self.pet.data_power)
            self.data_telegraph, self.data_window = DATA_TELEGRAPH[r], DATA_WINDOW[r]
            self.flash = "watch the feint — block high or low!"
        else:
            self.virus_speed = VIRUS_SPEEDS[self._attr_rank(self.pet.virus)]
            self.flash = "stop the bar high!"

    def _hp_round_len(self):
        """DVPet drawHPTraining: the per-round timer shrinks as the pet's battle HP grows
        (rank = fullHealthPoints // _hpTrainDifficultyChange -> Easy/Normal/Hard).  tuipet's
        battle HP is stage-based (battle.MAX_HEALTH)."""
        from .battle import MAX_HEALTH, MAX_HEALTH_DEFAULT
        full_hp = MAX_HEALTH.get(self.pet.stage, MAX_HEALTH_DEFAULT)
        return HP_ROUND_LEN[min(full_hp // HP_TRAIN_DIFFICULTY, 2)]

    def _new_hp_round(self):
        self.hp_target = random.randrange(3)
        self.hp_pick = 0
        self.round_len = self._hp_round_len()
        self.round_t = self.round_len
        self.flash = f"round {self.rep + 1}/{HP_ROUNDS} — match the symbol"

    def _hp_resolve(self, correct):
        if correct:
            self.rounds_won += 1
            self.flash = "RIGHT!"
            self._flash(6)
        else:
            self.flash = "wrong!"
            self._flash(9)
        self.rep += 1
        # DVPet loops while round < _hpTrainingRounds AND roundsWon < _hpTrainingRoundsWon:
        # win the instant you hit 2, or stop once the 3 rounds are spent.
        if self.rounds_won >= HP_ROUNDS_WON or self.rep >= HP_ROUNDS:
            won = self.rounds_won
            hits = 3 if won >= HP_ROUNDS_WON else won      # a 2-win is a full success (full Effort)
            self._finish(hits, 0, None, "hp")
        else:
            self._new_hp_round()

    def _finish(self, hits, power, attribute, game):
        self.success = hits >= 2
        self._strong = hits >= 3
        self.result = self.pet.apply_training(hits, power, attribute, game=game)
        if game in ("hp", "data"):
            # No pet counter-attack: HP flashes pose 6/9 per guess; DATA is purely DEFENSIVE
            # (DVPet attackGreen -> the CANNON shoots the pet, you just block -- the shot +
            # impact already played out in the drill).  Reveal the result directly.
            self.phase = "done"
            self.flash = self.result + "   (SPACE)"
        else:
            # vaccine/virus fire the pet's real orb at the bag (a battle-style volley), THEN
            # reveal the score.
            self.strike_attr = attribute
            self._build_strike()
            self.phase = "strike"
            self.flash = ""

    def _build_strike(self):
        """The battle volley, cloned for training: the pet rears back, fires its orb off the
        near edge, the view switches to the TARGET as the orb arrives, then the fullscreen
        explosion + break (success) or a whiff (fail).  Same beats as battlescreen."""
        strong = self._strong
        tl = []
        tl += [{"m": "windup", "wu": s} for s in range(WINDUP_T)]
        tl += [{"m": "fire_out", "prog": (s + 1) / FIRE_T, "double": strong} for s in range(FIRE_T)]
        tl += [{"m": "fire_in", "prog": (s + 1) / FIRE_T, "double": strong} for s in range(FIRE_T)]
        if self.success:                                    # HIT: strobing explosion, then the broken target
            tl += [{"m": "hit", "f": (s // EXPLODE_HOLD) % 2} for s in range(EXPLODE_FRAMES)]
            tl += [{"m": "break"}] * FLINCH_T
        else:                                               # FAIL: orb fizzles, target intact, pet deflates
            tl += [{"m": "miss"}] * FLINCH_T
        self.strike_tl = tl
        self.si = 0
        self._last_sm = None

    def _strike_sfx(self):
        """One-shot beep at each strike-beat edge -- launch sting, then the impact."""
        m = self.strike_tl[self.si].get("m")
        if m != self._last_sm:
            if m == "fire_out":
                self.sfx = "strongAttack" if self._strong else "attack"
            elif m == "hit":
                self.sfx = "strongHit" if self._strong else "attackHit"
            elif m == "miss":
                self.sfx = "cancel"
        self._last_sm = m

    # ---- anim (called each fast tick) ----
    def anim(self):
        self.frame_i += 1
        if self._strike_t > 0:
            self._strike_t -= 1
        if self.phase == "strike":
            if self.si < len(self.strike_tl) - 1:
                self.si += 1
                self._strike_sfx()
            else:                                           # volley done -> reveal the score
                self.phase = "done"
                self.flash = self.result + "   (SPACE)"
            return
        if self.phase != "play":
            return
        gk = self.gkey
        if gk == "hp":
            self.round_t -= 1
            if self.round_t <= 0:
                self._hp_resolve(False)                     # timed out -> a wrong guess
        elif gk == "vaccine":
            self.timer -= 1
            if self.timer <= 0:
                thr = self.vaccine_target                    # DVPet success = taps >= threshold (binary);
                hits = (3 if self.taps >= thr * 1.2 else     # tuipet keeps a graded reward around that
                        2 if self.taps >= thr else           # boundary: meeting the threshold = success,
                        1 if self.taps >= thr * 0.5 else 0)  # a clear overshoot = strong, near-miss = partial
                self._finish(hits, int(self.taps), "Vaccine", "vaccine")
        elif gk == "data":
            if self.fired:                                  # success is locked (DVPet onPreFinish); the
                if self.fly_t > 0:                          # finale is cosmetic.  Same beats as the battle
                    self.fly_t -= 1                          # collision.  DVPet attackGreen: the shot flies...
                    if self.fly_t == 0:
                        self.sfx = "attackHit"               # ...DVPet hitAnim: it LANDS -> the flash strobes
                        self.strobe_t = EXPLODE_FRAMES
                    return
                if self.strobe_t > 0:                        # DVPet hitAnim: the fullscreen flash strobes,
                    self.strobe_t -= 1                       # then aftermathGreen holds the pet's pose
                    if self.strobe_t == 0:
                        self.flinch_t = FLINCH_T
                    return
                if self.flinch_t > 0:
                    self.flinch_t -= 1
                    if self.flinch_t == 0:
                        self._finish(*self._impact_args)
                    return
                return
            self.data_t += 1
            if not self.locked:                             # telegraph: the cannon's barrel feints up/down
                if self.data_t % DATA_BOB == 0:
                    self.feint_up = not self.feint_up
                if self.data_t >= self.data_telegraph:      # ...then it COMMITS high or low: the barrel
                    self.locked = True                       # locks and the orb appears at the muzzle to
                    self.tgt_up = random.choice((True, False))  # charge (you can still toggle the shield)
                    self.data_t = 0
                    self.flash = "block it — toggle the shield!"
            elif self.data_t >= self.data_window:           # charge window closes -> EVAL (DVPet onPreFinish)
                self._data_resolve()
        else:  # virus -- DVPet drawVirusPre: the bar FILLS then snaps back to 0 and loops;
            self.pos += self.virus_speed                     # hit captures the level at that instant
            if self.pos >= VIRUS_MAX:
                self.pos = 0

    # ---- key ----
    def key(self, k):
        if self.phase == "strike":
            if k in ("space", "enter", "escape"):       # skip to the end of the volley (like battle)
                self.si = len(self.strike_tl) - 1
            return None
        if self.phase == "menu":
            # DVPet drawTrainingSelect diamond: ● Vaccine top, ■ Data left,
            # ▲ Virus right, HP bottom -- each arrow selects the drill in that direction.
            if k in ("up", "k"):
                self.gi = 1            # ● Vaccine (top)
            elif k in ("left", "h"):
                self.gi = 2            # ■ Data (left)
            elif k in ("right", "l"):
                self.gi = 3            # ▲ Virus (right)
            elif k in ("down", "j"):
                self.gi = 0            # HP (bottom)
            elif k in ("1", "2", "3", "4"):
                self.gi = int(k) - 1
                self._start_game()
            elif k in ("enter", "space"):
                self._start_game()
            elif k in ("escape", "t"):
                return ("done", None)
            return None
        if self.phase == "done":
            if k in ("space", "enter", "escape", "t"):
                return ("done", self.result)
            return None
        # phase == play
        if k in ("escape", "t"):
            return ("done", None)
        gk = self.gkey
        if gk == "hp":                       # read the bag's belly symbol, pick the match
            if k in ("up", "k", "left", "h"):           # the options stack vertically -> up/down
                self.hp_pick = (self.hp_pick - 1) % 3   # (left/right also work)
            elif k in ("down", "j", "right", "l"):
                self.hp_pick = (self.hp_pick + 1) % 3
            elif k in ("1", "2", "3"):
                self.hp_pick = int(k) - 1
                self._hp_resolve(self.hp_pick == self.hp_target)
            elif k in ("space", "enter"):
                self._hp_resolve(self.hp_pick == self.hp_target)
        elif gk == "data":                   # DVPet onShield: ONE button toggles the shield top<->bot.
            if not self.fired and k in ("space", "enter", "up", "down", "k", "j"):
                self.shield_up = not self.shield_up   # toggleable until the shot commits (onPreFinish)
        elif k == "space":                   # vaccine mash / virus stop
            self._strike()
        return None

    def _data_resolve(self):
        """The shot commits (DVPet checkSuccess: success = shieldActiveTop == isUp).  A block
        (shield matches the attack side) succeeds, else it gets through.  The shot then fires
        and lands -- attackGreen (fly) -> hitAnim (strobe) -> aftermathGreen (flinch) -- and
        the staged _finish (_impact_args) reveals the result once the flinch ends."""
        self.blocked = self.shield_up == self.tgt_up
        if self.blocked:
            self.flash = "BLOCKED!"
            self._impact_args = (3, 60, "Data", "data")
        else:
            self.flash = "hit you!"
            self._impact_args = (0, 0, "Data", "data")
        self.fired = True                                   # success LOCKED -> the shot fires (cosmetic)
        self.fly_t = DATA_FLY
        self.sfx = "attack"                                 # DVPet attackGreen turretShoot (cannon fires)

    def _flash(self, pose):
        """Briefly show a strike (6) or recoil (9) pose, like DVPet AttackSuccess/Fail."""
        self._strike_pose, self._strike_t = pose, 4
        if pose == 9:
            self.sfx = "cancel"                  # miss
        elif self.gkey == "vaccine":
            self.sfx = "scroll"                  # rapid mash -> short tick per tap
        else:
            self.sfx = "trainhit"                # discrete hit

    def _strike(self):
        gk = self.gkey
        if gk == "vaccine":
            self.taps += 1
            self.flash = f"{self.taps} hits!"
            self._flash(6)
        elif gk == "virus":
            v = int(self.pos)
            if v >= VIRUS_BAR_MIN:
                self._finish(3, v, "Virus", "virus")
            elif v >= 60:
                self._finish(2, v, "Virus", "virus")
            elif v >= 35:
                self._finish(1, v // 2, "Virus", "virus")
            else:
                self._finish(0, 0, "Virus", "virus")

    # ---- render ----
    def _frame(self, rec, idx):
        fr = rec["frames"]
        first = next((f for f in fr if f), fr[0])
        return (fr[idx] if idx < len(fr) and fr[idx] else first)

    def _pose_now(self, default):
        return self._strike_pose if self._strike_t > 0 else default

    def text(self):
        rec = data.load_sprites()[1][self.pet.num]
        if self.phase == "menu":
            return self._render_menu()
        if self.phase == "strike":
            return self._render_strike(rec)
        return self._render_play(rec)

    def _scene_palette(self):
        # the habitat background IS part of DVPet's layout -- show it during the strike (and
        # the vaccine/data drills).  The crisp sprites/explosion read fine over it now; only
        # the HP/virus minigames stay on a flat LCD (their own override) for readability.
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return on, bgimg

    def _render_play(self, rec):
        """The DVPet drills, rebuilt to match the real game with the real sprites:
          Vaccine: MASH the bag (bag LEFT, 'Hit!' label flashes, pet HIDDEN).
          Virus:   the power bar FILLS L->R; stop it in the zone (bar centred, pet HIDDEN).
          Data:    a FIXED cannon (left) fires a shot HIGH/LOW at the pet; raise the matching
                   shield (two slots in front of the pet RIGHT) to block it.  Defensive.
          HP:      read the bird bag's belly symbol, pick the matching attribute (bird LEFT,
                   pet RIGHT face-off; the picker glyphs live in the gauge) -- on a flat LCD."""
        gk = self.gkey
        E = data.load_effects()
        on, bgimg = self._scene_palette()
        ph = ARENA_ROWS * 2
        overlay = []
        placements = []

        if gk == "vaccine":                                 # DVPet drawVaccinePre: MASH to charge power.
            bag = E.get("punching_bag", [None])[0]           # the bag is the target; the pet is HIDDEN
            if bag:                                          # (it appears only for the strike).  The hit
                placements.append(_cell(bag, 0))             # bag in the LEFT grid cell, grounded 2px up
            if self._strike_t > 0:                           # drawn here.  Bag on the LEFT (DVPet ~locX 26),
                hit = E.get("train_hit", [None])[0]          # lined up with the strike's target side.
                if hit:                                      # the "Hit!" label (DVPet hitLabel) flashes per press
                    overlay.extend(_blit(hit, (COLS - len(hit[0])) // 2, 3))
        elif gk == "virus":                                 # DVPet drawVirusPre: pet AND bag HIDDEN
            # The real DVPet trainBar sprite is a 32-wide TRACK box (cols 0..31) + a separate
            # goal compartment (cols 32..37) == 38 wide.  Crop to the 32-wide track box so it
            # lands EXACTLY on the grid (x4..35) at NATIVE resolution -- no downscale (the old
            # _fit_width squashed the crisp box + dashes into glitch).  Fill = the native 30-wide
            # dashed trainBar, cropped to the level (1:1 with the 30px track interior, crisp).
            frame = E.get("train_bar_empty", [None])[0]      # only the power bar shows -- it FILLS
            fill = E.get("train_bar", [None])[0]             # L->R, loops 0->max, press to stop high
            if frame:
                frame = [row[:GRID_W] for row in frame]      # cols 0..31 = the track box (== the 32 grid)
            fh = len(frame) if frame else 5
            fx = GRID_X0                                     # track box on the grid's left edge (x4..35)
            fy = BASE_Y - fh                                 # grounded on the floor (2px above bottom)
            track_w = GRID_W - 2                             # interior between the box borders (30 == native fill width)
            if frame:
                overlay.extend(_blit(frame, fx, fy))
            if fill:                                         # REAL dashed trainBar, crisp, grows in the track
                fw_fill = max(len(r) for r in fill)
                w = max(0, min(fw_fill, track_w, round(track_w * min(self.pos, VIRUS_MAX) / VIRUS_MAX)))
                if w:
                    overlay.extend(_blit([row[:w] for row in fill], fx + 1, fy + 1))
            # target line: a 1px tick at the zone threshold (VIRUS_BAR_MIN) so you can see where to stop
            zx = fx + 1 + min(track_w - 1, int(track_w * VIRUS_BAR_MIN / VIRUS_MAX))
            overlay += [(zx, fy + y) for y in range(fh)]
        elif gk == "data":
            # Built like the VIRUS drill: the whole stage is CENTRED in the LCD (band-centred,
            # NOT jammed on the floor) over the same habitat bg.  Cannon LEFT, pet RIGHT, the
            # shield standing in front of the pet (high OR low), the shot flying between them.
            if self.strobe_t > 0:                            # COLLISION: clone DVPet hitAnim exactly --
                # resetScreen() then a CENTRED fullscreen flash strobing attackHit<->attackHitFlash.
                # Same render as the battle's hit (centred _EXPLODE), NOT a burst on the busy scene.
                ex = _EXPLODE[(self.strobe_t // EXPLODE_HOLD) % len(_EXPLODE)]
                overlay += _blit(ex, max(0, (COLS - len(ex[0])) // 2), max(0, (ph - len(ex)) // 2))
            else:
                aim_up = self.tgt_up if self.locked else self.feint_up
                cannon = E.get("train_green_up" if aim_up else "train_green", [None])[0]  # barrel aim only
                shield = E.get("train_shield", [None])[0]
                sh_h = len(shield) if shield else 6
                sw = len(shield[0]) if shield else 5
                ch = len(cannon) if cannon else 9
                if self.flinch_t > 0:                        # DVPet aftermathGreen: block -> the pet stands
                    pose = IDLE if self.blocked else COLLAPSE  # normal; a clean hit -> the hurt pose (+10)
                elif self.fired:                             # DVPet attackGreen: the pet braces for the shot
                    pose = IDLE
                else:                                        # DVPet drawDataPre bobs the pet (sprite 4<->1)
                    bob = 1 if (not self.locked and (self.frame_i // 2) % 2) else 0
                    pose = self._pose_now(bob)
                pf = self._frame(rec, pose)
                # the creature sprite is mostly empty padding -> crop to its real body so it can be
                # placed precisely (centred, hugged by the shields) instead of floating inside the box.
                _ys = [y for y, row in enumerate(pf) if "1" in row]
                _xs = [x for x in range(max(len(r) for r in pf))
                       if any(x < len(r) and r[x] == "1" for r in pf)]
                if _ys and _xs:
                    pf = [row[_xs[0]:_xs[-1] + 1] for row in pf[_ys[0]:_ys[-1] + 1]]
                pw = max(len(r) for r in pf)
                phh = len(pf)
                # Data layout, composed for tuipet's real estate (not a pixel-port -- our creature is a
                # tiny dot-matrix, DVPet's is a 48px giant): everything GROUNDED on the idle floor --
                # turret LEFT (barrel feints then commits high/low), pet RIGHT, and the two shields a
                # tight HIGH/LOW 2-stack (bottom directly under top) hugging the pet's front.  The two
                # orb lanes line up turret -> shields -> pet.  Raised side = SOLID, other = faint.
                cw = max(len(r) for r in cannon) if cannon else 10
                floor = BASE_Y                                     # the shared grid floor (2px above bottom)
                px = GRID_X0 + GRID_W - pw                          # pet's right edge on the grid's right edge (36)
                py = floor - phh                                   # sits on the ground, like idle gameplay
                cy = floor - ch                                    # turret grounded, level with the pet
                overlay.extend(_blit(cannon, DATA_MARGIN, cy))
                overlay.extend(_blit(pf, px, py))
                sx = px - sw - 1                                   # shields stand just in front of the pet
                lo_y = floor - sh_h                                # LOW guard grounded; HIGH guard stacked
                hi_y = lo_y - sh_h                                 # directly on top of it (one tight 2-stack)
                on_y = hi_y if self.shield_up else lo_y            # raised side = SOLID (trainShield)
                off_y = lo_y if self.shield_up else hi_y           # other side = faint (DVPet shieldTransp:
                if shield:                                         #   25% alpha -> a clean 1-in-4 dither)
                    overlay += [(sx + x, off_y + y) for y in range(sh_h) for x in range(sw)
                                if shield[y][x] == "1" and x % 2 == 0 and y % 2 == 0]
                    overlay.extend(_blit(shield, sx, on_y))
                if self.fired and self.fly_t > 0:                  # DVPet attackGreen: a SHORT hop from the
                    # muzzle in the committed lane (high=top shield row, low=bottom), pressing into the
                    # shield slot; then hitAnim's fullscreen flash plays (the orb never reaches the pet).
                    orb = data.load_orbs()["generic"]["Data"][0]   # DVPet spriteSheet[25]: generic Data orb
                    ow, oh = len(orb[0]), len(orb)
                    lane_top = hi_y if self.tgt_up else lo_y       # the lane follows the ATTACK (tgt_up)
                    lane_y = lane_top + sh_h // 2 - oh // 2         # orb centred on that shield row
                    mx, end_x = DATA_MARGIN + cw - 3, sx - ow + 3  # muzzle -> pressed against the shield
                    prog = (DATA_FLY - self.fly_t) / (DATA_FLY - 1)
                    overlay += _blit(orb, int(mx + (end_x - mx) * prog), lane_y)
        else:                                               # hp: a CLEAN tuipet face-off.
            # DVPet stacks 3 attribute icons vertically beside the pet; that doesn't survive the
            # drop to tuipet's 24px LCD (three 6px icons + a cursor box render as one black blob,
            # and the filled square icon reads as a wall).  So keep the ESSENCE, not the pixels:
            # the bird "battle bag" shows the round's target as a cutout symbol on its belly and
            # stands LEFT; the pet stands RIGHT; both GROUNDED on the floor like every other drill
            # (via render_scene placements), OVER THE HABITAT BACKGROUND like every other drill
            # (no flat-LCD override).  The player reads the belly and picks the matching attribute
            # from the crisp glyph strip in the gauge (● Vaccine / ■ Data / ▲ Virus).
            dummy = _HP_DUMMIES[("vaccine", "data", "virus")[self.hp_target]]
            pf = self._frame(rec, self._pose_now(0))
            placements = [_cell(dummy, 0),                              # bird bag LEFT cell, grounded
                          _cell(pf, 1)]                                 # pet RIGHT cell, grounded
        scene = render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        scene.append("\n")
        scene.append_text(self._gauge())
        scene.append_text(menu.footer(self._hint()))
        return scene

    def _gauge(self):
        """One compact status line under the arena, specific to the drill."""
        gk = self.gkey
        t = Text()
        if gk == "hp":
            t.append("match: ", style=INK)                     # crisp glyph picker (● Vaccine ■ Data ▲ Virus)
            for i, sym in enumerate(("●", "■", "▲")):
                sel = i == self.hp_pick
                t.append(f"[{sym}]" if sel else f" {sym} ", style=INK_B if sel else DIM)
            tb = int((max(self.round_t, 0) / max(self.round_len, 1)) * 9)
            t.append("  " + "▓" * tb + "░" * (9 - tb) + "\n", style=f"{ACCENT} on {LCD_BG}")
        elif gk == "vaccine":
            hit = self._strike_t > 0
            t.append("HIT!! " if hit else "hit!  ", style=INK_B if hit else INK)
            done = self.taps >= self.vaccine_target
            t.append(f"{self.taps}/{self.vaccine_target}  ", style=INK_B if done else INK)
            filled = int((max(self.timer, 0) / VACCINE_WINDOW) * 9)
            t.append("time " + "▓" * filled + "░" * (9 - filled) + "\n", style=f"{ACCENT} on {LCD_BG}")
        elif gk == "data":                                  # clean one-liner, like the virus gauge
            aim = ("CANNON HIGH!" if self.tgt_up else "CANNON LOW! ") if self.locked else "watch the aim..."
            t.append(aim, style=INK_B if self.locked else DIM)
            t.append(f"   shield {'UP' if self.shield_up else 'DOWN'}\n", style=INK)
        else:  # virus -- the bar is drawn in the LCD; the gauge just calls the zone
            inzone = int(self.pos) >= VIRUS_BAR_MIN
            t.append("IN THE ZONE - hit!" if inzone else "stop it in the zone", style=INK_B if inzone else INK)
            t.append(f"   {int(self.pos)}\n", style=INK)
        return t

    def _hint(self):
        return {"hp": "↑↓ pick   1/2/3 or SPACE to lock",
                "vaccine": "SPACE hit the orb!   ESC out",
                "data": "SPACE toggle the shield to match the cannon",
                "virus": "SPACE stop the marker in the zone"}[self.gkey]

    def _attr_pow(self):
        """The pet's power in the strike's attribute -> the orb tier (as the battle does)."""
        return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                "Virus": self.pet.virus}.get(self.strike_attr, 0)

    def _target_sprite(self, broken):
        """The thing being struck: the green target (Data drill) or the punching bag, which
        shows its BROKEN frame on a successful break (DVPet aftermathDefault).  Fit to the
        16px band so the strike animation sits in the same grid as the drill sprites."""
        E = data.load_effects()
        if self._is_data:
            return _fit_cell(E.get("train_green", [None])[0])   # no broken variant for the target
        return _fit_cell(E.get("punching_bag_broken" if broken else "punching_bag", [None])[0])

    def _strike_orb(self, leg, mouth, fr):
        """The pet's REAL orb (data.attack_orb) flying LEFT toward the target: off the near
        (left) edge on fire_out, in from the far (right) edge to the target's edge on fire_in.
        Mirrors battlescreen._orb_overlay (player fires left -> no flip)."""
        orb = data.attack_orb(self.pet.num, self.strike_attr, self._attr_pow())
        if not orb:
            return []
        w, h = len(orb[0]), len(orb)
        if leg == "out":                                        # leaves the mouth, off the near GRID edge
            x0, x1 = mouth - w, grid.X0 - w
        else:                                                   # arrives from the far GRID edge, stops at target
            x0, x1 = grid.X1, mouth
        x = int(x0 + (x1 - x0) * fr["prog"])
        if fr.get("double"):                                    # doubleAttack: BOTH orbs, top & bottom of band
            return _blit(orb, x, STRIKE_BAND_TOP) + _blit(orb, x, STRIKE_BAND_BOT - h)
        return _blit(orb, x, STRIKE_BAND_TOP + (16 - h) // 2)

    def _render_strike(self, rec):
        """A battle-style volley (battlescreen clone) with the TARGET in place of an enemy:
        ONE combatant on screen at a time.  windup -> the pet rears back; fire_out -> pose 6,
        the orb leaves off the near edge; fire_in -> the view switches to the TARGET as the orb
        arrives; hit -> the fullscreen explosion; break/miss -> the broken target / deflated pet.
        Pet stands RIGHT (faces left) and fires LEFT, exactly like the player in a battle."""
        fr = self.strike_tl[min(self.si, len(self.strike_tl) - 1)]
        m = fr["m"]
        on, bgimg = self._scene_palette()
        ph = ARENA_ROWS * 2
        overlay, placements, note = [], [], ""
        if m == "hit":                                          # fullscreen impact strobe, nothing else
            ex = _EXPLODE[fr["f"]]
            ox, oy = max(0, (COLS - len(ex[0])) // 2), max(0, (ph - len(ex)) // 2)
            overlay = _blit(ex, ox, oy)
            note = "HIT!"
        elif m in ("windup", "fire_out", "miss"):               # the PET is on screen (right, faces left)
            if m == "windup":
                pose = (TURN, TURN, IDLE, IDLE, CHARGE, CHARGE)[min(fr.get("wu", 0), 5)]
                xshift = min(3, fr.get("wu", 0) + 1)            # rear back toward the right wall
            elif m == "fire_out":
                pose = ATTACK
                xshift = -2 if fr["prog"] < 0.35 else 0         # lunge toward the target on release
            else:                                               # miss: deflated pose, DVPet getSpriteNum()+10
                pose, xshift = COLLAPSE, 0
            pet = self._frame(rec, pose)
            lo, hi = _cbounds(pet)
            x = _clamp_grid(((grid.X1 - 1) - hi) + xshift, lo, hi)   # pet's content right edge hugs the grid (x35), clamped
            placements = [(pet, x, False)]
            if m == "fire_out":
                overlay = self._strike_orb("out", x + lo, fr)   # mouth = the pet's left edge
            note = {"windup": "...", "fire_out": "Fire!", "miss": self.result}[m]
        else:                                                   # fire_in / break: the TARGET is on screen (left)
            tgt = self._target_sprite(m == "break")
            mouth = grid.X0 + 1
            if tgt:
                lo, hi = _cbounds(tgt)
                tx = grid.X0 - lo                               # target's content left edge hugs the grid (x4)
                placements = [(tgt, tx, False)]
                mouth = tx + hi + 1                             # the target's right edge, toward the pet
            if m == "fire_in":
                overlay = self._strike_orb("in", mouth, fr)
            note = "Incoming!" if m == "fire_in" else self.result
        scene = render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        scene.append("\n")
        scene.append_text(menu.note(note or "..."))
        scene.append_text(menu.footer(""))
        return scene

    def _render_menu(self):
        """DVPet drawTrainingSelect diamond, as a CLEAN text layout (crisp glyphs, not
        chunky pixel shapes): ● Vaccine top, ■ Data left, ▲ Virus right, ♥ HP bottom."""
        W = 34
        out = menu.header("TRAINING", "choose a drill")
        out.append_text(menu.blanks(1))

        def cell(gi, text):
            sel = gi == self.gi
            out.append(("▸" + text + "◂") if sel else (" " + text + " "),
                       style=(f"{ACCENT} on {LCD_BG}") if sel else INK_B)

        def centre(gi, text):
            pad = (W - (len(text) + 2)) // 2
            out.append(" " * pad, style=INK)
            cell(gi, text)
            out.append("\n")

        centre(1, "● Vaccine")                          # top
        out.append_text(menu.blanks(1))
        left, right = "■ Data", "▲ Virus"               # left + right row
        out.append("  ", style=INK)
        cell(2, left)
        out.append(" " * (W - 4 - (len(left) + 2) - (len(right) + 2)), style=INK)
        cell(3, right)
        out.append("\n")
        out.append_text(menu.blanks(1))
        centre(0, "♥ HP")                               # bottom
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(GAMES[self.gi][3]))
        out.append_text(menu.footer("↑●  ←■  →▲  ↓♥    ENTER start"))
        return out

    def _powerbar(self, pos):
        m = Text()
        m.append("[", style=INK)
        fill = int(pos / 100 * VBAR_W)
        needx = int(VIRUS_BAR_MIN / 100 * VBAR_W)
        for i in range(VBAR_W):
            if i == needx:
                m.append("|", style=INK_B)
            elif i < fill:
                m.append("█", style=f"{ACCENT} on {LCD_BG}")
            else:
                m.append("─", style=f"{MID} on {LCD_BG}")
        m.append("]", style=INK)
        return m
