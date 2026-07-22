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
    pet = Pet(num=-1, name="Testmon", stage="Rookie", bits=99,
              care_mistakes=3, generation=4)
    persistence.save(pet)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Testmon"
    assert loaded.stage == "Rookie"
    assert loaded.bits == 99
    assert loaded.care_mistakes == 3
    assert loaded.generation == 4


def test_load_missing_file():
    assert persistence.load() == (None, "")
    assert persistence.exists() is False


def test_old_save_migration():
    """A save written before newer fields existed must load with defaults,
    not crash (forward-compat for Joel's real save across updates) -- and a
    save carrying RETIRED fields (effect_id et al.) must shed them silently."""
    import os
    old = {"num": -1, "name": "Oldmon", "stage": "Champion", "bits": 10,
           "effect_id": 2, "effect_t": 42.0, "toilet_trained": 1,
           "_saved_at": time.time()}
    os.makedirs(persistence.SAVE_DIR, exist_ok=True)
    with open(persistence.SAVE_PATH, "w") as fh:
        json.dump(old, fh)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Oldmon"
    assert not hasattr(loaded, "effect_id")   # retired keys drop on load
    assert loaded.generation == 1             # absent keys take defaults


def test_a_closed_game_is_a_stopped_clock():
    """Joel 2026-07-22: "do we have an away system? like, where the mon still
    grows, even when its shut off? if so, we gotta remove it."  It did -- the
    bounded catch-up advanced age, the GROWTH clock, egg incubation, hunger,
    poop and sleep.  All of it is gone: a save reloads as the pet that was
    saved, whatever the wall clock did in between.  This is the one pin that
    replaces the whole test_offline_* family."""
    pet = Pet(num=-1, name="Stasismon", stage="Rookie")
    pet.hunger, pet.poop, pet.poop_sizes = 4, 0, []
    pet.energy, pet.dp = 5, 2
    persistence.save(pet)
    before = json.load(open(persistence.SAVE_PATH))

    data = dict(before)
    data["_saved_at"] = time.time() - 100 * 3600      # a hundred hours ago
    json.dump(data, open(persistence.SAVE_PATH, "w"))
    loaded, msg = persistence.load()

    assert loaded is not None
    for field in ("age_seconds", "stage_seconds", "world_seconds",
                  "hunger", "poop", "energy", "dp", "care_mistakes"):
        assert getattr(loaded, field) == before[field], \
            f"{field} must not move while the game is shut off"
    assert "away" not in msg and "Welcome back" not in msg, \
        "there is no away report any more -- nothing happened"


def test_a_closed_egg_does_not_incubate():
    """The egg used to hatch while you were gone (canon processSkippedSeconds
    replayed incubation).  With the clock stopped it waits for you."""
    egg = Pet(num=-1, name="Waitmon", stage="Egg")
    persistence.save(egg)
    data = json.load(open(persistence.SAVE_PATH))
    data["_saved_at"] = time.time() - 7200            # 2h >> EGG_DURATION
    json.dump(data, open(persistence.SAVE_PATH, "w"))
    loaded, _ = persistence.load()
    assert loaded.stage == "Egg" and loaded.stage_seconds == egg.stage_seconds
    loaded._tick_egg()                                # first tick after load
    assert not loaded.hatching, "incubation starts when YOU open the game"


def test_the_offline_machinery_is_gone_for_good():
    """Pinned as an ABSENCE: the catch-up and the flag that gated it are
    removed, not merely bypassed, so nothing can quietly re-enter through a
    default argument."""
    import inspect
    assert not hasattr(persistence, "_offline")
    assert not hasattr(persistence, "MAX_OFFLINE")
    assert "catch_up" not in inspect.signature(persistence.pet_from_save).parameters
    assert "catch_up" not in inspect.signature(persistence.load).parameters


def test_progress_signals_round_trip():
    persistence.egg_own(7)
    persistence.egg_own(7)            # idempotent
    persistence.note_generation(5)
    persistence.note_generation(3)   # max-only: must not lower
    persistence.note_stage_index(4)
    persistence.note_xanti()
    persistence.map_complete_add(2)
    persistence.tourney_add(9)

    assert persistence.get_eggs_owned() == {7}
    prog = persistence.get_progress()
    assert prog["max_gen"] == 5
    assert prog["max_stage"] == 4
    assert prog["xanti_ever"] is True
    assert 2 in prog["maps"]
    assert 9 in prog["tourneys"]
    # full shape the egg evaluator depends on
    for k in ("album", "wins", "max_gen", "max_stage", "xanti_ever", "maps",
              "tourneys", "last_field", "last_attr", "last_mood",
              "last_obed", "last_xanti"):
        assert k in prog


def test_snapshot_prev_gen():
    pet = Pet(num=-1, stage="Champion", attribute="Vaccine", mood=50, obedience=7)
    pet.field = "Nature Spirits"
    pet.x_antibody = "Permanent"
    persistence.snapshot_prev_gen(pet)
    prog = persistence.get_progress()
    assert prog["last_field"] == "Nature Spirits"
    assert prog["last_attr"] == "Vaccine"
    assert prog["last_mood"] == 50
    assert prog["last_obed"] == 7
    assert prog["last_xanti"] is True


def test_snapshot_ignores_egg():
    egg = Pet(num=-1, stage="Egg")
    persistence.snapshot_prev_gen(egg)
    # no last_gen written -> defaults
    assert persistence.get_progress()["last_field"] == "None"


def test_dna_bank_rides_the_estate():
    """DNA polish 2026-07-17: the BANKED DNA (bits + mash paid for it) is
    device-lifetime like the bag; the CHARGED distribution dies with the pet."""
    from tuipet import data
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    p.bits = 777
    p.dna_owned["NatureSpirit"] = 42
    p.dna_applied["NatureSpirit"] = 9
    persistence.snapshot_prev_gen(p)
    heir = Pet.new_egg(generation=2, egg_type=0)
    assert heir.bits == 777
    assert heir.dna_owned["NatureSpirit"] == 42          # the bank carries
    assert all(heir.dna_owned.get(f, 0) == 0
               for f in data.DNA_FIELDS if f != "NatureSpirit")
    assert all(v == 0 for v in heir.dna_applied.values())  # biology resets


def test_the_persistence_split_holds_its_boundaries():
    """Tier-4 split (2026-07-17): persistio owns the IO + the mutable
    save_failed flag (delegated via __getattr__); eggmigrate owns the bank
    tables; persistence keeps progress/estate and re-exports the old names."""
    import inspect
    from tuipet import eggmigrate, persistio
    src = inspect.getsource(persistence)
    for name in ("_atomic_write_json", "_pick_save_dir", "_migrate_egg_index",
                 "acquire_instance_lock"):
        assert f"def {name}" not in src, f"{name} crept back"
        assert hasattr(persistence, name)
    assert persistence.EGG_ORDER_V == eggmigrate.EGG_ORDER_V == 5
    # the mutable flag delegates live (a static re-export would freeze it)
    old = persistio.save_failed
    try:
        persistio.save_failed = "disk on fire"
        assert persistence.save_failed == "disk on fire"
    finally:
        persistio.save_failed = old


def test_a_poisoned_egg_type_heals_at_load():
    """The 'guide' incident, act two (2026-07-18): the crash handler SAVED
    the poisoned pet, so every launch died in the egg renderer.  A non-int
    egg_type must heal to a valid index at load, and the renderer itself
    must survive whatever reaches it."""
    from tuipet import egg
    p = Pet(num=-1, stage="Egg", attribute="None", egg_type=3)
    p.world_seconds = 100.0
    d = persistence.to_save_dict(p)
    d["egg_type"] = "guide"                       # the poisoned save
    healed, _msg = persistence.pet_from_save(d)
    assert healed is not None
    assert healed.egg_type == 0                   # a Botamon egg, not a crash
    # belt AND suspenders: the renderer can never die over it again
    assert egg.frames("guide")
    assert egg.record("guide")["name"] == "Digitama"
    assert egg.hatch_name(None) != ""
