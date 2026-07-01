"""Edge-case robustness (Workstream B).

A fuzz of ~30 edge inputs found the game degrades gracefully everywhere a user can
reach: a brand-new empty account, 0-bit purchases, dead-pet actions, corrupt /
partial / unknown-num saves, offline extremes, out-of-range egg indices. (The lone
crash, Pet.from_num on a nonexistent num, is an internal fail-loud on a data-
integrity error, not user-reachable — left as-is.) These tests pin the graceful
paths so a refactor can't turn them back into crashes.
"""
import json


from tuipet import data, egg, persistence
from tuipet.pet import Pet


# ---- brand-new empty account (gen 1, no previous-generation snapshot) ------

def test_empty_account_egg_flow():
    prog = persistence.get_progress()           # nothing saved yet
    assert prog["max_gen"] == 1
    assert prog["last_field"] == "None"         # no prev-gen snapshot -> safe defaults
    states = egg.egg_states(prog, set())
    assert states                               # no crash, full map
    sel = egg.selectable_eggs(prog, set())
    assert sel, "a fresh account must still have its starter eggs selectable"
    assert egg.locked_hint(prog, set()) is not None
    assert egg.auto_owned(prog, set()) is not None



# ---- dead-pet interactions are inert and safe ------------------------------

def test_dead_pet_actions_safe():
    p = Pet(num=-1, stage="Rookie", dead=True)
    # none of these may crash, and the pet stays dead
    p.apply_training(2, 100, game="hp")
    p.tick(100)
    assert p.dead is True


# ---- save/load resilience --------------------------------------------------

def test_load_corrupt_json():
    persistence.save(Pet(num=-1, stage="Rookie"))
    with open(persistence.SAVE_PATH, "w") as fh:
        fh.write("{ not json")
    assert persistence.load() == (None, "")


def test_load_partial_save():
    with open(persistence.SAVE_PATH, "w") as fh:
        json.dump({"num": -1, "stage": "Rookie"}, fh)   # missing _saved_at + many fields
    pet, _ = persistence.load()
    assert pet is not None and pet.stage == "Rookie"


def test_load_unknown_num():
    """A save whose species num no longer exists (data refresh) still loads."""
    persistence.save(Pet(num=999999, name="Ghost", stage="Rookie"))
    pet, _ = persistence.load()
    assert pet is not None and pet.num == 999999


def test_future_timestamp_no_time_travel():
    """A save dated in the future must not produce negative offline time."""
    p = Pet(num=-1, name="Fwd", stage="Rookie")
    persistence.save(p)
    blob = json.load(open(persistence.SAVE_PATH))
    import time
    blob["_saved_at"] = time.time() + 10_000      # future
    json.dump(blob, open(persistence.SAVE_PATH, "w"))
    pet, msg = persistence.load()
    assert pet is not None
    assert pet.world_seconds >= 0, "future save must clamp offline elapsed to 0"


# ---- offline catch-up at extremes ------------------------------------------

def test_offline_zero_elapsed():
    p = Pet(num=-1, stage="Rookie", mood=100, hunger=4)
    assert persistence._offline(p, 0) == ""
    assert p.mood == 100 and p.hunger == 4         # nothing decays at 0s


def test_offline_huge_elapsed_stays_bounded():
    p = Pet(num=-1, stage="Rookie", mood=300, hunger=4)
    persistence._offline(p, 10 ** 9)               # absurd gap
    assert -300 <= p.mood <= 300                    # mood stays clamped
    assert 0 <= p.hunger <= 4                        # hunger stays in range


# ---- egg helpers tolerate out-of-range indices -----------------------------

def test_egg_helpers_out_of_range():
    assert egg.frames(10 ** 6)                       # modulo-wrapped, returns frames
    assert egg.hatch_name(10 ** 6) is not None
    assert egg.password_egg(None) is None
