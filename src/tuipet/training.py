"""Training — DVPet's four drills, faithful to the SpriteAnim training states
(Vaccine_Training / Data_Training / Virus_Training / HP_Training -> Attacking ->
Attack_Contact -> Attack_Aftermath).

Every drill is fought against an on-screen OPPONENT that is present the whole time
-- the punching bag (HP / Vaccine / Virus) or the green pop-up target (Data) -- and
the skill phase flows straight into the strike -> impact -> aftermath, exactly like
the hardware (no abstract gauge with the opponent conjured up only at the end):

  HP    — pet RIGHT, bag LEFT: guess which of 3 attributes the hidden bag is,
          best of 3 (drawHPTraining); builds Effort.
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
from .render import render_scene
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, MID, ACCENT, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
# the post-drill strike CLONES the battle screen's alternating-view volley (one combatant
# on screen at a time: pet rears back & fires the real orb off the near edge -> view switches
# to the TARGET as the orb arrives -> fullscreen explosion -> break).  Reuse the battle's
# pose ids + beat timings + column-bounds helper so the two stay in lockstep.
from .battlescreen import (IDLE, TURN, ATTACK, CHARGE, COLLAPSE,  # noqa: F401
                           WINDUP_T, FIRE_T, EXPLODE_FRAMES, EXPLODE_HOLD, FLINCH_T,
                           _cbounds)

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
DATA_MARGIN = 2               # the data stage's side margin: cannon/pet anchor inside this, never the edge
DATA_FLY = 3                  # the committed shot's flight to the target (DVPet attackGreen: 3 intervals)
DATA_IMPACT = 6               # the shot's impact flash (DVPet hitAnim: attackHit/Flash strobe, ~6 frames)
HP_ROUNDS = 3
HP_ROUNDS_WON = 2
HP_ROUND_LEN = 28             # ticks to pick before a round times out (~2.8s)
VBAR_W = 24

COLS = 40
ARENA_ROWS = 12               # the app's ONE locked LCD area (== app SCREEN_ROWS / battle ROWS).
                              # DVPet's native LCD is 105x60px; tuipet shows it at 40x24 everywhere.

# strike sequence: a battle-style volley (windup -> fire_out -> fire_in -> hit -> break),
# beats imported from the battle screen so they march at the same pace.  The orb rides the
# lower 16px creature band, recomputed for the training arena's own height.
STRIKE_BAND_TOP = ARENA_ROWS * 2 - 18    # == battle BAND_TOP, relative to this LCD's height
STRIKE_BAND_BOT = ARENA_ROWS * 2 - 2

# the attribute symbols (DVPet: Vaccine=orb/red, Data=block/green, Virus=dart/yellow)
# -> circle / square / triangle.
ATTR_SYM = ["●", "■", "▲"]   # ● ■ ▲  (Vaccine / Data / Virus) for the HP-drill guess


def _blit(bm, ox, oy):
    """Sprite bitmap -> (x,y) pixel list for render_scene's overlay (projectile / flash)."""
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


# The REAL DVPet attribute icons, extracted 1:1 from the game's red/green/yellow.png
# (SpriteAnim _vaccineAttack/_dataAttack/_virusAttack) -- circle/square/triangle, each
# with DVPet's top-left highlight pixel.  'big' = native 14x14, 'small' = 7x7.  NOT
# hand-drawn -- pulled from the source art.
with open(os.path.join(os.path.dirname(__file__), "data", "attr_icons.json")) as _f:
    _ATTR_ICONS = json.load(_f)        # {'big': [v,d,v], 'small': [v,d,v]}  order Vaccine/Data/Virus

# The REAL DVPet HP training dummy -- the bird "battle bag" (battleBags.png frames 0/2/4)
# that holds the attribute symbol on its belly.  This is the "image on the training dummy"
# the player reads and matches.  Extracted 1:1 from the source art.
with open(os.path.join(os.path.dirname(__file__), "data", "hp_dummies.json")) as _f:
    _HP_DUMMIES = json.load(_f)         # {'vaccine','data','virus'} -> 1-bit bird w/ belly symbol


def _box(w, h):
    """Hollow 1-bit rectangle -- the HP-drill cursor framing the picked attribute."""
    return ["1" * w if y in (0, h - 1) else "1" + "0" * (w - 2) + "1" for y in range(h)]


def _plus_glyph(h=9):
    """A plus/cross for the HP option (health = +)."""
    t = h // 3
    return ["1" * h if t <= y < h - t else "0" * t + "1" * (h - 2 * t) + "0" * t
            for y in range(h)]


_HP_GLYPH = _plus_glyph()


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
        self.round_t = HP_ROUND_LEN
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
        self.impact_t = 0            # DVPet hitAnim countdown: the shot's impact flash plays out
        self._impact_args = None     # the staged _finish() call, fired when the flash ends
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

    def _new_hp_round(self):
        self.hp_target = random.randrange(3)
        self.hp_pick = 0
        self.round_t = HP_ROUND_LEN
        self.flash = f"round {self.rep + 1}/{HP_ROUNDS} — which attribute?"

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
                if self.fly_t > 0:                          # finale is cosmetic.  DVPet attackGreen: the
                    self.fly_t -= 1                          # committed shot flies to the shield/pet...
                    if self.fly_t == 0:
                        self.sfx = "attackHit"               # ...DVPet hitAnim: it lands
                        self.impact_t = DATA_IMPACT
                    return
                if self.impact_t > 0:                        # the impact flash strobes, THEN aftermathGreen
                    self.impact_t -= 1                       # reveals the result
                    if self.impact_t == 0:
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
        if gk == "hp":                       # pick which attribute the bag is, then guess
            if k in ("left", "h"):
                self.hp_pick = (self.hp_pick - 1) % 3
            elif k in ("right", "l"):
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
        """The shot lands (DVPet checkSuccess: success = shieldActiveTop == isUp).  A block
        (shield matches the attack side) succeeds, else it gets through.  Either way the
        impact flash (DVPet hitAnim) plays, THEN the result is revealed -- the _finish is
        staged in _impact_args and fired once impact_t counts down."""
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
          HP:      read the dummy's attribute, pick the matching icon (dummy LEFT, icons MID,
                   pet RIGHT) -- on a flat LCD."""
        gk = self.gkey
        E = data.load_effects()
        on, bgimg = self._scene_palette()
        ph = ARENA_ROWS * 2
        overlay = []

        if gk == "vaccine":                                 # DVPet drawVaccinePre: MASH to charge power.
            bag = E.get("punching_bag", [None])[0]           # the bag is the target; the pet is HIDDEN
            if bag:                                          # (it appears only for the strike).  The hit
                overlay.extend(_blit(bag, 6, ph - len(bag)))  # button is a DEVICE button (off-LCD) -> not
            if self._strike_t > 0:                           # drawn here.  Bag on the LEFT (DVPet ~locX 26),
                hit = E.get("train_hit", [None])[0]          # lined up with the strike's target side.
                if hit:                                      # the "Hit!" label (DVPet hitLabel) flashes per press
                    overlay.extend(_blit(hit, (COLS - len(hit[0])) // 2, 3))
        elif gk == "virus":                                 # DVPet drawVirusPre: pet AND bag HIDDEN
            frame = E.get("train_bar_empty", [None])[0]      # only the power bar shows -- it FILLS
            fill = E.get("train_bar", [None])[0]             # L->R, loops 0->100, press to stop high
            fw = len(frame[0]) if frame else 38
            fh = len(frame) if frame else 5
            fx = (COLS - fw) // 2                            # REAL trainBarEmpty, centred over the habitat
            fy = (ph - fh) // 2
            if frame:
                overlay.extend(_blit(frame, fx, fy))
            if fill:                                         # REAL dashed trainBar, grows in the main box
                w = max(0, min(30, round(30 * min(self.pos, VIRUS_MAX) / VIRUS_MAX)))
                if w:
                    overlay.extend(_blit([row[:w] for row in fill], fx + 1, fy + 1))
            if int(self.pos) >= VIRUS_BAR_MIN:               # front in the zone -> the goal box lights
                overlay += [(fx + 32 + x, fy + 1 + y) for y in range(3) for x in range(5)]
        elif gk == "data":
            # Built like the VIRUS drill: the whole stage is CENTRED in the LCD (band-centred,
            # NOT jammed on the floor) over the same habitat bg.  Cannon LEFT, pet RIGHT, the
            # shield standing in front of the pet (high OR low), the shot flying between them.
            aim_up = self.tgt_up if self.locked else self.feint_up
            cannon = E.get("train_green_up" if aim_up else "train_green", [None])[0]   # barrel aim only
            shield = E.get("train_shield", [None])[0]
            sh_h = len(shield) if shield else 6
            sw = len(shield[0]) if shield else 5
            cw = len(cannon[0]) if cannon else 10
            ch = len(cannon) if cannon else 9
            if self.impact_t > 0:                            # DVPet aftermathGreen: block -> the pet stands
                pose = IDLE if self.blocked else COLLAPSE    # normal; a clean hit -> the hurt pose (+10)
            elif self.fired:                                 # DVPet attackGreen: pet braces for the shot
                pose = IDLE
            else:                                            # DVPet drawDataPre bobs the pet (sprite 4<->1)
                bob = 1 if (not self.locked and (self.frame_i // 2) % 2) else 0
                pose = self._pose_now(bob)
            pf = self._frame(rec, pose)
            pw = max(len(r) for r in pf)
            pet_h = len(pf)
            band_top = (ph - pet_h) // 2                     # CENTRE the stage vertically (like virus)
            floor = band_top + pet_h                         # the shared baseline of the centred band
            px = COLS - pw - DATA_MARGIN                     # pet RIGHT, inside the margin
            overlay.extend(_blit(pf, px, floor - pet_h))
            overlay.extend(_blit(cannon, DATA_MARGIN, floor - ch))   # cannon LEFT, same baseline
            muzzle_x, muzzle_y = DATA_MARGIN + cw, floor - ch + 1
            sx = px - sw - 1                                 # the shield stands just in front of the pet
            hi_y = band_top + 1                              # high slot = top of the centred band
            lo_y = floor - sh_h - 1                          # low  slot = bottom of the centred band
            on_y = hi_y if self.shield_up else lo_y          # the raised shield = SOLID (trainShield)
            off_y = lo_y if self.shield_up else hi_y          # the other slot = a faint dotted ghost
            if shield:
                overlay += [(sx + x, off_y + y) for y in range(sh_h) for x in range(sw)
                            if shield[y][x] == "1" and (x + y) % 2 == 0]   # dotted = DVPet shieldTransp
                overlay.extend(_blit(shield, sx, on_y))
            if self.fired and self.impact_t == 0:            # DVPet attackGreen: the shot flies muzzle ->
                orb = data.attack_orb(self.pet.num, "Data", self.pet.data_power)   # the committed slot
                ow, oh = len(orb[0]), len(orb)
                blocked = self.shield_up == self.tgt_up
                end_x = (sx - ow) if blocked else (px - ow)
                lane_y = (hi_y if self.tgt_up else lo_y) + (sh_h - oh) // 2
                prog = (DATA_FLY - self.fly_t) / DATA_FLY
                fx = int(muzzle_x + (end_x - muzzle_x) * prog)
                fy = int((muzzle_y - oh // 2) + (lane_y - (muzzle_y - oh // 2)) * prog)
                overlay += _blit(orb, fx, fy)
            if self.impact_t > 0:                            # DVPet hitAnim: the impact flash at the slot
                ex = _EXPLODE[self.impact_t % len(_EXPLODE)]
                lane_y = (hi_y if self.tgt_up else lo_y)
                ix = min(max(0, sx + sw // 2 - len(ex[0]) // 2), COLS - len(ex[0]))
                iy = min(max(0, lane_y + sh_h // 2 - len(ex) // 2), ph - len(ex))
                overlay += _blit(ex, max(0, ix), iy)
        else:                                               # hp: the REAL DVPet drawHPTraining layout
            # Training dummy (bird w/ an attribute symbol on its belly) on the LEFT, the 3
            # stacked icons (Vaccine/Data/Virus) in the MIDDLE, the pet on the RIGHT.  Read
            # the dummy's belly symbol, click the matching icon.  Clean flat LCD (no photo).
            on, bgimg = LCD_ON, None
            dummy = _HP_DUMMIES[("vaccine", "data", "virus")[self.hp_target]]
            overlay.extend(_blit(dummy, 1, ph - len(dummy)))            # dummy LEFT, baseline
            for i in range(3):                              # the 3 stacked guess icons (real ● ■ ▲)
                iy = i * 8                                   # 6px icon + 2px gap = exact 22px fit
                overlay.extend(_blit(_ATTR_ICONS["small"][i], 19, iy))
                if i == self.hp_pick:                       # cursor frame around the current guess
                    overlay.extend(_blit(_box(8, 8), 18, iy - 1))
            pf = self._frame(rec, self._pose_now(0))        # the pet RIGHT
            overlay.extend(_blit(pf, COLS - max(len(r) for r in pf) - 1, ph - len(pf)))
        scene = render_scene([], COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        scene.append("\n")
        scene.append_text(self._gauge())
        scene.append_text(menu.footer(self._hint()))
        return scene

    def _gauge(self):
        """One compact status line under the arena, specific to the drill."""
        gk = self.gkey
        t = Text()
        if gk == "hp":
            t.append("match the dummy  ", style=INK)
            t.append(ATTR_SYM[self.hp_target], style=INK_B)        # the attribute the dummy shows
            tb = int((max(self.round_t, 0) / HP_ROUND_LEN) * 9)
            t.append("   time " + "▓" * tb + "░" * (9 - tb) + "\n", style=f"{ACCENT} on {LCD_BG}")
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
        return {"hp": "←→ match the symbol   SPACE strike",
                "vaccine": "SPACE hit the orb!   ESC out",
                "data": "SPACE toggle the shield to match the cannon",
                "virus": "SPACE stop the marker in the zone"}[self.gkey]

    def _attr_pow(self):
        """The pet's power in the strike's attribute -> the orb tier (as the battle does)."""
        return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                "Virus": self.pet.virus}.get(self.strike_attr, 0)

    def _target_sprite(self, broken):
        """The thing being struck: the green target (Data drill) or the punching bag, which
        shows its BROKEN frame on a successful break (DVPet aftermathDefault)."""
        E = data.load_effects()
        if self._is_data:
            return E.get("train_green", [None])[0]              # no broken variant for the target
        return E.get("punching_bag_broken" if broken else "punching_bag", [None])[0]

    def _strike_orb(self, leg, mouth, fr):
        """The pet's REAL orb (data.attack_orb) flying LEFT toward the target: off the near
        (left) edge on fire_out, in from the far (right) edge to the target's edge on fire_in.
        Mirrors battlescreen._orb_overlay (player fires left -> no flip)."""
        orb = data.attack_orb(self.pet.num, self.strike_attr, self._attr_pow())
        if not orb:
            return []
        w, h = len(orb[0]), len(orb)
        if leg == "out":                                        # leaves the mouth, off the near edge
            x0, x1 = mouth - w, -w
        else:                                                   # arrives from the far edge, stops at target
            x0, x1 = COLS, mouth
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
            x = ((COLS - 2) - hi) + xshift
            placements = [(pet, x, False)]
            if m == "fire_out":
                overlay = self._strike_orb("out", x + lo, fr)   # mouth = the pet's left edge
            note = {"windup": "...", "fire_out": "Fire!", "miss": self.result}[m]
        else:                                                   # fire_in / break: the TARGET is on screen (left)
            tgt = self._target_sprite(m == "break")
            mouth = 2
            if tgt:
                lo, hi = _cbounds(tgt)
                tx = 1 - lo
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
