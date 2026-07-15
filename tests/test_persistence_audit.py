"""Persistence/cloud-sync audit (2026-07): the failure modes that lose pets.

Found and fixed: a corrupt save.json silently started a NEW EGG and the next
autosave destroyed the old pet (now: .bak rotation + fallback, for settings
too — settings hold the album/wins/eggs/Digimemory); a save with the right
keys but wrong-typed values built a pet that crashed later in tick() (now:
critical-field sanity in pet_from_save, which also hardens the cloud probe).
Pinned: the pathological save stays far under the 64KB wire cap the server
silently drops oversized messages at."""
import json
import os

from tuipet.pet import Pet
from tuipet import persistence, cloudsync


def _pet(**kw):
    p = Pet(num=100, name="Gatomon", stage="Adult", attribute="Vaccine")

    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_corrupt_save_falls_back_to_the_backup():
    p = _pet(bits=777)
    persistence.save(p)
    persistence.save(p)                              # second save rotates the .bak
    assert os.path.exists(persistence.SAVE_PATH + ".bak")
    with open(persistence.SAVE_PATH, "w") as fh:
        fh.write('{"trunc')                          # the disk ate a write
    loaded, msg = persistence.load(catch_up=False)
    assert loaded is not None and loaded.bits == 777      # NOT a silent new egg
    assert "backup" in msg


def test_crash_between_the_two_renames_still_recovers():
    p = _pet(bits=555)
    persistence.save(p)
    persistence.save(p)
    os.remove(persistence.SAVE_PATH)                 # died after rotating, before landing
    loaded, _ = persistence.load(catch_up=False)
    assert loaded is not None and loaded.bits == 555


def test_corrupt_settings_fall_back_too():
    persistence.wins_add(42)
    persistence.wins_add(1)                          # second write rotates settings.bak
    with open(persistence.SETTINGS_PATH, "w") as fh:
        fh.write("\x00\x01 not json")
    # the .bak is one WRITE behind by design: 42, not 43 -- one stale win beats
    # losing the album/eggs/Digimemory wholesale
    assert persistence.get_wins() == 42


def test_wrong_typed_save_is_rejected_not_a_time_bomb():
    d = persistence.to_save_dict(_pet())
    d["hunger"] = "four"                             # right key, wrong type
    pet, _ = persistence.pet_from_save(json.loads(json.dumps(d)), catch_up=False)
    assert pet is None                               # rejected at load, not a tick() crash
    d2 = persistence.to_save_dict(_pet())
    d2["inventory"] = ["f:0"]                        # a list where a dict lives
    assert persistence.pet_from_save(d2, catch_up=False)[0] is None


def test_wrong_typed_cloud_save_never_clobbers_local(tmp_path, monkeypatch):
    persistence.save(_pet(bits=999))                 # a healthy local pet
    bad = persistence.to_save_dict(_pet())
    bad["energy"] = {"oops": 1}
    bad["_saved_at"] = 9e12                          # "newer" than anything local
    monkeypatch.setattr(cloudsync, "pull_save", lambda *a, **k: bad)
    assert cloudsync.sync_down_at_startup("ws://x/", "joel", "pw") == "cloud-save-invalid"
    loaded, _ = persistence.load(catch_up=False)
    assert loaded is not None and loaded.bits == 999      # local untouched


def test_pathological_save_stays_far_under_the_wire_cap():
    """server.py silently SKIPS messages over 64KB (MAX_MSG_BYTES) -- an oversized
    save would sync-fail forever with push_save still returning True.  Pin the
    worst realistic save at <32KB (2x headroom)."""
    p = _pet(stage="Ultimate-Super Ultimate")
    p.inventory = {f"f:{i}": 99 for i in range(60)} | {f"i:{i}": 99 for i in range(100)}
    p.levels_fought = [5] * 2000                     # a pathological one-stage grind
    p.trophies_won = {i: "Spring" for i in range(40)}
    p.habitat_record = {i: 9999.0 for i in range(8)}
    p.tourney_schedule = list(range(24))
    p.fought_today = list(range(40))
    p.digimemory = {"name": "X" * 24, "num": 1500, "vaccine": 999, "data": 999,
                    "virus": 999, "seconds": 99999.0}
    size = len(json.dumps(persistence.to_save_dict(p)))
    assert size < 32 * 1024, f"save grew to {size}b — approaching the 64KB drop cap"


def test_backup_never_blocks_a_legit_fresh_start():
    persistence.delete()
    try:
        os.remove(persistence.SAVE_PATH + ".bak")
    except OSError:
        pass
    assert persistence.load()[0] is None             # truly nothing -> a new game


def test_normal_load_message_is_unchanged():
    persistence.save(_pet(bits=5))
    loaded, msg = persistence.load(catch_up=False)
    assert loaded is not None and "backup" not in msg


def test_delete_takes_the_backup_with_it():
    persistence.save(_pet(bits=1))
    persistence.save(_pet(bits=2))                   # .bak now exists
    persistence.delete()
    assert persistence.load()[0] is None             # the deleted pet stays deleted
