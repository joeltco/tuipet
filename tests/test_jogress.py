"""Jogress vs DVPet: connecting only waives the special-type gate -- the fusion
form's full requirements still apply -- and the fusion drinks 66% of max energy."""
import random

import pytest

from tuipet.pet import Pet
from tuipet import data, jogress


def _jogress_parent():
    _, by = data.load_sprites()
    reqs = data.load_requirements()
    evo = data.load_evolutions()
    for n, r in by.items():
        if data.is_placeholder(n):
            continue
        if any(reqs.get(t, {}).get("special") in ("Jogress", "Fusion", "Mode")
               for t in evo.get(n, [])):
            return n, by
    return None, by


def test_unearned_pet_gets_no_fusions():
    random.seed(1)
    n, by = _jogress_parent()
    if n is None:
        pytest.skip("no jogress parents in the atlas")
    p = Pet(num=n, stage=by[n]["stage"], attribute=by[n]["attribute"] or "Vaccine")
    assert jogress.options(p) == []      # the fusion form's requirements gate the menu


def test_earned_fusion_opens_and_costs_energy():
    random.seed(4)
    n, by = _jogress_parent()
    if n is None:
        pytest.skip("no jogress parents in the atlas")
    p = Pet(num=n, stage=by[n]["stage"], attribute=by[n]["attribute"] or "Vaccine")
    p.vaccine, p.data_power, p.virus = 250, 60, 20
    p.battles, p.wins = 80, 70
    p.train_time = "Noon"
    p.overeat = 5
    p.levels_fought = [5, 5, 5, 5]
    p.evol_bonus = 100000            # push prob >= probBound: skip the (real) dice
    opts = jogress.options(p)
    assert opts, "a fully-raised pet unlocks its fusion"
    e0 = p.energy = p.max_energy
    cost = int(round(p.max_energy * jogress.JOGRESS_ENERGY_COST))   # 66% of the PRE-fuse max
    jogress.fuse(p, opts[0]["num"])
    assert p.energy == e0 - cost
