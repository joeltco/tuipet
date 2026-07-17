"""Armor evolutions vs canon (audit 2026-07-18, the LV/jogress treatment).

Verified: the eleven Digimental families are wikimon-canon by their EN egg
names -- with ONE fix: the JP/EN dub swap on Sincerity/Reliability (誠実 =
EN Reliability = the water armors, item 20; 純真 = EN Sincerity = the
ninja/plant armors, item 18).  The doors themselves were sound: the
Digimental is an extra gate, not a bypass -- Flamedramon still wants
battles >10 at zero mistakes, Magnamon a >75% veteran who has fought real
foes.  The report no longer displays the power walls v0.5.18 dropped.
"""
import random

from tuipet import data, evolution
from tuipet.pet import Pet


def _by_name(name):
    _, by = data.load_sprites()
    return next(n for n, r in by.items()
                if r["name"] == name and not data.is_placeholder(n))


def _vet(name):
    p = Pet(num=_by_name(name), stage="Rookie", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    p.battles, p.wins = 15, 12
    p.levels_fought = [3, 4]
    p.care_mistakes = 0
    return p


CANON_PAIRS = [
    ("Veemon", "egg_of_courage", "Flamedramon"),
    ("Veemon", "egg_of_friendship", "Raidramon"),
    ("Hawkmon", "egg_of_love", "Holsmon"),
    ("Armadimon", "egg_of_knowledge", "Digmon"),
    ("Armadimon", "egg_of_reliability", "Submarimon"),   # the dub-swap fix
    ("Hawkmon", "egg_of_sincerity", "Shurimon"),         # the dub-swap fix
    ("Patamon", "egg_of_hope", "Pegasmon"),
    ("Veemon", "egg_of_miracles", "Magnamon"),
    ("Terriermon", "egg_of_destiny", "Rapidmon"),
]


def test_the_canon_pairs_open_for_a_veteran():
    for base, egg, want in CANON_PAIRS:
        random.seed(7)
        p = _vet(base)
        p.add_item(egg)
        p.use_item(egg)
        got = data.record_for(p.num).get("name")
        assert got == want, f"{base} + {egg}: got {got}, want {want}"


def test_the_digimental_is_a_gate_not_a_bypass():
    """A fresh, unfought Veemon holds the Courage egg and nothing happens --
    the row's care gates (battles >10, mistakes 0) still judge."""
    p = Pet(num=_by_name("Veemon"), stage="Rookie", attribute="Vaccine",
            obedience=500)
    p.world_seconds = 600.0
    p.energy = p.max_energy
    p.add_item("egg_of_courage")
    out = p.use_item("egg_of_courage")
    assert data.record_for(p.num).get("name") == "Veemon"
    assert "can't" in out


def test_the_report_shows_no_dropped_power_walls():
    p = _vet("Veemon")
    rows = [label for _ok, label in evolution.requirement_report(p, 519)]
    assert not any("power total" in r or r.startswith("Va ") for r in rows)
    assert any("Digimental" in r for r in rows)          # the item gate shows
