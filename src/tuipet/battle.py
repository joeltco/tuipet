"""Battle engine — a faithful port of DVPet's Model.Battle combat.

Every value below is decompiled from raw_model/Battle.class + config.csv; nothing
here is invented. Where a DVPet subsystem cannot be reproduced from the shipped
data it is documented as such rather than approximated.

HP (Battle.setupOpponents / getOppMaxHealth):
  player starts full at the per-stage MaxHealth; enemy at its enemies.csv Health
  (Enemy.getEnemyHealth). config MaxHealth*: Rookie 10, Champion 15, Ultimate 20,
  Mega 30, default 10.

Per-round damage (Battle.attack -> finishAttack):
      dmg = getBaseAttack(stage) + calcAttackPower(attr) + affinityBonus
  getBaseAttack (config *BaseAttack): Fresh 1, InTraining 2, Rookie/Champion/
  Ultimate/Mega 5.  calcAttackPower (Battle.calcAttackPower) returns -1/0/+1 by
  comparing THIS side's count in the chosen attribute against the opponent's
  count (counts = vaccine/data/virus power).  affinityBonus (Battle.calcBonus =
  field-vs-field + element-vs-element affinity) is 0: the shipped fieldAffinity
  and elementAffinity matrices are entirely zero.  _attack is floored at 0.

Enemy AI (Battle: AIType selected from the PLAYER's win count):
  wins <15 Random, <30 Brute, <45 StrategicBrute, <60 StrategicDefense,
  >=60 StrategicDefense if (enemy power-sum+HP) > (player power-sum+HP) else
  StrategicBalanced.  config *AIWins: 0/15/30/45/60.
  randomAI: random among the attributes whose count > 0.
  bruteAI / strategic line: pick the attribute with the best calcAttackPower
  delta, breaking ties by greatest raw count (checkAttackTotalAndZero), and
  avoiding the attribute last remembered as dealing 0 (checkRememberZeroAttack).

  NOTE: the strategic AIs additionally weight per-attribute AttackEffect "chips"
  (calcBruteStrategyValues / checkAttackWeight / checkDefendWeight). Those effect
  weights are 0 for the shipped data (no chip effects populated), so all
  non-random AIs collapse to the brute delta-pick — matching the shipped game.

Win/lose (Battle.checkFinish / battleEnd): the battle ends the instant either
HP <= 0; the player loses iff its OWN HP <= 0 (a double-KO is therefore a loss).

NOT ported (documented, not faked):
  - AttackEffect/AttackCondition chip layer (AttackEffectProcess): the per-
    attribute effect+condition data lives in digimon.csv (Name:Effect:Condition)
    but is not yet wired; with it unset the engine matches shipped behaviour.
  - Player-side surrender/escape (PhysicalState.checkSurrender): an obedience/
    disposition morale mechanic that needs the obedience-factor model first.
"""
from __future__ import annotations
import random
from . import data

ATTRS = ("Vaccine", "Data", "Virus")

# config.csv *BaseAttack (per growth stage)
BASE_ATTACK = {"Fresh": 1, "InTraining": 2, "Rookie": 5,
               "Champion": 5, "Ultimate": 5, "Mega": 5}
# config.csv MaxHealth* — getOppMaxHealth(stage)
MAX_HEALTH = {"Rookie": 10, "Champion": 15, "Ultimate": 20, "Mega": 30}
MAX_HEALTH_DEFAULT = 10
# config.csv *AIWins thresholds (player win count -> enemy AI tier)
AI_RANDOM, AI_BRUTE, AI_STRAT_BRUTE, AI_STRAT_DEFENSE, AI_STRAT_BALANCED = 0, 15, 30, 45, 60


def ai_for_wins(wins, enemy_outmatches_player):
    """Battle ctor: enemy AIType from the player's win count."""
    if wins < AI_BRUTE:
        return "Random"
    if wins < AI_STRAT_BRUTE:
        return "Brute"
    if wins < AI_STRAT_DEFENSE:
        return "StrategicBrute"
    if wins < AI_STRAT_BALANCED:
        return "StrategicDefense"
    return "StrategicDefense" if enemy_outmatches_player else "StrategicBalanced"


def calc_attack_power(attr, my, opp):
    """Battle.calcAttackPower -> -1 / 0 / +1 (this side's count vs opponent's)."""
    if my[attr] > opp[attr]:
        return 1
    if my[attr] < opp[attr]:
        return -1
    return 0


def pick_enemy(pet, boss=False):
    pool = [e for e in data.enemies_for_stage(pet.stage) if e["boss"] == boss] \
        or data.enemies_for_stage(pet.stage)
    real = [e for e in pool if not data.is_placeholder(e["num"])]
    return random.choice(real or pool)


class Battle:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.enemy = dict(enemy or pick_enemy(pet))
        self._pet_counts = {"Vaccine": pet.vaccine, "Data": pet.data_power, "Virus": pet.virus}
        self._enemy_counts = {"Vaccine": self.enemy["vaccine"],
                              "Data": self.enemy["data_power"], "Virus": self.enemy["virus"]}
        # Enemy.getOppAttribute = its strongest power (battle "type")
        self.enemy["attribute"] = max(ATTRS, key=lambda a: self._enemy_counts[a])
        self.pet_max = self.pet_hp = MAX_HEALTH.get(pet.stage, MAX_HEALTH_DEFAULT)
        self.enemy_max = self.enemy_hp = max(2, self.enemy["hp"])
        psum = sum(self._pet_counts.values()) + self.pet_hp
        esum = sum(self._enemy_counts.values()) + self.enemy_hp
        self.ai = ai_for_wins(pet.wins, esum > psum)
        self.round = 0
        self.over = False
        self.won = None
        self.last = ""
        self.last_player_attr = None
        self.last_enemy_attr = None
        self.last_player_damage = 0
        self.last_enemy_damage = 0
        self._pet_zero_attack = None       # checkRememberZeroAttack
        self._enemy_zero_attack = None
        self.surrendered = False           # player-surrender not yet ported; never set

    def _damage(self, stage, attr, my, opp):
        atk = BASE_ATTACK.get(stage, 5) + calc_attack_power(attr, my, opp)  # + affinity (0)
        return atk if atk > 0 else 0

    def _enemy_choice(self):
        """enemyAttackChoose, dispatched on the AI type."""
        ec, pc = self._enemy_counts, self._pet_counts
        nonzero = [a for a in ATTRS if ec[a] > 0]
        if not nonzero:                                  # no usable attribute -> own type
            return self.enemy["attribute"]
        if self.ai == "Random":                          # randomAI
            return random.choice(nonzero)
        # brute / strategic: best calcAttackPower delta, avoiding the zero-attack,
        # tie-broken by greatest raw count (checkAttackTotalAndZero)
        cand = [a for a in nonzero if a != self._enemy_zero_attack] or nonzero
        best = max(calc_attack_power(a, ec, pc) for a in cand)
        top = [a for a in cand if calc_attack_power(a, ec, pc) == best]
        return max(top, key=lambda a: ec[a])

    def play_round(self, player_attr):
        if self.over:
            return self.last
        self.round += 1
        enemy_attr = self._enemy_choice()
        self.last_player_attr = player_attr
        self.last_enemy_attr = enemy_attr
        pdmg = self._damage(self.pet.stage, player_attr, self._pet_counts, self._enemy_counts)
        edmg = self._damage(self.enemy["stage"], enemy_attr, self._enemy_counts, self._pet_counts)
        self.last_player_damage, self.last_enemy_damage = pdmg, edmg
        move = data.move_name(self.pet.num, player_attr) or player_attr
        emove = data.move_name(self.enemy["num"], enemy_attr) or enemy_attr
        # sequential resolution; checkFinish ends the moment a side hits 0, so a
        # KO'd enemy never retaliates. _playerFirst defaults true (effect 5, which
        # can flip it, is part of the unported chip layer).
        self.enemy_hp -= pdmg
        if pdmg <= 0:
            self._pet_zero_attack = player_attr
        if self.enemy_hp > 0:
            self.pet_hp -= edmg
            if edmg <= 0:
                self._enemy_zero_attack = enemy_attr
        self.last = f"R{self.round}: {move} →{pdmg}   foe {emove} →{edmg}"
        if self.pet_hp <= 0 or self.enemy_hp <= 0:
            self._finish()
        return self.last

    def _finish(self):
        self.over = True
        self.won = self.pet_hp > 0          # battleEnd: player loses iff _health <= 0
        self.reward = self.pet.record_battle(self.won, self.enemy)
