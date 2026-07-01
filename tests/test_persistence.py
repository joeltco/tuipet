"""Save/load round-trip, old-save migration, bounded offline catch-up, and the
cross-generation progress signals that feed the egg-unlock engine.

All I/O is sandboxed by the autouse `isolate_save` fixture in conftest.
"""
import json
import time

from tuipet import persistence
from tuipet.pet import Pet


def test_isolation_is_real(tmp_path):
    """Belt-and-suspenders: the sandbox really points at tmp, not the live save."""
    assert persistence.SETTINGS_PATH.startswith(str(tmp_path))
    assert persistence.SAVE_PATH.startswith(str(tmp_path))


def test_round_trip_preserves_fields():
    pet = Pet(num=-1, name="Testmon", stage="Rookie",
              care_mistakes=3, generation=4)
    persistence.save(pet)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Testmon"
    assert loaded.stage == "Rookie"
    assert loaded.care_mistakes == 3
    assert loaded.generation == 4


def test_load_missing_file():
    assert persistence.load() == (None, "")
    assert persistence.exists() is False


def test_old_save_migration():
    """A save written before effect_id/progress existed must load with defaults,
    not crash (forward-compat for Joel's real save across updates)."""
    import os
    old = {"num": -1, "name": "Oldmon", "stage": "Champion", "bits": 10,
           "_saved_at": time.time()}
    os.makedirs(persistence.SAVE_DIR, exist_ok=True)
    with open(persistence.SAVE_PATH, "w") as fh:
        json.dump(old, fh)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Oldmon"
    assert loaded.generation == 1      # field absent in the save -> dataclass default


def test_offline_egg_does_not_decay():
    egg = Pet(num=-1, stage="Egg")
    egg.mood, egg.hunger = 0, 4
    msg = persistence._offline(egg, 7200)        # 2h away
    assert msg == ""
    assert egg.hunger == 4 and egg.mood == 0     # eggs are inert offline
    assert egg.world_seconds == 7200             # ...but the clock still advances
    assert egg.age_seconds == 7200


def test_offline_decay_applies():
    pet = Pet(num=-1, stage="Rookie")
    pet.mood, pet.hunger = 100, 4
    msg = persistence._offline(pet, 2 * 3600)    # 2h
    assert pet.mood < 100, "mood should decay while away"
    assert pet.hunger < 4, "hunger should drop while away"
    assert "away" in msg


def test_offline_cap_at_36h():
    """A save abandoned for days catches up at most MAX_OFFLINE (36h), never more."""
    pet = Pet(num=-1, name="Capmon", stage="Rookie")
    persistence.save(pet)
    # rewrite the timestamp far into the past
    data = json.load(open(persistence.SAVE_PATH))
    data["_saved_at"] = time.time() - 100 * 3600   # 100h ago
    json.dump(data, open(persistence.SAVE_PATH, "w"))
    loaded, msg = persistence.load()
    assert loaded is not None
    # capped elapsed == 36h -> message reports 36h, not 100h
    assert "36h" in msg


def test_progress_signals_round_trip():
    persistence.egg_own(7)
    persistence.egg_own(7)            # idempotent
    persistence.note_generation(5)
    persistence.note_generation(3)   # max-only: must not lower
    persistence.note_stage_index(4)
    persistence.map_complete_add(2)

    assert persistence.get_eggs_owned() == {7}
    prog = persistence.get_progress()
    assert prog["max_gen"] == 5
    assert prog["max_stage"] == 4
    assert 2 in prog["maps"]
    # full shape the egg evaluator depends on
    for k in ("album", "wins", "max_gen", "max_stage", "maps",
              "last_field", "last_attr", "last_elem", "last_mood",
              "last_obed"):
        assert k in prog


def test_snapshot_prev_gen():
    pet = Pet(num=-1, stage="Champion", attribute="Vaccine", mood=50, obedience=7)
    pet.field = "Nature Spirits"
    persistence.snapshot_prev_gen(pet)
    prog = persistence.get_progress()
    assert prog["last_field"] == "Nature Spirits"
    assert prog["last_attr"] == "Vaccine"
    assert prog["last_mood"] == 50
    assert prog["last_obed"] == 7


def test_snapshot_ignores_egg():
    egg = Pet(num=-1, stage="Egg")
    persistence.snapshot_prev_gen(egg)
    # no last_gen written -> defaults
    assert persistence.get_progress()["last_field"] == "None"
