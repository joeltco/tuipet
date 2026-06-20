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


def weight_category(weight, base):
    hi = base + round(base * WEIGHT_THRESH)
    lo = base - round(base * WEIGHT_THRESH)
    return "Over" if weight > hi else ("Under" if weight < lo else "Healthy")


def mood_category(mood):
    return "Happy" if mood >= 75 else ("Neutral" if mood >= 40 else
                                       ("Unhappy" if mood >= 15 else "Depressed"))


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


def check(pet, num):
    """checkEvolReq: every gate must pass (no DNA bypass in solo play)."""
    req = data.load_requirements().get(num)
    if req is None:
        return False
    if req.get("special", "None") != "None":
        return False  # jogress/fusion/mode need a special trigger, not normal evolution
    vac, dat, vir = _stats(pet)
    total = vac + dat + vir
    if not _stat_total_ok(req, total):
        return False
    gates = [
        _cmp(*req["battles"], pet.battles),
        _attr(req["data"][0], dat, total), _attr(req["data"][1], dat, total),
        _attr(req["vaccine"][0], vac, total), _attr(req["vaccine"][1], vac, total),
        _attr(req["virus"][0], vir, total), _attr(req["virus"][1], vir, total),
        req["time"] == "None",                          # no day-cycle yet
        req["weight"] == "None" or req["weight"] == weight_category(pet.weight, pet._base_weight()),
        _cmp(*req["disturb"], pet.disturb),
        _cmp(*req["overeat"], pet.overeat),
        _cmp(*req["sick"], pet.sick_count),
        _cmp(*req["injured"], pet.injuries),
        req["mood"] == "None" or req["mood"] == mood_category(pet.mood),
        _cmp(*req["obedience"], pet.obedience),
        _cmp(*req["wins"], _win_rate(pet)),
        _cmp(*req["mistakes"], pet.care_mistakes),
    ]
    if not all(gates):
        return False
    # probability: prob >= probBound -> always; else prob must beat a roll
    prob, bound = req["prob"], req["probBound"]
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
    if _met(req["battles"], pet.battles):
        score += R["battle"]
    for k, actual in (("data", dat), ("vaccine", vac), ("virus", vir)):
        for i in (0, 1):
            g = req[k][i]
            if g[0] != "None" and _attr(g, actual, total):
                score += R[k if k in R else "data"]
    if req["weight"] != "None" and req["weight"] == weight_category(pet.weight, pet._base_weight()):
        score += R["weight"]
    for k, actual in (("disturb", pet.disturb), ("overeat", pet.overeat),
                      ("sick", pet.sick_count), ("injured", pet.injuries),
                      ("obedience", pet.obedience)):
        if _met(req[k], actual):
            score += R.get(k, R["injury"] if k == "injured" else 1)
    if req["mood"] != "None" and req["mood"] == mood_category(pet.mood):
        score += R["mood"]
    if _met(req["wins"], _win_rate(pet)):
        score += R["winRate"]
    cond, val = req["mistakes"]
    if cond != "None" and _cmp(cond, val, pet.care_mistakes):
        score += {"LessThan": R["mistakeLess"], "GreaterThan": R["mistakeGreater"],
                  "EqualTo": R["mistakeEqual"]}.get(cond, R["mistakeNone"])
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


def select(pet):
    """Return the chosen evolution target num, or None."""
    _, by_num = data.load_sprites()
    targets = [t for t in data.load_evolutions().get(pet.num, [])
               if t in by_num and by_num[t]["stage"] != pet.stage]
    valid = [t for t in targets if check(pet, t)]
    if not valid:
        return None
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
