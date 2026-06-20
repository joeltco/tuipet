"""Battle engine — faithful in spirit to DVPet's attribute-triangle combat.

The Digimon attribute triangle (canon): Vaccine > Virus > Data > Vaccine. Each
round both sides attack with a chosen attribute; effective power is the chosen
attribute's power, boosted when it beats the opponent's attribute and dampened
when it loses to it. Higher effective power lands a hit (−1 HP); ties trade. The
side reduced to 0 HP loses. Wins/battles feed the evolution requirements.
"""
from __future__ import annotations
import random
from . import data

TRIANGLE = {"Vaccine": "Virus", "Virus": "Data", "Data": "Vaccine"}  # key beats value
ATTRS = ("Vaccine", "Data", "Virus")


def beats(a, b):
    return TRIANGLE.get(a) == b


def effective(att_attr, powers, def_attr):
    base = powers.get(att_attr, 0)
    if beats(att_attr, def_attr):
        return base * 1.5 + 12          # attribute advantage
    if beats(def_attr, att_attr):
        return base * 0.6               # at a disadvantage
    return base + 4                     # neutral baseline so 0-power can still chip


def pick_enemy(pet, boss=False):
    pool = [e for e in data.enemies_for_stage(pet.stage) if e["boss"] == boss] \
        or data.enemies_for_stage(pet.stage)
    real = [e for e in pool if not data.is_placeholder(e["num"])]
    return random.choice(real or pool)


class Battle:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.enemy = dict(enemy or pick_enemy(pet))
        ep = {"Vaccine": self.enemy["vaccine"], "Data": self.enemy["data_power"], "Virus": self.enemy["virus"]}
        self.enemy["attribute"] = max(ATTRS, key=lambda a: ep[a])  # battle type = strongest power
        self.pet_hp = self.pet_max = 4 + pet.strength          # 4..8
        self.enemy_hp = self.enemy_max = min(self.enemy["hp"], 7)  # cap for snappy fights
        self.round = 0
        self.over = False
        self.won = None
        self.last = ""

    def _powers(self, side):
        if side == "pet":
            return {"Vaccine": self.pet.vaccine, "Data": self.pet.data_power, "Virus": self.pet.virus}
        return {"Vaccine": self.enemy["vaccine"], "Data": self.enemy["data_power"], "Virus": self.enemy["virus"]}

    def _enemy_choice(self):
        # mostly attacks with its battle attribute (shown to the player), some bluff
        if random.random() < 0.2:
            return random.choice(ATTRS)
        return self.enemy["attribute"]

    def play_round(self, player_attr):
        if self.over:
            return self.last
        self.round += 1
        enemy_attr = self._enemy_choice()
        pe = effective(player_attr, self._powers("pet"), enemy_attr)
        ee = effective(enemy_attr, self._powers("enemy"), player_attr)
        if pe > ee:
            self.enemy_hp -= 1
            verb = "hits!" + (" (advantage)" if beats(player_attr, enemy_attr) else "")
            self.last = f"R{self.round}: your {player_attr} {verb}"
        elif ee > pe:
            self.pet_hp -= 1
            self.last = f"R{self.round}: enemy {enemy_attr} hits you!"
        else:
            self.enemy_hp -= 1
            self.pet_hp -= 1
            self.last = f"R{self.round}: clash! both take a hit"
        if self.enemy_hp <= 0 or self.pet_hp <= 0:
            self._finish()
        return self.last

    def _finish(self):
        self.over = True
        self.won = self.enemy_hp <= 0 and self.pet_hp > 0
        if self.pet_hp <= 0 and self.enemy_hp <= 0:
            self.won = False  # double-KO counts as a loss
        self.reward = self.pet.record_battle(self.won, self.enemy)
