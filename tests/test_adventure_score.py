"""Adventure polish — the RUN SCORE (arcade arc, 2026-07-21).

Pins the score: one number rolled from the tallies the summary card already
shows, recorded per zone as a standing best (profile-level), bragged on the
card when beaten, and shown in the zone picker as the number to chase.
"""
from tuipet import adventure, persistence
from tuipet.adventure import (Adventure, ZONES, SCORE_WIN, SCORE_FIND,
                              SCORE_LIFE, SCORE_STREAK, SCORE_CONQUEST)
from tuipet.adventurescreen import AdventurePanel, ZonePickPanel
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


class _Win:
    won = True


def test_the_score_is_exactly_the_cards_tallies():
    a = Adventure(_pet(), zone=ZONES[0])
    a.bits_earned, a.wins, a.finds, a.best_streak = 40, 3, 2, 3
    a.lives = 2
    expect = (40 + 3 * SCORE_WIN + 2 * SCORE_FIND + 2 * SCORE_LIFE
              + 2 * SCORE_STREAK)
    assert a.score() == expect                          # not conquered: no bonus
    a.done = True
    assert a.score() == expect + SCORE_CONQUEST


def test_the_best_book_keeps_only_the_high_water_mark():
    assert persistence.zone_best_set(4, 120) is True    # first entry: a best
    assert persistence.zone_best_set(4, 90) is False    # lower: books untouched
    assert persistence.zone_best_set(4, 150) is True    # higher: the new mark
    assert persistence.zone_bests() == {4: 150}


def test_a_run_of_substance_records_and_brags_a_new_best(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan.adv.holiday = None
    pan._fighting_enemy = {"name": "W", "bits": (8, 8), "num": 100}
    pan._battle_done(_Win())                            # substance: one won fight
    pan._home_msg = "test"
    pan._go_home()
    assert pan._summary and pan._new_best               # scored + it's the first best
    zi = adventure.zone_index(pan.adv.zone)
    assert persistence.zone_bests()[zi] == pan.adv.score()
    card = pan._summary_frame().plain
    assert f"Score   {pan.adv.score()}" in card and "new best" in card


def test_a_bare_turn_back_stays_out_of_the_books(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan._home_msg = "test"
    pan._go_home()                                      # nothing happened out there
    assert not pan._summary                             # no card...
    assert persistence.zone_bests() == {}               # ...and no score entry


def test_the_zone_picker_shows_the_number_to_chase():
    persistence.zone_best_set(0, 234)
    p = _pet()
    pick = ZonePickPanel(p)
    line = pick._fmt(0, 0)
    assert line.endswith("   234") and len(line) <= 34
    assert "234" not in pick._fmt(1, 1)                 # unscored zones stay clean
