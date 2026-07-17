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
# (the TourneyRandom*Power / *Health stat bands left with the classic
# battle -- 0.5 entrants are plain species cards at ideal condition)
HOME_LIMIT = 24                 # HomeTournamentLimit: one cup per game hour
ROUNDS = ["Quarterfinal", "Semifinal", "Final"]
_TIERS = ("Rookie", "Champion", "Ultimate", "Mega")


def trophy_label(t):
    if t["field_req"]:
        return "%s Cup" % data.pretty_field(t["field_req"])
    if t["attr_req"]:
        return "%s Cup" % t["attr_req"]
    return "%s Open #%d" % (t["season"], t["id"] + 1)   # display 1-based ("#0" reads like a bug)



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
    """Tournament.randTrophyIDs: bucket the cups by age tier, then fill
    the 24 hourly slots rotating open/Rookie/open/Champion/open/Ultimate/open/
    Mega; the fill STOPS at the first empty bucket (canon quirk).  Every cup in
    the classic data has Time=None, so the time-of-day match never gates.
    (The seasons left -- BASIC VPET 2026-07-17: ALL cups share one pool now;
    the CSV Season word survives only as the cup's flavor name.)"""
    buckets = {"free": [], "Rookie": [], "Champion": [], "Ultimate": [], "Mega": []}
    for t in data.load_tournies():
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
    """One rolled entrant, 0.5-style (2026-07-17): a plain species card --
    the HP race treats it as a wild Side at ideal condition, so stage rank
    and the attribute triangle carry the bracket (the old power-split/HP
    bands fed an engine that left)."""
    return {"num": rec["num"], "name": rec["name"], "stage": rec["stage"],
            "attribute": rec["attribute"], "bits": (0, 0)}



def _npc_winner(a, b):
    """An NPC match runs the REAL 0.5 engine (2026-07-17): two wild Sides,
    full HP race -- exactly how DVPet auto-fought its brackets."""
    from . import battle
    sa, sb = battle.Side.wild(a["num"]), battle.Side.wild(b["num"])
    _seq, ahp, bhp = battle.generate(sa, sb)
    if ahp == bhp:
        return a if random.random() < 0.5 else b
    return a if ahp > bhp else b


class Tournament:
    def __init__(self, pet, trophy):
        self.pet = pet
        self.trophy = trophy
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
        self.entrants = [_mk_entrant(random.choice(pool), trophy, open_mega)
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
            # canon tourneyEnd (SpriteAnim): an ELIMINATED pet leaves with the
            # praise window open (setIsWon(0) -> setPraise(true)) -- it fought
            # for you and lost; consoling it is the care (discipline audit
            # 2026-07-15).  The champion path has no such window.
            self.pet._open_praise()
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
            # seasonBeat; the trophy room shows the DAY it fell (the seasons
            # left with the calendar -- BASIC VPET 2026-07-17)
            from .pet import DAY_LENGTH
            won_map[self.trophy["id"]] = "day %d" % (
                int(self.pet.world_seconds // DAY_LENGTH) + 1)
            from . import persistence
            persistence.tourney_add(self.trophy["id"])     # gates the tournament egg unlocks
            extras = []
            if self.trophy["item"] >= 0:
                # the DVPet prize ids retired with the item system: the cup
                # pays a catalog treat instead
                self.pet.add_item("energy_drink"); extras.append("item")
            if self.trophy["food_id"] >= 0 and self.trophy["food_amt"] > 0:
                self.pet.add_item("best_fruit", self.trophy["food_amt"]); extras.append("food")
            tail = (" + " + "/".join(extras)) if extras else ""
            self.tree.append(["YOU"])                     # the top of the bracket
            self.last = "CHAMPION! +%db%s + trophy!" % (self.reward_bits, tail)
        else:
            self._resolve_npc_round()
            self.tree.append(list(self.bracket))          # the field after this round
            beat = " / ".join(self.results[:2])
            self.last = "Won! %s advance too. Now: the %s." % (beat or "The rest", self.round_name)
        return self.last
