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
    # the growth clock runs with the age clock (H5, audit 2026-07-19 --
    # supersedes the 2026-07-06 living-stage freeze): frozen, a near-elder
    # returned to an old-age death with zero stage progress.  Evolution
    # still fires only on a live tick.
    assert pet.stage_seconds == 2 * 3600


def test_offline_rates_match_the_live_sim():
    """H5 (gameplay audit 2026-07-19): the flat mins//5 hunger and mins//8
    poop ran ~6x harsher than playing -- quitting was strictly worse than
    idling.  Offline moves at the pet's OWN live cadences now: ~1800s per
    hunger heart, ~2700s per pile (modal species)."""
    pet = Pet(num=-1, stage="Rookie")
    pet.hunger, pet.poop = 4, 0
    persistence._offline(pet, 2 * 3600)          # 2h away
    # live: 7200s / ~1800s = 4 hearts... clamped by what it had; the OLD
    # code took all 4 within 20 minutes.  Allow the per-species scale.
    assert pet.hunger == 0
    assert 1 <= pet.poop <= 3, "2h should land ~2 piles at the live cadence, not 4"
    pet2 = Pet(num=-1, stage="Rookie")
    pet2.hunger, pet2.poop = 4, 0
    persistence._offline(pet2, 1800)             # 30 min away
    assert pet2.hunger >= 3, "30 min is ~one live heart, the old code took 6"
    assert pet2.poop == 0, "30 min is under one live pile interval"


def test_offline_honors_the_live_gates():
    """H5's gate half: the Steak's satiety and the Port. Potty must hold
    while away (they were void exactly when bought), and a sleeping pet
    must not be starved into a care mistake -- live sleep can't produce
    that state."""
    pet = Pet(num=-1, stage="Rookie")
    pet.hunger = 4
    pet.full_until = pet.world_seconds + 12 * 3600      # the Steak's 12h
    persistence._offline(pet, 6 * 3600)
    assert pet.hunger == 4, "satiety must hold offline"
    pet2 = Pet(num=-1, stage="Rookie")
    pet2.poop, pet2.poop_sizes = 2, [2, 2]
    pet2.auto_clean_until = pet2.world_seconds + 24 * 3600
    persistence._offline(pet2, 6 * 3600)
    assert pet2.poop == 0, "the Port. Potty flushes while it holds"
    pet3 = Pet(num=-1, stage="Rookie")
    pet3.hunger, pet3.asleep, pet3.lights = 4, True, False
    pet3.awake_lapse, pet3.awake_limit = 0.0, 600.0     # a full night owed
    m0 = pet3.care_mistakes
    persistence._offline(pet3, 600)                     # away for the night
    assert pet3.hunger >= 3, "a sleeping stomach floors, never starves"
    assert pet3.care_mistakes == m0


def test_offline_sleep_earns_energy_and_dp():
    """H5's third half: a full night away used to restore NOTHING -- no
    energy, no DP.  Sleep earns at the live crossing rates now, and the
    morning wakes the pet."""
    pet = Pet(num=-1, stage="Rookie")
    pet.asleep, pet.nap, pet.lights = True, False, False
    pet.energy, pet.dp = 0, 0
    pet.awake_lapse, pet.awake_limit = 0.0, 600.0       # a 10-game-hour night
    persistence._offline(pet, 3600)                     # away well past it
    assert pet.energy > 0, "sleep must earn energy offline"
    assert pet.dp > 0, "sleep must refill DP offline"
    assert not pet.asleep, "the morning came while away"


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
    healed, _msg = persistence.pet_from_save(d, catch_up=False)
    assert healed is not None
    assert healed.egg_type == 0                   # a Botamon egg, not a crash
    # belt AND suspenders: the renderer can never die over it again
    assert egg.frames("guide")
    assert egg.record("guide")["name"] == "Digitama"
    assert egg.hatch_name(None) != ""
