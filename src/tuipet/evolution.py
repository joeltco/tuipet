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


def _major_hab(pet):
    """DVPet getMajorHabitat: evolution gates on the habitat lived in MOST, not the current one."""
    mh = getattr(pet, "major_habitat", None)
    return mh() if callable(mh) else getattr(pet, "habitat", -1)  # Config.DNAFulfilledRate — priority weight per met DNA field gate
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


def mood_category(mood):
    if mood <= -250:            # ToDepressedMoodMin
        return "Depressed"
    if mood >= 150:             # MinHappyMood
        return "Happy"
    if mood <= -1:              # MinUnhappyMood
        return "Unhappy"
    return "Neutral"


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


def check(pet, num, item=-1):
    """checkEvolReq: every gate must pass, OR the form\'s DNA requirement is met
    (DVPet\'s `testX || getDNA` bypass). checkStatTotal + probability are never bypassed."""
    req = data.load_requirements().get(num)
    if req is None:
        return False
    if req.get("special", "None") != "None":
        return False  # jogress/fusion/mode need a special trigger, not normal evolution
    ev_item = req.get("evol_item", -1)
    if item == -1:
        if ev_item != -1:
            return False     # item-locked form: unreachable by timed care (need the item)
    elif ev_item != item:
        return False         # using an item only validates the forms that require it
    if req.get("xantibody", "None") in ("Induced", "Natural") and getattr(pet, "x_antibody", "None") == "None":
        return False  # X-Antibody forms are unreachable without the antibody
    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    if not _stat_total_ok(req, total):
        return False
    dna_ok = _dna_ok(pet, req)            # DVPet: getDNA() bypasses the care/stat/battle gates
    gates = [
        _cmp(*req["battles"], pet.battles),
        _attr(req["data"][0], dat, total), _attr(req["data"][1], dat, total),
        _attr(req["vaccine"][0], vac, total), _attr(req["vaccine"][1], vac, total),
        _attr(req["virus"][0], vir, total), _attr(req["virus"][1], vir, total),
        req["time"] == "None" or req["time"] == getattr(pet, "train_time", ""),
        req["weight"] == "None" or req["weight"] == weight_category(pet.weight, pet._base_weight()),
        _cmp(*req["disturb"], pet.disturb),
        _cmp(*req["overeat"], pet.overeat),
        _cmp(*req["sick"], pet.sick_count),
        _cmp(*req["injured"], pet.injuries),
        req["mood"] == "None" or req["mood"] == mood_category(pet.mood),
        req.get("major_food", "None") == "None"
        or req["major_food"] == (pet.major_food() if hasattr(pet, "major_food") else None),
        _cmp(*req.get("incarnations", ("None", 0)), getattr(pet, "generation", 1)),
        _cmp(*req["obedience"], pet.obedience),
        _cmp(*req["wins"], _win_rate(pet)),
        _cmp(*req["mistakes"], pet.care_mistakes),
    ]
    if not all(g or dna_ok for g in gates):
        return False
    # LevelFought: enough opponents of at least MinLevelFought power beaten this stage
    lf_min = req.get("level_fought_min", 0)
    if lf_min:
        cnt = sum(1 for lv in getattr(pet, "levels_fought", ()) if lv >= lf_min)
        if not (_cmp(*req["level_fought"], cnt) or dna_ok):
            return False
    # temperature + habitat conditions (DVPet gates evolution on these; we have
    # both systems, so honour them)
    tr = req.get("temp_req")
    if tr is not None and not (tr[0] <= getattr(pet, "temp", 50) <= tr[1]) and not dna_ok:
        return False
    hr = req.get("habitat_req", -1)
    if hr != -1 and _major_hab(pet) != hr and not dna_ok:
        return False
    # the antibody commits the pet to its X-form: skip the random prob gate
    if req.get("xantibody", "None") in ("Induced", "Natural") and getattr(pet, "x_antibody", "None") != "None":
        return True
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
    for k, actual in (("disturb", pet.disturb), ("overeat", pet.overeat),
                      ("sick", pet.sick_count), ("injured", pet.injuries),
                      ("obedience", pet.obedience)):
        if _met(req[k], actual):
            score += R.get(k, R["injury"] if k == "injured" else 1)
    if req["mood"] != "None" and req["mood"] == mood_category(pet.mood):
        score += R["mood"]
    if req.get("major_food", "None") != "None" and hasattr(pet, "major_food") \
            and req["major_food"] == pet.major_food():
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
    if req.get("xantibody", "None") in ("Induced", "Natural") and getattr(pet, "x_antibody", "None") != "None":
        score += X_ANTIBODY_RATE
    tr = req.get("temp_req")
    if tr is not None and tr[0] <= getattr(pet, "temp", 50) <= tr[1]:
        score += 1
    if req.get("habitat_req", -1) != -1 and _major_hab(pet) == req["habitat_req"]:
        score += 1
    for f, g in (req.get("dna") or {}).items():     # getDNAReq: priority per met Field gate
        if g[0] != "None" and _cmp(g[0], g[1], pet.dna_percent(f)):
            score += DNA_FULFILLED_RATE
    if _dna_ok(pet, req):                            # getDNAReq: full-match dnaFulfilledRate bonus
        score += DNA_FULFILLED_RATE
    # element/field affinity vs the pet's habitat (compatible +1, incompatible -1)
    h = data.load_habitats().get(getattr(pet, "habitat", -1))
    if h:
        if req.get("element", "None") in h["compat_elements"]:
            score += 1   # Config._compatibleElementPriorityChange
        if req.get("field", "None") in h["compat_fields"]:
            score += 1   # Config._compatibleFieldPriorityChange
        if req.get("field", "None") in h["incompat_fields"]:
            score -= 1   # Config._incompatibleFieldPriorityChange
        if req.get("element", "None") in h["incompat_elements"]:
            score -= 1   # Config._incompatibleElementPriorityChange
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
                      ("sick", pet.sick_count), ("injured", pet.injuries),
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


def _is_xform(num):
    return data.load_requirements().get(num, {}).get("xantibody", "None") in ("Induced", "Natural")


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


def item_direct(pet, dexnum):
    """Direct evolution item (items.csv DigimonID names the form): evolve into `dexnum`
    if it is a reachable graph neighbour of the current form."""
    if dexnum is None or dexnum < 0:
        return None
    return dexnum if dexnum in data.load_evolutions().get(pet.num, []) else None


def select(pet):
    """Return the chosen evolution target num, or None.

    Normal evolution climbs a stage; with the X-Antibody, an X-form is also
    reachable -- including a same-stage reformat (e.g. Agumon -> Agumon X)."""
    _, by_num = data.load_sprites()
    has_xa = getattr(pet, "x_antibody", "None") != "None"
    targets = []
    for t in data.load_evolutions().get(pet.num, []):
        if t not in by_num or t == pet.num:
            continue
        if data.is_placeholder(t):
            continue
        if by_num[t]["stage"] != pet.stage or (has_xa and _is_xform(t)):
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
                    and data.load_requirements().get(t, {}).get("evol_item", -1) == -1]
        if stage_up:
            return max(stage_up, key=lambda t: fulfilled(pet, t))
        return None
    if has_xa:
        xvalid = [t for t in valid if _is_xform(t)]
        if xvalid:
            valid = xvalid          # the X-Antibody steers evolution to an X-form
    best = max(fulfilled(pet, t) for t in valid)
    top = [t for t in valid if abs(fulfilled(pet, t) - best) < 1e-9]
    if len(top) > 1:
        mind = min(deviation(pet, t) for t in top)
        top = [t for t in top if deviation(pet, t) == mind]
    return random.choice(top)


def candidates(pet):
    """Debug helper: (num, name, passes, fulfilled) for each target."""
    _, by_num = data.load_sprites()
    out = []
    for t in data.load_evolutions().get(pet.num, []):
        if t in by_num and by_num[t]["stage"] != pet.stage:
            out.append((t, by_num[t]["name"], check(pet, t), round(fulfilled(pet, t), 2)))
    return out
