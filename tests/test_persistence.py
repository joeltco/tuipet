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
    pet = Pet(num=-1, name="Testmon", stage="Child", bits=99,
              care_mistakes=3, generation=4, saved_hit_type="mega",
              trainings_cur_stage=7, energy_bonus=3)
    persistence.save(pet)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Testmon"
    assert loaded.stage == "Child"
    assert loaded.bits == 99
    assert loaded.care_mistakes == 3
    assert loaded.generation == 4
    assert loaded.saved_hit_type == "mega"
    assert loaded.trainings_cur_stage == 7
    assert loaded.energy_bonus == 3


def test_load_missing_file():
    assert persistence.load() == (None, "")
    assert persistence.exists() is False


def test_offline_egg_is_inert():
    egg = Pet(num=-1, stage="Egg", wall_time=time.time() - 7200)
    assert egg.catch_up() == 0                   # eggs do not replay
    assert egg.hunger == 4


def test_offline_decay_applies():
    """A real away gap replays real minutes: hunger drops on the hourly
    decay and the greeting names the gap."""
    import random
    random.seed(1)
    pet = Pet.new_egg(egg_type=1)
    pet._hatch_into_fresh()
    pet.stage = "Adult"                          # a wide-awake window at noon
    pet.wall_time = time.time() - 3 * 3600       # 3h away
    pet.stage_minutes = 1
    persistence.save(pet)
    blob = json.load(open(persistence.SAVE_PATH))
    blob["_saved_at"] = time.time() - 3 * 3600
    json.dump(blob, open(persistence.SAVE_PATH, "w"))
    loaded, msg = persistence.load()
    assert loaded is not None
    assert loaded.total_minutes >= 60            # the minutes really replayed


def test_offline_cap_at_3_days():
    """A save abandoned for weeks replays at most the 3-day horizon."""
    from tuipet.pet import REPLAY_CAP_MIN
    pet = Pet.new_egg(egg_type=1)
    pet._hatch_into_fresh()
    pet.evo_blocked = True                       # hold the form for the pin
    pet.wall_time = time.time() - 30 * 86400
    n = pet.catch_up()
    assert n <= REPLAY_CAP_MIN


def test_progress_signals_round_trip():
    persistence.egg_own(7)
    persistence.egg_own(7)            # idempotent
    persistence.note_generation(5)
    persistence.note_generation(3)   # max-only: must not lower
    persistence.note_stage_index(4)
    persistence.note_xanti()
    persistence.map_complete_add(2)

    assert persistence.get_eggs_owned() == {7}
    prog = persistence.get_progress()
    assert prog["max_gen"] == 5
    assert prog["max_stage"] == 4
    assert prog["xanti_ever"] is True
    assert 2 in prog["maps"]
    # full shape the egg evaluator depends on
    for k in ("album", "wins", "max_gen", "max_stage", "xanti_ever", "maps",
              "tourneys", "last_field", "last_attr", "last_elem", "last_mood",
              "last_obed", "last_xanti"):
        assert k in prog


def test_snapshot_ignores_egg():
    egg = Pet(num=-1, stage="Egg")
    persistence.snapshot_prev_gen(egg)
    # no last_gen written -> defaults
    assert persistence.get_progress()["last_field"] == "None"
