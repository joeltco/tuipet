"""The card eggs' WILD gate (Joel 2026-10-15): a ZoneEnemyBeat value of
"MAP:DEX" opens the egg once that species is beaten as a wayside WILD on
that adventure map.  "MAP" alone keeps meaning the map's boss cleared
(Volcanic Beat), untouched.  The record is persistence's `wilds_beaten`
set of "MAP:DEX" strings, kept beside maps_cleared."""
import json

import tuipet.adventure as A
from tuipet import data, egg, persistence
from tuipet.adventure import ZONES
from tuipet.adventurescreen import AdventurePanel
from tuipet.pet import Pet

MAP = 6                                            # Moonlit Meadow
DEX = 64                                           # Renamon walks it as a wild


class _Win:
    won = True


class _Loss:
    won = False


def _rules_with(zone):
    """The real table plus ONE fixture row: the Volcanic Beat egg's row with
    its zone gate rewritten (no egg row is added to the CSV here; Joel wires
    the card eggs himself)."""
    rules = dict(data.load_egg_unlock())
    idx = next(i for i, r in rules.items() if r["name"] == "Volcanic Beat Egg")
    rules[idx] = dict(rules[idx], zone=zone)
    return idx, rules


def _prog(**kw):
    p = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0,
             wilds_beaten=set())
    p.update(kw)
    return p


def test_the_map_has_the_species_as_a_wild():
    assert ZONES[MAP]["name"] == "Moonlit Meadow"
    assert any(e["num"] == DEX and not e["boss"] for e in ZONES[MAP]["randoms"])


def test_beating_a_wild_on_the_road_records_map_and_species():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.adv_progress = MAP
    pan = AdventurePanel(p, zone=ZONES[MAP])
    wild = next(e for e in ZONES[MAP]["randoms"] if e["num"] == DEX)
    pan._fighting_enemy = wild
    pan._battle_done(_Loss())                      # a loss records nothing
    assert persistence.get_progress()["wilds_beaten"] == set()
    pan._fighting_enemy = wild
    pan._battle_done(_Win())
    assert persistence.get_progress()["wilds_beaten"] == {f"{MAP}:{DEX}"}


def test_the_wild_gate_needs_the_right_species_on_the_right_map(monkeypatch):
    idx, rules = _rules_with(f"{MAP}:{DEX}")
    monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
    assert egg.egg_state(idx, _prog(), set()) == "locked"
    assert egg.egg_state(idx, _prog(wilds_beaten={f"{MAP + 1}:{DEX}"}), set()) == "locked"
    assert egg.egg_state(idx, _prog(wilds_beaten={f"{MAP}:{DEX + 1}"}), set()) == "locked"
    # clearing the map's boss is NOT the wild gate
    assert egg.egg_state(idx, _prog(maps_cleared={MAP}, maps={4}), set()) == "locked"
    assert egg.egg_state(idx, _prog(wilds_beaten={f"{MAP}:{DEX}"}), set()) == "owned"


def test_the_boss_form_is_untouched(monkeypatch):
    idx, rules = _rules_with("20")
    monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
    assert egg.egg_state(idx, _prog(), set()) == "locked"
    assert egg.egg_state(idx, _prog(maps_cleared={20}), set()) == "owned"
    assert egg.unlock_progress(idx, _prog()) == rules[idx]["desc"]


def test_the_goal_line_names_the_wild_and_the_road(monkeypatch):
    idx, rules = _rules_with(f"{MAP}:{DEX}")
    monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
    assert egg.unlock_progress(idx, _prog()) == \
        "Beat a wild Renamon on the Moonlit Meadow road"
    assert egg.unlock_progress(idx, _prog(wilds_beaten={f"{MAP}:{DEX}"})) == ""
    assert egg.unlock_ratio(idx, _prog()) is None    # a yes/no gate, like the boss form


def test_an_old_save_without_the_key_loads_locked(monkeypatch):
    d = persistence.load_settings()
    d["progress"] = {"maps_cleared": [20], "wins": 3}
    persistence.save_settings(d)
    assert "wilds_beaten" not in json.load(open(persistence.SETTINGS_PATH, encoding="utf-8"))["progress"]
    prog = persistence.get_progress()
    assert prog["wilds_beaten"] == set() and prog["maps_cleared"] == {20}
    idx, rules = _rules_with(f"{MAP}:{DEX}")
    monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
    assert egg.egg_state(idx, prog, set()) == "locked"


def test_the_record_travels_with_the_profile():
    persistence.wild_beaten_add(MAP, DEX)
    assert persistence.progress_for_sync()["wilds_beaten"] == [f"{MAP}:{DEX}"]


def test_every_wild_row_names_a_species_that_walks_its_map(monkeypatch):
    assert egg.unreachable_wild_rows() == []           # the shipped table
    boss = ZONES[MAP]["bosses"][0]["num"]
    assert all(e["num"] != boss for e in ZONES[MAP]["randoms"])
    for zone in (f"{MAP}:{boss}", f"{MAP + 1}:{DEX}", f"{len(A.MAPS)}:{DEX}"):
        idx, rules = _rules_with(zone)
        monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
        assert egg.unreachable_wild_rows() == ["Volcanic Beat Egg"], zone
    idx, rules = _rules_with(f"{MAP}:{DEX}")
    monkeypatch.setattr(data, "load_egg_unlock", lambda: rules)
    assert egg.unreachable_wild_rows() == []
