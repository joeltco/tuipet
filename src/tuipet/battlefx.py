"""DVPet attack-effect / attack-condition system — a port of AttackEffectProcess
(checkEffect / checkCondition / checkSpecialConditions / calcGreater*).

Each Digimon attack in digimon.csv is "Name:Effect:Cond1:Cond2..." (parsed by
data.attack_info). In a round the chosen attack's effect fires only if ALL its
conditions pass (checkValidConditions: empty list => never fires). In PvE only
the player's attack carries effect data (enemies.csv has none), so this resolves
the player effect against the live battle state.

Everything here is decompiled from raw_model/AttackEffectProcess.class +
Enum$AttackEffect/Enum$AttackCondition; the is_player=True branch of the 52-case
checkCondition is what applies (player effect). Field abbreviations come from
getPlayerFieldOverrideAbbreviation.
"""
from __future__ import annotations
import random
from . import data

FIELD_ABBR = {"NSP": "NatureSpirit", "NS": "NightmareSoldier", "DR": "DragonsRoar",
              "DS": "DeepSaver", "WG": "WindGuardian", "DA": "DarkArea", "NA": "None",
              "JT": "JungleTrooper", "ME": "MetalEmpire", "VB": "VirusBuster"}

# checkCondition cases 1-9 (None + the Sacrifice/ForcePlayerSecond/EffectTimes*/
# ConditionsTimes* meta-conditions) return constant true.
_ALWAYS_TRUE = {"None", "ForcePlayerSecond", "SacrificeAttack", "SacrificeDefense",
                "SacrificeHealth", "EffectTimesTwo", "EffectTimesThree",
                "ConditionsTimesTwo", "ConditionsTimesThree"}


def _greater_effect(conds):
    """calcGreaterEffect: 3 if EffectTimesThree, else 2 if EffectTimesTwo, else 1."""
    if "EffectTimesThree" in conds:
        return 3
    if "EffectTimesTwo" in conds:
        return 2
    return 1


def _greater_condition(conds):
    """calcGreaterCondition: 3 if ConditionsTimesThree, else 2 if ConditionsTimesTwo, else 1."""
    if "ConditionsTimesThree" in conds:
        return 3
    if "ConditionsTimesTwo" in conds:
        return 2
    return 1


def _condition(c, st):
    """checkCondition(c, isPlayer=True) -> bool (verbatim from the 52-case table)."""
    if c in _ALWAYS_TRUE:
        return True
    pa, ea = st["player_attr"], st["enemy_attr"]
    pc, ec = st["p_counts"], st["e_counts"]
    if c == "EnemyIsVaccine":
        return ea == "Vaccine"
    if c == "EnemyIsData":
        return ea == "Data"
    if c == "EnemyIsVirus":
        return ea == "Virus"
    if c == "PlayerIsVaccine":
        return pa == "Vaccine"
    if c == "PlayerIsData":
        return pa == "Data"
    if c == "PlayerIsVirus":
        return pa == "Virus"
    if c == "AttackVaccine":            # getOppAttack()==Vaccine (the opponent's attack)
        return ea == "Vaccine"
    if c == "AttackData":
        return ea == "Data"
    if c == "AttackVirus":
        return ea == "Virus"
    # "Weaker" and "Stronger" are byte-identical in the binary (both: my < opp)
    if c in ("VaccineWeaker", "VaccineStronger"):
        return pc["Vaccine"] < ec["Vaccine"]
    if c in ("DataWeaker", "DataStronger"):
        return pc["Data"] < ec["Data"]
    if c in ("VirusWeaker", "VirusStronger"):
        return pc["Virus"] < ec["Virus"]
    if c in ("PlayerWeaker", "PlayerStronger"):
        return sum(pc.values()) < sum(ec.values())
    if c == "PlayerIsVB":               # special: reads ENEMY field override (verbatim)
        return st["e_field"] == "VirusBuster"
    if c.startswith("EnemyIs"):         # field override
        return st["e_field"] == FIELD_ABBR.get(c[len("EnemyIs"):], c[len("EnemyIs"):])
    if c.startswith("PlayerIs"):        # field override (attribute PlayerIs* handled above)
        return st["p_field"] == FIELD_ABBR.get(c[len("PlayerIs"):], c[len("PlayerIs"):])
    if c in ("PlayerFirst", "PlayerSecond"):   # identical bytecode
        return st["player_first"]
    if c == "LowerPlayerHealth":
        return (st["health"] + st["phc"]) < (st["ehealth"] + st["ehc"])
    if c == "HigherPlayerHealth":       # vs getEnemyAttack(), not enemyHealth (verbatim)
        return (st["health"] + st["phc"]) < (st["edmg"] + st["ehc"])
    if c in ("HalfPlayerHealth", "HalfOppHealth"):   # identical for isPlayer=True
        return (st["health"] + st["phc"]) <= st["full"] // 2
    return False


def _valid_conditions(conds, st):
    """checkValidConditions: every condition must pass; an empty list returns false."""
    return bool(conds) and all(_condition(c, st) for c in conds)


def _special_conditions(conds, st):
    """checkSpecialConditions(isPlayer=True): Sacrifice*/ForcePlayerSecond pre-mutations."""
    gc = _greater_condition(conds)
    for c in conds:
        if c == "ForcePlayerSecond":
            st["player_first"] = False
        elif c == "SacrificeAttack":
            st["pdmg"] -= gc
        elif c == "SacrificeDefense":      # isPlayer=True -> raises enemy attack (verbatim)
            st["edmg"] += gc
        elif c == "SacrificeHealth":
            st["phc"] -= gc


def _check_effect(effect, conds, st, b):
    """checkEffect(isPlayer=True): mutate the round's damages / order / health changes."""
    ge = _greater_effect(conds)
    if effect == "AttackUp":
        st["pdmg"] += ge
    elif effect == "DefenseUp":
        if st["edmg"] - ge > 0:
            st["edmg"] -= ge
    elif effect == "Weaken":
        st["pdmg"] = 1
        st["edmg"] = 1
    elif effect == "DisableAttack":
        st["pdmg"] = 1
        st["edmg"] = 0
    elif effect == "DisableEffect":
        pass                               # nullifies the opponent's effect (enemy has none in PvE)
    elif effect == "Counter":
        st["player_first"] = False
        if st["edmg"] - ge > 0:
            st["edmg"] -= ge
        st["pdmg"] += ge
    elif effect == "First":
        st["player_first"] = True
    elif effect == "Second":
        st["player_first"] = False
    elif effect == "Leech":
        if st["health"] > ge:
            st["pdmg"] += ge
            st["phc"] += ge
    elif effect == "Absorb":
        if st["edmg"] - ge > 0:
            st["edmg"] -= ge
        st["phc"] += ge
    elif effect == "Heal":
        st["pdmg"] = 0
        st["phc"] += ge
    elif effect in ("ForceOppVaccine", "ForceOppData", "ForceOppVirus"):
        na = effect[len("ForceOpp"):]
        st["enemy_attr"] = na
        st["edmg"] = b._damage(b.enemy["stage"], na, b._enemy_counts, b._pet_counts)
    # PlayerIs*/EnemyIs* attribute/field overrides (ords 15-40) are read only by the
    # description/UI layer in DVPet, not by damage calc -> no battle mutation here.


def _check_first(b):
    """Battle.checkFirst: weighted (attack-sum * health-fraction); tie = coin
    flip -- drawn from the ENGINE's rng so seeded PvP peers flip identically."""
    ps = sum(b._pet_counts.values()) * (b.pet_hp / b.pet_max if b.pet_max else 1.0)
    es = sum(b._enemy_counts.values()) * (b.enemy_hp / b.enemy_max if b.enemy_max else 1.0)
    if ps > es:
        return True
    if ps < es:
        return False
    return getattr(b, "rng", random).random() < 0.5


def resolve(b, player_attr, enemy_attr, pdmg, edmg):
    """Run the player's attack effect (if its conditions pass) for this round.
    Returns the adjusted {pdmg, edmg, enemy_attr, player_first, phc, ehc}."""
    info = data.attack_info(b.pet.num, player_attr)
    effect, conds = info["effect"], info["conditions"]
    e_field = (data.load_sprites()[1].get(b.enemy["num"], {}) or {}).get("field", "") or ""
    st = {
        "player_attr": player_attr, "enemy_attr": enemy_attr,
        "p_counts": b._pet_counts, "e_counts": b._enemy_counts,
        "health": b.pet_hp, "full": b.pet_max, "ehealth": b.enemy_hp, "efull": b.enemy_max,
        "p_field": b.pet.field or "", "e_field": e_field,
        "pdmg": pdmg, "edmg": edmg, "phc": 0, "ehc": 0,
        "player_first": _check_first(b),
    }
    st["effect_fired"] = None
    if effect != "None" and _valid_conditions(conds, st):
        _special_conditions(conds, st)
        _check_effect(effect, conds, st, b)
        st["effect_fired"] = effect          # the chip that activated this round (View feedback)
    st["pdmg"] = max(0, st["pdmg"])
    st["edmg"] = max(0, st["edmg"])
    return st
