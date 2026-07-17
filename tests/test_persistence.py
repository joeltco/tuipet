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
              effect_id=2, effect_t=42.0, care_mistakes=3, generation=4)
    persistence.save(pet)
    loaded, _ = persistence.load()
    assert loaded is not None
    assert loaded.name == "Testmon"
    assert loaded.stage == "Rookie"
    assert loaded.bits == 99
    assert loaded.effect_id == 2
    assert loaded.effect_t == 42.0
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
    assert loaded.effect_id == -1      # field absent in the save -> dataclass default
    assert loaded.effect_t == 0.0


def test_offline_egg_does_not_decay():
    egg = Pet(num=-1, stage="Egg")
    egg.mood, egg.hunger = 0, 4
    msg = persistence._offline(egg, 7200)        # 2h away
    assert msg == ""
    assert egg.hunger == 4 and egg.mood == 0     # eggs are inert offline
    assert egg.world_seconds == 7200             # ...but the clock still advances
    assert egg.age_seconds == 7200


def test_offline_egg_incubates():
    """Canon processSkippedSeconds replays incubation: an egg left alone while
    the game is off comes back HATCHING (age accrual without incubation was the
    incoherent half-state -- 2026-07-06)."""
    egg = Pet(num=-1, stage="Egg")
    persistence._offline(egg, 7200)              # 2h away >> EGG_DURATION
    assert egg.stage_seconds == 7200
    egg._tick_egg()                              # first tick after load
    assert egg.hatching, "the return should greet a hatch, not a frozen egg"


def test_offline_decay_applies():
    pet = Pet(num=-1, stage="Rookie")
    pet.mood, pet.hunger = 100, 4
    msg = persistence._offline(pet, 2 * 3600)    # 2h
    # (the offline mood decay left with the mood system)
    assert pet.hunger < 4, "hunger should drop while away"
    assert "away" in msg
    # don't-flip: BOUNDED decay means no growth/evolution while away -- only
    # the EGG's incubation replays (canon hatch); living stages stay frozen
    assert pet.stage_seconds == 0


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
