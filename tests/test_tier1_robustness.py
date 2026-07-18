"""Tier-1 professionalism pins (sweep 2026-07-14): a professional app fails
LOUDLY and SAFELY.  Corrupt saves are quarantined and announced, damaged
atlases explain themselves, crashes leave a log, second instances are caught,
and every cloud entry point honors one sync switch."""
import glob
import json
import os
import subprocess
import sys

import pytest

from tuipet import data, persistence
from tuipet.pet import Pet


# ---- corrupt-save quarantine -------------------------------------------------

def test_corrupt_save_is_quarantined_and_announced():
    open(persistence.SAVE_PATH, "w").write("{ not json")
    open(persistence.SAVE_PATH + ".bak", "w").write("also not json")
    pet, msg = persistence.load()
    assert pet is None
    assert "couldn't be read" in msg          # never plays off as a first launch
    kept = glob.glob(os.path.join(persistence.SAVE_DIR, "save.corrupt.*.json"))
    assert len(kept) == 1
    assert open(kept[0]).read() == "{ not json"   # the MAIN file is what's kept


def test_true_first_launch_stays_quiet():
    pet, msg = persistence.load()
    assert pet is None and msg == ""
    assert not glob.glob(os.path.join(persistence.SAVE_DIR, "save.corrupt.*"))


def test_bak_recovery_still_wins_over_quarantine():
    persistence.save(Pet.new_egg())
    os.replace(persistence.SAVE_PATH, persistence.SAVE_PATH + ".bak")
    open(persistence.SAVE_PATH, "w").write("torn write")
    pet, msg = persistence.load()
    assert pet is not None                     # the backup save carried it
    assert "recovered from the backup save" in msg
    assert not glob.glob(os.path.join(persistence.SAVE_DIR, "save.corrupt.*"))


# ---- cloud pull keeps the local backup ----------------------------------------

def test_write_save_dict_rotates_a_bak():
    p = Pet.new_egg()
    persistence.save(p)
    local = json.load(open(persistence.SAVE_PATH))
    persistence.write_save_dict(dict(local, name="CloudPet"))
    assert os.path.exists(persistence.SAVE_PATH + ".bak")
    assert json.load(open(persistence.SAVE_PATH + ".bak")) == local


# ---- damaged atlases fail in plain words ---------------------------------------

def test_missing_atlas_raises_players_words(tmp_path, monkeypatch):
    # the loaders read their OWN module's _DATA since the tier-1 split
    from tuipet import data_core
    monkeypatch.setattr(data_core, "_DATA", str(tmp_path))
    data.load_sprites.cache_clear()
    try:
        with pytest.raises(data.AssetsError) as e:
            data.load_sprites()
        assert "pip install --force-reinstall tuipet" in str(e.value)
        assert "setup_assets.sh" in str(e.value)
    finally:
        data.load_sprites.cache_clear()       # never leave the poisoned dir cached


def test_truncated_atlas_raises_players_words(tmp_path, monkeypatch):
    (tmp_path / "orbs.json.gz").write_bytes(b"\x1f\x8b\x08\x00trunc")
    # atlases route through data_core._load_bundled, which reads CORE's _DATA
    from tuipet import data_core
    monkeypatch.setattr(data_core, "_DATA", str(tmp_path))
    data.load_orbs.cache_clear()
    try:
        with pytest.raises(data.AssetsError):
            data.load_orbs()
    finally:
        data.load_orbs.cache_clear()


# ---- crash log ------------------------------------------------------------------

def test_write_crash_log_keeps_the_traceback():
    try:
        raise ValueError("boom at tick 42")
    except ValueError as e:
        p = persistence.write_crash_log(e)
    assert p and os.path.exists(p)
    body = open(p).read()
    assert "boom at tick 42" in body and "Traceback" in body


# ---- single-instance lock --------------------------------------------------------

def test_lock_acquire_release_cycle():
    assert persistence.acquire_instance_lock() is None
    lock = os.path.join(persistence.SAVE_DIR, persistence._LOCK_NAME)
    assert open(lock).read() == str(os.getpid())
    persistence.release_instance_lock()
    assert not os.path.exists(lock)


def test_lock_blocks_on_a_live_pid():
    lock = os.path.join(persistence.SAVE_DIR, persistence._LOCK_NAME)
    other = os.getppid()                       # a pid that is definitely alive
    open(lock, "w").write(str(other))
    assert persistence.acquire_instance_lock() == other
    assert open(lock).read() == str(other)     # never stomps a live claim


def test_lock_reclaims_a_dead_pid():
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait()                                # a real pid, now certainly dead
    lock = os.path.join(persistence.SAVE_DIR, persistence._LOCK_NAME)
    open(lock, "w").write(str(proc.pid))
    assert persistence.acquire_instance_lock() is None
    assert open(lock).read() == str(os.getpid())


def test_release_never_drops_someone_elses_lock():
    lock = os.path.join(persistence.SAVE_DIR, persistence._LOCK_NAME)
    open(lock, "w").write(str(os.getppid()))
    persistence.release_instance_lock()
    assert os.path.exists(lock)


# ---- one sync switch for every entry point ----------------------------------------

# (sync_enabled left with the cloud-sync cut 2026-07-18)

