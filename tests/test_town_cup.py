"""Town hub T4 — the DISTINCT road-only Town Cup (2026-07-20).

Pins: a town cup is its OWN trophy (id 900+, never a home cup), an open bracket
run by the real Tournament engine, a stake + purse, and one entry per town visit.
"""
from tuipet import tournament, persistence
from tuipet.townscreen import TownPanel, _MENU
from tuipet.pet import Pet


def _pet(bits=5000):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.bits = bits
    return p


class _Win:
    won = True


def _cup_index():
    return next(i for i, m in enumerate(_MENU) if m[0] == "cup")


def test_the_town_trophy_is_distinct_from_home_cups():
    cup = tournament.town_cup(_pet(), town_id=3)
    assert cup["id"] == tournament.TOWN_TROPHY_BASE + 3
    assert cup["id"] > 324                                  # past the home trophy range
    assert tournament.trophy_by_id(cup["id"]) is None       # not in the home data
    assert tournament.trophy_label(cup) == "Town Cup"       # names itself
    assert not cup["field_req"] and not cup["age_limit"]    # open to all comers


def test_entering_the_cup_pays_the_stake_and_opens_the_bracket():
    p = _pet()
    t = TownPanel(p, town_id=0)
    t.cursor = _cup_index()
    before = p.bits
    t.key("enter")
    assert t.tourney is not None and type(t.sub).__name__ == "BattlePanel"
    assert t._cup_done and p.bits < before                  # stake taken on entry


def test_winning_the_cup_pays_the_purse_and_records_its_trophy(monkeypatch):
    p = _pet()
    t = TownPanel(p, town_id=2)
    t.cursor = _cup_index()
    t.key("enter")
    tid = t.tourney.trophy["id"]
    before = p.bits
    for _ in range(20):                                     # win every match -> champion
        if t.tourney is None:
            break
        t.sub = None
        t._cup_match_done(_Win())
    assert t.tourney is None
    assert "champion" in t.msg.lower() and p.bits > before  # the purse landed
    assert tid in persistence.get_progress()["tourneys"]    # the distinct trophy recorded


def test_the_cup_runs_once_per_visit():
    p = _pet()
    t = TownPanel(p, town_id=0)
    t.cursor = _cup_index()
    t.key("enter")
    # abandon it, then try again this visit -> refused
    t.sub = None
    t._cup_match_done(None)
    t.key("enter")
    assert t.tourney is None and "run" in t.msg.lower()


def test_a_broke_pet_cannot_enter():
    p = _pet(bits=0)
    t = TownPanel(p, town_id=0)
    t.cursor = _cup_index()
    t.key("enter")
    assert t.tourney is None and "stake" in t.msg.lower() and not t._cup_done


def test_an_unfit_pet_is_refused_at_the_town_gate_too():
    """Cup audit 2026-07-21: the town cup skipped every pet gate -- the
    exact class the 2026-07-19 audit closed for home cups.  The SAME
    battle_condition + can_enter chain vets the town bracket now."""
    p = _pet()
    p.sick = True
    hub = TownPanel(p, town_id=3)
    hub._start_cup()
    assert hub.tourney is None and "sick" in hub.msg.lower()
    q = _pet()
    q.hunger = 0
    hub2 = TownPanel(q, town_id=3)
    hub2._start_cup()
    assert hub2.tourney is None and "hungry" in hub2.msg.lower()
    assert not hub._cup_done and not hub2._cup_done   # the visit's cup remains
    r = _pet()
    r.asleep = True
    hub3 = TownPanel(r, town_id=3)
    hub3._start_cup()                                 # the poke wakes it, like
    assert r.asleep is False                          # every care key does


def test_the_trophy_room_names_town_cups():
    """trophy_name speaks every id space: home labels, Town Cup #N for the
    900+ road trophies, the raw fallback only for truly unknown ids."""
    from tuipet import data
    home = data.load_tournies()[0]
    assert tournament.trophy_name(home["id"]) == tournament.trophy_label(home)
    assert tournament.trophy_name(tournament.TOWN_TROPHY_BASE + 11) == "Town Cup #12"
    assert tournament.trophy_name(899) == "cup 899"   # not a town, not a cup
    from tuipet import digicore
    p = _pet()
    p.trophies_won = {tournament.TOWN_TROPHY_BASE + 3: "day 2"}
    rows = digicore._trophy_rows(p)
    assert any("Town Cup #4" in name for name, _v in rows)   # the room reads it
    assert not any(name.startswith("cup ") for name, _v in rows)
