"""Battle engine — the authentic DM20 model (manual-verified).

DM20 battle is decided by POWER, not HP attrition:
  - Each Digimon has ONE fixed attribute (Vaccine/Data/Virus/Free) and a Power stat
    (its total attribute power).  You do NOT pick an attribute per round.
  - The attribute triangle Vaccine▸Virus▸Data▸Vaccine grants a +32 EFFECTIVE POWER
    bonus when your attribute beats the foe's (manual: "a +32 bonus to your Power").
    Free gets no bonus.
  - "If your power is higher than your enemy's power, your attacks are more likely to
    hit; the higher the difference, the higher the likelihood" -> hit chance is derived
    from the effective-power difference.
  - A pre-battle attack-order minigame sets who strikes first (`player_first`).
  - The clash then resolves automatically: attacks trade in initiative order, each one
    landing (a hit) or missing (a dodge) by its hit chance, until one side's small HP
    (a few clash "hearts") is depleted.
  - Losing (and sometimes winning) risks an injury; battling spends DP; the win record
    gates Stage V.  (All in pet.record_battle.)

`resolve()` plays the whole clash and returns a flat list of attack events that the
battle View animates; an optional seeded rng makes it deterministic for online PvP.
"""
from __future__ import annotations
import random
from . import data
from . import species

ATTRS = ("Vaccine", "Data", "Virus")
# Rock-paper-scissors: Vaccine beats Virus beats Data beats Vaccine.  Free beats nothing.
ATTR_BEATS = {"Vaccine": "Virus", "Virus": "Data", "Data": "Vaccine"}
ATTR_BONUS = 32                                  # manual: an attribute advantage = +32 Power

# clash "hearts" per authentic growth stage -- small, so a bout is a few decisive trades
MAX_HEALTH = {"Baby I": 2, "Baby II": 2, "Child": 3,
              "Adult": 4, "Perfect": 4, "Ultimate": 5, "Super Ultimate": 5}
MAX_HEALTH_DEFAULT = 3


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def beats(a, b):
    """True if attribute a has the triangle advantage over attribute b."""
    return ATTR_BEATS.get(a) == b


def effective_power(power, my_attr, opp_attr):
    """Power plus the +32 triangle bonus when my attribute beats the opponent's."""
    return power + (ATTR_BONUS if beats(my_attr, opp_attr) else 0)


def hit_chance(my_ep, opp_ep):
    """Manual: higher power -> more likely to hit, bigger gap -> higher likelihood."""
    return _clamp(0.55 + (my_ep - opp_ep) / 160.0, 0.15, 0.90)


def _hit_damage(margin, rng):
    """A landed hit does 1 (weak); a clear power edge can land a 2 (strong/critical)."""
    if margin > 16 and rng.random() < min(0.6, margin / 96.0):
        return 2
    return 1


def _norm_attr(a):
    return a if a in ATTRS else "Free"


def _enemy_from_species(r, boss=False):
    """Build an opponent dict from an authentic species record: its Power + attribute
    (base Power from humulos via species.base_power; a per-stage default for null-power mons)."""
    return {"num": r["num"], "name": r["name"], "stage": r["stage"],
            "attribute": _norm_attr(r.get("attribute")),
            "power": species.base_power(r["num"]),
            "hp": MAX_HEALTH.get(r["stage"], MAX_HEALTH_DEFAULT), "boss": boss}


def pick_enemy(pet, boss=False):
    """A stage-appropriate opponent drawn from the authentic DM20 roster."""
    pool = [r for r in species.roster()
            if r["stage"] == pet.stage and not data.is_placeholder(r["num"])]
    if not pool:
        pool = [r for r in species.roster() if not data.is_placeholder(r["num"])]
    if boss:                                     # a boss is the strongest of a small sample
        pool = sorted(random.sample(pool, min(5, len(pool))),
                      key=lambda r: r.get("power") or 0)[-1:] or pool
    return _enemy_from_species(random.choice(pool), boss)


def battle_card(pet):
    """A pet's battle snapshot, used as the opponent's dict in PvP (Power + attribute)."""
    _, by = data.load_sprites()
    return {"num": pet.num,
            "name": getattr(pet, "name", None) or by.get(pet.num, {}).get("name") or "?",
            "stage": pet.stage, "attribute": _norm_attr(getattr(pet, "attribute", "")),
            "power": int(pet.power), "hp": MAX_HEALTH.get(pet.stage, MAX_HEALTH_DEFAULT)}


class Battle:
    def __init__(self, pet, enemy=None):
        self.pet = pet
        self.enemy = dict(enemy or pick_enemy(pet))
        self.enemy["attribute"] = _norm_attr(self.enemy.get("attribute"))
        # Power + the attribute triangle -> each side's EFFECTIVE power
        self.pet_attr = _norm_attr(getattr(pet, "attribute", ""))
        self.enemy_attr = self.enemy["attribute"]
        self.pet_power = int(pet.power)
        self.enemy_power = int(self.enemy.get("power") or 30)
        self.pet_ep = effective_power(self.pet_power, self.pet_attr, self.enemy_attr)
        self.enemy_ep = effective_power(self.enemy_power, self.enemy_attr, self.pet_attr)
        self.pet_max = self.pet_hp = MAX_HEALTH.get(pet.stage, MAX_HEALTH_DEFAULT)
        self.enemy_max = self.enemy_hp = max(1, int(self.enemy.get("hp") or MAX_HEALTH_DEFAULT))
        self.over = False
        self.won = None
        self.surrendered = False
        self.reward = ""
        self.attacks = []
        self.player_first = True

    def _finish(self):
        if self.over:
            return
        self.over = True
        self.won = self.pet_hp > 0                # a double-KO (both 0) is a loss
        self.reward = self.pet.record_battle(self.won, self.enemy)

    def resolve(self, player_first=None, rng=None):
        """Play the whole clash. `player_first` (from the minigame) sets initiative; an
        optional seeded `rng` makes the outcome reproducible for online PvP.  Returns the
        flat list of attack events the View animates."""
        rng = rng or random
        first = (rng.random() < 0.5) if player_first is None else bool(player_first)
        self.player_first = first
        p_hit = hit_chance(self.pet_ep, self.enemy_ep)
        e_hit = hit_chance(self.enemy_ep, self.pet_ep)
        attacks = []
        guard = 0
        while not self.over and guard < 40:       # guard: a stray endless clash can't hang
            guard += 1
            for who in (("pet", "foe") if first else ("foe", "pet")):
                if self.over:
                    break
                if who == "pet":
                    dmg = _hit_damage(self.pet_ep - self.enemy_ep, rng) if rng.random() < p_hit else 0
                    self.enemy_hp = max(0, self.enemy_hp - dmg)
                else:
                    dmg = _hit_damage(self.enemy_ep - self.pet_ep, rng) if rng.random() < e_hit else 0
                    self.pet_hp = max(0, self.pet_hp - dmg)
                attacks.append({"atk": who, "dmg": dmg, "ph": self.pet_hp,
                                "fh": self.enemy_hp, "double": dmg >= 2})
                if self.pet_hp <= 0 or self.enemy_hp <= 0:
                    self._finish()
        if not self.over:                         # ran the guard out -> decide by remaining HP
            self.won = self.pet_hp >= self.enemy_hp
            self._finish()
        self.attacks = attacks
        return attacks

    def surrender(self):
        """The pet bows out -- the bout ends as neither win nor loss.  A fixed (non-random)
        foe still counts as a battle fought."""
        self.over = True
        self.won = False
        self.surrendered = True
        self.reward = "Surrendered."
        if self.enemy.get("boss"):
            self.pet.battles += 1
