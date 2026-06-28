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

# the full-screen spiky hit burst (attackHit/attackHitFlash), shared with the battle
# screen -- strobes outline<->filled to flash the LCD on impact (DVPet hitAnim).
with open(os.path.join(os.path.dirname(__file__), "data", "battle_overlays.json")) as _f:
    _EXPLODE = json.load(_f)["hit_explosion"]

# DVPet config (normal difficulty)
VACCINE_HITS_MIN = 20
VACCINE_WINDOW = 48           # ticks (0.1s each) to mash
VIRUS_BAR_MIN = 86
VIRUS_SPEED = 4
# Data is a SHIELD BLOCK (controller checkSuccess: success = shieldTop == isUp): the
# green target feints, then COMMITS its attack high or low; you raise your shield to
# the matching side to block it before the window closes.
DATA_BOB = 3                  # ticks per feint up/down toggle during the telegraph
DATA_TELEGRAPH = 15           # feint window before the attack commits (~1.5s)
DATA_WINDOW = 13              # reaction window to set the shield after it commits (~1.3s)
HP_ROUNDS = 3
HP_ROUNDS_WON = 2
HP_ROUND_LEN = 28             # ticks to pick before a round times out (~2.8s)
VBAR_W = 24

COLS = 40
ARENA_ROWS = 11               # play & strike share one arena height (room for the tall hanging bag)

# strike sequence (attackDefault/attackGreen -> hitAnim -> aftermathDefault)
STRIKE_FIRE = 8               # projectile travels to the opponent (0.8s)
STRIKE_FLASH = 6              # impact flash (0.6s)
STRIKE_AFTER = 12             # aftermath: broken-bag / recoil hold (1.2s)
STRIKE_TOTAL = STRIKE_FIRE + STRIKE_FLASH + STRIKE_AFTER

# the attribute symbols (DVPet: Vaccine=orb/red, Data=block/green, Virus=dart/yellow)
# -> circle / square / triangle.
ATTR_SYM = ["●", "■", "▲"]   # ● ■ ▲  (Vaccine / Data / Virus) for the HP-drill guess


def _blit(bm, ox, oy):
    """Sprite bitmap -> (x,y) pixel list for render_scene's overlay (projectile / flash)."""
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


def _attr_shape(kind, h=9):
    """Clean attribute symbol as a 1-bit bitmap (procedural, not hand-authored):
    0=circle (Vaccine), 1=square (Data), 2=triangle (Virus)."""
    if kind == 1:                                   # square
        return ["1" * h for _ in range(h)]
    rows = []
    if kind == 0:                                   # filled circle
        c = (h - 1) / 2
        for y in range(h):
            rows.append("".join("1" if (x - c) ** 2 + (y - c) ** 2 <= (c + 0.4) ** 2 else "0"
                                 for x in range(h)))
    else:                                           # filled upward triangle
        for y in range(h):
            w = 1 + int(y / (h - 1) * (h - 1))
            pad = (h - w) // 2
            rows.append("0" * pad + "1" * w + "0" * (h - w - pad))
    return rows


_ATTR_SHAPES = [_attr_shape(0), _attr_shape(1), _attr_shape(2)]   # ● ■ ▲


GAMES = [
    ("hp",      "HP Drill", "Effort",  "guess the bag — best of 3"),
    ("vaccine", "Vaccine",  "Vaccine", f"mash the bag to {VACCINE_HITS_MIN}"),
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
        self._strike_pose = None     # transient hit(6)/miss(9) pose during a drill
        self._strike_t = 0
        self.strike_step = 0         # the post-drill strike clock (fire -> flash -> aftermath)
        self._strong = False         # a full-success drill -> strong attack/hit

    @property
    def gkey(self):
        return GAMES[self.gi][0]

    @property
    def _is_data(self):
        return self.gkey == "data"

    # ---- lifecycle ----
    def _start_game(self):
        self.phase = "play"
        self._reset()
        gk = self.gkey
        if gk == "hp":
            self._new_hp_round()
        elif gk == "vaccine":
            self.flash = "MASH the bag!"
        elif gk == "data":
            self.flash = "watch the feint — block high or low!"
        else:
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
        if self.rep >= HP_ROUNDS:
            won = self.rounds_won
            hits = 3 if won >= 3 else (2 if won >= HP_ROUNDS_WON else won)
            self._finish(hits, 0, None, "hp")
        else:
            self._new_hp_round()

    def _finish(self, hits, power, attribute, game):
        self.success = hits >= 2
        self._strong = hits >= 3
        self.result = self.pet.apply_training(hits, power, attribute, game=game)
        if game == "hp":
            # HP training has NO projectile strike -- each guess already flashed pose
            # 6/9 (drawHPTrainingAttackSuccess/Fail = pose + impact, no orb).  Just
            # reveal the Effort result.
            self.phase = "done"
            self.flash = self.result + "   (SPACE)"
        else:
            # attribute drills fire the real attackDefault/attackGreen projectile at
            # the opponent first, THEN reveal the score.
            self.phase = "strike"
            self.strike_step = 0
            self.flash = ""

    # ---- anim (called each fast tick) ----
    def anim(self):
        self.frame_i += 1
        if self._strike_t > 0:
            self._strike_t -= 1
        if self.phase == "strike":
            self.strike_step += 1
            if self.strike_step == 1:                       # launch: strong vs normal attack sting
                self.sfx = "strongAttack" if self._strong else "attack"
            elif self.strike_step == STRIKE_FIRE + 1:       # impact: strong/normal hit, or the miss thud
                self.sfx = ("strongHit" if self._strong else "attackHit") if self.success else "cancel"
            if self.strike_step >= STRIKE_TOTAL:            # sequence done -> reveal the score
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
                ratio = self.taps / VACCINE_HITS_MIN
                hits = 3 if ratio >= 1.2 else (2 if ratio >= 0.8 else (1 if ratio >= 0.4 else 0))
                self._finish(hits, int(self.taps), "Vaccine", "vaccine")
        elif gk == "data":
            self.data_t += 1
            if not self.locked:                             # telegraph: the green feints up/down
                if self.data_t % DATA_BOB == 0:
                    self.feint_up = not self.feint_up
                if self.data_t >= DATA_TELEGRAPH:           # ...then the attack COMMITS high/low
                    self.locked = True
                    self.tgt_up = random.choice((True, False))
                    self.data_t = 0
                    self.flash = "block it — UP or DOWN!"
            elif self.data_t >= DATA_WINDOW:                # window closed -> resolve the block
                self._data_resolve()
        else:  # virus -- the power bar sweeps; hit to stop it
            self.pos += self.dir * VIRUS_SPEED
            if self.pos >= 100:
                self.pos = 100
                self.dir = -1
            elif self.pos <= 0:
                self.pos = 0
                self.dir = 1

    # ---- key ----
    def key(self, k):
        if self.phase == "strike":
            return None                  # the strike plays out uninterrupted (DVPet has no skip)
        if self.phase == "menu":
            if k in ("up", "k"):
                self.gi = (self.gi - 1) % len(GAMES)
            elif k in ("down", "j"):
                self.gi = (self.gi + 1) % len(GAMES)
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
        elif gk == "data":                   # raise the shield to the matching side to block
            if k in ("up", "k"):
                self.shield_up = True
            elif k in ("down", "j"):
                self.shield_up = False
        elif k == "space":                   # vaccine mash / virus stop
            self._strike()
        return None

    def _data_resolve(self):
        """The attack landed: a block (shield matches the attack side) succeeds, else
        it gets through.  One attempt -> the strike (attackGreen)."""
        self.blocked = self.shield_up == self.tgt_up
        if self.blocked:
            self.flash = "BLOCKED!"
            self._flash(6)
            self._finish(3, 60, "Data", "data")
        else:
            self.flash = "hit you!"
            self._flash(9)
            self._finish(0, 0, "Data", "data")

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
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        return on, bgimg

    def _render_play(self, rec):
        """The skill phase, matching the DVPet guide minigames:
        Vaccine = hit the orb ("Hit!!"); Data = a cannon aims high/low and you raise
        the matching shield to block; Virus = stop the sweeping marker in the target
        range; HP = match the shown attribute symbol.  The pet watches from the right."""
        gk = self.gkey
        E = data.load_effects()
        on, bgimg = self._scene_palette()
        px_h = ARENA_ROWS * 2
        placements = []
        overlay = []
        pet = self._frame(rec, self._pose_now(0))
        pw = max(len(r) for r in pet)
        pet_x = COLS - pw - 2
        if gk == "vaccine":                                 # HIT the orb (DVPet "Hit!!")
            placements.append((pet, pet_x, False))
            orb = _attr_shape(0, 11)                         # a solid black orb
            ow, oh = len(orb[0]), len(orb)
            bob = -2 if self._strike_t > 0 else (1 if (self.frame_i // 3) % 2 else 0)
            overlay += _blit(orb, COLS // 2 - ow, (px_h - oh) // 2 + bob)
        elif gk == "data":                                  # CANNON aims high/low -> raise the matching SHIELD
            placements.append((pet, pet_x, False))
            up = self.tgt_up if self.locked else self.feint_up
            cannon = E.get("train_green_up" if up else "train_green", [None])[0]
            if cannon:
                ch = len(cannon)
                cy = (px_h - 6 - ch - 7) if up else (px_h - 6 - ch)   # cannon sits high (up) or low
                overlay += _blit(cannon, 4, max(0, cy))
            shield = E.get("train_shield", [None])[0]        # two slots by the pet; the active one is solid
            if shield:
                sw, shh = len(shield[0]), len(shield)
                sx = pet_x - sw - 2
                top_y, bot_y = px_h - 6 - shh - 7, px_h - 6 - shh
                overlay += _blit(shield, sx, top_y if self.shield_up else bot_y)
                ey = bot_y if self.shield_up else top_y      # the empty slot: a faint outline
                overlay += [(sx + x, ey + y) for y in range(shh) for x in range(sw)
                            if x in (0, sw - 1) or y in (0, shh - 1)]
        elif gk == "hp":                                    # match the shown attribute symbol
            bag = E.get("battle_bag", [None])[0]
            if bag:
                placements.append((bag, 2, False))
            placements.append((pet, pet_x, False))
            sym = _ATTR_SHAPES[self.hp_target]
            sw, shh = len(sym[0]), len(sym)
            overlay += _blit(sym, (COLS - sw) // 2, (px_h - shh) // 2 - 1)
        else:                                               # virus: stop the marker in the target range
            placements.append((pet, pet_x, False))
            bx, bw, by = 3, COLS - 7, 6                     # a wide bar across the top of the LCD
            lo = bx + int(VIRUS_BAR_MIN / 100 * bw)
            overlay += [(bx + x, by) for x in range(bw)]                       # the bar rail
            for x in range(lo, bx + bw):                                       # the target zone (a box)
                overlay += [(x, by - 2), (x, by + 2)]
            overlay += [(lo, by + dy) for dy in (-2, -1, 0, 1, 2)]             # zone left edge
            mx = bx + int(self.pos / 100 * bw)
            overlay += [(mx, by + dy) for dy in (-3, -2, -1, 0, 1, 2, 3)]      # the sweeping marker
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
            t.append("bag ", style=INK)
            t.append(ATTR_SYM[self.hp_target], style=INK_B)        # the symbol you must match
            t.append("  match ", style=INK)
            for i, sym in enumerate(ATTR_SYM):
                sel = i == self.hp_pick
                t.append(f"[{sym}]" if sel else f" {sym} ",
                         style=(f"{ACCENT} on {LCD_BG}") if sel else INK_B)
            tb = int((max(self.round_t, 0) / HP_ROUND_LEN) * 5)
            t.append(" " + "▓" * tb + "░" * (5 - tb) + "\n", style=f"{ACCENT} on {LCD_BG}")
        elif gk == "vaccine":
            hit = self._strike_t > 0
            t.append("HIT!! " if hit else "hit!  ", style=INK_B if hit else INK)
            done = self.taps >= VACCINE_HITS_MIN
            t.append(f"{self.taps}/{VACCINE_HITS_MIN}  ", style=INK_B if done else INK)
            filled = int((max(self.timer, 0) / VACCINE_WINDOW) * 9)
            t.append("time " + "▓" * filled + "░" * (9 - filled) + "\n", style=f"{ACCENT} on {LCD_BG}")
        elif gk == "data":
            if self.locked:
                t.append("CANNON " + ("HIGH! " if self.tgt_up else "LOW!  "), style=INK_B)
            else:
                t.append("aiming...  ", style=DIM)
            t.append("shield ", style=INK)
            t.append("[UP]" if self.shield_up else " up ", style=(f"{ACCENT} on {LCD_BG}") if self.shield_up else INK)
            t.append("[DN]" if not self.shield_up else " dn ", style=(f"{ACCENT} on {LCD_BG}") if not self.shield_up else INK)
            t.append("\n", style=INK)
        else:  # virus -- the bar is drawn in the LCD; the gauge just calls the zone
            inzone = int(self.pos) >= VIRUS_BAR_MIN
            t.append("IN THE ZONE - hit!" if inzone else "stop it in the zone", style=INK_B if inzone else INK)
            t.append(f"   {int(self.pos)}\n", style=INK)
        return t

    def _hint(self):
        return {"hp": "←→ match the symbol   SPACE strike",
                "vaccine": "SPACE hit the orb!   ESC out",
                "data": "↑ / ↓ raise the shield the cannon faces",
                "virus": "SPACE stop the marker in the zone"}[self.gkey]

    def _render_strike(self, rec):
        """DVPet attackDefault/attackGreen -> hitAnim -> aftermathDefault.  The pet
        fires its projectile at the opponent; it flashes on impact; then the bag shows
        BROKEN on success / the pet RECOILS to pose 10 on a fail.  Data fires RIGHT at
        the green target, everything else fires LEFT at the punching bag -- the same
        sides the drill used, so the strike flows straight out of it."""
        s = self.strike_step
        E = data.load_effects()
        on, bgimg = self._scene_palette()
        px_h = ARENA_ROWS * 2
        after = s > STRIKE_FIRE + STRIKE_FLASH
        pose = (0 if self.success else 10) if after else 6      # strike(6) -> idle(0) / recoil(10)
        pet = self._frame(rec, pose)
        pw = max(len(r) for r in pet)
        fire_y = px_h - 12
        if self._is_data:                                       # pet LEFT (faces right), green RIGHT
            opp = E.get("train_green", [None])[0]
            ow = max((len(r) for r in opp), default=10) if opp else 10
            pet_x, opp_x = 2, COLS - ow - 3
            placements = [(pet, pet_x, True)]
            if opp:
                placements.append((opp, opp_x, False))
            x_from, x_to, rightward = pet_x + pw, opp_x, True
        else:                                                   # pet RIGHT (faces left), bag LEFT
            broken = after and self.success
            opp = E.get("punching_bag_broken" if broken else "punching_bag", [None])[0]
            ow = max((len(r) for r in opp), default=6) if opp else 6
            pet_x, opp_x = COLS - pw - 3, 2
            placements = [(pet, pet_x, False)]
            if opp:
                placements.append((opp, opp_x, False))
            x_from, x_to, rightward = pet_x, opp_x + ow, False
        overlay = []
        if s <= STRIKE_FIRE:                                    # the projectile crosses to the opponent
            orb = E.get("attack") or []
            of = orb[min((s - 1) // 2, len(orb) - 1)] if orb else None
            if of:
                ow_orb = max(len(r) for r in of)
                if rightward:
                    x0, x1 = x_from, x_to - ow_orb
                    src = [r[::-1] for r in of]                 # orb art faces left -> flip to fly right
                else:
                    x0, x1 = x_from - ow_orb, x_to
                    src = of
                ox = int(x0 + (x1 - x0) * (s / STRIKE_FIRE))
                overlay += _blit(src, ox, fire_y)
        elif not after:                                        # impact: the full hit-burst strobes over the LCD
            ex = _EXPLODE[((s - STRIKE_FIRE - 1) // 2) % len(_EXPLODE)]
            ox = max(0, (COLS - len(ex[0])) // 2)
            oy = max(0, (px_h - len(ex)) // 2)
            overlay += _blit(ex, ox, oy)
        scene = render_scene(placements, COLS, ARENA_ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        scene.append("\n")
        scene.append_text(menu.note(self.result if after else "..."))
        scene.append_text(menu.footer(""))
        return scene

    def _render_menu(self):
        out = menu.header("TRAINING", "pick a drill")
        out.append_text(menu.note(GAMES[self.gi][3]))
        out.append_text(menu.blanks(1))
        for i, (gk, label, attr, blurb) in enumerate(GAMES):
            tag = "effort" if gk == "hp" else f"{attr[:4]} pow"
            out.append_text(menu.row(f"{label:<9} {tag}", i == self.gi))
        out.append_text(menu.footer("↑↓ pick   ENTER start   ESC out"))
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
