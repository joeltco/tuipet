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


def test_the_road_strip_is_the_whole_key_set_holding_still(monkeypatch):
    """Joel's named order 2026-07-30: "thin the strip to just the keys.  you
    should be able to fit the whole thing without the message change
    mechanism."  The ~2s rotation (HINT_BEAT, retired) existed only because a
    ribbon, energy, hearts and the chain shared this 40-cell line with the
    keys -- the ROAD CARD carries every one of those now, so all three
    labelled keys fit at once and the line never changes under the player."""
    import re
    from rich.cells import cell_len
    pan = _land(monkeypatch)
    p = pan.pet
    p.inventory = {"town_transport": 1}                # holding a warp -> T shows
    p.energy = 125                                      # 3 digits: no longer on the line
    pan.adv.streak = 12                                 # a fat chain: likewise gone
    plain = re.sub(r"\[/?[^\[\]]*\]", "", pan.strip())
    assert plain == "SPACE hurry \u00b7 T warp \u00b7 ESC home"
    assert cell_len(plain) <= 40
    # ...and it HOLDS: every frame of what used to be a full rotation is
    # byte-identical, so nothing on the road strip changes under the player
    for f in (0, 7, 20, 33, 60, 119):
        pan.frame_i = f
        assert pan.strip() == pan.strip()
        assert re.sub(r"\[/?[^\[\]]*\]", "", pan.strip()) == plain
    assert pan.strip().count("[") == pan.strip().count("]")   # markup balanced
    # nothing but keys: the numbers moved to the card (statusbox.road)
    for gone in ("\u26a1", "\u2665", "\u00d7", "\u25c6", "\u2691"):
        assert gone not in plain, f"{gone!r} still on the strip"
    # no transport held -> T drops WITH its label, the rest holds still
    p.inventory = {}
    assert re.sub(r"\[/?[^\[\]]*\]", "", pan.strip()) == "SPACE hurry \u00b7 ESC home"
