"""Tournament -- DVPet's HOME tournament (Tournament.java + tournies.csv).

The real thing is a SCHEDULED 8-entrant bracket, not an always-open menu:

- Each game day, dailyChange rolls a 24-slot trophy schedule (one cup per game
  hour) from the season's pool -- randTrophyIDs interleaves the age tiers
  (open/Rookie/open/Champion/open/Ultimate/open/Mega) so tier cups pepper the
  day.  Only the CURRENT hour's cup is enterable (checkTourneyClosed).
- Entry runs Tournament.isEligible: not already fought today (SameDayRetry
  cups exempt), not too old for an age-limited cup, field/attribute
  restrictions, and a Prelim chain (its qualifier beaten this season).
  DVPet's fully-recovered gate has no tuipet analog (battle HP is per-fight).
- The bracket is the player + 7 entrants drawn from the DEX (TournamentAble
  forms filtered by the cup's stage/field/attribute/element rules; the default
  tier follows the pet's AGE via TourneyRandom*Age).  Each entrant rolls real
  stats: stage-banded HP and a power total split main/2 weak/6 rest/3 by its
  attribute.  Pairs are (0,1)(2,3)(4,5)(6,7) with the player at a random slot;
  the OTHER matches auto-resolve between rounds.
- Prizes: calcBits = sum over the 7 entrants of their stage's Tourney*Bits x
  the cup's BitModifier (a Mega entrant pays TourneyMaxBits once the pet is
  past TourneyRandomMegaAge).  Losing still pays: nothing from the
  quarterfinal, a third from the semi, half from the final.
"""
from __future__ import annotations
import random
from . import data

# config.csv (classic column)
TOURNEY_BITS = {"Rookie": 125, "Champion": 150, "Ultimate": 175, "Mega": 200}
TOURNEY_MAX_BITS = 225          # per Mega ENTRANT when the pet is past MegaAge (not a cap)
TOURNEY_AGES = {"Rookie": 3, "Champion": 6, "Ultimate": 9, "Mega": 12}   # TourneyRandom*Age (days)
POWER_MAX = {"Rookie": 150, "Champion": 200, "Ultimate": 250, "Mega": 300}   # TourneyRandom*Power
OPEN_MEGA_POWER = (350, 501)    # TourneyRandomMinPower..MaxPower (open-cup Mega field)
MIN_HEALTH = 5                  # TourneyMinHealth
MAX_HEALTH = {"Rookie": 10, "Champion": 15, "Ultimate": 20, "Mega": 25, "Ultra": 30}
HOME_LIMIT = 24                 # HomeTournamentLimit: one cup per game hour
ROUNDS = ["Quarterfinal", "Semifinal", "Final"]
_TIERS = ("Rookie", "Champion", "Ultimate", "Mega")


def trophy_label(t):
    if t["field_req"]:
        return "%s Cup" % data.pretty_field(t["field_req"])
    if t["attr_req"]:
        return "%s Cup" % t["attr_req"]
    return "%s Open #%d" % (t["season"], t["id"] + 1)   # display 1-based ("#0" reads like a bug)


def biome_cup_id(season, field):
    """The field-restricted cup for a biome's field this season (a town's
    signature championship), or -1 when the field has no cup.  Every town
    biome field has a cup in all four seasons in the classic data."""
    if not field:
        return -1
    for t in data.load_tournies():
        if t["season"] == season and t.get("field_req") == field:
            return t["id"]
    return -1


def trophy_by_id(tid):
    for t in data.load_tournies():
        if t["id"] == tid:
            return t
    return None


def _hour(pet):
    from .pet import DAY_LENGTH
    return int((pet.world_seconds % DAY_LENGTH) / DAY_LENGTH * 24)


def pet_tier(pet):
    """The pet's cup tier by STAGE.  Canon (Trophy.getStageByAge) keyed this to
    age-days because its clock made age and stage equivalent; the 2026-07 pacing
    rebuild compressed growth ~4x, leaving age-tiered cups one tier BEHIND the
    pet for its whole growth arc.  Stage is the truth the tier stood for.
    None = a Mega (the open field + the max-bits purse, like canon's >12d)."""
    s = pet.stage
    if s in ("Egg", "Fresh", "InTraining", "Rookie"):
        return "Rookie"
    if s in ("Champion", "Ultimate"):
        return s
    return None


_TIER_RANK = {"Rookie": 0, "Champion": 1, "Ultimate": 2, "Mega": 3}


def _pet_tier_rank(pet):
    t = pet_tier(pet)
    return _TIER_RANK.get(t, 3)          # None (Mega) ranks past everything


ENTRY_FEE_DIV = 4                        # the stake = expected purse / 4


def entry_fee(pet, t):
    """THE STAKE (bit-sink design 2026-07-14): a quarter of the bracket's
    EXPECTED purse (7 entrants x the tier's stage bits x BitModifier), put
    down at entry.  The champion nets +75% of the purse, a final loss +25%,
    a semi loss ~+8%, and a quarterfinal exit eats the stake whole -- cups
    were the game's dominant faucet with zero risk.  An open cup stakes the
    pet's own tier: a Mega pays the open-field MaxBits rate it also wins by."""
    if t["age_limit"]:
        base = TOURNEY_BITS.get(t["age_limit"], 0)
    elif pet_tier(pet) is None:
        base = TOURNEY_MAX_BITS
    else:
        base = TOURNEY_BITS.get(pet_tier(pet), TOURNEY_BITS["Rookie"])
    return int(7 * base * t["bit_mod"]) // ENTRY_FEE_DIV


def _rand_trophy_ids(pet):
    """Tournament.randTrophyIDs: bucket the season's cups by age tier, then fill
    the 24 hourly slots rotating open/Rookie/open/Champion/open/Ultimate/open/
    Mega; the fill STOPS at the first empty bucket (canon quirk).  Every cup in
    the classic data has Time=None, so the time-of-day match never gates."""
    season = pet.season
    buckets = {"free": [], "Rookie": [], "Champion": [], "Ultimate": [], "Mega": []}
    for t in data.load_tournies():
        if t["season"] != season:
            continue
        buckets[t["age_limit"] if t["age_limit"] in buckets else "free"].append(t)
    order = ["free", "Rookie", "free", "Champion", "free", "Ultimate", "free", "Mega"]
    sched = []
    while len(sched) < HOME_LIMIT:
        for name in order:
            pool = buckets[name]
            if not pool:
                return sched + [-1] * (HOME_LIMIT - len(sched))
            t = pool.pop(random.randrange(len(pool)))
            sched.append(t["id"])
            if len(sched) >= HOME_LIMIT:
                break
    return sched


def schedule(pet):
    """The day's hourly cup schedule (setTrophySchedule; dailyChange re-rolls
    it and clears foughtTrophiesToday)."""
    from .pet import DAY_LENGTH
    day = int(pet.world_seconds // DAY_LENGTH)
    if pet.tourney_day != day or len(pet.tourney_schedule) != HOME_LIMIT:
        pet.tourney_day = day
        pet.tourney_schedule = _rand_trophy_ids(pet)
        pet.fought_today = []
        pet.fought_hours = []                      # a new day, every cup-hour fresh
        pet.tourney_alarm = -1                     # dailyChange: _tourneyAlarm = -1
        pet.tourney_alert = False
    return pet.tourney_schedule


def town_schedule(pet, town):
    """Town.getTrophies -> randTrophyIDs(season, [tournamentLimit], forced):
    slots 0-23 are hourly cups; slots PAST 23 (where the forced trophies pin)
    are ALWAYS open (getTourneyTime returns -1 -> never closed)."""
    n = max(0, int(town.get("tournament_limit", 0)))
    sched = _rand_trophy_ids(pet)[:min(n, HOME_LIMIT)]
    while len(sched) < n:
        sched.append(-1)
    forced = [t for t in town.get("forced_trophies", []) if trophy_by_id(t)]
    for i, tid in enumerate(forced):
        if n - 1 - i >= 0:
            sched[n - 1 - i] = tid
    # biome bias (Joel 2026-07-09): the town's always-open signature slot (index
    # > 23, never closed) hosts its biome field's championship, on top of the
    # rotating hourly bracket -- a themed cup the biome's own kind can always enter
    from . import world
    cup = biome_cup_id(pet.season, world.town_field(town.get("id", -1)))
    if cup >= 0:
        for i in range(len(sched) - 1, HOME_LIMIT - 1, -1):   # always-open slots
            if sched[i] == -1:
                sched[i] = cup
                break
    return sched


def town_slot_open(pet, index):
    """checkTourneyClosed with getTourneyTime: hourly for 0-23, open past 23."""
    return index > 23 or index == _hour(pet)


def open_now(pet):
    """The current game-hour's cup -- every other slot is closed
    (checkTourneyClosed: start hour != current hour)."""
    sched = schedule(pet)
    tid = sched[_hour(pet)] if _hour(pet) < len(sched) else -1
    return trophy_by_id(tid) if tid >= 0 else None


def eligibility(pet, t):
    """Tournament.isEligible, minus the fully-recovered gate (no persistent
    battle HP in tuipet).  Returns a refusal reason or None.

    THE CUP-HOUR GATE (Joel 2026-07-13, economy audit): every trophy in the
    shipped data carries SameDayRetry=TRUE, so canon's foughtTrophiesToday
    lock never fires -- the open cup could be re-entered without limit,
    re-rolling its bracket for the full purse each time (~1,500b a minute,
    an order of magnitude past an adventure).  tuipet's rule: **the cup RUNS
    once per hour**.  Entering spends that hour's slot; the next hour brings
    a fresh cup.  Canon's own per-trophy lock is kept underneath for any
    future SameDayRetry=FALSE data.
    """
    if _hour(pet) in (getattr(pet, "fought_hours", None) or []):
        return "That cup has run — the next one starts on the hour."
    if t["id"] in (pet.fought_today or []) and not t["same_day_retry"]:
        return "Already fought that cup today."
    if t["age_limit"] and _pet_tier_rank(pet) > _TIER_RANK.get(t["age_limit"], 3):
        return "Too old for the %s bracket." % t["age_limit"]
    if t["field_req"] and t["field_req"] != getattr(pet, "field", ""):
        return "%s only." % data.pretty_field(t["field_req"])
    if t["attr_req"] and t["attr_req"] != getattr(pet, "attribute", ""):
        return "%s only." % t["attr_req"]
    if t.get("prelim"):
        # seasonBeat: set once on a win and NEVER reset -- every cup in
        # tournies.csv has ResetWonOnSeasonChange=FALSE, so the qualifier
        # stays beaten for life.  (A ==season check locked the cross-season
        # grand chain 14->92->170->248 forever: audit 2026-07.)
        won = getattr(pet, "trophies_won", {}) or {}
        if t["prelim"] not in won:
            q = trophy_by_id(t["prelim"])
            return "Win the %s first." % (trophy_label(q) if q else "qualifier")
    fee = entry_fee(pet, t)
    if pet.bits < fee:
        return "The stake is %db — you can't cover it." % fee
    return None


def next_winnable(pet):
    """The next hour TODAY whose cup this pet can actually enter (eligibility
    passes) -- scanning from the current hour forward through the schedule.
    Returns (hour, trophy) or None when nothing enterable is left today."""
    sched = schedule(pet)
    run = getattr(pet, "fought_hours", None) or []
    for i in range(_hour(pet), len(sched)):
        tid = sched[i]
        if tid < 0 or i in run:                    # that hour's cup has already run
            continue
        tr = trophy_by_id(tid)
        # the hour gate only speaks for THIS hour; a FUTURE slot is judged on
        # the rest of the rules (we have not reached it yet)
        if tr and _eligibility_rest(pet, tr) is None:
            return (i, tr)
    return None


def _eligibility_rest(pet, t):
    """Eligibility WITHOUT the cup-hour gate -- for judging a FUTURE slot."""
    if t["id"] in (pet.fought_today or []) and not t["same_day_retry"]:
        return "Already fought that cup today."
    if t["age_limit"] and _pet_tier_rank(pet) > _TIER_RANK.get(t["age_limit"], 3):
        return "Too old for the %s bracket." % t["age_limit"]
    if t["field_req"] and t["field_req"] != getattr(pet, "field", ""):
        return "%s only." % data.pretty_field(t["field_req"])
    if t["attr_req"] and t["attr_req"] != getattr(pet, "attribute", ""):
        return "%s only." % t["attr_req"]
    if t.get("prelim"):
        won = getattr(pet, "trophies_won", {}) or {}
        if t["prelim"] not in won:
            q = trophy_by_id(t["prelim"])
            return "Win the %s first." % (trophy_label(q) if q else "qualifier")
    return None


def can_enter(pet):
    if getattr(pet, "dead", False):
        return "It rests now — press N for a new egg."   # dead sweep 2026-07-06
    if pet.stage in ("Egg", "Fresh", "InTraining"):
        return "Too young for the cup."
    if pet.asleep:
        return pet._disturbed()   # a player poke wakes the sleeper, like every care key
    if not data.load_tournies():
        return "No cups exist."
    return None


# ---- the 8-entrant bracket ---------------------------------------------------

def _eligible_forms(pet, trophy):
    """randomEnemies' entrant pool: TournamentAble dex forms matching the cup's
    enemy overrides (or, absent those, its restrictions / the pet's age tier)."""
    reqs = data.load_requirements()
    _, by_num = data.load_sprites()
    tier = trophy["enemy_stage"] or trophy["age_limit"] or pet_tier(pet) or "Mega"
    out = []
    for num, rec in by_num.items():
        if rec["stage"] in ("Egg", "Fresh", "InTraining") or rec["stage"] != tier:
            continue
        if not reqs.get(num, {}).get("tournament_able", True):
            continue
        if trophy["enemy_field"]:
            if rec["field"] != trophy["enemy_field"]:
                continue
        elif trophy["field_req"] and rec["field"] != trophy["field_req"]:
            continue
        if trophy["enemy_attr"]:
            if rec["attribute"] != trophy["enemy_attr"]:
                continue
        elif trophy["attr_req"] and rec["attribute"] != trophy["attr_req"]:
            continue
        if trophy["enemy_elem"] and rec.get("element") != trophy["enemy_elem"]:
            continue
        if data.is_placeholder(num):
            continue
        out.append(rec)
    return out


def _mk_entrant(rec, trophy, open_mega):
    """One rolled entrant: stage-banded HP + a power total split by attribute
    (main /2, weak /6, the rest /3 -- Vaccine>red, Data>green, Virus>yellow)."""
    st = rec["stage"]
    if open_mega and st == "Mega":
        hp = random.randrange(MIN_HEALTH * 2) + (MAX_HEALTH["Ultra"] - MIN_HEALTH * 2)
        lo, hi = OPEN_MEGA_POWER
    else:
        hp = random.randrange(MIN_HEALTH) + (MAX_HEALTH.get(st, 10) - MIN_HEALTH)
        hi = POWER_MAX.get(st, 150)
        lo = {"Rookie": POWER_MAX["Rookie"] // 3, "Champion": POWER_MAX["Rookie"],
              "Ultimate": POWER_MAX["Champion"], "Mega": POWER_MAX["Ultimate"]}.get(st, 50)
    power = random.randint(lo, hi)
    attr = rec["attribute"]
    split = {"Vaccine": ("vaccine", "data_power", "virus"),
             "Data": ("data_power", "virus", "vaccine"),
             "Virus": ("virus", "vaccine", "data_power")}.get(attr)
    e = {"num": rec["num"], "name": rec["name"], "stage": st, "attribute": attr,
         "hp": max(2, hp), "bits": (0, 0),        # the cup pays via calcBits, not loot
         "vaccine": 0, "data_power": 0, "virus": 0}
    if split:
        main, weak, mid = split
        e[main], e[weak], e[mid] = power // 2, power // 6, power // 3
    else:
        e["vaccine"] = e["data_power"] = e["virus"] = power // 3
    return e


def _biased_choice(pool, field_bias, trophy):
    """Draw one entrant, skewed toward the biome field when the CUP itself
    sets no field (a field cup already dictates its roster).  Soft (~60%)
    so the bracket still varies, and it never narrows an empty pool."""
    if field_bias and not trophy["field_req"] and not trophy["enemy_field"]:
        biome = [r for r in pool if r.get("field") == field_bias]
        if biome and random.random() < 0.6:
            return random.choice(biome)
    return random.choice(pool)


def _npc_winner(a, b):
    """DVPet auto-fights NPC matches with the full battle engine; tuipet's
    engine is pet-centric, so the bracket resolves on the same scalar the data
    uses for levelFought -- (powers + hp*100), odds proportional."""
    wa = a["vaccine"] + a["data_power"] + a["virus"] + a["hp"] * 100
    wb = b["vaccine"] + b["data_power"] + b["virus"] + b["hp"] * 100
    return a if random.uniform(0, wa + wb) < wa else b


class Tournament:
    def __init__(self, pet, trophy, field_bias=""):
        self.pet = pet
        self.trophy = trophy
        self.field_bias = field_bias
        self.name = trophy_label(trophy)
        self.round = 0
        self.over = False
        self.champion = False
        self.reward_bits = 0
        # the stake is paid AT ENTRY like the hour slot: a forfeit or an
        # abandoned bracket does not hand it back.  eligibility() vets
        # affordability first; a direct construction that cannot pay (tests,
        # rogue callers) stakes nothing rather than silently owing.
        self.stake = entry_fee(pet, trophy)
        if not pet.spend_bits(self.stake):
            self.stake = 0
        pool = _eligible_forms(pet, trophy)
        open_mega = not trophy["age_limit"] and not trophy["enemy_stage"] \
            and pet_tier(pet) is None
        # randomEnemies draws WITH replacement (duplicates are canon)
        if not pool:                               # no exact match in the dex: relax the
            relaxed = dict(trophy, enemy_elem="")  # element, then the field/attr walls
            pool = _eligible_forms(pet, relaxed)
        if not pool:
            pool = _eligible_forms(pet, dict(trophy, enemy_elem="", enemy_field="",
                                             enemy_attr="", field_req="", attr_req=""))
        if not pool:
            # an impossible cup (a tier with no TournamentAble forms): field ANY
            # tier rather than crash the bracket (audit 2026-07 guard)
            _, by_num = data.load_sprites()
            pool = [r for n, r in by_num.items()
                    if r["stage"] not in ("Egg", "Fresh", "InTraining")
                    and not data.is_placeholder(n)]
        self.entrants = [_mk_entrant(_biased_choice(pool, field_bias, trophy), trophy, open_mega)
                         for _ in range(7)]
        # the bracket: entrants + the player at a random slot, pairs (0,1)(2,3)...
        self.bracket = list(self.entrants)
        self.player_i = random.randrange(8)
        self.bracket.insert(self.player_i, "YOU")
        self.results = []
        self.tree = [list(self.bracket)]     # round-by-round history for the bracket page
        self.last = "%s — 8 enter, one leaves with the trophy." % self.name
        # spend this hour's slot AT ENTRY, not at the finish: a bracket
        # abandoned (ESC forfeits; a force-quit does not even reach _finish)
        # must not hand back a free re-roll of the field
        hrs = getattr(pet, "fought_hours", None)
        if hrs is None:
            pet.fought_hours = hrs = []
        h = _hour(pet)
        if h not in hrs:
            hrs.append(h)

    @property
    def round_name(self):
        return ROUNDS[min(self.round, 2)]

    def current_opponent(self):
        i = self.bracket.index("YOU")
        return self.bracket[i + 1] if i % 2 == 0 else self.bracket[i - 1]

    def _resolve_npc_round(self):
        """The other pairs fight while you catch your breath (npcFight/autoFight)."""
        nxt, notes = [], []
        for i in range(0, len(self.bracket), 2):
            a, b = self.bracket[i], self.bracket[i + 1]
            if a == "YOU" or b == "YOU":
                nxt.append("YOU")
                continue
            w = _npc_winner(a, b)
            notes.append(w["name"])
            nxt.append(w)
        self.bracket = nxt
        self.results = notes

    def _calc_bits(self):
        """Tournament.calcBits: the purse is the sum of the FIELD's stage bits
        x BitModifier (a Mega entrant pays MaxBits once the pet is past 12d)."""
        total = 0
        for e in self.entrants:
            base = TOURNEY_BITS.get(e["stage"], 0)
            if e["stage"] == "Mega" and pet_tier(self.pet) is None:
                base = TOURNEY_MAX_BITS      # a Mega pet's open field pays the max purse
            # canon truncates the RUNNING total each step ((int)(bits + term)):
            # a 1.1-modifier all-Rookie field pays 959, not the float-sum's 962
            # (identical IEEE doubles Java-side -- the halves floor away per step)
            total = int(total + base * self.trophy["bit_mod"])
        return total

    def _finish(self, bits):
        from .pet import weekend_bonus
        bits = int(bits * weekend_bonus())   # x1.5 purse on real weekends
        self.over = True
        self.reward_bits = bits
        if bits:
            self.pet.bits += bits
        if not self.trophy["same_day_retry"]:      # endTourney -> foughtTrophiesToday
            ft = self.pet.fought_today or []
            if self.trophy["id"] not in ft:
                ft.append(self.trophy["id"])
            self.pet.fought_today = ft

    def record(self, won):
        if self.over:
            return self.last
        if not won:
            # setIsWon(0): the QF pays nothing, the semi a third, the final half
            bits = (0, self._calc_bits() // 3, self._calc_bits() // 2)[min(self.round, 2)]
            self._finish(bits)
            self.champion = False
            tail = (" +%db" % self.reward_bits) if self.reward_bits else ""
            self.last = "Eliminated in the %s.%s" % (self.round_name, tail)
            return self.last
        self.round += 1
        if self.round >= 3:
            self._finish(self._calc_bits())        # setIsWon(2): the full purse
            self.champion = True
            self.pet.trophies += 1
            won_map = getattr(self.pet, "trophies_won", None)
            if won_map is None:
                self.pet.trophies_won = won_map = {}
            won_map[self.trophy["id"]] = self.pet.season   # seasonBeat; season kept for the trophy room
            from . import persistence
            persistence.tourney_add(self.trophy["id"])     # gates the tournament egg unlocks
            extras = []
            if self.trophy["item"] >= 0:
                self.pet.add_item("i:%d" % self.trophy["item"]); extras.append("item")
            if self.trophy["food_id"] >= 0 and self.trophy["food_amt"] > 0:
                self.pet.add_item("f:%d" % self.trophy["food_id"], self.trophy["food_amt"]); extras.append("food")
            tail = (" + " + "/".join(extras)) if extras else ""
            self.tree.append(["YOU"])                     # the top of the bracket
            self.last = "CHAMPION! +%db%s + trophy!" % (self.reward_bits, tail)
        else:
            self._resolve_npc_round()
            self.tree.append(list(self.bracket))          # the field after this round
            beat = " / ".join(self.results[:2])
            self.last = "Won! %s advance too. Now: the %s." % (beat or "The rest", self.round_name)
        return self.last
