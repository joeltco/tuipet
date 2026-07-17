"""Tier-3 professionalism pins (sweep 2026-07-14): moment framing.  The game
already computed what happened while you were away, which firsts fell, and
which generations came before -- it just never SAID any of it."""
from tuipet import data, persistence
from tuipet.app import TuiPetApp
from tuipet.digicorescreen import _legacy_rows, _trophy_rows
from tuipet.pet import Pet


# ---- the itemized welcome back ---------------------------------------------------

def _aged_pet():
    p = Pet(num=100, name="Agumon", stage="Champion", hunger=4)
    p.world_seconds = 10 * 60.0
    return p


def test_offline_return_is_itemized():
    p = _aged_pet()
    msg = persistence._offline(p, 3 * 3600.0)          # 3h away
    assert "3h away" in msg and "While you were gone" in msg
    assert "went hungry (+1 care mistake)" in msg      # hunger 4 drains in 20min
    assert "poop" in msg


def test_offline_short_absence_stays_quiet():
    assert persistence._offline(_aged_pet(), 20.0) == ""


def test_offline_uneventful_return_just_greets():
    p = _aged_pet()
    msg = persistence._offline(p, 120.0)               # 2min: hunger 4 -> 4
    assert "missed you" in msg and "While you were gone" not in msg


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
    p.age_seconds = 12 * 1440.0                        # 12 game days
    persistence.snapshot_prev_gen(p)
    rows = _legacy_rows()
    assert rows[0][0] == "gen 3"
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
