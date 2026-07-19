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
    # canon: energy += Math.ceil(-0.66 x max) -- ceil rounds the negative product
    # TOWARD ZERO (max 24 drains 15, not the old round()'s 16)
    import math
    cost = -math.ceil(-jogress.JOGRESS_ENERGY_COST * p.max_energy)
    jogress.fuse(p, opts[0]["num"])
    assert p.energy == e0 - cost


def test_dp_refusal_names_only_the_refill_that_exists():
    """The DP hint sent players feeding steaks for DP that never came --
    sleep is the ONE refill since nutrition left (jogress audit 2026-07-19).
    The sick-partner catch stays a deliberately dormant canon record."""
    import inspect
    from tuipet import jogress
    from tuipet.pet import Pet, DP_MAX
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    p.dp = DP_MAX - 1
    msg = jogress.can_jogress(p)
    assert msg and "sleep" in msg and "protein" not in msg
    # the one DP grant in the codebase is the sleep tick
    from tuipet import petbody, petcare, shop
    assert "dp += 1" in inspect.getsource(petbody)
    for mod in (petcare, shop):
        assert "dp +=" not in inspect.getsource(mod)
