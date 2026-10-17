"""Local-only reproductions for sync audit 2026-10-14."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tuipet import cloudsync, net, persistence


class Socket:
    def __init__(self, frames):
        self.frames = frames
        self.sent = []

    async def send(self, raw):
        self.sent.append(json.loads(raw))

    async def close(self):
        pass

    def __aiter__(self):
        async def frames():
            for frame in self.frames:
                if callable(frame):
                    frame()
                else:
                    yield json.dumps(frame)
        return frames()


@pytest.fixture
def relay(tmp_path, monkeypatch):
    import server
    async def inline(fn, *args):
        return fn(*args)
    monkeypatch.setattr(server.asyncio, "to_thread", inline)
    for attr in ("ACCOUNTS", "SAVES", "HOLDERS", "LEASES", "BOOT_SEEN", "CLIENTS", "WIPED", "_RATE_BUCKETS"):
        monkeypatch.setattr(server, attr, {})   # rate buckets too: limits must not leak between tests
    for attr in ("ACCOUNTS_PATH", "SAVES_PATH", "HOLDERS_PATH", "WIPED_PATH"):
        monkeypatch.setattr(server, attr, str(tmp_path / (attr + ".json")))
    monkeypatch.setattr(server, "_make_account", lambda name, pw: {"name": name})
    monkeypatch.setattr(server, "_verify", lambda pw, acc: True)
    return server


def login(device="phone", boot=10):
    return {"t": "login", "name": "owner", "pw": "pw", "sync_only": True,
            "device": device, "boot": boot}


def test_spectator_does_not_revoke_holder_lease(relay):
    holder = SimpleNamespace(lease=None)
    relay.HOLDERS["owner"] = {"device": "phone", "label": "phone"}
    relay._take_lease(holder, "owner", 10)
    asyncio.run(relay.handler(Socket([login("pc", 20)])))
    assert relay._lease_ok(holder, "owner")


def test_explicit_take_gives_old_launch_a_working_lease(relay):
    old = SimpleNamespace(lease=None)
    relay._take_lease(old, "owner", 10)
    relay._take_lease(SimpleNamespace(lease=None), "owner", 20)
    relay.HOLDERS["owner"] = {"device": "pc", "label": "PC"}
    sock = Socket([login("phone", 10), {"t": "take"},
                   {"t": "save", "save": {"stage": "Egg"}}])
    asyncio.run(relay.handler(sock))
    assert next(m for m in sock.sent if m["t"] == "saved")["ok"]


def test_wipe_revokes_connected_uploaders(relay):
    client = SimpleNamespace(lease=None)
    relay._take_lease(client, "owner", 10)
    relay.SAVES["owner"] = {"stage": "Egg"}
    relay.HOLDERS["owner"] = {"device": "phone", "label": "phone"}
    asyncio.run(relay._wipe_account("owner"))
    assert not relay._lease_ok(client, "owner")


@pytest.mark.parametrize("name", [12, [], {"bad": "name"}])
def test_bad_remote_save_name_is_rejected_without_crashing(relay, name):
    assert relay._valid_save({"stage": "Rookie", "name": name}) is False


@pytest.mark.parametrize("bad", [[1], {"progress": [1]}, {"account": [1]}])
def test_settings_bad_shape_recovers_backup(bad):
    Path(persistence.SETTINGS_PATH).write_text(json.dumps(bad), encoding="utf-8")
    Path(persistence.SETTINGS_PATH + ".bak").write_text(
        json.dumps({"account": {"name": "owner", "pw": "pw"}}), encoding="utf-8")
    assert persistence.get_account() == ("owner", "pw")


def test_local_timestamp_handles_json_array():
    Path(persistence.SAVE_PATH).write_text("[]", encoding="utf-8")
    assert persistence.local_saved_at() == 0


def test_junk_progress_does_not_destroy_valid_history():
    persistence.save_settings({"progress": {"album": [1], "wins": 5}})
    persistence.merge_progress({"album": [{"bad": 1}], "wins": 8})
    assert persistence.load_settings()["progress"]["album"] == [1]
    assert persistence.get_wins() == 8


def test_erase_removes_rescue_and_interrupted_writes():
    for name in ("save.rescue.20261014-010101.json", "save.json.tmp", "settings.json.tmp"):
        Path(persistence.SAVE_DIR, name).write_text("secret", encoding="utf-8")
    persistence.erase_all()
    assert not list(Path(persistence.SAVE_DIR).iterdir())


def test_blocking_push_bad_stamp_is_fail_soft(monkeypatch):
    monkeypatch.setattr(cloudsync, "probe", lambda *a: ("ok", {"_saved_at": "bad"}))
    monkeypatch.setattr(cloudsync, "_connect", lambda *a: pytest.fail("must not upload"))
    assert cloudsync.push_save("ws://127.0.0.1:9", "owner", "pw", {"_saved_at": 1}) is False


def test_background_welcome_reports_foreign_holder(monkeypatch):
    monkeypatch.setattr(persistence, "device_id", lambda: "phone")
    client = net.SyncClient("ws://127.0.0.1:9", "owner")
    client._handle(json.dumps({"t": "welcome", "holder": {"device": "pc", "label": "PC"}}))
    assert client.not_holder == {"device": "pc", "label": "PC"}


@pytest.fixture
def app_stub(monkeypatch):
    from tuipet import app
    from tuipet.pet import Pet
    async def inline(fn, *args):
        return fn(*args)
    monkeypatch.setattr(app, "_to_thread", inline)
    stub = SimpleNamespace(pet=Pet.new_egg(), mode=None, _new_game=True,
                           _verdict=lambda *a: None, beep=lambda *a, **kw: None,
                           _start_sync=lambda: None, _stop_sync=lambda: None,
                           repaint=lambda: None, _open_mode=lambda *a: None, _after_egg_pick=lambda *a: None,
                           _open_first_signin=lambda *a: None)
    return app, stub


def test_same_account_case_change_keeps_local_pet(app_stub, monkeypatch):
    app, stub = app_stub
    persistence.set_account("Owner", "pw")
    stub.pet.bits = 4321
    monkeypatch.setattr(cloudsync, "probe", lambda *a: ("ok", None))
    monkeypatch.setattr(cloudsync, "push_save", lambda *a: True)
    asyncio.run(app.TuiPetApp._switch_account(stub, "owner", "pw"))
    assert stub.pet.bits == 4321


def test_same_account_signin_repairs_cached_credentials(app_stub, monkeypatch):
    app, stub = app_stub
    persistence.set_account("owner", "wrong")
    monkeypatch.setattr(cloudsync, "probe", lambda *a: ("ok", None))
    asyncio.run(app.TuiPetApp._switch_account(stub, "owner", "correct"))
    assert persistence.get_account() == ("owner", "correct")


def test_empty_account_switch_resets_old_holder_cache(app_stub, monkeypatch):
    app, stub = app_stub
    persistence.set_account("old", "pw")
    persistence.set_holder_cache(False)
    monkeypatch.setattr(cloudsync, "probe", lambda *a: ("ok", None))
    monkeypatch.setattr(cloudsync, "push_save", lambda *a: True)
    asyncio.run(app.TuiPetApp._switch_account(stub, "new", "pw"))
    assert persistence.holder_cache() is True


def test_first_signin_empty_foreign_cartridge_takes_ownership(app_stub, monkeypatch):
    app, stub = app_stub
    monkeypatch.setattr(cloudsync, "gate", lambda *a: ("ok", None, {"device": "pc"}))
    calls = []
    monkeypatch.setattr(cloudsync, "take", lambda *a: (calls.append(a) or True, None))
    asyncio.run(app.TuiPetApp._first_signin(stub, "owner", "pw"))
    assert calls, "empty cloud can still have a holder after pruning"


def test_first_signin_rejects_changed_take_payload(app_stub, monkeypatch):
    app, stub = app_stub
    valid = persistence.to_save_dict(stub.pet)
    monkeypatch.setattr(cloudsync, "gate", lambda *a: ("ok", valid, None))
    monkeypatch.setattr(cloudsync, "take", lambda *a: (True, {"stage": "Child"}))
    asyncio.run(app.TuiPetApp._first_signin(stub, "owner", "pw"))
    assert persistence.get_account()[0] is None
    assert not persistence.exists()


def test_warm_data_pins_lazy_attack_table(monkeypatch):
    from tuipet import appboot, data_world
    monkeypatch.setattr(data_world, "_ATTACKS", None)
    appboot.warm_data()
    assert data_world._ATTACKS is not None


def test_muted_peer_cannot_bypass_block_through_home_sync():
    persistence.set_blocked(["muted"])
    client = net.SyncClient("ws://127.0.0.1:9", "owner")
    client._handle(json.dumps({"t": "pm", "from_name": "muted", "text": "spam"}))
    client._handle(json.dumps({"t": "announce", "text": "notice"}))
    assert client.inbox == [(net.ANNOUNCE, "notice")]


@pytest.mark.parametrize("take_result", [(False, None), (True, {"stage": "Child"})])
def test_boot_failed_or_invalid_take_cannot_keep_holder_cache(monkeypatch, take_result):
    from tuipet import app
    persistence.set_account("owner", "pw")
    persistence.set_holder_cache(True)
    monkeypatch.setattr(app, "_preflight", lambda: None)
    monkeypatch.setattr(app, "warm_data", lambda: None)
    monkeypatch.setattr(persistence, "acquire_instance_lock", lambda: None)
    monkeypatch.setattr(persistence, "release_instance_lock", lambda: None)
    monkeypatch.setattr(cloudsync, "gate", lambda *a, **kw: ("ok", None, {"device": "pc"}))
    monkeypatch.setattr(cloudsync, "take", lambda *a: take_result)
    monkeypatch.setattr("builtins.input", lambda *a: "yes")
    monkeypatch.setattr(app, "TuiPetApp", lambda: SimpleNamespace(run=lambda: None))
    app.main()
    assert persistence.holder_cache() is False


def test_concurrent_registration_cannot_replace_first_password(relay, monkeypatch):
    async def hashing(fn, *args):
        await asyncio.sleep(0)
        return fn(*args)
    monkeypatch.setattr(relay.asyncio, "to_thread", hashing)
    monkeypatch.setattr(relay, "_make_account", lambda name, pw: {"name": name, "pw": pw})
    monkeypatch.setattr(relay, "_verify", lambda pw, acc: pw == acc["pw"])
    a, b = login(), login("pc", 20)
    a["pw"], b["pw"] = "first", "second"
    sa, sb = Socket([a]), Socket([b])
    async def go():
        await asyncio.gather(relay.handler(sa), relay.handler(sb))
    asyncio.run(go())
    assert relay.ACCOUNTS["owner"]["pw"] == "first"
    assert any(m["t"] == "login_failed" for m in sb.sent)


def test_an_erased_device_cannot_reconnect_and_reupload(relay):
    """Saves call #27 = A (Joel 2026-10-15): this was the decision evidence --
    the erased pet came back from a device still signed in.  Now refused."""
    import time
    first = Socket([login(), {"t": "save", "save": {"stage": "Egg", "bits": 4321}}])
    asyncio.run(relay.handler(first))
    asyncio.run(relay._wipe_account("owner"))
    zombie = Socket([login(), {"t": "save", "save": {"stage": "Egg", "bits": 4321}}])
    asyncio.run(relay.handler(zombie))
    assert "owner" not in relay.SAVES
    fresh = Socket([login(), {"t": "save", "save": {"stage": "Egg", "bits": 1,
                                                    "born_at": time.time()}}])
    asyncio.run(relay.handler(fresh))
    assert relay.SAVES["owner"]["bits"] == 1


def test_design_repro_reconnect_queue_keeps_old_peer_id():
    client = net.LobbyClient("ws://127.0.0.1:9", "owner")
    client.invite(42, "battle")
    client._on_disconnect()
    client._on_retry_wait()
    assert client._q.get_nowait() == {"t": "invite", "to": "42", "kind": "battle"}  # ids are strings (2026-10-17)
