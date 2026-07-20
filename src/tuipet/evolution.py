"""Care-quality evolution engine — a faithful port of DVPet's Model/Evolution.

A candidate evolves into the form whose requirement gates it best satisfies:
gather the current form's evolution targets, keep those that pass every gate
(checkEvolReq), then pick the highest fulfilledReq, breaking ties by the
smallest deviation, then at random. Comparison semantics match testCondition:
GreaterThan -> actual > threshold, LessThan -> actual < threshold, EqualTo -> ==.
"""
from __future__ import annotations
import random
from . import data

WEIGHT_THRESH = 0.5  # Config.OverUnderWeightThreshold
X_ANTIBODY_RATE = 3  # Config.XAntibodyRate — bonus when an X-form's req is met
DNA_FULFILLED_RATE = 2


WIN_RATE_PROB_COEF = 0.4  # Config._winRateEvolProbabilityIncCoefficient

# Config *Rate constants used to weight how well each met gate counts.
R = {
    "battle": 1, "data": 1, "vaccine": 1, "virus": 1, "time": 1, "weight": 1,
    "disturb": 1, "overeat": 1, "sick": 1, "injury": 1, "mood": 1, "obedience": 1,
    "winRate": 1, "mistakeLess": 1, "mistakeGreater": 2, "mistakeEqual": 2, "mistakeNone": 0,
}


def _cmp(cond, threshold, actual):
    if cond == "None":
        return True
    if cond == "GreaterThan":
        return actual > threshold
    if cond == "LessThan":
        return actual < threshold
    if cond == "EqualTo":
        return actual == threshold
    return False


def _attr(gate, actual, total):
    """Attribute-power gate; fractional thresholds (0<v<1) compare a ratio."""
    cond, val = gate
    if cond == "None":
        return True
    if 0.0 < val < 1.0:
        return _cmp(cond, val, actual / total) if total > 0 else False
    return _cmp(cond, val, actual)


def _scale_rate(cond, first, second):
    """Config.scaleRate: weight a met attribute gate by the target threshold's
    distance from the current form's threshold (Java switch fall-through)."""
    if cond in ("GreaterThan", "EqualTo") and first > second:
        return (first - second) / first if first else 1.0
    if second > first:
        return (second - first) / second if second else 1.0
    return 1.0


def weight_category(weight, base):
    hi = base + round(base * WEIGHT_THRESH)
    lo = base - round(base * WEIGHT_THRESH)
    return "Over" if weight > hi else ("Under" if weight < lo else "Healthy")


def _stats(pet):
    return pet.vaccine, pet.data_power, pet.virus


def _win_rate(pet):
    return int(pet.wins / pet.battles * 100) if pet.battles else 0


def _stat_total_ok(req, total):
    s = 0
    for key in ("vaccine", "data", "virus"):
        cond, val = req[key][0]
        if cond in ("GreaterThan", "EqualTo"):
            s += int(val) + (1 if cond == "GreaterThan" else 0)
    return total >= s


def _dna_ok(pet, req):
    """testDNA + hasDNARequirement: the form declares Field-DNA gates AND the pet's
    charged-DNA distribution satisfies every one. This is DVPet's universal
    evolution-requirement bypass (EnableDNAReqReplacement=TRUE)."""
    dna = req.get("dna")
    if not dna or not any(g[0] != "None" for g in dna.values()):
        return False                       # hasDNARequirement: no Field gate set
    return all(_cmp(cond, val, pet.dna_percent(f)) for f, (cond, val) in dna.items())


def check(pet, num, item=-1, food=-1, connecting=False):
    """checkEvolReq, verbatim semantics (canon re-audit 2026-07):

    * the DNA replacement is CONSUME-ONCE: canon's getDNA() clears its flag on
      the first failing gate it excuses -- so a met DNA charge forgives exactly
      ONE failed gate, not all of them.  With short-circuit ||, that reduces to:
      pass iff no gate fails, or (DNA met and exactly one fails).
    * special types follow checkSpecialCondition + the optional flags:
      JogressOptional=TRUE (classic) -- a Jogress form IS reachable by normal
      timed care (its heavy gates still apply); FusionOptional=FALSE -- Fusion
      needs the handshake; Failed forms compete like anyone; Mode/Death/Xros
      have their own triggers.  `connecting` waives the whole type gate (the
      jogress/mode/death helpers all pass it, as before).
    * only an INDUCED X requirement demands the antibody (canon gates Natural
      forms by care alone -- 180 corpus forms were wrongly locked); the
      probability roll applies to X forms like everyone (the old skip was not
      canon).  The probability roll is never DNA-bypassed.  (checkStatTotal
      and the per-attr stat gates left 2026-07-17 -- DVPet-only power walls
      the humulos guides never speak.)"""
    req = data.load_requirements().get(num)
    if req is None:
        return False
    special = req.get("special", "None")
    if not connecting:
        if special in ("Mode", "Death", "Xros"):
            return False          # checkSpecialCondition: their own triggers only
        if special == "Fusion":
            return False          # FusionOptional=FALSE: the handshake only
        # "Jogress" (JogressOptional=TRUE), "Failed" and "None" compete normally
    ev_item = req.get("evol_item", -1)
    if item == -1:
        if ev_item != -1:
            return False     # item-locked form: unreachable by timed care (need the item)
    elif ev_item != item:
        return False         # using an item only validates the forms that require it
    # the FOOD lock is UNLOCKED (Joel 2026-07-16, with the item-system
    # clone): the food catalog is gone, so Citramon -- the corpus' one
    # food-locked form (EvolFood 42, the Orange) -- competes by timed care
    # like everyone; its remaining requirement gates still apply.
    if req.get("xantibody", "None") == "Induced" and getattr(pet, "x_antibody", "None") == "None":
        return False  # Induced X-forms are unreachable without the antibody (canon: Induced ONLY)
    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    # (checkStatTotal DROPPED with the six per-attr stat gates, 2026-07-17:
    # the same DVPet-only power wall under the same +1-per-win economy)
    gates = [
        _cmp(*req["battles"], pet.battles),
        # (the six vaccine/data/virus stat gates DROPPED 2026-07-17: they
        # were DVPet-app truth -- the humulos guides gate on mistakes/
        # trainings/battles/wins, never power numbers -- and the 0.5 economy
        # (+1 power per win) put their digimon.csv thresholds out of reach.
        # The fulfilled-score/deviation legs still read the live stats.)
        # (the "trains at Morning/Noon/Night" TIME gate DROPPED with the
        # day/night system -- BASIC VPET 2026-07-17: an hour nothing can
        # reach would wall 374 corpus forms, the temp_req/habitat_req call)
        req["weight"] == "None" or req["weight"] == weight_category(pet.weight, pet._base_weight()),
        _cmp(*req["disturb"], pet.disturb),
        _cmp(*req["overeat"], pet.overeat),
        # (the sick_count gates DROPPED with the sickness system (BASIC VPET 2026-07-17) --
        # GreaterThan rows would wall forever on a count nothing can move;
        # the injured gates already read a pinned 0 -- and 41 GreaterThan
        # rows, Omnimon's Fusion among them, were WALLS on a counter nothing
        # can move.  DROPPED like every other dead-meter family; Fusion/Mode
        # canon audit 2026-07-18)
        # checkMoodReq: getCurrentMood -- the STICKY tier (Depressed holds until
        # checkDepressed's exit roll; a threshold recompute is never Depressed).
        # The old mood_category invented a Depressed tier at <= -250, failing
        # the 70 Mood=Unhappy requirement rows for any deeply-sad pet.
        True,   # (mood gates left with the mood system; BASIC VPET 2026-07-16)
        True,   # (obedience gates left with the discipline system)
        _cmp(*req["wins"], _win_rate(pet)),
        _cmp(*req["mistakes"], pet.care_mistakes),
        True,   # (major_food gates left with the nutrition/taste system)
        _cmp(*req.get("incarnations", ("None", 0)), getattr(pet, "generation", 1)),
    ]
    # LevelFought: enough opponents of at least MinLevelFought power beaten this stage
    lf_min = req.get("level_fought_min", 0)
    if lf_min:
        cnt = sum(1 for lv in getattr(pet, "levels_fought", ()) if lv >= lf_min)
        gates.append(_cmp(*req["level_fought"], cnt))
    # (temp_req gates left with the weather system -- BASIC VPET 2026-07-16:
    # a temperature band nothing can move would permanently wall those forms)
    # (habitat_req gates DROPPED with the habitat system -- BASIC VPET
    # 2026-07-16: a home nothing can move to would permanently wall those
    # forms, the same call the temp_req gates got)
    failed = sum(1 for g in gates if not g)
    # (the DNA gate-forgiveness -- canon getDNA()'s consume-once excuse --
    # left with the DNA slim, BASIC VPET 2026-07-16: the charge still BENDS
    # selection through the fulfilled-score bonus and arms divergence, but a
    # failed care gate is a failed gate)
    if failed > 0:
        return False
    # probability: prob >= probBound -> always; else prob must beat a roll.
    # DVPet boosts prob by the care bonus + winRate*coefficient (checkEvolReq).
    boost = getattr(pet, "evol_bonus", 0) + int(_win_rate(pet) * WIN_RATE_PROB_COEF)
    prob, bound = req["prob"] + boost, req["probBound"]
    if prob < bound:
        return prob > random.randint(0, bound - 1)
    return True


def _met(gate, actual):
    cond, val = gate
    return cond != "None" and _cmp(cond, val, actual)


def fulfilled(pet, num):
    """getFulfilledReq: 1 + priority + summed rates of every met gate."""
    req = data.load_requirements()[num]
    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    score = 1.0 + req["priority"]
    cur = data.load_requirements().get(pet.num, {})   # current form, for scaleRate
    if _met(req["battles"], pet.battles):
        score += R["battle"]
    for k, actual in (("data", dat), ("vaccine", vac), ("virus", vir)):
        cg = cur.get(k) or [("None", 0), ("None", 0)]
        for i in (0, 1):
            g = req[k][i]
            if g[0] != "None" and _attr(g, actual, total):
                cur_thr = cg[i][1] if i < len(cg) else 0
                score += R[k if k in R else "data"] * _scale_rate(g[0], g[1], cur_thr)
    if req["weight"] != "None" and req["weight"] == weight_category(pet.weight, pet._base_weight()):
        score += R["weight"]
    for k, actual in (("disturb", pet.disturb), ("overeat", pet.overeat)):
        if _met(req[k], actual):
            score += R.get(k, 1)
    if False:   # (the mood score left with the mood system; BASIC VPET)
        score += R["mood"]
    if False:   # (the major_food score left with the taste system)
        score += 1
    if _met(req["wins"], _win_rate(pet)):
        score += R["winRate"]
    cond, val = req["mistakes"]
    if cond != "None" and _cmp(cond, val, pet.care_mistakes):
        score += {"LessThan": R["mistakeLess"], "GreaterThan": R["mistakeGreater"],
                  "EqualTo": R["mistakeEqual"]}.get(cond, R["mistakeNone"])
    lf_min = req.get("level_fought_min", 0)
    if lf_min and req["level_fought"][0] != "None":
        cnt = sum(1 for lv in getattr(pet, "levels_fought", ()) if lv >= lf_min)
        if _cmp(*req["level_fought"], cnt):
            score += 1  # Config._levelFoughtRate
    # canon scores ONLY an Induced X requirement (evolution audit 2026-07-06:
    # the old "Natural" arm over-scored 180 corpus forms)
    if req.get("xantibody", "None") == "Induced" and getattr(pet, "x_antibody", "None") != "None":
        score += X_ANTIBODY_RATE
    for f, g in (req.get("dna") or {}).items():     # getDNAReq: priority per met Field gate
        if g[0] != "None" and _cmp(g[0], g[1], pet.dna_percent(f)):
            score += DNA_FULFILLED_RATE
    if _dna_ok(pet, req):                            # getDNAReq: full-match dnaFulfilledRate bonus
        score += DNA_FULFILLED_RATE
    # (the habitat_req score leg and the major-habitat element/field
    # affinity shade left with the habitat system -- BASIC VPET 2026-07-16.
    # A dangling element fragment survived that cut INSIDE the _dna_ok
    # branch above -- a latent NameError on `h` for any DNA-charged pet --
    # and left with the element system, 2026-07-18.)
    return score


def deviation(pet, num):
    """tieBreaker: total absolute distance from the met gates' thresholds."""
    req = data.load_requirements()[num]
    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    dev = 0.0
    if _met(req["battles"], pet.battles):
        dev += abs(req["battles"][1] - pet.battles)
    for k, actual in (("data", dat), ("vaccine", vac), ("virus", vir)):
        for i in (0, 1):
            g = req[k][i]
            if g[0] != "None" and _attr(g, actual, total):
                dev += abs(g[1] - actual)
    for k, actual in (("disturb", pet.disturb), ("overeat", pet.overeat),
                      ("mistakes", pet.care_mistakes)):
        if _met(req[k], actual):
            dev += abs(req[k][1] - actual)
    if _met(req["wins"], _win_rate(pet)):
        dev += abs(req["wins"][1] - _win_rate(pet))
    return dev


def _failed_form(pet, by_num):
    """DVPet's safety net: a pet that meets no requirement still evolves -- into
    its species' 'Failed' form (e.g. Numemon) rather than getting stuck."""
    failed = [t for t in data.load_evolutions().get(pet.num, [])
              if t in by_num and by_num[t]["stage"] != pet.stage
              and not data.is_placeholder(t)
              and data.load_requirements().get(t, {}).get("special") == "Failed"]
    return random.choice(failed) if failed else None


def item_select(pet, item_id):
    """Forms reachable by USING item `item_id`: graph targets whose EvolItemID == item_id
    and whose care gates pass (the item is an extra gate, not a bypass). Best by fulfilled."""
    _, by_num = data.load_sprites()
    targets = [t for t in data.load_evolutions().get(pet.num, [])
               if t in by_num and not data.is_placeholder(t)]
    valid = [t for t in targets if check(pet, t, item=item_id)]
    if not valid:
        return None
    best = max(fulfilled(pet, t) for t in valid)
    top = [t for t in valid if abs(fulfilled(pet, t) - best) < 1e-9]
    if len(top) > 1:
        mind = min(deviation(pet, t) for t in top)
        top = [t for t in top if deviation(pet, t) == mind]
    return random.choice(top)


def food_select(pet, food_id):
    """Forms reachable by EATING food `food_id` (processFoodEvol): graph
    targets whose EvolFood == food_id and whose care gates pass -- the meal
    is an extra gate, not a bypass.  Best by fulfilled, like item_select."""
    if food_id is None or food_id < 0:
        return None
    _, by_num = data.load_sprites()
    targets = [t for t in data.load_evolutions().get(pet.num, [])
               if t in by_num and not data.is_placeholder(t)]
    valid = [t for t in targets if check(pet, t, food=food_id)]
    if not valid:
        return None
    best = max(fulfilled(pet, t) for t in valid)
    top = [t for t in valid if abs(fulfilled(pet, t) - best) < 1e-9]
    if len(top) > 1:
        mind = min(deviation(pet, t) for t in top)
        top = [t for t in top if deviation(pet, t) == mind]
    return random.choice(top)


def item_direct(pet, dexnum):
    """Direct evolution item (items.csv DigimonID names the form): evolve into `dexnum`
    if it is a reachable graph neighbour of the current form."""
    if dexnum is None or dexnum < 0:
        return None
    return dexnum if dexnum in data.load_evolutions().get(pet.num, []) else None


def select(pet):
    """Return the chosen evolution target num, or None.

    Normal evolution climbs a stage.  (The X-Antibody steering and same-stage
    X reformat are retired -- LINES_SPEC §4: X-forms belong to X egg lines;
    an antibody-carrying corpus pet still passes check()'s Induced gate, but
    the antibody no longer hijacks the choice.)"""
    _, by_num = data.load_sprites()
    targets = []
    for t in data.load_evolutions().get(pet.num, []):
        if t not in by_num or t == pet.num:
            continue
        if data.is_placeholder(t):
            continue
        if by_num[t]["stage"] != pet.stage:
            targets.append(t)
    valid = [t for t in targets if check(pet, t)]
    if not valid:
        # nothing fully qualifies -> Failed form if the species has one, else the
        # best-matched stage-up target, so a pet NEVER gets stuck below Mega
        ff = _failed_form(pet, by_num)
        if ff is not None:
            return ff
        stage_up = [t for t in targets if by_num[t]["stage"] != pet.stage
                    and data.load_requirements().get(t, {}).get("special", "None") == "None"
                    and data.load_requirements().get(t, {}).get("evol_item", -1) == -1
                    # the Induced gate check()/divergence enforce: without it
                    # the fallback pushed an antibody-less pet into an X form
                    # and evolve_to locked x_antibody="Permanent" -- a free X
                    # with no X egg or chip (gameplay audit 2026-07-19)
                    and (data.load_requirements().get(t, {}).get("xantibody", "None") != "Induced"
                         or getattr(pet, "x_antibody", "None") != "None")]
        if stage_up:
            return max(stage_up, key=lambda t: fulfilled(pet, t))
        return None
    best = max(fulfilled(pet, t) for t in valid)
    top = [t for t in valid if abs(fulfilled(pet, t) - best) < 1e-9]
    if len(top) > 1:
        mind = min(deviation(pet, t) for t in top)
        top = [t for t in top if deviation(pet, t) == mind]
    return random.choice(top)


# ---- DNA divergence: the wild road ("ultimate v-pet" arc, 2026-07-07) -------
# The lines are the raising spine (529 forms); the corpus graph reaches 1,454.
# Divergence is the door between them: a pet whose CHARGED DNA has a
# strict-max Field at/over its stage's threshold steers evolution off the
# chart -- the graph's NEXT-STAGE children of the current form in that Field
# become the candidates, judged by this engine's own gates (check ->
# fulfilled -> deviation).  The charge is consumed by evolve_to's reset_dna
# like any evolution; the caller re-anchors via lines.adopt_line (a chart
# that claims the target keeps the pet on lines; otherwise it rides this
# corpus engine from then on -- a road it PAID for).
#
# Thresholds are the balance knob: the charge bill is ENERGY, 1/unit on
# your own Field and 2/unit off-Field over the -24..24 meter (the old
# spirit bill left with its system), so each figure below is still N charge
# SESSIONS with recovery between, not one action -- plus the wager bits
# that banked the DNA.
DIVERGE_NEED = {"Fresh": 2, "InTraining": 4, "Rookie": 8,
                "Champion": 12, "Ultimate": 16}
_STAGE_ORDER = ["Fresh", "InTraining", "Rookie", "Champion", "Ultimate", "Mega"]


def divergence_target(pet):
    """The armed steer's destination, or None while unarmed (no strict-max
    Field, an under-threshold charge, or no graph edge in that Field)."""
    field = pet.highest_dna()
    if not field or field == "None":       # the None bin is wasted DNA, not a road
        return None
    need = DIVERGE_NEED.get(pet.stage)
    if need is None or pet.dna_applied.get(field, 0) < need:
        return None
    try:
        nxt = _STAGE_ORDER[_STAGE_ORDER.index(pet.stage) + 1]
    except (ValueError, IndexError):
        return None
    _, by_num = data.load_sprites()
    reqs = data.load_requirements()
    out = []
    for t in data.load_evolutions().get(pet.num, []):
        rec = by_num.get(t)
        if rec is None or t == pet.num or data.is_placeholder(t):
            continue
        if rec["stage"] != nxt or rec["field"] != field:
            continue
        req = reqs.get(t, {})
        if req.get("special", "None") != "None" or req.get("evol_item", -1) != -1:
            continue        # jogress/fusion/mode/item roads keep their own doors
        if req.get("xantibody", "None") == "Induced" \
                and getattr(pet, "x_antibody", "None") == "None":
            continue        # Induced X-forms stay X-egg territory (LINES_SPEC §4)
        out.append(t)
    if not out:
        return None
    # the paid steer always fires: gates pick among qualifiers, else the
    # best-fulfilled edge (select()'s never-stuck fallback idiom)
    valid = [t for t in out if check(pet, t)]
    pool = valid or out
    best = max(fulfilled(pet, t) for t in pool)
    top = [t for t in pool if abs(fulfilled(pet, t) - best) < 1e-9]
    if len(top) > 1:
        mind = min(deviation(pet, t) for t in top)
        top = [t for t in top if deviation(pet, t) == mind]
    return random.choice(top)


def divergence_roads(pet):
    """{field: [target nums]} of every next-stage graph edge from the current
    form, by Field -- the DNA screen's map of where each charge can lead
    (legibility arc: the door must be visible to be a choice)."""
    try:
        nxt = _STAGE_ORDER[_STAGE_ORDER.index(pet.stage) + 1]
    except (ValueError, IndexError):
        return {}
    _, by_num = data.load_sprites()
    reqs = data.load_requirements()
    roads = {}
    for t in data.load_evolutions().get(pet.num, []):
        rec = by_num.get(t)
        if rec is None or t == pet.num or data.is_placeholder(t):
            continue
        if rec["stage"] != nxt or rec["field"] == "None":
            continue
        req = reqs.get(t, {})
        if req.get("special", "None") != "None" or req.get("evol_item", -1) != -1:
            continue
        if req.get("xantibody", "None") == "Induced" \
                and getattr(pet, "x_antibody", "None") == "None":
            continue
        roads.setdefault(rec["field"], []).append(t)
    return roads


def is_mode_form(num):
    """This form IS a Mode (SpecialEvolution=Mode) -- mode change reverts it."""
    return data.load_requirements().get(num, {}).get("special") == "Mode"


def can_mode_change(pet):
    """Evolution.canModeChange: the current form is a Mode, or any of its
    evolution targets is one (raw dex check; validity is tested on use)."""
    if is_mode_form(pet.num):
        return True
    return any(is_mode_form(t) for t in data.load_evolutions().get(pet.num, []))


def mode_targets(pet):
    """The valid Mode evolutions right now (checkSpecialCondition Mode + the
    FULL requirement gates -- check's connecting flag waives only the
    special-type early-return, exactly like jogress), best-fulfilled first."""
    out = [t for t in data.load_evolutions().get(pet.num, [])
           if is_mode_form(t) and check(pet, t, connecting=True)]
    return sorted(out, key=lambda t: -fulfilled(pet, t))


def death_targets(pet):
    """The valid Death-special evolutions (checkSpecialCondition Death: only a
    dying pet qualifies; the full requirement gates still apply), best first."""
    out = [t for t in data.load_evolutions().get(pet.num, [])
           if data.load_requirements().get(t, {}).get("special") == "Death"
           and check(pet, t, connecting=True)]
    return sorted(out, key=lambda t: -fulfilled(pet, t))


def pre_evolution(num):
    """getPreEvolutions().get(0): the first dex form that evolves into `num`."""
    for src in sorted(data.load_evolutions()):
        if num in data.load_evolutions()[src]:
            return src
    return None


_SYM = {"GreaterThan": ">", "LessThan": "<", "EqualTo": "="}


def requirement_report(pet, num):
    """The data book's requirement checklist for one evolution target: a list of
    (met, text) rows, one per CONSTRAINED gate, mirroring check()'s reads exactly
    (unconstrained "None" gates are skipped).  met is True/False, or None for an
    informational row (the probability line, the DNA-bypass note)."""
    req = data.load_requirements().get(num)
    if req is None:
        return [(False, "unknown form")]
    rows = []

    def cmp_row(label, gate, actual, pct=False):
        cond, val = gate
        if cond == "None":
            return
        unit = "%" if pct else ""
        rows.append((_cmp(cond, val, actual),
                     f"{label} {_SYM.get(cond, '?')}{val:g}{unit}  (now {actual:g}{unit})"))

    # hard locks first: forms normal timed care can never reach
    special = req.get("special", "None")
    if special == "Fusion":
        rows.append((False, "via Fusion (jogress handshake) only"))
    elif special == "Mode":
        rows.append((False, "via Mode Change only"))
    elif special == "Death":
        rows.append((False, "at death's door only"))
    elif special == "Jogress":
        rows.append((None, "a Jogress line \u2014 care can reach it"))
    ev_item = req.get("evol_item", -1)
    if ev_item != -1:
        item = data.consumable_by_key(f"i:{ev_item}")
        # the bag stores NAMED keys (the crest eggs) -- checking the raw
        # "i:N" icon key read a held Digimental as forever-unmet, inflating
        # every item-locked form's unmet count (gameplay audit 2026-07-19)
        from .pet import Pet as _Pet
        named = next((k for k, v in _Pet._CREST_IDS.items() if v == ev_item),
                     None)
        bag = getattr(pet, "inventory", {})
        held = (named in bag if named is not None else f"i:{ev_item}" in bag)
        rows.append((held,
                     f"use {(item or {}).get('name', f'item {ev_item}')}"))
    if req.get("xantibody", "None") == "Induced":     # canon gates Induced only
        rows.append((getattr(pet, "x_antibody", "None") != "None", "X-Antibody"))

    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    # (the power-total + per-attr stat ROWS left with their gates, 2026-07-18:
    # v0.5.18 dropped the DVPet power walls from check() but the report kept
    # DISPLAYING them -- a checklist lying about what actually gates)
    cmp_row("battles", req["battles"], pet.battles)
    cmp_row("win rate", req["wins"], _win_rate(pet), pct=True)
    cmp_row("disturbs", req["disturb"], pet.disturb)
    cmp_row("overeats", req["overeat"], pet.overeat)
    cmp_row("care slips", req["mistakes"], pet.care_mistakes)
    cmp_row("generation", req.get("incarnations", ("None", 0)), getattr(pet, "generation", 1))
    if req["weight"] != "None":
        rows.append((req["weight"] == weight_category(pet.weight, pet._base_weight()),
                     f"weight: {req['weight']}"))
    # (the mood requirement row left with the mood system; BASIC VPET 2026-07-16)
    lf_min = req.get("level_fought_min", 0)
    if lf_min and req["level_fought"][0] != "None":
        cnt = sum(1 for lv in getattr(pet, "levels_fought", ()) if lv >= lf_min)
        cmp_row(f"foes \u2265lv{lf_min}", req["level_fought"], cnt)
    dna = req.get("dna") or {}
    dna_gated = [(f, g) for f, g in dna.items() if g[0] != "None"]
    for f, (cond, val) in dna_gated:
        rows.append((_cmp(cond, val, pet.dna_percent(f)),
                     f"DNA {data.pretty_field(f)} {_SYM.get(cond, '?')}{val:g}%"
                     f"  (now {pet.dna_percent(f):g}%)"))
    prob, bound = req["prob"], req["probBound"]
    if prob < bound:
        boost = getattr(pet, "evol_bonus", 0) + int(_win_rate(pet) * WIN_RATE_PROB_COEF)
        rows.append((None, f"then a {min(prob + boost, bound)}/{bound} chance"))
    return rows or [(True, "no requirements \u2014 time alone")]


def candidates(pet):
    """Debug helper: (num, name, passes, fulfilled) for each target."""
    _, by_num = data.load_sprites()
    out = []
    for t in data.load_evolutions().get(pet.num, []):
        if t in by_num and by_num[t]["stage"] != pet.stage:
            out.append((t, by_num[t]["name"], check(pet, t), round(fulfilled(pet, t), 2)))
    return out
