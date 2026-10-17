"""Approved animation budgets and skips must leave game decisions untouched."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from tuipet import adventure, battlescreen, dnascreen, tournament
from tuipet.adventurescreen import AdventurePanel
from tuipet.battlescreen import BattlePanel, boss_death_timeline, round_timeline
from tuipet.lobbybout import BoutMixin
from tuipet.lobbyscreen import LobbyPanel
from tuipet.pet import Pet
from tuipet.raidscreen import RaidPanel
from tuipet.tournamentscreen import TournamentPanel


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500,
               energy=100, bits=10000)


def _road(pet=None, zone=None):
    return AdventurePanel(pet or _pet(), zone=zone or adventure.ZONES[0])


def _cup():
    pet = _pet()
    panel = TournamentPanel(pet)
    tid = tournament.schedule(pet)[tournament._hour(pet)]
    panel.tourney = tournament.Tournament(pet, tournament.trophy_by_id(tid))
    panel.phase, panel.tree_view = "bracket", True
    return panel


@pytest.mark.parametrize("dealt,taken", [(1, 1), (1, 0), (0, 1), (0, 0)])
@pytest.mark.parametrize("first", [True, False])
def test_full_round_keeps_original_duration_without_changing_hp(dealt, taken, first):
    # Joel reversed speed changes 2026-10-14; only passive skips remain approved.
    timeline = round_timeline(5, 5, dealt, taken, first)
    assert len(timeline) == 103 + 7 * (bool(dealt) + bool(taken))
    assert (timeline[-1]["ph"], timeline[-1]["fh"]) == (5 - taken, 5 - dealt)
    assert sum(f["m"] == "faceoff" for f in timeline) == 9
    assert sum(f["m"] == "windup" for f in timeline) == 18
    assert sum(f["m"] == "fire_out" for f in timeline) == 24
    assert sum(f["m"] == "fire_in" for f in timeline) == 24


def test_boss_ko_keeps_original_forty_ticks_and_all_stages():
    timeline = boss_death_timeline(3)
    assert len(timeline) == 40
    assert sum(f["stage"] == "on" for f in timeline) == 12
    assert [f["keep"] for f in timeline if f["stage"] == "squash"] == [8] * 6 + [4] * 6 + [2] * 6
    assert all((f["ph"], f["fh"]) == (3, 0) for f in timeline)


def test_original_dodge_turns_away_and_lands_facing_the_foe(monkeypatch):
    panel = BattlePanel(_pet())
    facing = []
    original = panel._place_one

    def place(view, rows, xshift=0, turn=False):
        facing.append(turn)
        return original(view, rows, xshift, turn=turn)

    monkeypatch.setattr(panel, "_place_one", place)
    dodge = [f for f in round_timeline(5, 5, 0, 1, True) if f["m"] == "dodge"]
    assert len(dodge) == 14
    for frame in dodge:
        assert panel._render_scene_frame(frame) is not None
    assert facing == [True] * 9 + [False] * 5


@pytest.mark.parametrize("options", [{}, {"wild": True}, {"raid": True}, {"duel": True}])
def test_battle_first_and_repeat_intro_both_play_full_length(options):
    pet = _pet()
    first = BattlePanel(pet, **options)
    assert len(first.timeline) == 36
    repeat = BattlePanel(_pet(), **options)
    assert len(repeat.timeline) == 36
    # Check elapsed clocks as well as frame arrays; repetition never shortens them.
    for panel, ticks in ((first, 36), (repeat, 36)):
        for _ in range(ticks - 1):
            panel.anim()
        assert panel.phase == "intro"
        panel.anim()
        assert panel.phase == "ready" and panel.locked is None


@pytest.mark.parametrize("key", ["space", "enter", "escape", "x"])
def test_intro_skip_never_locks_flees_or_builds_a_battle(key):
    pet = _pet()
    panel = BattlePanel(pet)
    before = deepcopy(pet.__dict__)
    assert panel.key(key) is None
    assert panel.phase == "ready" and panel.battle is None
    assert panel.locked is None and not panel.ran_away
    assert pet.__dict__ == before
    # A same-frame second lock press is still protected by the original arm timer.
    panel.key("space")
    assert panel.locked is None


def test_cup_battle_starts_at_bar_and_preserves_full_generic_intro():
    panel = BattlePanel(_pet(), skip_intro=True)
    assert panel.phase == "ready"
    assert len(BattlePanel(_pet()).timeline) == 36
    assert battlescreen.LOCK_ARM_T == 5 and battlescreen.SKIP_DEBOUNCE == 6
    assert battlescreen.DUEL_AUTOLOCK_T == 300


@pytest.mark.parametrize("key", ["space", "enter", "escape", "z"])
def test_duel_intro_skip_is_not_a_commit_or_forfeit(key):
    show = BattlePanel(_pet(), duel=True)
    panel = SimpleNamespace(bshow=show, bphase="lock", bt_my_commit_sent=False)
    panel._forfeit = lambda: pytest.fail("skip forfeited")
    panel._commit_lock = lambda grade: pytest.fail("skip chose a grade")
    assert BoutMixin._key_battle(panel, key) is None
    assert show.phase == "ready" and show.locked is None


def test_duel_fight_still_labels_and_applies_forfeit():
    show = BattlePanel(_pet(), duel=True)
    show.phase = "anim"
    panel = SimpleNamespace(bshow=show, bphase="fight")
    calls = []
    panel._forfeit = lambda: calls.append("forfeit")
    assert "forfeit" in show.strip()
    BoutMixin._key_battle(panel, "escape")
    assert calls == ["forfeit"]


def test_entry_repeat_and_homecoming_keep_full_teleport():
    first, repeat = _road(), _road()
    for panel, ticks in ((first, 96), (repeat, 96)):
        for _ in range(ticks - 1):
            panel.anim()
        assert panel._trans is not None and not getattr(panel.pet, "away", False)
        panel.anim()
        assert panel._trans is None and panel.pet.away
        panel._summary_shown = True
        panel._go_home()
        for _ in range(95):
            panel.anim()
        assert panel.auto_close is None
        panel.anim()
        assert panel.auto_close == ("done", panel._home_msg)
        assert not panel.pet.away


@pytest.mark.parametrize("key", ["space", "enter", "escape", "t", "z"])
def test_teleport_skip_only_lands_and_home_skip_only_closes(key):
    panel = _road()
    before = (panel.adv.loc, panel.pet.energy, deepcopy(panel.pet.inventory))
    assert panel.key(key) is None
    assert panel._trans is None and panel.travelling and panel.pet.away
    assert (panel.adv.loc, panel.pet.energy, panel.pet.inventory) == before
    panel._summary_shown = True
    panel._go_home()
    assert panel.key(key) is None
    assert panel.auto_close == ("done", panel._home_msg)
    assert not panel.pet.away
    panel._finish_teleport()  # completion is idempotent
    assert (panel.adv.loc, panel.pet.energy, panel.pet.inventory) == before


def _dig(panel):
    panel.key("z")  # entry skip
    panel._find = panel.adv.zone["find_keys"][0]
    panel._dig()


def test_dig_timeout_keeps_original_fixed_show_and_full_meter():
    panel = _road()
    _dig(panel)
    for _ in range(101):
        panel.anim()
    assert panel._scene is not None
    panel.anim()
    assert panel._scene is None
    from tuipet.adventurescreen import DIG_METER_T, INV_END_T
    assert (DIG_METER_T, INV_END_T) == (48, 54)


@pytest.mark.parametrize("key", ["escape", "space", "enter", "t", "z"])
def test_dig_skip_after_lock_keeps_grade_reward_and_road_position(key):
    panel = _road()
    _dig(panel)
    from tuipet.adventurescreen import INV_WALK_T
    for _ in range(INV_WALK_T):
        panel.anim()
    panel._scene["meter"]["bar"] = 12
    panel._scene["meter"]["hist"] = [12]
    panel.key("space")
    scene = panel._scene
    assert scene["grade"] == "mega" and "meter" not in scene
    before = (deepcopy(panel.pet.inventory), panel.pet.bits, panel.adv.loc, panel.adv.finds)
    panel.key(key)
    assert panel._scene is None and scene["grade"] == "mega"
    assert (panel.pet.inventory, panel.pet.bits, panel.adv.loc, panel.adv.finds) == before
    assert panel._note == panel._find_msg


def test_dig_escape_cannot_skip_or_grade_a_live_meter():
    from tuipet.adventurescreen import INV_WALK_T
    panel = _road()
    _dig(panel)
    for _ in range(INV_WALK_T):
        panel.anim()
    panel.key("escape")
    assert panel._scene is not None and panel._scene["grade"] is None
    assert panel._scene["meter"]["left"] == 48


def test_skipping_an_already_revealed_dig_does_not_repeat_the_reward_chime():
    from tuipet.adventurescreen import INV_WALK_T, INV_REVEAL_T
    panel = _road()
    _dig(panel)
    for _ in range(INV_WALK_T):
        panel.anim()
    panel.key("space")
    for _ in range(INV_REVEAL_T - INV_WALK_T):
        panel.anim()
    assert panel.sfx == "reward"
    panel.sfx = None  # the app drained this frame's sound
    panel.key("escape")
    assert panel._scene is None and panel.sfx is None


def test_hazard_windows_and_verdict_keep_original_durations():
    from tuipet.adventurescreen import HZ_TELE_T, HZ_LUNGE_T, HZ_END_T, REFUSE_T
    assert (HZ_TELE_T, HZ_LUNGE_T, HZ_END_T, REFUSE_T) == (8, 8, 10, 24)
    panel = _road()
    panel.key("z")
    panel._hazard = {"t": 0, "dodged": False, "hit": False}
    for _ in range(8):
        panel._hazard_tick()
    panel.key("space")
    assert panel._hazard["dodged"]
    energy = panel.pet.energy
    for _ in range(17):
        panel._hazard_tick()
    assert panel._hazard is not None
    panel._hazard_tick()
    assert panel._hazard is None and panel.pet.energy == energy


def _clear(panel):
    panel.key("z")
    panel._fighting_boss = True
    panel._fighting_enemy = panel.adv.boss
    panel._battle_done(SimpleNamespace(won=True))


def test_map_clear_first_and_repeat_both_keep_full_duration():
    first, repeat, other = _road(), _road(), _road(zone=adventure.ZONES[1])
    for panel, ticks in ((first, 54), (repeat, 54), (other, 54)):
        _clear(panel)
        assert panel._pulse["ticks"] == ticks
        before = (panel.pet.bits, deepcopy(panel.pet.inventory), panel.pet.adv_progress)
        for _ in range(ticks - 1):
            panel.anim()
        assert panel._pulse is not None
        panel.anim()
        assert panel._pulse is None and panel._summary
        assert (panel.pet.bits, panel.pet.inventory, panel.pet.adv_progress) == before


def test_pulse_and_final_parade_skips_land_on_summary_without_double_reward():
    panel = _road()
    _clear(panel)
    panel._pulse["parade"] = [100, 100, 100]
    panel._pulse["msg"] = adventure.FINAL_PARADE_MSG
    before = (panel.pet.bits, deepcopy(panel.pet.inventory), panel.pet.adv_progress)
    panel.key("escape")
    assert panel._pulse is None and panel._parade is not None
    assert not panel._summary
    panel.key("space")
    assert panel._parade is None and panel._summary and panel._trans is None
    assert adventure.FINAL_PARADE_MSG in panel.text().plain
    assert (panel.pet.bits, panel.pet.inventory, panel.pet.adv_progress) == before


def test_final_parade_keeps_forty_ticks_per_boss():
    panel = _road()
    panel.key("z")
    panel._parade = {"t": 0, "nums": [100] * 3, "msg": "ending"}
    for _ in range(119):
        panel.anim()
    assert panel._parade is not None
    panel.anim()
    assert panel._parade is None


def test_cup_first_repeat_walkin_full_duration_and_skip_consumption():
    first, repeat = _cup(), _cup()
    for panel, ticks in ((first, 38), (repeat, 38)):
        panel.key("space")
        for _ in range(ticks - 1):
            panel.anim()
        assert panel._intro is not None
        panel.anim()
        assert panel._intro is None and panel.sub.phase == "ready"
    panel = _cup()
    panel.key("space")
    assert panel.key("escape") is None
    assert panel.sub.phase == "ready" and panel.sub.locked is None
    assert not panel.tourney.over


@pytest.mark.parametrize("show", ["_advance", "_ceremony"])
@pytest.mark.parametrize("key", ["escape", "space", "enter", "z"])
def test_cup_show_skip_only_returns_to_bracket(show, key):
    panel = _cup()
    setattr(panel, show, {"t": 0, "nums": [100, 100, 100]})
    before = deepcopy(panel.pet.__dict__)
    assert panel.key(key) is None
    assert getattr(panel, show) is None and panel.tree_view and panel.sub is None
    assert not panel.tourney.over and panel.pet.__dict__ == before


def test_cup_npc_and_repeat_podium_keep_original_durations():
    panel = _cup()
    panel._advance = {"t": 0, "nums": [100] * 3}
    for _ in range(59):
        panel.anim()
    assert panel._advance is not None
    panel.anim()
    assert panel._advance is None
    # Complete two real brackets; rewards occur before the podium, never on skip.
    for ticks in (40, 40):
        panel = _cup()
        for _ in range(3):
            panel._advance = None
            panel.sub = SimpleNamespace(key=lambda k: ("done", SimpleNamespace(won=True)))
            panel.key("space")
        assert panel.tourney.champion and panel._ceremony["ticks"] == ticks
        for _ in range(ticks - 1):
            panel.anim()
        assert panel._ceremony is not None
        panel.anim()
        assert panel._ceremony is None


def _raid():
    state = SimpleNamespace(me_id=1, login_failed=None, error=None)
    client = SimpleNamespace(state=state, raid={}, last_hit=None, raid_reward=None,
                             raid_get=lambda: None, raid_ack=lambda rid: None)
    return RaidPanel(_pet(), lambda *args: client, client=client)


def test_raid_fall_and_reward_keep_original_durations():
    panel = _raid()
    panel._pool_seen = (1, 100, 1000, "boss", 100)
    panel.client.raid = {"now": 2, "boss": {"start": 2, "hp": 100, "num": 100}}
    panel.anim()
    assert panel._fell[2] == panel.frame_i + 40
    for _ in range(39):
        panel.anim()
    assert panel._fell is not None
    panel.anim()
    assert panel._fell is None
    panel._apply_reward({"ok": True, "id": "anim-raid", "items": [], "defeated": False, "bits": 100})
    for _ in range(119):
        panel.anim()
    assert panel._won is not None
    panel.anim()
    assert panel._won is None


@pytest.mark.parametrize("key", ["escape", "space", "enter", "c", "z"])
def test_raid_reward_skip_never_claims_or_starts_or_leaves(key):
    panel = _raid()
    panel._apply_reward({"ok": True, "id": "anim-raid", "items": [], "defeated": False, "bits": 100})
    panel.client.raid_claim = lambda *args: pytest.fail("skip claimed reward")
    before = (panel.pet.bits, panel.pet.battles, panel.pet.energy)
    assert panel.key(key) is None
    assert panel._won is None and panel.sub is None
    assert (panel.pet.bits, panel.pet.battles, panel.pet.energy) == before


def test_ladder_podium_expires_after_original_120_tick_hold():
    panel = LobbyPanel.__new__(LobbyPanel)
    panel.client = None
    panel.bshow = panel.jshow = None
    panel.pshow = {"t": 0, "line": "paid"}
    panel.phase = "login"
    panel.entry = None
    # The clock also checks the relay state; no connection means no events.
    panel.state = None
    for _ in range(120):
        panel.anim()
    assert panel.pshow is not None
    panel.anim()
    assert panel.pshow is None


def test_dna_result_holds_readable_text_after_initial_blink():
    panel = dnascreen.DNAPanel(_pet())
    panel.phase = "result"
    panel.won = ("Dragon'sRoar", 1, 1, 1, 0)
    panel.blink = 6
    assert "Got" not in panel._text_result().plain
    for tick in range(8, 24):
        panel.blink = tick
        assert "Got" in panel._text_result().plain
    assert dnascreen.MASH_TICKS == 100
