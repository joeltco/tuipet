"""The AWAY flag — set by the road, read by the body (2026-07-21).

Joel's @-line question ("shouldnt the @ say what zone the mon is in during
adventure?") uncovered a dangling wire: every consumer of pet.away existed
(the assistant's canon _isHome gate, filth, gift call, the app's death
clear) but NOTHING ever set it — the setter died with the old adventure.
Pins: the teleport toggles it both ways (canon), the status card's @ line
goes live with the zone, and the assistant truly pauses on the road.
"""
from tuipet import adventure, statusbox
from tuipet.adventurescreen import AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _land(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(_pet(), zone=adventure.ZONES[0])
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):
        pan.anim()
        if pan.travelling:
            return pan
    raise AssertionError("never landed")


def test_the_teleport_toggles_away_both_ways(monkeypatch):
    pan = _land(monkeypatch)
    p = pan.pet
    assert p.away is True                              # landed: OUT
    assert p.away_where == pan.adv.name                # ...and WHERE
    pan.key("escape")                                  # turn back
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 4):
        pan.anim()
        if pan.auto_close:
            break
    assert pan.auto_close and p.away is False          # home: the flag is down
    assert p.away_where == ""


def test_the_at_line_names_the_zone_while_away(monkeypatch):
    pan = _land(monkeypatch)
    p = pan.pet
    card = "\n".join(statusbox.home_lines(p))
    assert "@" + statusbox._zone_display(pan.adv.name, 16) in card
    p.away, p.away_where = False, ""                   # home again
    card = "\n".join(statusbox.home_lines(p))
    assert "@" + statusbox._zone_display(pan.adv.name, 16) not in card
    assert "@" in card                                 # ...the home scene returns
    #      (the Quest line may still NAME the zone -- that's the frontier)


def test_the_assistant_pauses_on_the_road(monkeypatch):
    """The canon _isHome gate finally has a live flag to read: while away,
    the assistant neither bills the retainer nor visits (the dangling-wire
    bug had it billing mid-run)."""
    pan = _land(monkeypatch)
    p = pan.pet
    p.auto_care = True
    p.bits = 1000
    p.hunger = 0                                       # bait: a visit-worthy state
    bits0 = p.bits
    p._tick_auto_care(3600.0)                          # an HOUR on the road
    assert p.bits == bits0 and p.auto_care             # no retainer, no visit, no quit
    p.away = False                                     # home: the helper resumes
    p._tick_auto_care(float(60 * 60))
    assert p.bits < bits0 or p.hunger > 0              # it billed or it served
