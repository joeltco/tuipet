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


# ---- purchase / inventory bounds -------------------------------------------

def test_buy_with_zero_bits():
    from tuipet import shop
    p = Pet(num=-1, stage="Child", bits=0)
    e = shop.catalog()[0]
    msg, sfx = shop.buy(p, e)
    assert "Need" in msg and sfx == "error"
    assert p.bits == 0 and e["key"] not in p.inventory


def test_sell_empty_bag():
    from tuipet import shop
    p = Pet(num=-1, stage="Child")
    msg, sfx = shop.sell(p, {"key": "normal_fruit", "name": "Fruit", "price": 100})
    assert sfx == "error"


def test_use_missing_item():
    assert Pet(num=-1, stage="Child").use_item("i:99999") is None


# ---- dead-pet interactions are inert and safe ------------------------------

def test_dead_pet_actions_safe():
    p = Pet(num=-1, stage="Child", dead=True)
    p.inventory["normal_fruit"] = 1
    # none of these may crash, and the pet stays dead with its bag intact
    assert p.feed_meat() is None
    assert p.train_result(True) is False
    p.tick(100)
    assert p.dead is True
    assert p.inventory.get("normal_fruit") == 1, "a dead pet keeps its bag"


# ---- save/load resilience --------------------------------------------------

def test_load_corrupt_json():
    """A corrupt save with no usable backup announces itself (professionalism
    sweep 2026-07-14) -- it used to return (None, '') and play off as a first
    launch, silently hatching a new egg over a lost pet."""
    persistence.save(Pet(num=-1, stage="Child"))
    with open(persistence.SAVE_PATH, "w") as fh:
        fh.write("{ not json")
    pet, msg = persistence.load()
    assert pet is None and "couldn't be read" in msg


def test_load_partial_save():
    with open(persistence.SAVE_PATH, "w") as fh:
        json.dump({"num": -1, "stage": "Rookie"}, fh)   # missing _saved_at + many fields
    pet, _ = persistence.load()
    assert pet is not None and pet.stage == "Rookie"


def test_load_unknown_num():
    """A save whose species num no longer exists (data refresh) still loads."""
    persistence.save(Pet(num=999999, name="Ghost", stage="Child"))
    pet, _ = persistence.load()
    assert pet is not None and pet.num == 999999


def test_unknown_num_survives_the_first_paint():
    """Loading an unknown num is only half the contract: the FIRST LCD paint
    raw-indexed the sprite dict and crashed -- a loop, since the .bak holds
    the same num (audit 2026-07-13).  Every sprite fetch wears the
    placeholder instead."""
    from tuipet import data
    rec = data.record_for(999999)
    assert rec["frames"] and rec.get("_placeholder"), "unknown nums wear the placeholder"
    fr = data.bob_frame(999999, 0)
    assert fr is not None, "bob_frame must never hand a scene a None for a positive num"
    from tuipet.arena import Screen
    ghost = Pet(num=999999, name="Ghost", stage="Child")
    scr = Screen.__new__(Screen)
    rows = scr._pose_rows(ghost, "idle", 0)       # raw-indexed before the fix
    assert rows is not None


def test_future_timestamp_no_time_travel():
    """A save dated in the future must not produce negative offline time."""
    p = Pet(num=-1, name="Fwd", stage="Child")
    persistence.save(p)
    blob = json.load(open(persistence.SAVE_PATH))
    import time
    blob["_saved_at"] = time.time() + 10_000      # future
    json.dump(blob, open(persistence.SAVE_PATH, "w"))
    pet, msg = persistence.load()
    assert pet is not None
    assert pet.total_minutes >= 0, "future save must clamp offline elapsed to 0"


# ---- offline catch-up at extremes ------------------------------------------

def test_offline_zero_elapsed():
    import time as _t
    p = Pet(num=0, stage="Child", hunger=4, wall_time=_t.time())
    assert p.catch_up() == 0
    assert p.hunger == 4                            # nothing decays at 0s


def test_offline_huge_elapsed_stays_bounded():
    import time as _t
    from tuipet.pet import REPLAY_CAP_MIN
    p = Pet(num=0, stage="Child", hunger=4, wall_time=_t.time() - 10 ** 9)
    n = p.catch_up()
    assert n <= REPLAY_CAP_MIN                      # the 3-day horizon holds
    assert 0 <= p.hunger <= 4


# ---- egg helpers tolerate out-of-range indices -----------------------------

def test_egg_helpers_out_of_range():
    assert egg.frames(10 ** 6)                       # modulo-wrapped, returns frames
    assert egg.hatch_name(10 ** 6) is not None
