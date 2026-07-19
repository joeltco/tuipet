"""KO6 / Mega-class counter and the album egg axis (egg audit 2026-07-14).

⛔ JP/EN STAGE-NAME GOTCHA.  DMX's gate reads "Defeat N Stage VI Digimon", and
humulos' dmx.json spells the ladder out verbatim:

    "Stage V (Perfect)"   == EN **Ultimate**
    "Stage VI (Ultimate)" == EN **Mega**      (WarGreymon, MetalGarurumon)

We counted ("Ultimate", "Mega"), folding all of Stage V in.  That swept 44% of
the enemy roster instead of 17%, silently loosening every KO6 evolution gate and
turning the "Mega-class" eggs into early-game errands (Ultimates are ordinary
random encounters in map 1 zone 1; the first random *Mega* is map 1 zone 4).

⛔ ALBUM COUNTS STAGES, NOT PETS.  album_add fires on every save, so one pet's
run to Mega records SIX species (Fresh/InTraining/Rookie/Champion/Ultimate/Mega).
Nine eggs were gated at 3/5/6/8 -- i.e. every one of them inside the player's
first ~1.5 pets.  The album axis must span GENERATIONS.
"""
import csv
import os

from tuipet import data_meta  # noqa: E402
from tuipet import data
from tuipet.battle import Battle
from tuipet.pet import Pet


def _enemy(stage, num=-1):
    return {"num": num, "name": "Foe", "stage": stage, "vaccine": 0,
            "data_power": 0, "virus": 0, "hp": 10, "boss": False, "bits": (1, 5)}


def _pet():
    return Pet(num=-1, stage="Champion", vaccine=5, data_power=5, virus=5)


# ---------------------------------------------------------------- the counter

def test_stage_vi_is_mega_not_ultimate():
    """An Ultimate (Stage V / Perfect) is NOT a KO6 kill.  A Mega is."""
    p = _pet()
    p.record_battle(True, _enemy("Ultimate"))
    assert p.mega_kills == 0, "Stage V (Perfect) must not count as Stage VI"

    p.record_battle(True, _enemy("Mega"))
    assert p.mega_kills == 1, "Stage VI (Mega) must count"


def test_lesser_stages_never_count():
    p = _pet()
    for st in ("Fresh", "InTraining", "Rookie", "Champion"):
        p.record_battle(True, _enemy(st))
    assert p.mega_kills == 0


def test_a_loss_to_a_mega_is_not_a_kill():
    p = _pet()
    p.record_battle(False, _enemy("Mega"))
    assert p.mega_kills == 0


def test_pvp_megas_are_not_farmable():
    """The opponent's stage rides an UNTRUSTED peer card -- two colluding tamers
    must not be able to trade wins with Mega pets and farm KO6/the eggs."""
    p = _pet()
    p.record_battle(True, _enemy("Mega"), source="pvp")
    assert p.mega_kills == 0, "a PvP 'Mega' must never bump the KO6 counter"

    # ...and the host path resolves through the real engine, so Battle must
    # carry the source too, or the exclusion leaks on the host side.
    host = Battle(_pet(), _enemy("Mega"), source="pvp")
    assert host.source == "pvp"
    assert Battle(_pet(), _enemy("Mega")).source == "battle"


# ---------------------------------------------------------------- the roster

def test_mega_foes_demand_real_map_progress():
    """The whole point of the fix: a Mega is not an early random encounter."""
    es = data.load_enemies()
    mega = [e for e in es if e["stage"] == "Mega"]
    assert mega, "no Mega foes in the roster?"

    # Stage V must NOT be lumped in -- that was the bug.
    assert len(mega) < len([e for e in es if e["stage"] == "Ultimate"])

    first_random = min((e for e in mega if not e["boss"]),
                       key=lambda e: (e["map"], e["zone"]))
    assert (first_random["map"], first_random["zone"]) >= (1, 4), (
        "a random Mega this early makes the Mega-class eggs trivial again")


# ---------------------------------------------------------------- the eggs

def _egg_rows():
    path = os.path.join(data_meta._DATA, "eggUnlock.csv")   # the OWNING module's dir (facade _DATA is whichever module copied last)
    rows = list(csv.reader(open(path, newline="")))
    hdr = rows[0]
    i_alb = next(i for i, h in enumerate(hdr) if h.startswith("AlbumCount"))
    i_desc = next(i for i, h in enumerate(hdr) if h.startswith("LockedDescription"))
    return rows[1:], i_alb, i_desc


ONE_LIFETIME = len(data.STAGE_ORDER)        # == 6 species, egg -> Mega


def test_album_eggs_span_generations():
    """No album egg may fall out of a SINGLE pet's lifetime."""
    rows, i_alb, i_desc = _egg_rows()
    gated = [(r[0], int(r[i_alb])) for r in rows
             if r and i_alb < len(r) and (r[i_alb] or "").strip() not in ("", "-1")]
    assert gated, "no album-gated eggs found -- did the column move?"
    for name, n in gated:
        assert n > ONE_LIFETIME, (
            f"{name} unlocks at {n} species, but one pet records {ONE_LIFETIME} "
            f"-- it would drop on the first lifetime")


def test_album_copy_does_not_lie():
    """It counts SPECIES, not pets: 'Raise N different Digimon' was never true."""
    rows, i_alb, i_desc = _egg_rows()
    for r in rows:
        if not r or i_alb >= len(r) or (r[i_alb] or "").strip() in ("", "-1"):
            continue
        desc = r[i_desc]
        assert "different Digimon" not in desc, f"{r[0]}: stale copy {desc!r}"
        assert str(int(r[i_alb])) in desc, f"{r[0]}: copy must name the real gate"


def test_mega_egg_ladder_stays_spread():
    """3 -> 5 -> 10 Megas: the ladder only means something now the counter is right."""
    rules = data.load_egg_unlock()
    needs = sorted({r["mega"] for r in rules.values() if r.get("mega")})
    assert needs == [3, 5, 10], needs
