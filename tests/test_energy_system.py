"""Energy-system canon audit pins (2026-07-06) vs DVPet PhysicalState.

setEnergy itself was rebuilt in the mood arc; this audit covered the rest.
Sleep/nap regeneration and the perfect-conditions bounce verified verbatim
(NapEnergyGain is 1 for ALL 1574 species -- the flat +1 was already right).
Found: the item loader int()'d FRACTIONAL energies to zero (canon applyItem
treats a sub-1 value as a share of maxEnergy -- the X-Program's -0.8, the
Digimentals' -0.66), the X-Program/ItemEvol branches skipped the applyItem
stat core entirely, and can_battle/can_train carried invented hard gates
(MinEnergyForActivity is -127 on the classic column; the refusal roll is
canon's only gate)."""
import math
import random

from tuipet import data
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 10 * 60.0
    p.weight = p._base_weight()
    p.mood = 100
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --- fractional item energy -----------------------------------------------------

def test_the_loader_keeps_fractional_energies():
    assert data.consumable_by_key("i:14")["energy"] == -0.8    # X-Program Sample
    assert data.consumable_by_key("i:15")["energy"] == -0.66   # Courage Digimental
    assert isinstance(data.consumable_by_key("f:0")["energy"], int)   # whole stays int

def test_fractional_energy_is_a_share_of_max():
    p = _pet(energy=24, max_energy=24, enthusiasm=0)
    p._apply_item_stats(dict(data.consumable_by_key("i:15")), 1.0)
    # ceil(-0.66 x 24) = -15: the Digimental drinks 66% like a jogress
    assert p.energy == 24 + math.ceil(-0.66 * 24)

def test_the_x_program_bills_its_full_canon_price(monkeypatch):
    p = _pet(energy=24, max_energy=24, hunger=4, strength=4, enthusiasm=0, mood=300)
    p.inventory["i:14"] = 1
    monkeypatch.setattr(Pet, "check_refused", lambda self, **k: False)
    monkeypatch.setattr(random, "randrange", lambda n: 0)      # the life roll draws free
    msg = p.use_item("i:14")
    assert "X-Program complete" in msg and p.x_antibody == "Permanent"
    assert p.energy == 24 + math.ceil(-0.8 * 24)               # -19
    assert p.hunger == 0                                       # 4 - 10 floors
    assert p.strength == 0                                     # 4 - 13 floors
    # the -300 mood DELTA (300 -> 0), then the spirit crashing into its -10
    # boundary bills MaxEnthusiasmMoodPenalty on top
    assert p.mood == -10 and p.enthusiasm == -10

def test_a_digimental_drains_the_new_forms_ceiling(monkeypatch):
    from tuipet import pet as pet_mod
    p = _pet(energy=24, max_energy=24, compliance=False)
    p.inventory["i:15"] = 1
    monkeypatch.setattr(Pet, "check_refused", lambda self, **k: False)
    monkeypatch.setattr(pet_mod.evolution, "item_select", lambda pet, iid: 102)
    msg = p.use_item("i:15")
    assert "evolved" in msg and p.num == 102
    assert p.energy == min(24, p.max_energy) + math.ceil(-0.66 * p.max_energy)

def test_an_unaffordable_digimental_is_refused():
    p = _pet(energy=5, max_energy=24, obedience=150, compliance=False)
    # 5 + ceil(-0.66 x 24) < 0: the affordability auto-refuse, like jogress
    assert p.check_refused(item=data.consumable_by_key("i:15"), energy_change=-0.66)
    q = _pet(energy=20, max_energy=24, obedience=150, compliance=False)
    assert not q.check_refused(item=data.consumable_by_key("i:15"), energy_change=-0.66)


# --- no hard activity gates (the refusal roll is the gate) -----------------------

def test_a_worn_pet_may_still_fight_and_train():
    """MinEnergyForActivity -127 (classic column): canon canBattle/canExercise
    hard-gate NOTHING -- fatigue and emptiness shade the refusal roll
    (unwellMod) and the injury odds instead."""
    p = _pet(energy=-3, fatigue_length=30.0, compliance=True)
    assert p.can_battle() is None
    assert p.can_train() is None

def test_the_dead_and_egg_gates_still_hold():
    p = _pet()
    p.dead = True
    assert p.can_battle() is not None and p.can_train() is not None
    q = Pet(num=-1, name="Digitama", stage="Egg")
    assert q.can_battle() is not None and q.can_train() is not None
