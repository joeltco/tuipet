"""Authentic DM20 care-gated evolution.

Each evolution edge carries the corpus `parsed` conditions (care_mistakes / training /
overfeed / battles / victories). A pet evolves into the MOST SPECIFIC branch whose care
record satisfies the conditions; the empty-condition edge is the bad-care catch-all
(e.g. Agumon -> Numemon). Deterministic given the care state.
"""
from __future__ import annotations
import random
from . import data
from . import species as _sp

WEIGHT_THRESH = 0.5  # over/under-weight threshold (fraction of base weight)

_PET_VALUE = {
    "care_mistakes": lambda p: p.care_mistakes,
    "training":      lambda p: getattr(p, "trainings", 0),
    "overfeed":      lambda p: getattr(p, "overeat", 0),
    "battles":       lambda p: p.battles,
    "battles_n":     lambda p: p.battles,
    "victories":     lambda p: p.wins,
}
_SOFT = {"time_min", "special_egg", "version_egg"}   # timer/egg-origin: handled elsewhere, non-blocking
_JOGRESS_ONLY = {"tag_battle_with"}                  # reachable only via jogress, not normal evolution


def _in_range(spec, val):
    """Whether `val` satisfies a corpus condition value ('0-2' / '3+' / '5-15' / 15 / True)."""
    if isinstance(spec, bool):
        return True                                  # 'battles': True is a redundant flag
    if isinstance(spec, (int, float)):
        return val >= spec                           # 'battles_n': 15 -> at least 15
    s = str(spec).strip()
    if s.endswith("+"):
        return val >= int(s[:-1])
    if "-" in s.lstrip("-"):
        a, b = s.split("-", 1)
        return int(a) <= val <= int(b)
    if s.lstrip("-").isdigit():
        return val >= int(s)
    return True


def _edge_met(pet, parsed):
    for k, v in (parsed or {}).items():
        if k in _JOGRESS_ONLY:
            return False
        if k in _SOFT:
            continue
        getter = _PET_VALUE.get(k)
        if getter is not None and not _in_range(v, getter(pet)):
            return False
    return True


def _specificity(parsed):
    return sum(1 for k in (parsed or {}) if k in _PET_VALUE)


def species_select(pet):
    """The authentic next-stage target for `pet`, gated on its care record. None if no edge."""
    by_id = {r["id"]: r["num"] for r in _sp.roster()}
    _, by_num = data.load_sprites()
    want = data.next_stage(pet.stage)
    edges = []
    for e in _sp.evolutions(pet.num):
        t = by_id.get(e.get("to_id"))
        if t is None or t not in by_num or data.is_placeholder(t):
            continue
        if want is not None and by_num[t]["stage"] != want:
            continue                                 # normal evolution climbs exactly one stage
        edges.append((t, e.get("parsed") or {}))
    met = [(t, p) for t, p in edges if _edge_met(pet, p)]
    if met:
        best = max(_specificity(p) for _, p in met)  # most-specific branch wins; {} is the catch-all
        return random.choice([t for t, p in met if _specificity(p) == best])
    return random.choice([t for t, _ in edges]) if edges else None


def select(pet):
    """The chosen evolution target num (authentic DM20 care-gated branch), or None."""
    return species_select(pet)


def weight_category(weight, base):
    """Over / Healthy / Under relative to a base weight (the overweight-injury gate)."""
    hi = base + round(base * WEIGHT_THRESH)
    lo = base - round(base * WEIGHT_THRESH)
    return "Over" if weight > hi else ("Under" if weight < lo else "Healthy")


def candidates(pet):
    """Debug helper: (num, name, conditions-met, parsed) per next-stage edge."""
    by_id = {r["id"]: r["num"] for r in _sp.roster()}
    _, by_num = data.load_sprites()
    out = []
    for e in _sp.evolutions(pet.num):
        t = by_id.get(e.get("to_id"))
        if t in by_num:
            out.append((t, by_num[t]["name"], _edge_met(pet, e.get("parsed") or {}), e.get("parsed") or {}))
    return out
