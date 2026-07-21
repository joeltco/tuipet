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
    assert unlocked_indices(p) == [0] and frontier(p) == 0
    assert pick_zone(p) is ZONES[0]                 # the frontier is the default embark


def test_felling_the_frontier_boss_unlocks_the_next_only():
    p = _champ()
    assert record_win(p, ZONES[0]) is True and p.adv_progress == 1
    assert unlocked_indices(p) == [0, 1]
    assert is_conquered(p, 0) and not is_conquered(p, 1)
    # replaying a conquered zone advances nothing
    assert record_win(p, ZONES[0]) is False and p.adv_progress == 1
    # you cannot skip: "beating" a still-locked zone is not the frontier
    assert record_win(p, ZONES[5]) is False and p.adv_progress == 1


def test_progress_never_runs_past_the_last_zone():
    p = _champ()
    p.adv_progress = len(ZONES)                     # all conquered
    assert frontier(p) == len(ZONES) - 1            # clamped for indexing
    assert unlocked_indices(p) == list(range(len(ZONES)))
    assert record_win(p, ZONES[-1]) is False        # nothing left to unlock


def test_the_picker_lists_unlocked_zones_and_defaults_to_the_frontier():
    p = _champ()
    p.adv_progress = 3
    pk = ZonePickPanel(p)
    assert pk.indices == [0, 1, 2, 3]               # only unlocked
    assert pk.indices[pk.cursor] == 3               # cursor on the frontier
    # marks: conquered ✓, frontier ★
    assert pk._fmt(0, 0).startswith("✓")
    assert pk._fmt(3, 3).startswith("★")


def test_the_picker_embarks_on_enter_and_backs_out_on_esc():
    p = _champ()
    p.adv_progress = 2
    pk = ZonePickPanel(p)
    pk.cursor = 1
    assert pk.key("enter") == ("done", ZONES[1])    # embark on the picked zone
    assert ZonePickPanel(p).key("escape") == ("done", None)   # back out of Adventure


def test_a_panel_boss_win_records_progression():
    A.ENCOUNTER_CHANCE = 0.0
    A.FIND_CHANCE = 0.0
    p = _champ()
    pan = AdventurePanel(p, zone=ZONES[0])
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
    from tuipet import statusbox
    p = _champ()
    assert "not begun" in statusbox.adventure_line(p)          # before the first run
    p.adv_progress = 5
    assert f"5/{len(ZONES)}" in statusbox.adventure_line(p)    # partway
    p.adv_progress = len(ZONES)
    assert "cleared" in statusbox.adventure_line(p)            # all done
    # and it rides the home card (single-source, liveness rule)
    assert any("Quest" in line for line in statusbox.home_lines(p))
