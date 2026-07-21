"""Cup + festival egg gates (unlock-spread pass, 2026-07-20).

Two pillars were egg-hollow: cups gated just one digitama (Dokimon) and the
four festival DAYS granted nothing unique.  This pins the fix -- a second cup
egg (Hack -> the Fall Champion Cup) and the game's first festival egg (DORU
/ Alphamon, the grand festival prize -- a targeted Royal Knight, swapped in
for Draco's grab-bag tree 2026-07-20), plus the festival signal that feeds it.
"""
from tuipet import data, egg, persistence, adventure
from tuipet.adventure import ZONES
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T, TRAVEL_TICKS
from tuipet.pet import Pet


def _by():
    rules = data.load_egg_unlock()
    return rules, {r["name"]: i for i, r in rules.items()}


def _prog(**over):
    p = {"album": set(), "wins": 0, "mega_kills": 0, "max_gen": 1, "max_stage": 0,
         "xanti_ever": False, "maps": set(), "raids": 0, "tourneys": set(),
         "last_field": "None", "last_attr": "None", "last_mood": 0, "last_obed": 0,
         "last_xanti": False, "connections": 0, "festivals": set()}
    p.update(over)
    return p


# -- CUP: two egg gates now, at two tiers/seasons ----------------------------
def test_cups_gate_two_distinct_eggs():
    rules, by = _by()
    tourney_eggs = sorted((r["tourney"], r["name"])
                          for r in rules.values() if r.get("tourney") is not None)
    assert tourney_eggs == [(146, "Dokimon"), (187, "Hack Egg")]   # Summer-Mega + Fall-Champion


def test_hack_needs_its_cup_not_wins():
    rules, by = _by()
    assert rules[by["Hack Egg"]]["wins"] is None            # left the wins ladder
    assert egg.egg_state(by["Hack Egg"], _prog(wins=99999), set()) == "locked"
    assert egg.egg_state(by["Hack Egg"], _prog(tourneys={187}), set()) == "owned"


# -- FESTIVAL: the seasonal pillar finally grants a unique egg ----------------
def test_doru_is_the_festival_egg():
    rules, by = _by()
    r = rules[by["DORU Egg"]]
    assert r["festivals_n"] == 2 and r["connections"] is None   # left the connection ladder
    assert egg.egg_state(by["DORU Egg"], _prog(), set()) == "locked"
    assert egg.egg_state(by["DORU Egg"],
                         _prog(festivals={"Halloween Festival"}), set()) == "locked"   # 1 < 2
    assert egg.egg_state(by["DORU Egg"],
                         _prog(festivals={"Halloween Festival", "Christmas Festival"}),
                         set()) == "owned"


def test_festival_progress_line_is_countable():
    _, by = _by()
    line = egg.unlock_progress(by["DORU Egg"], _prog(festivals={"New Year Festival"}))
    assert line == "festivals celebrated 1/2"              # the egg-guide counter


def test_festival_add_records_distinct_festivals(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    persistence.festival_add("Halloween Festival")
    persistence.festival_add("Halloween Festival")         # same day -> counts once
    persistence.festival_add("Christmas Festival")
    assert persistence.get_progress()["festivals"] == {"Halloween Festival",
                                                        "Christmas Festival"}


def test_conquering_on_a_holiday_celebrates_the_festival(tmp_path, monkeypatch):
    """The adventure conquer hook: felling a zone boss on a festival day stamps
    the festival (next to the map-clear signal)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(Pet(num=100, stage="Champion", attribute="Vaccine",
                             obedience=500), zone=ZONES[0])
    pan.adv.holiday = "Odaiba Memorial Day"                # pretend it's the festival
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None

    class _Win:
        won = True
    pan._battle_done(_Win())
    assert "Odaiba Memorial Day" in persistence.get_progress()["festivals"]
