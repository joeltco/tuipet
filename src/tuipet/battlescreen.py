"""Battle — pet vs enemy, rendered in the display box. Combat logic lives in
battle.Battle (a faithful DVPet port); this is presentation only.

The per-round animation is a faithful reconstruction of View/SpriteAnim's battle
sequence (verified from the decompiled bytecode):

  * Layout — setupBattleCharacter / setupBattleOpponent: the player sits on the
    RIGHT (drawNumMirror mirror=false -> faces left), the opponent on the LEFT
    (mirror=true -> faces right).
  * Shoot — battlePlayerShootAnim: the attacker winds up through frames 1 -> 0 ->
    4 while lunging at the foe, then snaps to frame 6 (the strike) and launches
    the attack sprite, which flies across to the target.
  * Brace — battlePlayerReceiveAttackAnim: while the sprite is in flight the
    target toggles frames 4 <-> 0 (a flinching brace).
  * Impact — battlePlayerHit / battlePlayerHitAftermath: on a damaging hit the
    target draws frame 10 (the collapse pose) and its health drains; a 0-damage
    attack is a dodge (the target stays idle). HP changes happen AT impact.
  * Projectile — checkAttackSprite: the attack sprite is chosen by the attacker's
    attribute (Vaccine / Data / Virus each have their own sprite).
  * Both sides attack each round in initiative order (Battle.last_player_first);
    a side KO'd by the first attack does not retaliate (Battle.checkFinish).
"""
from __future__ import annotations
from . import data
from .battle import Battle
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, SIL_DAY, SIL_NIGHT
from . import menu
COLS, ROWS = 40, 8
_E = data.load_effects()
HIT = (_E.get("hit") or [None])[0]
FLASH = (_E.get("flash") or [None])[0]
# checkAttackSprite: the projectile sprite is selected by the attacker's attribute.
ATK_SPRITE = {"Vaccine": (_E.get("atk_vaccine") or _E.get("attack") or [None])[0],
              "Data":    (_E.get("atk_data") or _E.get("attack") or [None])[0],
              "Virus":   (_E.get("atk_virus") or _E.get("attack") or [None])[0]}

# Verified frame poses (drawNumMirror args in the battle methods):
SHOOT_WINDUP = [1, 1, 0, 4]   # battlePlayerShootAnim: 1 -> 0 -> 4, lunging in
SHOOT_STRIKE = 6              # ...then frame 6 at the moment the sprite launches
BRACE = [4, 0]               # battlePlayerReceiveAttackAnim: target toggles 4 <-> 0
HURT = 10                    # battlePlayerHitAftermath: damaged target draws frame 10
IDLE = 0

# Per-attack timeline (one tick == one DVPet sequence step; _frame += _interval):
WIND_T = len(SHOOT_WINDUP)   # ticks 0..WIND_T-1 : windup poses, lunging at the foe
STRIKE_T = WIND_T            # tick WIND_T        : strike (frame 6) + launch
FLY = 5                      # flight length
FLY_T0 = STRIKE_T            # the sprite is airborne from the strike tick onward
IMPACT_T = STRIKE_T + 1 + FLY
IMPACT_LEN = 3
END_T = IMPACT_T + IMPACT_LEN
LUNGE_MAX = 3                # cols the attacker dashes toward the foe (TUI scale of the pixel lunge)


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.seq = []                 # queued attacks for the current round
        self.ai = 0                   # index into seq
        self.t = 0                    # ticks into the current attack
        self.dp = self.battle.pet_hp  # displayed HP (drains at each impact)
        self.de = self.battle.enemy_hp
        self.surrender_req = False    # the pet has asked to give up; awaiting Y/N

    # ---- round driving -------------------------------------------------
    def _start_round(self, which):
        b = self.battle
        pre_p, pre_e = b.pet_hp, b.enemy_hp
        b.play_round(which)                              # resolves the round (mutates HP to final)
        p_atk = {"attacker": "pet", "victim": "enemy",
                 "attr": b.last_player_attr, "dmg": max(0, b.last_player_damage)}
        e_atk = {"attacker": "enemy", "victim": "pet",
                 "attr": b.last_enemy_attr, "dmg": max(0, b.last_enemy_damage)}
        order = [p_atk, e_atk] if b.last_player_first else [e_atk, p_atk]
        # walk the initiative order, recording the victim HP after each blow; a
        # KO'd victim does not let the other side retaliate (checkFinish).
        cur_p, cur_e = pre_p, pre_e
        seq = []
        for atk in order:
            if atk["victim"] == "enemy":
                cur_e = max(0, cur_e - atk["dmg"]); atk["after"] = cur_e
                seq.append(atk)
                if cur_e <= 0:
                    break
            else:
                cur_p = max(0, cur_p - atk["dmg"]); atk["after"] = cur_p
                seq.append(atk)
                if cur_p <= 0:
                    break
        self.dp, self.de = pre_p, pre_e
        self.seq, self.ai, self.t = seq, 0, 0

    def anim(self):
        self.frame_i += 1
        if not self.seq:
            return
        self.t += 1
        atk = self.seq[self.ai]
        if self.t == IMPACT_T:                           # battlePlayerHitAftermath: drain HP at impact
            if atk["victim"] == "enemy":
                self.de = atk["after"]
            else:
                self.dp = atk["after"]
        if self.t >= END_T:
            self.ai += 1
            self.t = 0
            if self.ai >= len(self.seq):                 # round done
                self.dp, self.de = self.battle.pet_hp, self.battle.enemy_hp
                self.seq = []
                if not self.battle.over:
                    self._check_surrender()

    def _check_surrender(self):
        """DVPet onRoundEnd: after a round the pet may give up (1) or beg to flee (2)."""
        b = self.battle
        s = b.pet.check_surrender(b.pet_hp, b.enemy_hp, b.enemy_max, b.pet_max)
        if s == 1:
            b.pet.surrender_effect(1, b.pet_hp, b.enemy_hp)
            b.surrender()
        elif s == 2:
            self.surrender_req = True

    def key(self, k):
        if self.surrender_req:                           # pet asking to quit -- Y accept / N refuse
            b = self.battle
            if k in ("y", "Y"):
                b.pet.surrender_effect(2, b.pet_hp, b.enemy_hp)
                b.surrender()
                self.surrender_req = False
            elif k in ("n", "N"):
                b.pet.surrender_reject()                 # sulks, fights on
                self.surrender_req = False
            return None
        which = {"1": "Vaccine", "2": "Data", "3": "Virus"}.get(k)
        if which:
            if not (self.battle.over or self.seq):
                self._start_round(which)
            return None
        if k in ("escape", "space"):
            return ("done", self.battle if self.battle.over else None)
        return None

    # ---- rendering -----------------------------------------------------
    def _rows(self, num, pose):
        rec = data.load_sprites()[1][num]
        return rec["frames"][pose] or rec["frames"][0]

    def _idle_rows(self, num):
        return self._rows(num, data.ROLES["idle"][self.frame_i % len(data.ROLES["idle"])])

    def _hp(self, hp, mx):
        hp = max(0, hp)
        return "█" * hp + "░" * (mx - hp) if mx <= 12 else f"{hp}/{mx}"

    def _attack_overlay(self, atk, pet_x, pw, enemy_x, ew):
        """The flying attack sprite (checkAttackSprite) + the contact flash/burst."""
        orb = ATK_SPRITE.get(atk["attr"])
        py = ROWS * 2 - 13
        if STRIKE_T <= self.t < IMPACT_T and orb:        # in flight
            ow = len(orb[0])
            if atk["attacker"] == "pet":                 # player (right) fires left
                x0, x1 = pet_x - ow, enemy_x + ew
                src = [r[::-1] for r in orb]             # face the travel direction
            else:                                        # foe (left) fires right
                x0, x1 = enemy_x + ew, pet_x - ow
                src = orb
            prog = (self.t - STRIKE_T) / float(FLY)
            ox = int(x0 + (x1 - x0) * min(1.0, prog))
            if 0 <= ox <= COLS - ow:
                return _blit(src, ox, py)
            return []
        if self.t >= IMPACT_T and atk["dmg"] > 0:        # contact burst on the struck side
            vx, vw = (enemy_x, ew) if atk["victim"] == "enemy" else (pet_x, pw)
            cx = vx + vw // 2
            fx = FLASH if self.t == IMPACT_T else HIT
            if not fx:
                return []
            w = len(fx[0])
            x = min(max(0, cx - w // 2), COLS - w)
            fy = max(0, (ROWS * 2 - len(fx)) // 2)
            return _blit(fx, x, fy)
        return []

    def _poses_and_lunge(self, atk):
        """Return (pet_pose, enemy_pose, pet_lunge, enemy_lunge) for the current tick."""
        att, vic = atk["attacker"], atk["victim"]
        t = self.t
        if t < WIND_T:                                   # windup: attacker poses, lunging in
            apose, vpose = SHOOT_WINDUP[t], IDLE
            lunge = LUNGE_MAX * (t + 1) // WIND_T
        elif t == STRIKE_T:                              # strike + launch
            apose, vpose, lunge = SHOOT_STRIKE, BRACE[0], LUNGE_MAX
        elif t < IMPACT_T:                               # flight: follow-through + target braces
            apose = SHOOT_STRIKE
            vpose = BRACE[(t - STRIKE_T) % len(BRACE)]
            lunge = max(0, LUNGE_MAX - (t - STRIKE_T))   # ease back out
        else:                                            # impact: hurt pose (10) on damage, else dodge
            apose = IDLE
            vpose = HURT if atk["dmg"] > 0 else IDLE
            lunge = 0
        poses = {att: apose, vic: vpose}
        lunges = {att: lunge, vic: 0}
        return poses["pet"], poses["enemy"], lunges["pet"], lunges["enemy"]

    def text(self):
        b = self.battle
        atk = self.seq[self.ai] if self.seq else None
        if atk:
            pet_pose, enemy_pose, pet_lunge, enemy_lunge = self._poses_and_lunge(atk)
            pet_rows = self._rows(self.pet.num, pet_pose)
            enemy_rows = self._rows(b.enemy["num"], enemy_pose)
        else:
            pet_rows = self._idle_rows(self.pet.num)
            enemy_rows = self._idle_rows(b.enemy["num"])
            pet_lunge = enemy_lunge = 0
        pw = max(len(r) for r in pet_rows)
        ew = max(len(r) for r in enemy_rows)
        # player RIGHT (faces left), opponent LEFT (faces right) -- lunge toward the centre
        pet_x = COLS - pw - 1 - pet_lunge
        enemy_x = 1 + enemy_lunge
        overlay = self._attack_overlay(atk, pet_x, pw, enemy_x, ew) if atk else []
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        scene = render_scene([(pet_rows, pet_x, False), (enemy_rows, enemy_x, True)],
                             COLS, ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        boss = "BOSS" if b.enemy["boss"] else ""
        out = menu.bar(f"BATTLE  vs {b.enemy['name']}"[:32], boss)
        out.append_text(scene)
        out.append(f"\nYou {self._hp(self.dp, b.pet_max)}", style=INK)
        out.append(f"   Foe[{b.enemy['attribute'][:2]}] {self._hp(self.de, b.enemy_max)}\n", style=INK)
        note = b.last or "Choose your attack!"
        if self.surrender_req and not b.over:
            note = f"{self.pet.name} wants to give up!"
        out.append_text(menu.note(note))
        if b.over:
            res = "SURRENDER" if getattr(b, "surrendered", False) else ("VICTORY!" if b.won else "DEFEAT")
            out.append_text(menu.footer(f"{res}  {b.reward}   SPACE"))
        elif self.surrender_req:
            out.append_text(menu.footer("Let it quit?   Y yes   N fight on"))
        else:
            out.append_text(menu.footer("1 Vac   2 Data   3 Vir   ESC flee"))
        return out
