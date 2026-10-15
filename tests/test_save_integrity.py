"""Foreign-save integrity (the 2026-07-04 'Child' incident): an outdated
client pushed a rebuild-era save (stage 'Child', empty name, alien dex space)
through the cloud probe; the local pet became a blank-named ghost that could
never evolve.  The cloud boundary now REJECTS foreign formats; the local load
REPAIRS them into a playable line pet instead of wiping to a fresh egg."""
from tuipet import lines, persistence
from tuipet.pet import Pet


def _foreign_save(**kw):
    """The literal shape found in Joel's save.json on 2026-07-04."""
    d = persistence.to_save_dict(Pet.from_num(1))
    d.update({"name": "", "stage": "Child", "line_id": None,
              "age_seconds": 2463.7, "stage_seconds": 0.0, "bits": 777})
    d.update(kw)
    return d


def test_local_load_repairs_a_foreign_save():
    pet, msg = persistence.pet_from_save(_foreign_save())
    assert pet is not None
    assert "repaired" in msg
    # identity re-derived from the dex; the line re-bound by name (dex 1 =
    # YukimiBotamon = the verE root's name -> the pet lands ON the line)
    assert pet.name == "YukimiBotamon" and pet.stage == "Fresh"
    assert (pet.num, pet.line_id) == (1410, "verE") and lines.active(pet)
    assert pet.bits == 777                    # progress survives the repair
    assert pet.age_seconds > 2000


def test_cloud_probe_rejects_a_foreign_save():
    pet, _ = persistence.pet_from_save(_foreign_save(), strict=True)
    assert pet is None                        # sync_down_at_startup keeps the local pet


def test_unknown_dex_survives_locally_but_never_syncs_in():
    # local: the data-refresh robustness contract (test_load_unknown_num) holds
    pet, _ = persistence.pet_from_save(_foreign_save(num=999999))
    assert pet is not None and pet.num == 999999
    # cloud: the strict probe refuses what this build cannot verify
    pet, _ = persistence.pet_from_save(_foreign_save(num=999999), strict=True)
    assert pet is None


def test_healthy_saves_pass_untouched():
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    p.bits = 42
    d = persistence.to_save_dict(p)
    for strict in (False, True):
        q, msg = persistence.pet_from_save(d, strict=strict)
        assert q is not None and "repaired" not in (msg or "")
        assert (q.num, q.name, q.line_id, q.bits) == (p.num, p.name, p.line_id, 42)


def test_egg_saves_are_exempt():
    d = persistence.to_save_dict(Pet.new_egg(egg_type=1))
    q, msg = persistence.pet_from_save(d, strict=True)
    assert q is not None and q.stage == "Egg"


def test_server_refuses_foreign_saves(tmp_path, monkeypatch):
    """The lobby server itself must not carry old-format saves -- the cloud was
    the ghost's delivery vehicle in the 'Child' incident."""
    import os
    import sys
    # no reload: re-executing server.py resets FEED_PATH/BUGS_PATH to the real
    # repo files, silently undoing conftest's sandbox (the 2026-07-10 leak)
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server as srv
    assert not srv._valid_save({"stage": "Child", "name": "", "_saved_at": 1})
    assert not srv._valid_save({"stage": "Rookie", "name": "", "_saved_at": 1})
    assert not srv._valid_save("junk")
    assert srv._valid_save({"stage": "Rookie", "name": "Agumon", "_saved_at": 1})
    assert srv._valid_save({"stage": "Egg", "name": "", "_saved_at": 1})


def test_session_lease_stops_the_two_device_fork():
    """2026-07-04 (Joel: 'things arent getting saved between quits'): a phone
    left running kept autosave-pushing its own FORK with newer wall clocks, so
    every fresh desktop session lost its play to the background device.  Only
    the LATEST login's connection may push saves."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
    import server as srv
    srv.LEASES.pop("joeltco", None)      # fresh lease slate (reload used to do this)

    class _C:                                     # a connection, duck-typed
        lease = None
    phone, desktop = _C(), _C()
    srv._take_lease(phone, "joeltco", 100.0)      # phone launches first...
    assert srv._lease_ok(phone, "joeltco")        # ...and may push
    srv._take_lease(desktop, "joeltco", 200.0)    # the desktop opens the game LATER
    assert srv._lease_ok(desktop, "joeltco")      # the newer launch owns saves
    assert not srv._lease_ok(phone, "joeltco")    # the background fork is staled
    phone2 = _C()
    srv._take_lease(phone2, "joeltco", 100.0)     # phone RECONNECTS (same launch):
    assert not srv._lease_ok(phone2, "joeltco")   # a wifi blip must not steal it back
    assert srv._lease_ok(desktop, "joeltco")
    srv._take_lease(phone2, "joeltco", 300.0)     # the player relaunches ON the phone
    assert srv._lease_ok(phone2, "joeltco") and not srv._lease_ok(desktop, "joeltco")
    legacy = _C()
    srv._take_lease(legacy, "joeltco", 0.0)       # an un-upgraded client (no stamp):
    assert srv._lease_ok(legacy, "joeltco")       # keeps last-login-wins until updated
    srv._take_lease(desktop, "joeltco", 200.0)    # ...and any stamped login takes over
    assert srv._lease_ok(desktop, "joeltco")


def test_earned_history_is_kept_per_account(tmp_path, monkeypatch):
    """Saves call #28 = A (Joel 2026-10-15): a second account signed in on
    this device no longer inherits the first one's album and unlocks."""
    from tuipet import persistence
    persistence.save_settings({"progress": {"album": [29], "wins": 7}})
    persistence.set_account("joel", "pw")             # the pre-split history is joel's
    assert persistence.get_album() == {29}
    persistence.set_account("layla", "pw")
    assert persistence.get_album() == set()           # her own, empty book
    persistence.album_add(100)
    persistence.set_account("joel", "pw")
    assert persistence.get_album() == {29}            # his book untouched
    persistence.set_account("layla", "pw")
    assert persistence.get_album() == {100}


def test_an_elder_remembers_its_own_cups_not_the_lineage_total():
    """Eggs call #31 = A (Joel 2026-10-15)."""
    from tuipet import persistence
    from tuipet.hallscreen import HallPanel
    from tuipet.pet import Pet
    gen1 = Pet(num=29, stage="Rookie", attribute="Vaccine")
    gen1.trophies = 3
    persistence.snapshot_prev_gen(gen1)
    gen2 = Pet.new_egg(generation=2, egg_type=0)
    assert gen2.trophies == 3 and gen2.trophies_at_birth == 3
    gen2.stage, gen2.num = "Rookie", 29
    gen2.trophies = 5                                     # won two of its own
    persistence.snapshot_prev_gen(gen2)
    legacy = persistence.load_settings()["progress"]["legacy"]
    assert [r["cups_life"] for r in legacy] == [3, 2]
    assert [r["cups"] for r in legacy] == [3, 5]
    pan = HallPanel.__new__(HallPanel)
    assert "2 cups" in pan._epitaph(legacy[-1]) and "total" not in pan._epitaph(legacy[-1])
    old = {k: v for k, v in legacy[-1].items() if k != "cups_life"}   # a pre-split headstone
    assert "5 cups total" in pan._epitaph(old)
