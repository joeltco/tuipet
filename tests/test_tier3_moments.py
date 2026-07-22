"""Tier-3 professionalism pins (sweep 2026-07-14): moment framing.  The game
already computed what happened while you were away, which firsts fell, and
which generations came before -- it just never SAID any of it."""
from tuipet import data, persistence
from tuipet.app import TuiPetApp
from tuipet.digicorescreen import _legacy_rows, _trophy_rows
from tuipet.pet import Pet


# ---- the welcome back went with the offline catch-up ----------------------
# The itemized "While you were gone: it slept, went hungry (+1 care mistake),
# 2 poops piled up" report had nothing left to report once a closed game
# became a stopped clock (Joel 2026-07-22).  Its three pins retired with it;
# tests/test_persistence.py::test_a_closed_game_is_a_stopped_clock is the
# replacement contract.


# ---- firsts are announced -----------------------------------------------------------

def test_album_has_tracks_canonical_firsts():
    assert not persistence.album_has(100)
    persistence.album_add(100)
    assert persistence.album_has(100)
    assert persistence.album_has(-1)                   # sentinels are never "firsts"


def test_evolve_msg_names_a_double_first():
    app = TuiPetApp.__new__(TuiPetApp)                 # no Textual mount needed
    app.pet = Pet(num=100, name="Greymon", stage="Champion")
    msg = app._evolve_msg(37)
    assert "evolved into" in msg
    assert "your first Champion ever" in msg           # fresh progress: max_stage 0
    assert "NEW species for the album" in msg


def test_evolve_msg_stays_plain_once_seen():
    persistence.album_add(100)
    persistence.note_stage_index(data.STAGE_ORDER.index("Champion"))
    app = TuiPetApp.__new__(TuiPetApp)
    app.pet = Pet(num=100, name="Greymon", stage="Champion")
    assert "★" not in app._evolve_msg(37)


# ---- the legacy book ------------------------------------------------------------------

def test_legacy_page_remembers_retired_generations():
    assert any("no elders yet" in v for _, v in _legacy_rows())
    p = Pet(num=100, name="Coredramon", stage="Champion", generation=3)
    p.age_seconds = 12 * 86400.0                       # 12 REAL days of ticks
    persistence.snapshot_prev_gen(p)
    rows = _legacy_rows()
    assert rows[0][0] == "gen 3"
    # real-time unit, like the Age row (the old pin asserted the 60x
    # game-day reading; digicore audit 2026-07-19)
    assert "Coredramon" in rows[0][1] and "12d" in rows[0][1]
    assert all(len(v) <= 30 for _, v in rows)          # the 30-col value budget


def test_legacy_bank_caps_at_thirty():
    for g in range(1, 41):
        p = Pet(num=100, name=f"Pet{g}", stage="Rookie", generation=g)
        persistence.snapshot_prev_gen(p)
    legacy = persistence.load_settings()["progress"]["legacy"]
    assert len(legacy) == 30 and legacy[0]["gen"] == 11    # oldest rolled off


def test_trophy_page_shows_raid_conquest():
    rows = _trophy_rows(Pet(num=100, stage="Champion"))
    assert any("raid bosses felled" in v for _, v in rows)
    assert len(rows) <= 9                              # the page's row budget


# ---- rare drops break the monotone -------------------------------------------------------

def test_quit_prints_a_saved_acknowledgement():
    import inspect
    from tuipet import app as app_mod
    src = inspect.getsource(app_mod.main)
    assert "Saved ✓" in src
    assert "couldn't save" in src                      # ...but never over a dead disk
