"""Training — DVPet's four drills, faithful to the SpriteAnim training states
(Vaccine_Training / Data_Training / Virus_Training / HP_Training -> Attacking ->
Attack_Contact -> Attack_Aftermath).

Every drill is fought against an on-screen OPPONENT that is present the whole time
-- the punching bag (HP / Vaccine / Virus) or the sparring partner (Data) -- and
the skill phase flows straight into the strike -> impact -> aftermath, exactly like
the hardware (no abstract gauge with the opponent conjured up only at the end):

  HP    — the round's target attribute shows LEFT (big icon), 3 pickable option
          icons MIDDLE, pet RIGHT: read the symbol, pick the match, best of 3
          (drawHPTraining, first to 2 wins); builds Effort.
  Vaccine — pet HIDDEN, bag on screen: mash the hit button (drawVaccinePre);
          builds Vaccine power.  Pet appears for the strike.
  Data  — the REAL DM20's versus training (canon rebuild 2026-07-13; DVPet's
          turret duel here was pure fan invention -- Joel: "i dont think this
          system is canon at all", and it isn't).  Manual: "you choose to fire
          a high shot or a low shot.  If your shot gets past your partner's
          shield, you succeed.  You need to succeed 3 out of the 5 rounds."
  Virus — pet HIDDEN, bag on screen: stop the sweeping power bar high
          (drawVirusPre); builds Virus power.

The stat outcome stays in Pet.apply_training; this module is the presentation.
"""
from __future__ import annotations
import json
import os
import random
from . import data
from . import grid
from . import strikefx
from .render import render_scene
from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, MID, ACCENT, SIL_DAY, SIL_NIGHT  # noqa: F401  (palette names bound for theme.apply propagation)
from . import menu
# the post-drill strike CLONES the battle screen's alternating-view volley (one combatant
# on screen at a time: pet rears back & fires the real orb off the near edge -> view switches
# to the TARGET as the orb arrives -> fullscreen explosion -> break).  Reuse the battle's
# pose ids + beat timings + column-bounds helper so the two stay in lockstep.
from .battlescreen import (IDLE, TURN, ATTACK, CHARGE, COLLAPSE,  # noqa: F401
                           EXPLODE_FRAMES, EXPLODE_HOLD, FLINCH_T, FIRE_T)

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
# Data is the REAL DM20's VERSUS training (humulos.com/digimon/dm20/manual): "you choose
# to fire a high shot or a low shot.  If your shot gets past your partner's shield, you
# succeed.  You need to succeed 3 out of the 5 rounds for training to be successful."
# The partner's shield follows the manual's REPEATING PATTERN -- "pressing the buttons
# according to the chart below will let you win tag training every time" -- the six
# winning-button rows ported VERBATIM (5 rounds each, sessions cycle 1..6 and repeat,
# indexed by the pet's stage_trainings so the cheat chart works like the hardware).
# The manual never says which of A/B fires high; tuipet reads A=HIGH (adaptation, the
# one unspecified bit) -- the shield therefore stands OPPOSITE each winning shot.
DATA_ROUNDS = 5               # rounds per session (manual: "3 out of the 5 rounds")
DATA_PASS = 3                 # shots that must get past for a successful training
DATA_WIN_CHART = ("ABABB", "BBAAB", "BAABB", "ABBAA", "BABAB", "ABABA")   # manual, verbatim
DATA_BLOCK_HOLD = 4           # beats the blocked tableau holds before the next round
#  collision = the battle's exact beats: EXPLODE_FRAMES strobe (hitAnim) on a shot that gets past
HP_ROUNDS = 3                 # DVPet _hpTrainingRounds
HP_ROUNDS_WON = 2             # DVPet _hpTrainingRoundsWon (first to 2 wins the drill)
HP_TRAIN_DIFFICULTY = 11      # DVPet _hpTrainDifficultyChange: rank = fullHealthPoints // 11
HP_SCROLL = (8, 6, 4)         # ticks between reel steps by rank -- the drill REDO (Joel
#                               2026-07-06): the selector auto-scrolls under the target in
#                               the LCD and SPACE stops it on the match; the message box
#                               is a status strip again, never a gaming area
HP_ROUND_LEN = (60, 50, 40)   # ticks/round by rank (Easy/Normal/Hard).  DVPet shrinks this with HP,
                              # but at tuipet's 10Hz that left only ~1s/round on a grown pet (you
                              # couldn't move + lock after round 1) -- floored generous: 6/5/4s.

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


# drill sprite helpers -- thin aliases over the shared grid module (single source of truth)
def _fit_cell(sprite):
    """Cap a sprite to the 16px band height so it fits the grid like the 16x16 creatures."""
    return grid.fit_band(sprite)


from .render import blit as _blit    # one blit for app/training/strikefx (refactor 2026-07-05)


def _pop(overlay, ink):
    """Layer `ink` on TOP of the staged overlay: punch a 1px clearance halo
    out of everything already under it, then add the ink.  On a 1-bit LCD
    adjacency IS fusion -- the halo is how a foreground actor (a held shield,
    a flying pellet) reads as its own object over a busy stage.  Occlusion,
    not art: no sprite's pixels change, the back actor is just behind."""
    guard = {(x + dx, y + dy) for x, y in ink
             for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    return [pt for pt in overlay if pt not in guard] + list(ink)


def _crop(pf):
    """Crop a creature frame to its real body (the sheets are mostly padding) so
    the drills can place it on exact columns.  Shared by vaccine/data/hp."""
    ys = [y for y, row in enumerate(pf) if "1" in row]
    xs = [x for x in range(max(len(r) for r in pf))
          if any(x < len(r) and r[x] == "1" for r in pf)]
    if ys and xs:
        return [row[xs[0]:xs[-1] + 1] for row in pf[ys[0]:ys[-1] + 1]]
    return pf


# The REAL DVPet HP training dummy -- the "battle bag" figure on a stand (battleBags.png top row,
# the clean frames DVPet's getBattleBagSprite maps as Vaccine=circle / Virus=triangle / Data=square).
with open(os.path.join(os.path.dirname(__file__), "data", "hp_dummies.json")) as _f:
    _HP_DUMMIES = json.load(_f)         # {'vaccine','virus','data'} -> 1-bit training dummy w/ belly symbol

# HP target symbol: the dummy's belly cutout is illegible at this scale (all three look the
# same), so the round's target attribute is shown as a CLEAR icon -- the real DVPet attribute
# symbol (atk_vaccine=circle / atk_data=square / atk_virus=triangle, 7x7) stacked in the LCD.
_HP_ICON_KEYS = ("atk_vaccine", "atk_data", "atk_virus")   # index == hp_target (0/1/2)
# (HP_SYMS picker glyphs retired with the reel redo 2026-07-06 -- the real icons stack in the LCD)


GAMES = [
    ("hp",      "HP Drill", "Effort",  "stop the reel on the match"),
    ("vaccine", "Vaccine",  "Vaccine", "mash the bag — fast!"),
    ("data",    "Data",     "Data",    "beat the shield — 3 of 5"),
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
        self.rep = 0
        self.hits = 0
        self.power = 0
        self.taps = 0
        self.timer = VACCINE_WINDOW
        self.vaccine_target = VACCINE_HITS[1]   # rank-based, set per drill start (below)
        self.virus_speed = VIRUS_SPEEDS[1]      # rank-based bar fill speed
        self.round_len = HP_ROUND_LEN[1]
        self.round_t = self.round_len
        self.rounds_won = 0
        self.hp_target = 0           # hidden attribute the bag "is" (0/1/2)
        self.hp_pick = 0             # the player's cursor over the 3 guess buttons
        # data versus-training state (real DM20 tag training)
        self.tt_round = 0            # current round, 0..DATA_ROUNDS-1
        self.tt_past = 0             # shots that got past the shield so far
        self.tt_log = []             # per-round outcomes (True = past), for the strip pips
        self.tt_shield = ()          # the partner's 5-lane chart row (True = shield HIGH)
        self.tt_shield_up = False    # this round's revealed shield lane (set on fire)
        self.shot_up = False         # the lane the player fired
        self.blocked = False         # this round's outcome
        self.fired = False           # a shot is playing out (the round's volley timeline runs)
        self.tt_tl = []              # the round's beat timeline (fire_out/fire_in/hit|block)
        self.tt_i = 0                # index into tt_tl
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
        # onPreTrain -> canExercise -> checkRefused: a non-compliant pet may blow
        # off the drill (its own attribute obeys while spirited)
        # canExercise passes the drill's attribute; the HP drill is att=None ->
        # the activity branch (canon: `att != None ? (null,att,...) : (null,null,true..)`)
        attr = GAMES[self.gi][2] if GAMES[self.gi][2] in ("Vaccine", "Data", "Virus") else None
        if self.pet.check_refused(attr=attr):
            # canon onPreTrain: !canExercise -> _currentMenu = Menu.None + State.Refusing --
            # the menu CLOSES and the pet head-shakes on the main LCD.  (The old silent
            # stay-in-menu made a refusal look like a dead drill.)
            self.pet._set_anim("refuse", 1.0)
            self.sfx = "refuse"
            return ("done", f"{self.pet.name} refuses to train!")
        self.phase = "play"
        self._reset()
        gk = self.gkey
        if gk == "hp":
            self._new_hp_round()
        elif gk == "vaccine":
            self.vaccine_target = self._vaccine_threshold()
            self.flash = "MASH the bag!"
        elif gk == "data":
            # the partner's shield lanes for THIS session: the manual's repeating
            # chart row, cycled by lifetime drills this stage (the printed cheat
            # sequences work on tuipet exactly as on the hardware).  The row lists
            # WINNING shots (A=HIGH); the shield stands in the opposite lane.
            row = DATA_WIN_CHART[self.pet.stage_trainings % len(DATA_WIN_CHART)]
            self.tt_shield = tuple(c == "B" for c in row)   # win LOW -> shield was HIGH
            self.flash = f"round 1/{DATA_ROUNDS} — UP high · DOWN low"
        else:
            self.virus_speed = VIRUS_SPEEDS[self._attr_rank(self.pet.virus)]
            self.flash = "stop the bar high!"

    def _hp_round_len(self):
        """DVPet drawHPTraining: the per-round timer shrinks as the pet's battle
        HP grows (rank = fullHealthPoints // _hpTrainDifficultyChange).  Battle
        HP is the TRAINED full_health (perfect wins / HP chips), so the drill
        genuinely gets harder as you master it."""
        full_hp = getattr(self.pet, "full_health", 0) or 10
        return HP_ROUND_LEN[min(full_hp // HP_TRAIN_DIFFICULTY, 2)]

    def _new_hp_round(self):
        self.hp_target = random.randrange(3)
        # the reel never STARTS on the match (a round-open SPACE would be a
        # free win); it lands there on its own -- that's the timing skill
        self.hp_pick = (self.hp_target + random.choice((1, 2))) % 3
        rank = min((getattr(self.pet, "full_health", 0) or 10) // HP_TRAIN_DIFFICULTY, 2)
        self.hp_scroll = HP_SCROLL[rank]
        self.hp_scroll_t = self.hp_scroll
        self.round_len = self._hp_round_len()
        self.round_t = self.round_len
        self.flash = f"round {self.rep + 1}/{HP_ROUNDS} — SPACE on the match"

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
        if game == "data":
            # DATA already played its five volleys IN the drill (every round is a
            # full fire -> reveal -> impact beat) -- a sixth would be noise.  Reveal.
            self.phase = "done"
            self.flash = self.result + "   (SPACE)"
        else:
            # hp / vaccine / virus: after the skill phase the pet fires its orb at the target
            # (the SAME battle volley for all three) -> hit (success) or miss -> reveal the score.
            self.strike_attr = attribute or ("Vaccine", "Data", "Virus")[self.hp_target]
            self._build_strike()
            self.phase = "strike"
            self.flash = ""

    def _build_strike(self):
        """The pet's attack volley -- the SAME animation the battle screen fires (strikefx),
        with the training target in place of an enemy."""
        self.strike_tl = strikefx.build_volley(self.success, self._strong)
        self.si = 0
        self._last_sm = None

    def _strike_sfx(self):
        """One-shot beep at each strike-beat edge -- launch sting, then the impact."""
        m = self.strike_tl[self.si].get("m")
        if m != self._last_sm:
            s = strikefx.beat_sfx(m, self._strong)
            if s:
                self.sfx = s
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
            self.hp_scroll_t -= 1
            if self.hp_scroll_t <= 0:                       # the reel turns on its own
                self.hp_scroll_t = self.hp_scroll
                self.hp_pick = (self.hp_pick + 1) % 3
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
            if not self.fired:                              # the PICK act waits on the player --
                return                                      # turn-based, like the HP reel's stop
            if self.tt_i < len(self.tt_tl) - 1:             # the round's volley marches, beat by beat
                self.tt_i += 1
                m = self.tt_tl[self.tt_i]["m"]
                if m != self._last_sm:                      # one-shot sting at each beat edge
                    if m == "hit":
                        self.sfx = "attackHit"               # DVPet hitAnim: it got PAST
                    elif m == "block":
                        self.sfx = "cancel"                  # dead on the shield
                self._last_sm = m
            else:
                self._data_next_round()
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
            # tuipet's ONE picker grammar (the habitat/egg convention): arrows
            # browse the ring, digits jump, ENTER starts.  (The old up/left/
            # right/down diamond was DVPet's drawTrainingSelect mouse layout --
            # canon menu polish 2026-07-13.)
            if k in ("left", "h", "up", "k"):
                self.gi = (self.gi - 1) % len(GAMES)
            elif k in ("right", "l", "down", "j"):
                self.gi = (self.gi + 1) % len(GAMES)
            elif k in ("1", "2", "3", "4"):
                self.gi = int(k) - 1
                return self._start_game()          # a refusal closes the menu (canon)
            elif k in ("enter", "space"):
                return self._start_game()
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
        if gk == "hp":                       # the reel spins itself: SPACE stops it on the match
            if k in ("space", "enter"):
                self._hp_resolve(self.hp_pick == self.hp_target)
        elif gk == "data":                   # DM20 versus training: A/B = fire high or low
            if not self.fired and k in ("up", "k"):
                self._data_fire(True)
            elif not self.fired and k in ("down", "j"):
                self._data_fire(False)
        elif k == "space":                   # vaccine mash / virus stop
            self._strike()
        return None

    def _data_fire(self, up):
        """The player's shot commits (DM20 manual: past = the partner's shield stood
        in the OTHER lane).  The round plays out in the battle's alternating-view
        volley grammar: fire_out (the mon looses its real orb) -> fire_in (cut to
        the partner -- the shield lane REVEALS, the orb arrives) -> the fullscreen
        hit strobe (past) or the blocked tableau."""
        self.shot_up = up
        self.tt_shield_up = self.tt_shield[self.tt_round]
        self.blocked = (up == self.tt_shield_up)
        ft = max(3, FIRE_T // 2)                 # the battle's flight halved: five rounds
        #                                          per session need a brisker volley
        tl = [{"m": "fire_out", "prog": (s + 1) / ft} for s in range(ft)]
        tl += [{"m": "fire_in", "prog": (s + 1) / ft} for s in range(ft)]
        if self.blocked:
            tl += [{"m": "block"}] * DATA_BLOCK_HOLD
        else:
            tl += [{"m": "hit", "f": (s // EXPLODE_HOLD) % 2} for s in range(EXPLODE_FRAMES)]
        self.tt_tl, self.tt_i = tl, 0
        self.fired = True
        self._last_sm = "fire_out"
        self.sfx = "attack"
        self.flash = "HIGH!" if up else "LOW!"

    def _data_next_round(self):
        """Score the round, then the next pick -- or the session verdict (manual:
        "You need to succeed 3 out of the 5 rounds")."""
        past = not self.blocked
        self.tt_log.append(past)
        if past:
            self.tt_past += 1
        # the family's hit/miss tell rides the next act (pose only -- the round's
        # own sting already played at the hit/block beat, no double beep)
        self._strike_pose, self._strike_t = (6 if past else 9), 4
        self.tt_round += 1
        self.fired = False
        self._last_sm = None
        if self.tt_round >= DATA_ROUNDS:
            p = self.tt_past                 # canon pass = 3 of 5; graded around that line
            hits = 3 if p >= DATA_ROUNDS else 2 if p >= DATA_PASS else 1 if p >= 1 else 0
            self._finish(hits, p * 20, "Data", "data")
        else:
            self.flash = f"round {self.tt_round + 1}/{DATA_ROUNDS} — UP high · DOWN low"

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
        # .get: an egg (num -1) has no roster sheet -- the panel is gated by
        # can_train, but a raw [num] here CRASHED on direct construction, the
        # habitat-crash pattern (egg-training audit 2026-07-06); the placeholder
        # record keeps every drill renderable if a future path ever slips one in
        rec = (data.load_sprites()[1].get(self.pet.num)
               or {"frames": [data.bob_frame(self.pet.num, self.frame_i,
                                             egg_type=getattr(self.pet, "egg_type", 0))
                              or [""]] * 12})
        if self.phase == "menu":
            return self._render_menu()
        if self.phase == "strike":
            return self._render_strike(rec)
        if self.phase == "done":
            return self._render_done(rec)
        return self._render_play(rec)

    def _render_done(self, rec):
        """DVPet aftermath (aftermathDefault / aftermathGreen): the pet stands in its NORMAL pose
        beside the BROKEN target on success, or in the HURT pose (sprite +10) beside the intact
        target on a fail -- understated, NOT a cheer.  The happy/sad reaction plays back on the
        main view (apply_training _set_anim).  SPACE returns to the main view."""
        on, bgimg = self._scene_palette()
        pf = self._frame(rec, IDLE if self.success else COLLAPSE)   # normal / hurt(+10), like DVPet
        tgt = self._target_sprite(self.success)                     # broken target on success (bag drills)
        placements = (grid.faceoff(tgt, pf, left_mirror=self._target_mirror())
                      if tgt else [grid.center(pf)])   # target + pet face each other (props keep sheet facing)
        # scene-only: the result + controls ride the strip (box-clip audit 2026-07-04)
        return render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, bgimg=bgimg, clip=grid.WINDOW)

    def _scene_palette(self):
        # the habitat background IS part of DVPet's layout -- show it during the strike (and
        # the vaccine/data drills).  The crisp sprites/explosion read fine over it now; only
        # the HP/virus minigames stay on a flat LCD (their own override) for readability.
        bgimg = self.pet.background()
        return menu.scene_ink(bgimg), bgimg

    def _render_play(self, rec):
        """The DVPet drills, rebuilt to match the real game with the real sprites:
          Vaccine: MASH the bag (bag LEFT, 'Hit!' label flashes, pet HIDDEN).
          Virus:   the power bar FILLS L->R; stop it in the zone (bar centred, pet HIDDEN).
          Data:    the REAL DM20 versus training -- fire HIGH/LOW past the sparring
                   partner's shield, 3 of 5 rounds (the fan turret is gone).
          HP:      read the target the training dummy wants, pick the matching attribute (dummy LEFT,
                   pet RIGHT face-off; the picker glyphs live in the gauge) -- on a flat LCD."""
        gk = self.gkey
        E = data.load_effects()
        on, bgimg = self._scene_palette()
        ph = ARENA_ROWS * 2
        overlay = []
        placements = []

        if gk == "vaccine":                                 # DVPet drawVaccinePre: MASH to charge power.
            # Rebuilt to the department's staging standard (polish 2026-07-04) --
            # the old scene was a STATIC bag alone in a field: nothing on the
            # arena moved per tap and the Hit! label floated in the sky.  Now it
            # stages like the data drill's fixed columns: bag LEFT, PET RIGHT,
            # and every tap SHOWS the punch -- the pet lunges in its strike pose
            # (the _flash(6) each tap already sets), the bag rocks away 1px, and
            # the Hit! label (DVPet hitLabel) pops over the BAG it belongs to.
            # spacing polish (layout audit 2026-07-06, the hp lesson applied):
            # placed BY MEASUREMENT -- the GRID anchors ran a 16px mon OFF the
            # right edge (Devimon spanned x26..41 on the 40px LCD) and the
            # HIT!! label sat at y0 flush on the top border
            punching = self._strike_t > 0
            hit = E.get("train_hit", [None])[0]
            if punching and hit:
                # the Hit!! banner is a FULL-WINDOW 32x16 banner, staged
                # exactly like the battle start banner (Joel 2026-07-12):
                # the scene YIELDS -- bag and pet step offstage for the
                # strike beat and the banner owns the window.  The native
                # 13x5 hitLabel decode at a 2x integer upscale (mechanical,
                # dot-crisp) centred in the band.
                big = ["".join(c * 2 for c in row) for row in hit
                       for _ in range(2)]
                bw, bh = max(len(r) for r in big), len(big)
                overlay = _blit(big, GRID_X0 + (GRID_W - bw) // 2,
                                BAND_TOP + (BASE_Y - BAND_TOP - bh) // 2)
            else:
                bag = _fit_cell(E.get("punching_bag", [None])[0] or [])
                if bag:
                    placements.append((bag, GRID_X0 + 1, False))
                # the pet throws the punches from the window's right edge (LAW
                # 2026-07-11: every canon sprite lives inside the 32x16)
                pose = self._pose_now(1 if (self.frame_i // 2) % 2 else 0)  # idle bob between taps
                pf = _crop(self._frame(rec, pose))
                pw_ = max(len(r) for r in pf)
                px = GRID_X0 + GRID_W - pw_
                overlay.extend(_blit(pf, px, BASE_Y - len(pf)))   # grounded; faces left natively
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
            fy = BAND_TOP                                    # DVPet trainBar y16 of 60 -> the band top
            #                                                  (upper third, like the guide screenshot)
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
            # The REAL DM20's VERSUS TRAINING (canon rebuild 2026-07-13 -- DVPet's
            # turret duel here was fan invention; manual: "you choose to fire a
            # high shot or a low shot.  If your shot gets past your partner's
            # shield, you succeed").  Each round plays in the battle's
            # alternating-view volley grammar -- ONE combatant on screen at a
            # time, the same look every other drill's strike already wears:
            #   PICK -- faceoff: the sparring partner (the square-marked Data
            #           dummy) LEFT, the mon RIGHT, both idle; UP/DOWN commits
            #   OUT  -- cut to the mon: it looses its REAL orb along the lane
            #   IN   -- cut to the partner: the shield SNAPS to the chart's
            #           lane (the reveal) as the orb arrives -- pressed dead on
            #           the shield (blocked) or through into the partner (past)
            #   HIT  -- past: the battle's fullscreen strobe owns the window
            fr = self.tt_tl[min(self.tt_i, len(self.tt_tl) - 1)] if self.fired else None
            m = fr["m"] if fr else "pick"
            orb = data.attack_orb(self.pet.num, "Data", self.pet.data_power)
            oh = len(orb) if orb else 8
            ow = max(len(r) for r in orb) if orb else 8
            lane_y = BAND_TOP if self.shot_up else BASE_Y - oh   # HIGH rides the band top, LOW the floor
            shield = E.get("train_shield", [None])[0]
            sh_h = len(shield) if shield else 6
            sw = len(shield[0]) if shield else 5
            if m == "hit":                                   # PAST: DVPet hitAnim, the window is the flash
                ex = _EXPLODE[fr["f"]]
                overlay += _blit(ex, GRID_X0 + max(0, (GRID_W - len(ex[0])) // 2),
                                 BAND_TOP + max(0, (BASE_Y - BAND_TOP - len(ex)) // 2))
            elif m == "pick":                                # the faceoff: partner vs mon, like the done screen
                dummy = _fit_cell(_HP_DUMMIES["data"])
                pf = self._frame(rec, self._pose_now(1 if (self.frame_i // 2) % 2 else 0))
                placements = grid.faceoff(dummy, pf)         # partner mirrored to face the mon
            elif m == "fire_out":                            # the mon's view: it looses the shot
                pose = ATTACK
                xshift = -2 if fr["prog"] < 0.35 else 0      # the battle's release lunge
                placements, mouth = strikefx.place_combatant(True, self._frame(rec, pose), xshift)
                if orb:                                      # from the mouth, off the near edge, in-lane
                    ox = int((mouth - ow) + ((GRID_X0 - ow) - (mouth - ow)) * fr["prog"])
                    overlay = _pop(overlay, _blit(orb, ox, lane_y))
            else:                                            # fire_in / block: the partner's view
                dummy = _fit_cell(_HP_DUMMIES["data"])
                dm = [r[::-1] for r in dummy]                # creature stand-in faces the mon (canon mirror)
                overlay.extend(_blit(dm, GRID_X0, BASE_Y - len(dm)))
                dw = max(len(r) for r in dummy)
                sx = GRID_X0 + dw - sw + 2                   # the shield WORN on the partner's front edge,
                on_y = BAND_TOP + 1 if self.tt_shield_up else BASE_Y - sh_h   # snapped to the chart's lane
                if shield:                                   # _pop: it reads as a held object, not a growth
                    overlay = _pop(overlay, _blit(shield, sx, on_y))
                if orb:
                    stop_x = (sx + sw - 1) if self.blocked else (GRID_X0 + 2)   # dead on the shield / through
                    prog = 1.0 if m == "block" else fr["prog"]
                    ox = int(grid.X1 + (stop_x - grid.X1) * prog)   # arrives from the far (right) edge
                    overlay = _pop(overlay, _blit(orb, ox, lane_y))
        else:                                               # hp: pick the shape the dummy wants
            # The marked training dummy (battle bag) LEFT, full height, grounded,
            # and -- canon drawHPTraining (restaged 2026-07-04, the vaccine
            # lesson) -- the CHAR on the RIGHT, REACTING to every guess: pose 6
            # flash on a right pick, 9 on a wrong one (the old layout hid the
            # pet, so the reaction poses fired invisibly).  The round's TARGET
            # is the real 7x7 attribute symbol in the free sky lane between
            # them; the pick lives in the gauge (▸●◂), scrolled with ←→.
            # a wrong pick makes the dummy TAUNT for the flash beat (SpriteAnim
            # draws getBattleBagSprite(attr)+1 -- the sheet's bottom-row lean)
            taunting = self._strike_t > 0 and self._strike_pose == 9
            key = ("vaccine", "data", "virus")[self.hp_target] + ("_taunt" if taunting else "")
            dummy = _HP_DUMMIES[key]
            # TIME-MULTIPLEXED, the hardware way (LAW 2026-07-11): dummy(13)
            # + icons(7) + mon(16) never fit a 32px window at once -- the old
            # measured layout leaked into the bezel on BOTH edges and hung the
            # target icon over the matrix.  So the stage takes turns, like a
            # real V-Pet: the REEL act shows the dummy with the target/pick
            # pair beside it; every SPACE cuts to the REACTION act -- dummy +
            # the mon's 6/9 pose sharing the floor.
            dummy = _fit_cell(dummy)                                  # the 17px bag art fits the band
            placements = [(dummy, GRID_X0, True)]                     # MIRRORED (canon
            #                                       drawHPTraining: drawNumMirror(bag, true) --
            #                                       the dummy faces the char like a foe)
            if self._strike_t > 0:                                    # REACTION act
                pf = _crop(self._frame(rec, self._pose_now(
                    1 if (self.frame_i // 2) % 2 else 0)))            # 6/9 reactions
                overlay.extend(_blit(pf, GRID_X0 + GRID_W - max(len(r) for r in pf),
                                     BASE_Y - len(pf)))
            else:                                                     # REEL act
                ic = E.get(_HP_ICON_KEYS[self.hp_target], [None])[0]
                pk = E.get(_HP_ICON_KEYS[self.hp_pick], [None])[0]
                iy = BAND_TOP + 4                                     # band-centred: (16-7)//2 off the top
                if ic:
                    overlay.extend(_blit(ic, GRID_X0 + 15, iy))       # the target...
                if pk:
                    overlay.extend(_blit(pk, GRID_X0 + 24, iy))       # ...and the spinning pick
        # scene-only: the gauge + hint ride the strip (box-clip audit 2026-07-04)
        return render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg, clip=grid.WINDOW)

    def _gauge(self):
        """The drill's live gauge as one MARKUP line: it rides the #msg strip
        under the LCD (box-clip audit 2026-07-04 -- in-LCD it overflowed the
        physical box).  Must stay <= 40 visible cols so it never marquees:
        a live meter has to hold still."""
        gk = self.gkey
        if gk == "hp":
            # STATUS only -- the game objects live in the LCD now (the redo,
            # Joel 2026-07-06: the message box is never a gaming area)
            tb = int((max(self.round_t, 0) / max(self.round_len, 1)) * 8)
            # 18+2+3+2+8 == 33 <= HUD_W 40 (menu-bounds audit 2026-07-07:
            # the wordy cue ran the strip to 42 and the whole line marqueed);
            # same wording as the round flash
            return (f"[b]SPACE[/] on the match  "
                    f"{self.rep + 1}/{HP_ROUNDS}  {'▓' * tb}{'░' * (8 - tb)}")
        # ONE strip formula for every drill (consistency audit 2026-07-06):
        # action cue + progress + meter.  Game OBJECTS live in the LCD, the
        # NUMBERS live on the status card -- the strip only cues and counts.
        if gk == "vaccine":
            filled = int((max(self.timer, 0) / VACCINE_WINDOW) * 8)
            cue = "[b]HIT!![/]" if self._strike_t > 0 else "[b]SPACE[/] punch!"
            return (f"{cue}  {self.taps}/{self.vaccine_target}  "
                    f"{'▓' * filled}{'░' * (8 - filled)}")
        if gk == "data":
            # round pips: ▓ past / ░ blocked / · to play (3 of 5 passes) -- the
            # pips ARE the score; raw numbers and game glyphs stay off the strip
            pips = "".join("▓" if p else "░" for p in self.tt_log).ljust(DATA_ROUNDS, "·")
            cue = "[b]...[/]" if self.fired else "[b]UP[/] high · [b]DOWN[/] low"
            return f"{cue}  {pips}"
        cue = ("[b]IN THE ZONE — SPACE![/]" if int(self.pos) >= VIRUS_BAR_MIN
               else "[b]SPACE[/] stops it in the zone")
        return cue                           # the bar itself shows in the scene

    def strip(self):
        """The one-line chrome under the LCD."""
        if self.phase == "menu":
            # the hint convention (2026-07-10): every screen's strip = hints;
            # plain "↑↓ pick · 1-4 jump · ENTER start" = 32 cols (ESC is universal)
            return menu.hints(("↑↓", "pick"), ("1-4", "jump"), ("ENTER", "start"))
        if self.phase == "done":
            return f"{self.result or ''}  [dim]· SPACE finish[/]"
        if self.phase == "strike":
            return getattr(self, "_strike_note", "") or "..."
        return self._gauge()

    def _hint(self):
        # keep every hint <= menu.W (38 cols) or footer() clips it mid-word
        return {"hp": "SPACE stops the reel   ESC out",
                "vaccine": "SPACE punch the bag!   ESC out",
                "data": "UP/DOWN fires past   ESC out",
                "virus": "watch the marker   SPACE stops it"}[self.gkey]

    def _attr_pow(self):
        """The pet's power in the strike's attribute -> the orb tier (as the battle does)."""
        return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                "Virus": self.pet.virus}.get(self.strike_attr, 0)

    def _target_mirror(self):
        """Canon facing for the drill's target.  The HP dummy and the Data drill's
        sparring partner are CREATURE stand-ins: DVPet drawHPTraining places its
        dummy left with drawNumMirror(.., true) -- mirrored (drawNum keeps
        _isMirror, so the taunt flips with it).  The punching bag is a PROP drawn
        via setAltIcon -- never flipped."""
        return self.gkey in ("hp", "data")

    def _target_sprite(self, broken):
        """The thing being struck: the sparring partner (Data), the marked dummy (HP),
        or the punching bag, which shows its BROKEN frame on a successful break
        (DVPet aftermathDefault).  Fit to the 16px band so the strike animation sits
        in the same grid as the drill sprites."""
        E = data.load_effects()
        if self._is_data:                                       # the versus partner, intact either way
            return _HP_DUMMIES["data"]
        if self.gkey == "hp":                                   # HP fires at the training dummy (full height)
            return _HP_DUMMIES[("vaccine", "data", "virus")[self.hp_target]]
        return _fit_cell(E.get("punching_bag_broken" if broken else "punching_bag", [None])[0])

    def _strike_orb(self, leg, mouth, fr):
        """The pet's REAL orb, flown by the shared strikefx (the pet always fires left)."""
        orb = data.attack_orb(self.pet.num, self.strike_attr, self._attr_pow())
        m = "fire_out" if leg == "out" else "fire_in"
        return strikefx.orb_flight(orb, True, m, fr["prog"], mouth, fr.get("double"))

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
            ox = GRID_X0 + max(0, (GRID_W - len(ex[0])) // 2)   # the 32x16 flash fills
            oy = BAND_TOP + max(0, (BASE_Y - BAND_TOP - len(ex)) // 2)   # the window exactly
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
            placements, mouth = strikefx.place_combatant(True, pet, xshift)  # shared: pet right, faces left
            if m == "fire_out":
                overlay = self._strike_orb("out", mouth, fr)    # mouth = the pet's left edge
            note = {"windup": "...", "fire_out": "Fire!", "miss": self.result}[m]
        else:                                                   # fire_in / break: the TARGET is on screen (left)
            tgt = self._target_sprite(m == "break")
            mouth = grid.X0 + 1
            if tgt:                                             # shared placement: target LEFT, faces the pet
                placements, mouth = strikefx.place_combatant(False, tgt,
                                                             mirror=self._target_mirror())
            if m == "fire_in":
                overlay = self._strike_orb("in", mouth, fr)
            note = "Incoming!" if m == "fire_in" else self.result
        self._strike_note = note                        # surfaces on the strip
        return render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg, clip=grid.WINDOW)

    def _render_menu(self):
        """The drill menu, tuipet's STANDARD list (menu polish take 2,
        2026-07-13): DVPet's ●■▲♥ mouse diamond died first; then the
        scene-only preview proved invisible AS a menu (Joel: "whered the
        training menu go?!?!???" -- a lone faceoff in the habitat reads as
        the main screen, not a picker).  So: the options-screen grammar --
        a VISIBLE cursor list, hints on the strip."""
        out = menu.header("TRAINING", "choose a drill")
        out.append_text(menu.blanks(1))
        for gi, (gk, name, attr, desc) in enumerate(GAMES):
            sel = gi == self.gi
            out.append(f" {'▸ ' if sel else '  '}{name:<8}",
                       style=(f"{ACCENT} on {LCD_BG}") if sel else INK_B)
            out.append(f" {desc}\n", style=INK_B if sel else DIM)
        out.append_text(menu.blanks(1))
        out.append_text(menu.note(f"builds {GAMES[self.gi][2]}"))
        return out

