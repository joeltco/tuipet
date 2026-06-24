"""Tournament — faithful to DVPet's per-season trophy cups (tournies.csv).

Each trophy is a cup gated by Season + Field/Attribute restriction + age (stage), with
an 8-entrant single-elim bracket (Quarter/Semi/Final) whose opponents take the trophy's
enemy overrides. Winning awards bits = min(TourneyMaxBits, stage-base * BitModifier) plus
the trophy's ItemWon / FoodWon, and records the trophy for the season (resets on season
change when ResetWonOnSeasonChange). Each match reuses the battle engine, so tournament
fights still count toward battle/win evolution requirements.
"""
from __future__ import annotations
from . import battle, data

# config TourneyRookieBits/ChampBits/UltBits/MegaBits + TourneyMaxBits
TOURNEY_BITS = {"Rookie": 125, "Champion": 150, "Ultimate": 175, "Mega": 200}
TOURNEY_MAX_BITS = 225
ROUNDS = ["Quarterfinal", "Semifinal", "Final"]


def trophy_label(t):
    if t["field_req"]:
        return "%s Cup" % data.pretty_field(t["field_req"])
    if t["attr_req"]:
        return "%s Cup" % t["attr_req"]
    return "%s Open #%d" % (t["season"], t["id"])


def available(pet):
    """Trophies the pet may enter right now: current season + field/attribute restriction
    met + old enough + not already won this season (unless same-day retry)."""
    if pet.stage in ("Egg", "Fresh", "InTraining"):
        return []
    won = getattr(pet, "trophies_won", {}) or {}
    season = pet.season
    out = []
    for t in data.load_tournies():
        if t["season"] != season:
            continue
        if t["field_req"] and t["field_req"] != getattr(pet, "field", ""):
            continue
        if t["attr_req"] and t["attr_req"] != getattr(pet, "attribute", ""):
            continue
        if t["age_limit"] and data.stage_rank(pet.stage) < data.stage_rank(t["age_limit"]):
            continue
        ws = won.get(t["id"])
        if ws is not None and not t["same_day_retry"]:
            if not (t["reset_season"] and ws != season):   # won; back only after a season change
                continue
        out.append(t)
    return out


def can_enter(pet):
    if pet.stage in ("Egg", "Fresh", "InTraining"):
        return "Too young for the cup."
    if pet.asleep:
        return "zzz... asleep"
    if not available(pet):
        return "No cup open this season."
    return None


class Tournament:
    def __init__(self, pet, trophy):
        self.pet = pet
        self.trophy = trophy
        self.name = trophy_label(trophy)
        self.round = 0
        self.over = False
        self.champion = False
        self.reward_bits = 0
        self.opponents = [self._opponent(boss=(i == 2)) for i in range(3)]
        self.last = "%s — fight for the trophy!" % self.name

    def _opponent(self, boss):
        """Pick a stage-appropriate foe, then apply the trophy's enemy overrides."""
        e = dict(battle.pick_enemy(self.pet, boss=boss))
        t = self.trophy
        if t["enemy_stage"]:
            e["stage"] = t["enemy_stage"]
        if t["enemy_attr"]:
            e["attribute"] = t["enemy_attr"]
        if t["enemy_field"]:
            e["field"] = t["enemy_field"]
        if t["enemy_elem"]:
            e["element"] = t["enemy_elem"]
        return e

    @property
    def round_name(self):
        return ROUNDS[min(self.round, 2)]

    def current_opponent(self):
        return self.opponents[min(self.round, 2)]

    def record(self, won):
        if not won:
            self.over = True
            self.champion = False
            self.last = "Eliminated in the %s." % self.round_name
            return self.last
        self.round += 1
        if self.round >= 3:
            self.over = True
            self.champion = True
            base = TOURNEY_BITS.get(self.pet.stage, TOURNEY_BITS["Rookie"])
            self.reward_bits = min(TOURNEY_MAX_BITS, int(base * self.trophy["bit_mod"]))
            self.pet.bits += self.reward_bits
            self.pet.trophies += 1
            won = getattr(self.pet, "trophies_won", None)
            if won is None:
                self.pet.trophies_won = {}
                won = self.pet.trophies_won
            won[self.trophy["id"]] = self.pet.season
            from . import persistence
            persistence.tourney_add(self.trophy["id"])   # gates the tournament egg unlocks
            extras = []
            if self.trophy["item"] >= 0:
                self.pet.add_item("i:%d" % self.trophy["item"]); extras.append("item")
            if self.trophy["food_id"] >= 0 and self.trophy["food_amt"] > 0:
                self.pet.add_item("f:%d" % self.trophy["food_id"], self.trophy["food_amt"]); extras.append("food")
            tail = (" + " + "/".join(extras)) if extras else ""
            self.last = "CHAMPION! +%db%s + trophy!" % (self.reward_bits, tail)
        else:
            self.last = "Won the %s! On to the %s." % (ROUNDS[self.round - 1], self.round_name)
        return self.last
