"""Adventure rebuild — the MARCH engine (phase 2, 2026-07-20).

Pins the travel loop: honest progress across a zone, the ribbon, arrival, and
the panel's auto-march that rides the teleport home with the victory verdict.
The risk systems (encounters, boss, drain, towns) are later phases and absent.
"""
import pytest
from tuipet import adventure
from tuipet.adventure import Adventure, INTERACTIVE_STEPS, ZONES, pick_zone
from tuipet.adventurescreen import (AdventurePanel, TELE_LEAVE_T, TELE_ARRIVE_T,
                                    TRAVEL_TICKS)
from tuipet.pet import Pet


def _champ(num=100):
    return Pet(num=num, stage="Champion", attribute="Vaccine", obedience=500)


def _bossless_zone():
    """A synthetic zone with NO gate boss, so the crossing itself is the win --
    isolates the pure march from the boss-gate phase."""
    return {"name": "Testfield", "scene": "greenhills",
            "steps": INTERACTIVE_STEPS, "randoms": [], "bosses": []}


@pytest.fixture
def no_encounters(monkeypatch):
    """Isolate the MARCH from the wild-encounter roll AND the loot-find roll
    (phases 3/9) so these tests exercise pure travel/progress."""
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)


def test_zone_pick_is_deterministic_and_one_biome():
    p = _champ()
    z = pick_zone(p)
    assert z in ZONES and pick_zone(p) is z            # stable, no RNG
    a = Adventure(p)
    assert a.scene == z["scene"] and a.name == z["name"]
    assert a.total == INTERACTIVE_STEPS                # one biome, ~40 legs


def test_travel_advances_to_arrival_then_stops(no_encounters):
    a = Adventure(_champ(), zone=_bossless_zone())   # bossless: crossing == win
    assert a.pct == 0 and a.done is False
    seen = [a.pct]
    for _ in range(a.total - 1):
        assert a.travel() == "step"
        seen.append(a.pct)
    assert a.done is False and a.pct < 100
    assert a.travel() == "arrived"                     # the last leg reaches the goal
    assert a.done is True and a.pct == 100
    assert a.travel() is None                          # a finished run does not move
    assert seen == sorted(seen)                        # progress only ever grows


def test_the_ribbon_tracks_the_pet_toward_the_goal(no_encounters):
    a = Adventure(_champ())
    assert a.ribbon()[0] == "◆"                   # the pet starts at the head
    for _ in range(a.total):
        a.travel()
    assert a.ribbon().endswith("◆")               # ...and ends on the goal cell
    assert a.ribbon().count("◆") == 1             # exactly one pet marker


def test_the_panel_auto_marches_to_the_boss_gate(no_encounters):
    # with encounters off, the pet walks the whole zone and the END opens the
    # gate BOSS (every real zone has one) -- crossing is not the win
    pan = AdventurePanel(_champ())
    budget = TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20
    marched = False
    for _ in range(budget):
        pan.anim()
        assert pan.text()
        if pan.travelling and pan.adv.pct > 0:
            marched = True
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    assert marched                                     # it actually walked the road
    assert pan._fighting_boss                           # ...and reached the boss gate
    assert type(pan.sub).__name__ == "BattlePanel"
    assert pan.sub._enemy.get("boss") and pan.sub.scene == pan.adv.scene
    assert pan.adv.done is False                        # not won until the boss falls


def test_the_walking_sequence_crosses_the_window(no_encounters):
    """The MARCH (walking sequence restored from the old build, 8ab28a0 --
    Joel: "mon should walk across the screen"): travelling, the mon walks
    clear across the window, exits the RIGHT edge fully, and re-enters from
    hidden LEFT (the lawful exits) -- never stepping in place at an anchor."""
    from tuipet import grid
    from tuipet.adventurescreen import SPRITE_W_MARCH
    pan = AdventurePanel(_champ())
    pan._trans = None
    pan._landed = True
    pan.travelling = True                     # land instantly: the march begins
    xs = []
    for _ in range(220):                      # > one full 96-tick crossing
        pan.anim()
        if pan._town_prompt:
            pan.key("space")                  # walk on -- towns pause the march
        if pan._fighting_boss or pan._trans is not None:
            break
        assert pan.text()                     # every march frame renders clean
        xs.append(int(pan._wx))
    assert max(xs) >= grid.X1 - 1             # it walked out the right side
    assert min(xs) <= grid.X0 - SPRITE_W_MARCH + 1   # ...and slid back in hidden
    assert len(set(xs)) > 30                  # a real sweep, not an anchor


def test_beats_play_where_the_mon_stands_not_at_centre(no_encounters):
    """A road beat (the glint stop) plays at the CLAMPED march x -- "beats
    play wherever it stands" (old build) -- not snapped back to centre."""
    from tuipet import grid
    pan = AdventurePanel(_champ())
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan._wx = float(grid.X1 - 4)              # caught mid-exit, half off the edge
    rows = pan._rows(0)
    lo, hi = grid.roam_bounds(grid.width(rows))
    assert pan._jx(rows) == hi                # clamped in-band at the spot it reached
    assert pan._jx(rows) != (lo + hi) // 2    # NOT the old centre snap
    pan._find = "i:1"
    assert pan.text()                         # the glint beat renders there


def test_the_march_faces_the_direction_of_travel(no_encounters, monkeypatch):
    """Marching, the mon FACES the way it's going (mirror flip -- the art's
    native facing is the other way), like the old build's crossing."""
    from tuipet import menu
    pan = AdventurePanel(_champ())
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append(pl), real(pl, *a, **k))[1])
    pan.text()
    (rows, x, mirror), = calls[-1]
    assert mirror is True


def test_space_hurries_a_leg_while_travelling(no_encounters):
    p = _champ()
    pan = AdventurePanel(p)
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + 2):  # land first
        pan.anim()
        if pan.travelling:
            break
    assert pan.travelling and pan.adv.loc == 0
    pan.key("space")
    assert pan.adv.loc == 1                             # SPACE advanced a leg immediately
