"""Battle — pet vs enemy with attack effects, rendered in the display box."""
from __future__ import annotations
from rich.text import Text
from . import data
from .battle import Battle
from .render import render_scene

from .theme import LCD_ON, LCD_BG, INK, INK_B, DIM, SIL_DAY, SIL_NIGHT
from . import menu
COLS, ROWS = 40, 8
_E = data.load_effects()
HIT = (_E.get("hit") or [None])[0]
FLASH = (_E.get("flash") or [None])[0]
ORB = (_E.get("attack") or [None])[0]            # the attackSprites projectile (checkAttackSprite)
FLY = 5


def _blit(bm, ox, oy):
    return [(ox + x, oy + y) for y, row in enumerate(bm)
            for x, c in enumerate(row) if c == "1"]


class BattlePanel:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.battle = Battle(pet, enemy)
        self.frame_i = 0
        self.atk = None

    def anim(self):
        self.frame_i += 1
        if self.atk:
            self.atk["step"] += 1
            if self.atk["step"] > FLY + 2:
                self.atk = None

    def key(self, k):
        which = {"1": "Vaccine", "2": "Data", "3": "Virus"}.get(k)
        if which:
            if not (self.battle.over or self.atk):
                be, bp = self.battle.enemy_hp, self.battle.pet_hp
                self.battle.play_round(which)
                enemy_hurt = self.battle.enemy_hp < be
                pet_hurt = self.battle.pet_hp < bp
                attacker = "pet" if enemy_hurt else "enemy"
                attr = which if attacker == "pet" else self.battle.last_enemy_attr
                if attacker == "pet":
                    pw_val = {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power,
                              "Virus": self.pet.virus}.get(attr, 0)
                else:
                    e = self.battle.enemy
                    pw_val = {"Vaccine": e["vaccine"], "Data": e["data_power"],
                              "Virus": e["virus"]}.get(attr, 0)
                count = max(1, min(4, 1 + pw_val // 50))
                self.atk = {"attacker": attacker, "step": 0, "count": count,
                            "pet_hurt": pet_hurt, "enemy_hurt": enemy_hurt}
            return None
        if k in ("escape", "space"):
            return ("done", self.battle if self.battle.over else None)
        return None

    def _frames(self, num, mode):
        rec = data.load_sprites()[1][num]
        if mode == "attack":
            roles = data.ROLES["attack"]
        elif mode == "recoil":
            roles = (9,)                                  # weary/hurt recoil pose
        else:
            roles = data.ROLES["idle"]
        idx = roles[self.frame_i % len(roles)]
        return rec["frames"][idx] or rec["frames"][0]

    def _hp(self, hp, mx):
        hp = max(0, hp)
        return "█" * hp + "░" * (mx - hp) if mx <= 12 else f"{hp}/{mx}"

    def _attack_overlay(self, pet_x, pw, enemy_x, ew):
        a = self.atk
        if not a:
            return []
        py = ROWS * 2 - 13
        if a["step"] <= FLY and ORB:                      # a stream of orbs flies
            ow = len(ORB[0])
            if a["attacker"] == "pet":
                x0, x1 = pet_x + pw - 1, enemy_x - ow
            else:
                x0, x1 = enemy_x - ow, pet_x + pw - 1
            lead = int(x0 + (x1 - x0) * (a["step"] / FLY))
            gap = ow + 1
            cells = []
            for i in range(a.get("count", 1)):
                ox = lead - i * gap if a["attacker"] == "pet" else lead + i * gap
                if 0 <= ox <= COLS - ow:
                    cells += _blit(ORB, ox, py)
            return cells
        # contact: a bright flash, then the burst, centred on the struck side
        cx = (enemy_x + ew // 2) if a["attacker"] == "pet" else (pet_x + pw // 2)
        fx = FLASH if a["step"] == FLY + 1 else HIT
        if not fx:
            return []
        w = len(fx[0])
        x = min(max(0, cx - w // 2), COLS - w)
        fy = max(0, (ROWS * 2 - len(fx)) // 2)
        return _blit(fx, x, fy)

    def text(self):
        b = self.battle
        a = self.atk
        flying = bool(a and a["step"] <= FLY)
        pet_mode = enemy_mode = "idle"
        if a and flying:
            if a["attacker"] == "pet":
                pet_mode = "attack"
            else:
                enemy_mode = "attack"
        elif a:                                           # contact: the struck side flinches
            if a.get("pet_hurt"):
                pet_mode = "recoil"
            if a.get("enemy_hurt"):
                enemy_mode = "recoil"
        pet_rows = self._frames(self.pet.num, pet_mode)
        enemy_rows = self._frames(b.enemy["num"], enemy_mode)
        pw = max(len(r) for r in pet_rows)
        ew = max(len(r) for r in enemy_rows)
        pet_x, enemy_x = 1, COLS - ew - 1
        overlay = self._attack_overlay(pet_x, pw, enemy_x, ew)
        bgimg = self.pet.background()
        on = SIL_NIGHT if self.pet.day_phase == "night" else (SIL_DAY if bgimg else LCD_ON)
        scene = render_scene([(pet_rows, pet_x, True), (enemy_rows, enemy_x, False)],
                             COLS, ROWS, on, LCD_BG, overlay=overlay, bgimg=bgimg)
        boss = "BOSS" if b.enemy["boss"] else ""
        out = menu.bar(f"BATTLE  vs {b.enemy['name']}"[:32], boss)
        out.append_text(scene)
        out.append(f"\nYou {self._hp(b.pet_hp, b.pet_max)}", style=INK)
        out.append(f"   Foe[{b.enemy['attribute'][:2]}] {self._hp(b.enemy_hp, b.enemy_max)}\n", style=INK)
        out.append_text(menu.note(b.last or "Choose your attack!"))
        if b.over:
            res = ("SURRENDER!" if b.surrendered else "VICTORY!") if b.won else "DEFEAT"
            out.append_text(menu.footer(f"{res}  {b.reward}   SPACE"))
        else:
            out.append_text(menu.footer("1 Vac   2 Data   3 Vir   ESC flee"))
        return out
