"""The title-screen WHAT'S NEW line (Joel 2026-07-07): first launch on a new
build announces the release in the msg box; the seen stamp persists in
settings so it shows exactly once per build.  Persistence is sandboxed by the
autouse isolate_save fixture."""
from tuipet import persistence
from tuipet.pet import Pet
from tuipet.app import TuiPetApp


def test_whats_new_shows_once_per_build():
    app = TuiPetApp(pet=Pet(num=-1, stage="Child"))   # __init__ only
    first = app._whats_new()
    assert first and "WHAT'S NEW" in first and app.WHATS_NEW in first
    assert persistence.load_settings().get("seen_version")
    assert app._whats_new() is None                    # stamped: shown once
    # a new build (stale stamp) re-announces
    s = persistence.load_settings()
    s["seen_version"] = "0.0.0"
    persistence.save_settings(s)
    assert app._whats_new()
