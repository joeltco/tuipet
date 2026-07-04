"""Cross-device cloud save: the persistence payload helpers, plus a real
round-trip through a live server subprocess (push on one 'device', pull on
another, last-write-wins, wrong-password rejection, offline = silent).
"""
import json
import os
import socket
import subprocess
import sys
import time

import pytest

from tuipet import persistence, cloudsync
from tuipet.pet import Pet


# ---- payload helpers (no network) ------------------------------------------

def test_save_dict_roundtrips_through_pet():
    pet = Pet(num=-1, stage="Rookie", vaccine=12, data_power=3, virus=4)
    data = persistence.to_save_dict(pet)
    assert "_saved_at" in data and data["_saved_at"] > 0
    back, _ = persistence.pet_from_save(data, catch_up=False)
    assert back is not None
    assert (back.stage, back.vaccine, back.data_power, back.virus) == ("Rookie", 12, 3, 4)


def test_pet_from_save_rejects_garbage():
    assert persistence.pet_from_save(None)[0] is None
    assert persistence.pet_from_save({"not": "a pet"})[0] is None       # missing required fields tolerated


def test_write_and_read_local_saved_at(tmp_path):
    p = str(tmp_path / "s.json")
    assert persistence.local_saved_at(p) == 0.0                          # no file
    persistence.write_save_dict({"stage": "Egg", "_saved_at": 1234.5}, p)
    assert persistence.local_saved_at(p) == 1234.5


# ---- live server round-trip ------------------------------------------------

def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def server(tmp_path):
    """A real server.py subprocess on a free port with temp accounts/saves."""
    port = _free_port()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {**os.environ,
           "TUIPET_PORT": str(port),
           "TUIPET_HOST": "127.0.0.1",
           "TUIPET_ACCOUNTS": str(tmp_path / "accounts.json"),
           "TUIPET_SAVES": str(tmp_path / "saves.json")}
    proc = subprocess.Popen([sys.executable, os.path.join(root, "server", "server.py")],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    uri = f"ws://127.0.0.1:{port}/"
    # wait until the port accepts connections
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        proc.kill()
        pytest.skip("server did not start")
    yield uri
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_push_then_pull_across_devices(server):
    a = {"num": 42, "name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0}
    assert cloudsync.push_save(server, "joel", "secret", a) is True       # device A claims + pushes
    got = cloudsync.pull_save(server, "joel", "secret")                   # device B pulls
    assert got["name"] == "Agumon" and got["_saved_at"] == 1000.0


def test_last_write_wins(server):
    cloudsync.push_save(server, "joel", "secret", {"name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0})
    cloudsync.push_save(server, "joel", "secret", {"name": "OLD", "stage": "Rookie", "_saved_at": 500.0})
    assert cloudsync.pull_save(server, "joel", "secret")["name"] == "Agumon"   # stale rejected
    cloudsync.push_save(server, "joel", "secret", {"name": "Greymon", "stage": "Champion", "_saved_at": 2000.0})
    assert cloudsync.pull_save(server, "joel", "secret")["name"] == "Greymon"  # newer wins


def test_wrong_password_is_blocked(server):
    cloudsync.push_save(server, "joel", "secret", {"name": "Agumon", "stage": "Rookie", "_saved_at": 1000.0})
    assert cloudsync.pull_save(server, "joel", "WRONG") is None


def test_startup_pull_mirrors_cloud_to_local(server, tmp_path, monkeypatch):
    # isolate_save (autouse) already sandboxes SAVE_PATH; push a cloud save, then
    # a fresh device's startup pull should write it locally.
    # the pushed blob must be a REAL save: the pull now validates it can become
    # a pet before overwriting local (a malformed cloud payload used to mean a
    # silent fresh-egg wipe)
    cloud_pet = Pet.from_num(100)      # a REAL record: the strict probe now rejects
    #                                    hand-built pets whose name/stage lie about their dex
    blob = persistence.to_save_dict(cloud_pet)
    blob["_saved_at"] = 9000.0
    cloudsync.push_save(server, "joel", "secret", blob)
    assert not os.path.exists(persistence.SAVE_PATH)
    assert cloudsync.sync_down_at_startup(server, "joel", "secret") == "pulled"
    assert json.load(open(persistence.SAVE_PATH))["name"] == "Gatomon"   # dex 100's real name
    # a second pull is a no-op (local is now as new as the cloud)
    assert cloudsync.sync_down_at_startup(server, "joel", "secret") == ""


def test_offline_is_silent():
    # nothing listening -> never raises, returns falsy
    assert cloudsync.pull_save("ws://127.0.0.1:1/", "joel", "secret", timeout=0.5) is None
    assert cloudsync.push_save("ws://127.0.0.1:1/", "joel", "secret", {"_saved_at": 1}, timeout=0.5) is False
    assert cloudsync.sync_down_at_startup("ws://127.0.0.1:1/", "joel", "secret", timeout=0.5) == ""
