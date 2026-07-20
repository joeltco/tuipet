"""Battle — the 0.5 HP race (clone rebuild 2026-07-15; ported onto the
classic tree 2026-07-17, Joel: "replace the battle system" — DSprite is
the ultimate truth for animations and mechanics).

Both sides start at 5 HP.  The whole fight is PRECOMPUTED round by round
(the screen replays it): each round both sides roll to hit; damage per
landed hit is the side's PROJECTILE count, which comes from its trained
hit-type (mega: 90% double / normal: 50% / miss: 20%).  The per-round hit
chance is care's scoreboard — win rate, stage rank, this-stage training,
lifetime training, strength/hunger/energy meters, weight closeness and the
attribute triangle all feed it.  Transcribed EXACTLY from the source rule
set (ripped from multiple fan games).
"""
from __future__ import annotations
import random

from . import data

HP = 5
ROUNDS_LOCAL = 20
ROUNDS_ONLINE = 5
ROUNDS_RAID = 10
RAID_PLAYER_HP = 10

# battle stage ranks on the CLASSIC growth ladder (the clone's Baby I..
# Super Ultimate names mapped to this roster's Fresh..Mega; no Armor/
# Special tiers ship here)
_RANK = {"Egg": 0, "Fresh": 1, "InTraining": 2, "Rookie": 3,
         "Champion": 4, "Ultimate": 5, "Mega": 6}


def _tri(mine, theirs):
    """The attribute triangle: ±0.05 hit chance."""
    a, b = (mine or "").lower(), (theirs or "").lower()
    if (a, b) in (("vaccine", "virus"), ("virus", "data"), ("data", "vaccine")):
        return 0.05
    if (a, b) in (("virus", "vaccine"), ("data", "virus"), ("vaccine", "data")):
        return -0.05
    return 0


class Side:
    """One combatant, normalized: a live Pet, a lobby card, or a wild foe."""

    def __init__(self, num, name="", stage="", attribute="",
                 strength=4, strength_max=4, hunger=4, hunger_max=4,
                 energy=5, energy_max=5, weight=None, base_weight=10,
                 trainings_cur=0, trainings_total=0,
                 battles=0, wins=0, hit_type="normal", boss=False):
        self.num = num
        self.name = name or (data.record_for(num).get("name", "?") if num >= 0 else "?")
        self.stage = stage
        self.attribute = attribute
        self.strength, self.strength_max = strength, max(1, strength_max)
        self.hunger, self.hunger_max = hunger, max(1, hunger_max)
        self.energy, self.energy_max = energy, max(1, energy_max)
        self.base_weight = base_weight
        self.weight = base_weight if weight is None else weight
        self.trainings_cur = trainings_cur
        self.trainings_total = trainings_total
        self.battles, self.wins = battles, wins
        self.hit_type = "mega" if battles >= 999 else hit_type
        self.boss = boss

    @classmethod
    def of_pet(cls, pet):
        return cls(pet.num, name=pet.name, stage=pet.stage,
                   attribute=pet.attribute,
                   strength=pet.strength, strength_max=4,
                   hunger=pet.hunger, hunger_max=4,
                   energy=max(0, pet.energy), energy_max=pet.max_energy,
                   weight=pet.weight, base_weight=pet._base_weight(),
                   trainings_cur=pet.stage_trainings,
                   trainings_total=getattr(pet, "total_trainings", 0),
                   battles=pet.battles, wins=pet.wins,
                   hit_type=getattr(pet, "saved_hit_type", "normal"))

    @classmethod
    def wild(cls, num, boss=False):
        """A wild foe: its species at ideal condition, untrained.  (The
        classic roster carries no meter columns -- ideal condition IS the
        definition, so the perfect gauges are pinned directly.)"""
        rec = data.record_for(num)
        return cls(num, name=rec.get("name", "?"), stage=rec.get("stage", ""),
                   attribute=rec.get("attribute", "Free"),
                   strength=4, strength_max=4, hunger=4, hunger_max=4,
                   energy=5, energy_max=5,
                   weight=10, base_weight=10, boss=boss)

    @classmethod
    def of_card(cls, card):
        """A lobby peer's relayed card (clamped upstream)."""
        return cls(int(card.get("num", 0)), name=card.get("name", "?"),
                   stage=card.get("stage", "Child"),
                   attribute=card.get("attribute", "Free"),
                   strength=card.get("strength", 4),
                   strength_max=card.get("strength_max", 4),
                   hunger=card.get("hunger", 4),
                   hunger_max=card.get("hunger_max", 4),
                   energy=card.get("energy", 5),
                   energy_max=card.get("energy_max", 5),
                   weight=card.get("weight", 10),
                   base_weight=card.get("base_weight", 10),
                   trainings_cur=card.get("trainings_cur", 0),
                   trainings_total=card.get("trainings_total", 0),
                   battles=card.get("battles", 0), wins=card.get("wins", 0),
                   hit_type=card.get("hit_type", "normal"))

    def _rank(self):
        return _RANK.get(self.stage, 3)

    def _condition(self):
        """The meter terms of the hit formula (each 0..0.1 - 0.05)."""
        st = (self.strength / self.strength_max) * 0.1 - 0.05
        hu = (self.hunger / self.hunger_max) * 0.1 - 0.05
        en = (self.energy / self.energy_max) * 0.1 - 0.05
        if self.base_weight > 0:
            w = (1 - min(1, abs(self.weight - self.base_weight) / 15)) * 0.2 - 0.1
        else:
            w = 0
        return st + hu + en + w

    def hit_chance(self, other):
        wr = self.wins / self.battles if self.battles > 0 else 0.5
        p = (0.3 + (wr - 0.5) * 0.1
             + (self._rank() - other._rank()) * 0.1
             + min(self.trainings_cur / 999 * 0.1, 0.1)
             + min(self.trainings_total / 9999 * 0.2, 0.2)
             + self._condition()
             + _tri(self.attribute, other.attribute))
        return min(1.0, max(0.0, p))

    def roll_damage(self, rng):
        t = self.hit_type
        if t == "mega":
            return 2 if rng() < 0.9 else 1
        if t == "miss":
            return 2 if rng() < 0.2 else 1
        return 2 if rng() < 0.5 else 1


def generate(me, foe, rounds=ROUNDS_LOCAL, rng=None):
    """The whole fight: [(my_hit, my_dmg, foe_hit, foe_dmg), ...] plus final
    HPs.  A simultaneous double-KO flips a fair coin on who whiffs."""
    rng = rng or random.random
    my_hp, foe_hp = HP, HP
    p_me, p_foe = me.hit_chance(foe), foe.hit_chance(me)
    seq = []
    for _ in range(rounds):
        if my_hp <= 0 or foe_hp <= 0:
            break
        my_dmg = me.roll_damage(rng)
        my_hit = rng() < p_me
        foe_dmg = foe.roll_damage(rng)
        foe_hit = rng() < p_foe
        if my_hit and foe_hit:
            if my_hp - foe_dmg <= 0 and foe_hp - my_dmg <= 0:
                if rng() < 0.5:
                    foe_hit = False
                else:
                    my_hit = False
        if my_hit:
            foe_hp -= my_dmg
        if foe_hit:
            my_hp -= foe_dmg
        seq.append((my_hit, my_dmg, foe_hit, foe_dmg))
    return seq, max(0, my_hp), max(0, foe_hp)


class Battle:
    """A playable fight the screen steps through round by round."""

    def __init__(self, pet, enemy=None, source="battle", rng=None,
                 rounds=ROUNDS_LOCAL):
        self.pet = pet
        rng = rng or random.random
        if enemy is None:
            enemy = pick_enemy(pet)
        self.enemy = enemy                     # dict, kept for the HUD
        # (the clone duck-typed on hunger_max, a clone-pet field; the classic
        # pet has flat 4-heart gauges, so type on Side directly)
        self.me = pet if isinstance(pet, Side) else Side.of_pet(pet)
        self.foe = enemy["side"] if "side" in enemy else Side.wild(
            enemy.get("num", 0), boss=bool(enemy.get("boss")))
        self.seq, self._my_end, self._foe_end = generate(
            self.me, self.foe, rounds=rounds, rng=rng)
        self.pet_hp, self.enemy_hp = HP, HP
        self.pet_max = self.enemy_max = HP
        self.round = 0
        self.over = False
        self.won = False
        self.reward = ""
        self.source = source

    def play_round(self, _choice=None):
        """Advance one precomputed round -> the round record for the stage
        show: dict(pdmg, edmg, my_hit, foe_hit, ph, fh)."""
        if self.over or self.round >= len(self.seq):
            self._finish()
            return None
        my_hit, my_dmg, foe_hit, foe_dmg = self.seq[self.round]
        self.round += 1
        if my_hit:
            self.enemy_hp = max(0, self.enemy_hp - my_dmg)
        if foe_hit:
            self.pet_hp = max(0, self.pet_hp - foe_dmg)
        rec = {"pdmg": my_dmg if my_hit else 0,
               "edmg": foe_dmg if foe_hit else 0,
               "my_hit": my_hit, "foe_hit": foe_hit,
               "ph": self.pet_hp, "fh": self.enemy_hp}
        if self.pet_hp <= 0 or self.enemy_hp <= 0 \
                or self.round >= len(self.seq):
            self._finish()
        return rec

    def _finish(self):
        if self.over:
            return
        self.over = True
        # winner: the standing side; equal HP reads as a narrow win for the
        # higher survivor, a draw counts as a loss for progression
        if self.enemy_hp <= 0 and self.pet_hp > 0:
            self.won = True
        elif self.pet_hp <= 0:
            self.won = False
        else:
            self.won = self.pet_hp > self.enemy_hp
        if hasattr(self.pet, "record_battle"):
            self.pet.record_battle(self.won, self.enemy,
                                   online=self.source == "pvp")
        if self.source != "pvp":
            # record_battle grants the +2 on EVERY local bout, win or lose --
            # gating the line on won left the losing grant silent under a
            # DEFEAT card with an empty reward line
            self.reward = "training +2"

    def surrender(self):
        if self.over:
            return          # the bout already ended -- never a second
            #                 record_battle on top of _finish's (audit 2026-07-19)
        self.over = True
        self.won = False
        if hasattr(self.pet, "record_battle"):
            self.pet.record_battle(False, self.enemy,
                                   online=self.source == "pvp")
        if self.source != "pvp":
            self.reward = "training +2"      # the surrendered bout still bills + trains


class RaidBout:
    """The raid attempt wearing the Battle interface, so the battlescreen
    can replay it with the full volley show (tuipet raid adaptation: the
    clone ran raids as lobby text -- Joel demanded sprites).  10 rounds
    from RAID_PLAYER_HP; the boss NEVER falls (its bar holds at full) and
    `dealt` accumulates for the relay report.  Writes NOTHING on the pet,
    exactly like the clone's generate_raid."""

    def __init__(self, pet, boss, rng=None):
        self.pet = pet
        self.enemy = boss                        # dict, kept for the HUD
        me = Side.of_pet(pet)
        foe = Side.wild(int(boss.get("num", 0)), boss=True)
        self.seq, self.dealt, self._end_hp = generate_raid(me, foe, rng=rng)
        self.pet_hp = self.pet_max = RAID_PLAYER_HP
        self.enemy_hp = self.enemy_max = HP      # display only
        self.round = 0
        self.over = False
        self.won = False
        self.reward = ""
        self.source = "raid"

    def play_round(self, _choice=None):
        if self.over or self.round >= len(self.seq):
            self._finish()
            return None
        my_hit, my_dmg, boss_hit, boss_dmg = self.seq[self.round]
        self.round += 1
        if boss_hit:
            self.pet_hp = max(0, self.pet_hp - boss_dmg)
        rec = {"pdmg": my_dmg if my_hit else 0,
               "edmg": boss_dmg if boss_hit else 0,
               "my_hit": my_hit, "foe_hit": boss_hit,
               "ph": self.pet_hp, "fh": self.enemy_hp}
        if self.pet_hp <= 0 or self.round >= len(self.seq):
            self._finish()
        return rec

    def _finish(self):
        self.over = True                         # no record_battle: a report, not a bout
        # presentation only: the ATTEMPT succeeded when the pet stood through
        # its rounds -- won=False forever ended EVERY raid on the loser
        # collapse frame, even a full-damage run (the boss still never falls)
        self.won = self.pet_hp > 0

    def surrender(self):
        self.over = True


def generate_raid(me, boss, rng=None):
    """The raid attempt: 10 rounds against an effectively-invincible boss.
    The player fights from 10 HP; the boss never falls IN the fight -- the
    raw damage landed here is what the shared pool eats (x5000 x stage-mult,
    applied server-side).  Returns (rounds, raw_dealt, my_end_hp)."""
    rng = rng or random.random
    my_hp = RAID_PLAYER_HP
    p_me, p_boss = me.hit_chance(boss), boss.hit_chance(me)
    seq = []
    dealt = 0
    for _ in range(ROUNDS_RAID):
        if my_hp <= 0:
            break
        my_dmg = me.roll_damage(rng)
        my_hit = rng() < p_me
        boss_dmg = boss.roll_damage(rng)
        boss_hit = rng() < p_boss
        if my_hit:
            dealt += my_dmg
        if boss_hit:
            my_hp -= boss_dmg
        seq.append((my_hit, my_dmg, boss_hit, boss_dmg))
    return seq, dealt, max(0, my_hp)


def pick_enemy(pet, boss=False):
    """A wild foe scaled to the pet: same stage bracket, one up for a boss."""
    ladder = ["InTraining", "Rookie", "Champion", "Ultimate", "Mega"]
    st = pet.stage if pet.stage in ladder else "Rookie"
    if boss and ladder.index(st) < len(ladder) - 1:
        st = ladder[ladder.index(st) + 1]
    pool = [r for r in data.load_sprites()[0] if r["stage"] == st]
    rec = random.choice(pool)
    return {"num": rec["num"], "name": rec["name"], "boss": boss,
            "stage": rec["stage"], "attribute": rec["attribute"]}


def battle_card(pet):
    """The stats card a lobby host/challenger relays (clamped by the peer)."""
    s = Side.of_pet(pet)
    return {"num": s.num, "name": s.name, "stage": s.stage,
            "attribute": s.attribute,
            "strength": s.strength, "strength_max": s.strength_max,
            "hunger": s.hunger, "hunger_max": s.hunger_max,
            "energy": s.energy, "energy_max": s.energy_max,
            "weight": s.weight, "base_weight": s.base_weight,
            "trainings_cur": s.trainings_cur,
            "trainings_total": s.trainings_total,
            "battles": s.battles, "wins": s.wins, "hit_type": s.hit_type,
            "proto": 3, "hp": HP}


# plausible_card is gone (audit 2026-07-15): it was never called, and the
# real anti-tamper line is lobbyscreen._clamp_card, which now also derives
# stage/attribute from the claimed num's species record.
