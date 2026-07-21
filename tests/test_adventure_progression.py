"""Adventure rebuild — PROGRESSION & zone selection (phase 8, 2026-07-20).

Pins the journey: pet.adv_progress tracks zones conquered = the frontier index;
zones unlock as their gate boss falls; the ZonePickPanel lists unlocked zones to
embark on (conquered ✓, frontier ★); adv_progress persists across saves.
"""
import tuipet.adventure as A
from tuipet.adventure import (ZONES, unlocked_indices, is_conquered, record_win,
                              frontier, pick_zone)
from tuipet.adventurescreen import (ZonePickPanel, AdventurePanel, TELE_LEAVE_T,
                                    TELE_ARRIVE_T, TRAVEL_TICKS)
from tuipet import persistence
from tuipet.pet import Pet


def _champ():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


class _Win:
    won = True


def test_a_fresh_pet_starts_at_the_first_zone():
    p = _champ()
    assert p.adv_progress == 0
    first = A.PROGRESSION[0]                        # the road's easiest stop
    assert unlocked_indices(p) == [first] and frontier(p) == first
    assert pick_zone(p) is ZONES[first]             # the frontier is the default embark


def test_felling_the_frontier_boss_unlocks_the_next_only():
    p = _champ()
    road = A.PROGRESSION
    assert record_win(p, ZONES[road[0]]) is True and p.adv_progress == 1
    assert unlocked_indices(p) == road[:2]
    assert is_conquered(p, road[0]) and not is_conquered(p, road[1])
    # replaying a conquered zone advances nothing
    assert record_win(p, ZONES[road[0]]) is False and p.adv_progress == 1
    # you cannot skip: "beating" a still-locked zone is not the frontier
    assert record_win(p, ZONES[road[5]]) is False and p.adv_progress == 1


def test_progress_never_runs_past_the_last_zone():
    p = _champ()
    p.adv_progress = len(ZONES)                     # all conquered
    assert frontier(p) == A.PROGRESSION[-1]         # clamped to the last stop
    assert unlocked_indices(p) == A.PROGRESSION
    assert record_win(p, ZONES[A.PROGRESSION[-1]]) is False   # nothing left


def test_the_picker_lists_unlocked_zones_and_defaults_to_the_frontier():
    p = _champ()
    p.adv_progress = 3
    pk = ZonePickPanel(p)
    assert pk.indices == A.PROGRESSION[:4]          # only unlocked, road order
    assert pk.indices[pk.cursor] == A.PROGRESSION[3]   # cursor on the frontier
    # marks: conquered ✓, frontier ★
    assert pk._fmt(A.PROGRESSION[0], 0).startswith("✓")
    assert pk._fmt(A.PROGRESSION[3], 3).startswith("★")


def test_the_picker_embarks_on_enter_and_backs_out_on_esc():
    p = _champ()
    p.adv_progress = 2
    pk = ZonePickPanel(p)
    pk.cursor = 1
    assert pk.key("enter") == ("done", ZONES[A.PROGRESSION[1]])   # the picked zone
    assert ZonePickPanel(p).key("escape") == ("done", None)   # back out of Adventure


def test_a_panel_boss_win_records_progression(monkeypatch):
    # monkeypatch, not bare assignment: the old direct writes leaked zeroed
    # chances into every later test (pollution fix 2026-07-21)
    monkeypatch.setattr(A, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(A, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(A, "FIND_CHANCE", 0.0)
    p = _champ()
    pan = AdventurePanel(p, zone=ZONES[A.PROGRESSION[0]])   # the road's frontier
    for _ in range(TELE_LEAVE_T + TELE_ARRIVE_T + pan.adv.total * TRAVEL_TICKS + 20):
        pan.anim()
        if pan._town_prompt:
            pan.key("space")
        if pan._fighting_boss:
            break
    pan.sub = None
    pan._battle_done(_Win())
    assert p.adv_progress == 1
    assert "New ground opens" in pan._home_msg


def test_adv_progress_survives_a_save_round_trip():
    p = _champ()
    p.adv_progress = 7
    d = persistence.to_save_dict(p)
    assert d["adv_progress"] == 7
    q, _ = persistence.pet_from_save(d, catch_up=False)
    assert q.adv_progress == 7


def test_an_old_save_without_the_field_defaults_to_zero():
    p = _champ()
    d = persistence.to_save_dict(p)
    d.pop("adv_progress", None)                      # a pre-rebuild save
    q, _ = persistence.pet_from_save(d, catch_up=False)
    assert q.adv_progress == 0                       # a safe default, not a crash


def test_the_home_card_shows_live_quest_progress():
    """The card names the FRONTIER zone (Joel 2026-07-21) alongside the live
    count: dim '▸ name' before the first run, 'N/26 ▸ name' partway, the
    cleared star at the end.  The name shortens to the gate BOSS when the
    full name overflows the 26-col stats column."""
    from tuipet import statusbox
    p = _champ()
    line = statusbox.adventure_line(p)
    first = ZONES[A.PROGRESSION[0]]["name"]
    assert "▸" in line and (first in line or first.split("'s ", 1)[0] in line)
    p.adv_progress = 5
    line = statusbox.adventure_line(p)
    assert f"5/{len(ZONES)}" in line                           # partway, count kept
    sixth = ZONES[A.PROGRESSION[5]]["name"]
    assert sixth in line or sixth.split("'s ", 1)[0][:11] in line
    p.adv_progress = len(ZONES)
    assert "cleared" in statusbox.adventure_line(p)            # all done
    # and it rides the home card (single-source, liveness rule)
    assert any("Quest" in line for line in statusbox.home_lines(p))
    # the line never overflows the 26-col stats panel, any frontier
    from rich.text import Text
    for prog in range(len(ZONES)):
        p.adv_progress = prog
        vis = len(Text.from_markup(statusbox.adventure_line(p)).plain)
        assert vis <= 26, (prog, statusbox.adventure_line(p))


def test_the_road_runs_in_difficulty_order():
    """Option b (balance audit 2026-07-21): the unlock ROAD is sorted by the
    rosters' measured difficulty key -- every zone exactly once, the key
    never decreasing, the all-Mega den (Dexmon) dead last -- while zone
    IDENTITY (indices, bests, maps) stays untouched."""
    road = A.PROGRESSION
    assert sorted(road) == list(range(len(ZONES)))   # a permutation, nothing lost
    keys = [A._difficulty(ZONES[i]) for i in road]
    assert keys == sorted(keys)                      # monotonic: no cliffs mid-road
    assert ZONES[road[-1]]["name"].startswith("Dexmon")   # the Mega den caps it
    # the old zones.csv order had Mega wilds at its 4th stop; the road's first
    # QUARTER now carries no Mega wilds at all
    for zi in road[:len(road) // 4]:
        stages = {e.get("stage") for e in ZONES[zi]["randoms"]}
        assert "Mega" not in stages, ZONES[zi]["name"]
