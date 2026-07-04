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
    pet, msg = persistence.pet_from_save(_foreign_save(), catch_up=False)
    assert pet is not None
    assert "repaired" in msg
    # identity re-derived from the dex; the line re-bound by name (dex 1 =
    # YukimiBotamon = the verE root's name -> the pet lands ON the line)
    assert pet.name == "YukimiBotamon" and pet.stage == "Fresh"
    assert (pet.num, pet.line_id) == (1410, "verE") and lines.active(pet)
    assert pet.bits == 777                    # progress survives the repair
    assert pet.age_seconds > 2000


def test_cloud_probe_rejects_a_foreign_save():
    pet, _ = persistence.pet_from_save(_foreign_save(), catch_up=False, strict=True)
    assert pet is None                        # sync_down_at_startup keeps the local pet


def test_unknown_dex_survives_locally_but_never_syncs_in():
    # local: the data-refresh robustness contract (test_load_unknown_num) holds
    pet, _ = persistence.pet_from_save(_foreign_save(num=999999), catch_up=False)
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
        q, msg = persistence.pet_from_save(d, catch_up=False, strict=strict)
        assert q is not None and "repaired" not in (msg or "")
        assert (q.num, q.name, q.line_id, q.bits) == (p.num, p.name, p.line_id, 42)


def test_egg_saves_are_exempt():
    d = persistence.to_save_dict(Pet.new_egg(egg_type=1))
    q, msg = persistence.pet_from_save(d, catch_up=False, strict=True)
    assert q is not None and q.stage == "Egg"


def test_server_refuses_foreign_saves(tmp_path, monkeypatch):
    """The lobby server itself must not carry old-format saves -- the cloud was
    the ghost's delivery vehicle in the 'Child' incident."""
    import sys
    sys.path.insert(0, "server")
    import importlib
    import server as srv
    importlib.reload(srv)
    assert not srv._valid_save({"stage": "Child", "name": "", "_saved_at": 1})
    assert not srv._valid_save({"stage": "Rookie", "name": "", "_saved_at": 1})
    assert not srv._valid_save("junk")
    assert srv._valid_save({"stage": "Rookie", "name": "Agumon", "_saved_at": 1})
    assert srv._valid_save({"stage": "Egg", "name": "", "_saved_at": 1})
