"""The PyPI update check must order versions correctly and fail soft — offline,
bad data, or a source install (no metadata) never raises and never nags."""
import io
import json
import pytest
from tuipet import update as u


def test_key_orders_versions_numerically():
    assert u._key("0.1.10") > u._key("0.1.2")        # 10 > 2, not string "10" < "2"
    assert u._key("0.2.0") > u._key("0.1.9")
    assert u._key("1.0.0") > u._key("0.9.9")
    assert not (u._key("0.1.0") > u._key("0.1.0"))   # equal is not newer


def _fake_resp(version):
    class _R:
        def __enter__(self): return io.BytesIO(json.dumps({"info": {"version": version}}).encode())
        def __exit__(self, *a): return False
    return lambda *a, **k: _R()


def test_newer_release_is_reported(monkeypatch):
    monkeypatch.setattr(u, "current_version", lambda: "0.1.0")
    monkeypatch.setattr(u.urllib.request, "urlopen", _fake_resp("0.2.0"))
    assert u.latest_if_newer() == "0.2.0"


def test_same_version_is_not_reported(monkeypatch):
    monkeypatch.setattr(u, "current_version", lambda: "0.2.0")
    monkeypatch.setattr(u.urllib.request, "urlopen", _fake_resp("0.2.0"))
    assert u.latest_if_newer() is None


def test_older_pypi_is_not_reported(monkeypatch):
    monkeypatch.setattr(u, "current_version", lambda: "0.3.0")
    monkeypatch.setattr(u.urllib.request, "urlopen", _fake_resp("0.2.0"))
    assert u.latest_if_newer() is None


def test_offline_is_silent(monkeypatch):
    monkeypatch.setattr(u, "current_version", lambda: "0.1.0")
    def boom(*a, **k): raise OSError("offline")
    monkeypatch.setattr(u.urllib.request, "urlopen", boom)
    assert u.latest_if_newer() is None               # never raises


def test_source_install_skips_check(monkeypatch):
    # no package metadata (running from a checkout) -> nothing to compare, no network
    monkeypatch.setattr(u, "current_version", lambda: None)
    def must_not_call(*a, **k): raise AssertionError("should not hit the network")
    monkeypatch.setattr(u.urllib.request, "urlopen", must_not_call)
    assert u.latest_if_newer() is None


# --- the app worker turns a newer release into the HUD nudge string ----------

def test_worker_sets_hud_message_when_newer(monkeypatch):
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet import app as app_mod
    monkeypatch.setattr(app_mod.update_check, "latest_if_newer", lambda: "0.9.9")
    s = TuiPetApp.__new__(TuiPetApp)             # bypass Textual mount
    s._update_msg = None
    asyncio.run(s._check_update())
    assert s._update_msg and "0.9.9" in s._update_msg
    assert "pip install -U tuipet" in s._update_msg


def test_worker_stays_silent_when_current(monkeypatch):
    import asyncio
    from tuipet.app import TuiPetApp
    from tuipet import app as app_mod
    monkeypatch.setattr(app_mod.update_check, "latest_if_newer", lambda: None)
    s = TuiPetApp.__new__(TuiPetApp)
    s._update_msg = None
    asyncio.run(s._check_update())
    assert s._update_msg is None
