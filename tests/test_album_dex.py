"""Album/dex — canon Evolution.setUnlocked at digivolve + checkNaturalUnlocked's
NAME sync across duplicate roster rows (the 1410+ egg-hatch block mirrors the
chart's canonical rows), persisted device-lifetime (saves/Shared/tree.txt ->
tuipet's settings progress channel).  Audit 2026-07-06."""
from tuipet import data, persistence
from tuipet.egg import _conditions_met


def test_name_twins_share_one_canonical_num():
    assert data.canonical_num(1432) == data.canonical_num(944) == 944  # ChibiKiwimon
    assert data.canonical_num(1410) == 1                               # Yukimibotamon
    assert data.canonical_num(100) == data.canonical_num(100)          # stable
    assert data.canonical_num(999999) == 999999                        # unknown: identity


def test_the_album_records_and_reveals_by_name():
    """Raising a form under its hatch-twin num reveals BOTH (canon
    checkNaturalUnlocked): the album stores the canonical identity and
    album_seen answers for either alias."""
    persistence.album_add(1432)                    # lived as the hatch twin
    assert persistence.album_seen(944)             # ...the chart row is revealed
    assert persistence.album_seen(1432)
    assert 944 in persistence.get_album() and 1432 not in persistence.get_album()


def test_old_raw_entries_canonicalize_on_read():
    """Existing saves may hold duplicate-block nums from before the sync --
    get_album() canonicalizes on read, no migration needed."""
    d = persistence.load_settings()
    d.setdefault("progress", {})["album"] = [1410, 102]   # an old-save shape
    persistence.save_settings(d)
    persistence._ALBUM_SEEN.clear()
    assert persistence.get_album() == {1, 102}
    assert persistence.album_seen(1)               # the chart twin answers


def test_the_chibikiwimon_gate_accepts_either_twin():
    """Egg 22's unlock history demands num 944 -- raising ChibiKiwimon from
    its own egg (which hatches 1432) must satisfy it, like canon's name sync
    (the exact stranding this audit found)."""
    rule = next(r for r in data.load_egg_unlock().values()
                if r["name"] == "ChibiKiwimon")
    assert rule["history"] == [944]
    prog = {"album": {944}, "wins": 10**9, "mega_kills": 10**9, "max_gen": 99,
            "max_stage": 99, "xanti_ever": True, "maps": set(range(99)),
            "tourneys": set(range(999)), "last_field": rule.get("prev_field"),
            "last_xanti": True, "last_attribute": rule.get("prev_attribute"),
            "last_element": rule.get("prev_element")}
    # the album arrives canonicalized (get_album) -- 1432 stored old-style
    # resolves to 944; simulate both shapes through the gate:
    assert _conditions_met(rule, dict(prog, album={data.canonical_num(1432)}))
    assert _conditions_met(rule, dict(prog, album={944}))
    assert not _conditions_met(rule, dict(prog, album={1}))


def test_erase_all_forgets_the_album_mirror():
    """'Erase all data' wipes the files but the in-process _ALBUM_SEEN mirror
    survived it: a species raised BEFORE the erase silently never re-recorded
    in the fresh album (album_add early-returns on the cached num; audit
    2026-07-13)."""
    persistence._ALBUM_SEEN.clear()
    persistence.album_add(29)
    assert 29 in persistence._ALBUM_SEEN
    persistence.erase_all()
    assert 29 not in persistence._ALBUM_SEEN, "the mirror dies with the files"
    persistence.album_add(29)                     # a fresh run re-records it
    assert persistence.album_seen(29)
