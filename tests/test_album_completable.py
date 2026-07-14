"""The album must be COMPLETABLE (roster audit 2026-07-14).

The dex carries 329 duplicate rows -- one species can sit on several device
pages (five Petitmon, seven Omnimon MM), which is faithful to the source data.
persistence.album_add() stores the CANONICAL num, so `seen` can only ever
reach the canonical count.  The digicore compared it to the RAW row count, so
the album read 1218/1547: impossible to finish, however perfectly you played.
"""
from tuipet import data


def test_the_album_denominator_is_actually_reachable():
    _, by = data.load_sprites()
    live = [n for n in by if not data.is_placeholder(n)]
    raw = len(live)
    reachable = len({data.canonical_num(n) for n in live})
    assert reachable < raw, "the dex really does carry duplicate rows"

    from tuipet import digicorescreen
    import inspect
    src = inspect.getsource(digicorescreen)
    assert "canonical_num(n) for n in by" in src, \
        "the Album total must count canonical species, not raw rows"


def test_every_duplicate_folds_onto_one_canonical_id():
    """album_add stores the canonical identity, so raising any Petitmon --
    from whichever egg -- counts once."""
    petitmon = [954, 1437, 1612, 1613, 1615]
    canon = {data.canonical_num(n) for n in petitmon}
    assert len(canon) == 1, f"the five Petitmon must fold to one album entry: {canon}"


def test_album_gated_eggs_stay_within_reach():
    """No egg may ask for more species than the album can hold."""
    _, by = data.load_sprites()
    reachable = len({data.canonical_num(n) for n in by if not data.is_placeholder(n)})
    for r in data.load_egg_unlock().values():
        need = r.get("album_n") or 0
        assert need <= reachable, f"{r['name']} needs {need} > {reachable} possible"
