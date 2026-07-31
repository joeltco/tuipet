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


def test_the_at_line_names_the_zone_biome_while_away(monkeypatch):
    """@-habitat fix 2026-07-24 (Joel "does it display the correct habitat name
    while in adventure?"): the @ line is a PLACE, so on the road it shows the
    BIOME half of the '{Boss}'s {biome}' zone name, never the boss (the boss is
    the Quest line's objective).  Off the road the home scene returns."""
    pan = _land(monkeypatch)
    p = pan.pet
    boss, biome = pan.adv.name.split("'s ", 1)

    def at_line(pet):
        return next(l for l in statusbox.home_lines(pet) if l.startswith("@"))

    assert at_line(p).startswith("@" + biome)          # the habitat, a place
    assert boss not in at_line(p)                       # NOT the boss name
    p.away, p.away_where = False, ""                    # home again
    assert not at_line(p).startswith("@" + biome)       # the adventure biome is gone
    #      (the Quest line may still name the frontier boss -- that's the objective)


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


def test_the_road_key_hint_cycles_anchor_then_labels(monkeypatch):
    """Hint cycle, revised 2026-07-28 ("still seeing space esc"): the bare
    anchor beat is GONE -- an unlabelled keyset is a mystery whichever keys
    it names.  Every ~2s (HINT_BEAT) beat names exactly one key; the set
    cycles so every out reaches the player.  T (warp) only joins when a
    transport is held.  Every step stays within the strip box."""
    import re
    from tuipet.adventurescreen import HINT_BEAT
    pan = _land(monkeypatch)
    p = pan.pet
    p.inventory = {"town_transport": 1}                # holding a warp -> T shows
    p.energy = 5                                        # modest, so no edge overflow
    seen = set()
    for step in range(6):                              # one full anchor+labels loop
        pan.frame_i = step * HINT_BEAT
        line = pan.strip()
        assert line.count("[") == line.count("]")      # markup balanced
        assert len(re.sub(r"\[/?[^\[\]]*\]", "", line)) <= 40
        seen.add(re.sub(r"\[/?[^\[\]]*\]", "", line).split("· ", 1)[-1].strip())
    assert "SPACE T ESC" not in seen                    # the bare anchor is dead
    assert "SPACE hurry" in seen and "T warp" in seen and "ESC home" in seen
    # no transport held -> T drops from BOTH the anchor and the rotation
    p.inventory = {}
    hints = set()
    for step in range(4):
        pan.frame_i = step * HINT_BEAT
        hints.add(re.sub(r"\[/?[^\[\]]*\]", "", pan.strip()).split("· ", 1)[-1].strip())
    assert hints == {"SPACE hurry", "ESC home"}   # T gone WITH its label
