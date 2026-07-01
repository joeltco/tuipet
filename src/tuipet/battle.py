"""Battle engine — a faithful port of DVPet's Model.Battle combat.

Every value below is decompiled from raw_model/Battle.class + config.csv; nothing
here is invented. Where a DVPet subsystem cannot be reproduced from the shipped
data it is documented as such rather than approximated.

HP (Battle.setupOpponents / getOppMaxHealth):
  player starts full at the per-stage MaxHealth; enemy at its enemies.csv Health
  (Enemy.getEnemyHealth). config MaxHealth*: Rookie 10, Champion 15, Ultimate 20,
  Mega 25, default 10.

Per-round damage (Battle.attack -> finishAttack):
      dmg = getBaseAttack(stage) + calcAttackPower(attr) + affinityBonus
  getBaseAttack (config *BaseAttack): Fresh 1, InTraining 2, Rookie/Champion/
  Ultimate/Mega 5.  calcAttackPower (Battle.calcAttackPower) returns -1/0/+1 by
  comparing THIS side's count in the chosen attribute against the opponent's
  count (counts = vaccine/data/virus power).  affinityBonus (Battle.calcBonus =
  field-vs-field + element-vs-element affinity) is 0: the shipped fieldAffinity
  and elementAffinity matrices are entirely zero.  _attack is floored at 0.

Enemy AI (tuipet ADAPTATION -- deliberately NOT faithful; kept as a difficulty ramp):
  tuipet sets the ENEMY's AI tier from the PLAYER's win count:
    wins <15 Random, <30 Brute, <45 StrategicBrute, <60 StrategicDefense,
    >=60 StrategicDefense if (enemy power-sum+HP) > (player power-sum+HP) else
    StrategicBalanced.  (config *AIWins: 0/15/30/45/60.)
  In DVPet this win-count ladder actually sets the *player's* auto-AI (_playerAI,
  Battle.java 261-270). The real ENEMY AI is randomizeAI(isBoss) -- a RANDOM tier
  each battle (non-boss ~1/3 Random / 1/3 Brute / 1/3 Strategic; boss always
  Strategic). tuipet makes attack-picking interactive (the human chooses), so
  _playerAI has no role here and the win-count formula is repurposed onto the enemy
  ON PURPOSE, so foes get tougher as you win. Intentional difficulty ramp, NOT fidelity.

  Attack choice is also SIMPLIFIED (another deliberate adaptation):
    randomAI -> random among attributes with count>0 (this part is faithful).
    every non-random tier -> ONE brute-style pick: best calcAttackPower delta,
      tie-break greatest raw count, avoiding the remembered zero-attack.
  DVPet's real Brute vs evenStrategy/bruteStrategy/defenseStrategy differ (health-
  based defending at <=half HP, checkAttackTotalAndZero specific tie-breaks,
  checkZeroAttackSubstitute, and per-effect weights via checkAttackWeight/
  checkDefendWeight). tuipet does not replicate those.
  (AttackEffects ARE populated in the shipped data -- ~62% of attacks -- but wild
  enemies from enemies.csv carry none, so those weights would not change a wild
  enemy's pick regardless.)

Win/lose (Battle.checkFinish / battleEnd): the battle ends the instant either
HP <= 0; the player loses iff its OWN HP <= 0 (a double-KO is therefore a loss).

Companion systems (ported elsewhere, faithful):
  - AttackEffect/AttackCondition chip layer -> battlefx.py (the per-attribute
    effect+condition data is pre-baked into digimon.csv and resolved per round).
  - Player-side surrender/escape (PhysicalState.checkSurrender) -> pet.py
    (check_surrender / surrender_effect); battlescreen drives the Y/N request and
    Battle.surrender() ends the bout as neither win nor loss.
"""
from __future__ import annotations
import random
from . import data
from . import battlefx

ATTRS = ("Vaccine", "Data", "Virus")

# config.csv *BaseAttack (per growth stage)
BASE_ATTACK = {"Fresh": 1, "InTraining": 2, "Rookie": 5,
               "Champion": 5, "Ultimate": 5, "Mega": 5}
# config.csv MaxHealth* — getOppMaxHealth(stage)
MAX_HEALTH = {"Rookie": 10, "Champion": 15, "Ultimate": 20, "Mega": 25}  # config MaxHealth* (classic)
MAX_HEALTH_DEFAULT = 10
# config.csv *AIWins thresholds (player win count -> enemy AI tier)
AI_RANDOM, AI_BRUTE, AI_STRAT_BRUTE, AI_STRAT_DEFENSE, AI_STRAT_BALANCED = 0, 15, 30, 45, 60


def ai_for_wins(wins, enemy_outmatches_player):
    """tuipet enemy-difficulty ramp (ADAPTED): enemy AI tier from the player's win
    count. In DVPet this formula sets the *player's* auto-AI; the real enemy AI is
    randomizeAI(isBoss). Repurposed here on purpose -- see module docstring."""
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


def battle_card(pet):
    """A pet's battle-relevant snapshot, used as the opponent's Enemy dict in PvP."""
    _, by = data.load_sprites()
    return {"num": pet.num,
            "name": getattr(pet, "name", None) or by.get(pet.num, {}).get("name") or "?",
            "stage": pet.stage, "vaccine": pet.vaccine, "data_power": pet.data_power,
            "virus": pet.virus, "hp": MAX_HEALTH.get(pet.stage, MAX_HEALTH_DEFAULT), "bits": (1, 5)}


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
        self.last_player_first = True
        self._pet_zero_attack = None       # checkRememberZeroAttack
        self._enemy_zero_attack = None
        self.last_effect = None            # the player chip that fired this round (DefenseUp etc.)
        self.surrendered = False           # set True by surrender() (PhysicalState.checkSurrender)
        self._forced_enemy_attr = None     # PvP: the partner's real choice overrides the AI

    def _damage(self, stage, attr, my, opp):
        atk = BASE_ATTACK.get(stage, 5) + calc_attack_power(attr, my, opp)  # + affinity (0)
        return atk if atk > 0 else 0

    def _enemy_choice(self):
        """enemyAttackChoose, dispatched on the AI type."""
        if self._forced_enemy_attr is not None:        # PvP: use the partner's move
            return self._forced_enemy_attr
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
        pdmg = self._damage(self.pet.stage, player_attr, self._pet_counts, self._enemy_counts)
        edmg = self._damage(self.enemy["stage"], enemy_attr, self._enemy_counts, self._pet_counts)
        # attack-effect "chip" layer (AttackEffectProcess): the player's attack effect
        # fires if its conditions pass, adjusting damage / initiative / health changes.
        fx = battlefx.resolve(self, player_attr, enemy_attr, pdmg, edmg)
        self.last_effect = fx.get("effect_fired")
        pdmg, edmg, enemy_attr = fx["pdmg"], fx["edmg"], fx["enemy_attr"]
        self.last_enemy_attr = enemy_attr
        self.last_player_damage, self.last_enemy_damage = pdmg, edmg
        self.last_player_first = fx["player_first"]    # initiative order (checkFirst) for the View
        move = data.move_name(self.pet.num, player_attr) or player_attr
        emove = data.move_name(self.enemy["num"], enemy_attr) or enemy_attr
        # resolve in initiative order (checkFirst / First / Counter / ForcePlayerSecond);
        # a KO'd side does not retaliate (checkFinish ends the moment HP hits 0).
        if fx["player_first"]:
            self.enemy_hp -= pdmg
            if self.enemy_hp > 0:
                self.pet_hp -= edmg
        else:
            self.pet_hp -= edmg
            if self.pet_hp > 0:
                self.enemy_hp -= pdmg
        if pdmg <= 0:
            self._pet_zero_attack = player_attr
        if edmg <= 0:
            self._enemy_zero_attack = enemy_attr
        # processHealthChange: Leech/Absorb/Heal heal; Sacrifice* costs (clamped to max)
        if fx["phc"]:
            self.pet_hp = min(self.pet_max, self.pet_hp + fx["phc"])
        if fx["ehc"]:
            self.enemy_hp = min(self.enemy_max, self.enemy_hp + fx["ehc"])
        self.last = f"R{self.round}: {move} →{pdmg}   foe {emove} →{edmg}"
        if self.pet_hp <= 0 or self.enemy_hp <= 0:
            self._finish()
        return self.last

    def _finish(self):
        self.over = True
        self.won = self.pet_hp > 0          # battleEnd: player loses iff _health <= 0
        self.reward = self.pet.record_battle(self.won, self.enemy)

    def surrender(self):
        """Battle.surrender: the pet bows out -- the bout ends as neither win nor loss.
        Costs SurrenderEnthusiasmDec spirit; a fixed (non-random) foe still counts as a
        battle fought.  SurrenderEnergyDec/SurrenderWeightDec are 0 in the shipped config."""
        from .pet import SURR_ENTH_DEC
        self.over = True
        self.won = False
        self.surrendered = True
        self.reward = "Surrendered."
        self.pet._set_enthusiasm(self.pet.enthusiasm - SURR_ENTH_DEC)
        if self.enemy.get("boss"):          # getIsRandom() == false -> battles += 1
            self.pet.battles += 1
