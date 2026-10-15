"""Regression probes for the battle audit 2026-10-14 (no async/network)."""
from types import SimpleNamespace

import pytest

from tuipet import battle, data, tournament
from tuipet.lobbybout import _clamp_card
from tuipet.pet import Pet, DAY_LENGTH
from tuipet.raidscreen import RaidPanel
from tuipet.tournamentscreen import TournamentPanel


def cup():
    return dict(data.load_tournies()[0], id=12345, season="Summer",
                field_req="", attr_req="", age_limit="Rookie",
                enemy_stage="", enemy_attr="", enemy_field="",
                prelim=0, same_day_retry=True, bit_mod=1.0)


def pet():
    num = next(n for n, r in data.load_sprites()[1].items()
               if r["stage"] == "Rookie" and not data.is_placeholder(n))
    p = Pet.from_num(num)
    p.bits = 10000
    p.energy = p.max_energy
    return p


def raid_server(monkeypatch, tmp_path):
    import server
    monkeypatch.setattr(server, "RAID_PATH", str(tmp_path / "raid.json"))
    monkeypatch.setattr(server, "RAID", {"boss": None, "board": {},
                                       "history": [], "claimed": {}, "attempts": {}})
    server._raid_rotate(now=1000)
    return server


def test_zero_damage_volley_reports_and_spends_attempt(monkeypatch, tmp_path):
    srv = raid_server(monkeypatch, tmp_path)
    p = pet()
    calls = []
    client = SimpleNamespace(raid=srv._raid_view("joel", now=1001))

    def hit(raw):
        calls.append(raw)
        srv._raid_hit("joel", raw, p.num, now=1001)

    client.raid_hit = hit
    panel = RaidPanel(p, None, client=client)
    before = p.energy
    panel._report(SimpleNamespace(dealt=0, won=False))
    assert calls == [0]
    assert srv._raid_attempts("joel", now=1001)["left"] == 2
    assert p.energy == before - 5 and p.battles == 0


def test_thrown_raid_reports_while_view_is_in_flight():
    calls = []
    panel = RaidPanel(pet(), None, client=SimpleNamespace(
        raid=None, raid_hit=lambda raw: calls.append(raw)))
    panel._report(SimpleNamespace(dealt=3, won=True))
    assert calls == [3]


def test_zero_damage_ack_is_not_described_as_refusal():
    client = SimpleNamespace(raid=None, last_hit={"ok": True, "dealt": 0},
                             state=SimpleNamespace(me_id=None, login_failed=None, error=None))
    panel = RaidPanel(pet(), None, client=client)
    panel.anim()
    assert "attempt spent" in panel.msg and "refused" not in panel.msg


def test_zero_damage_is_not_a_reward_contribution(monkeypatch, tmp_path):
    srv = raid_server(monkeypatch, tmp_path)
    srv._raid_hit("whiff", 0, None, now=1001)
    assert srv._raid_attempts("whiff", now=1001)["left"] == 2
    # Also cover a zero row in an old archived save.
    srv.RAID["board"]["old_whiff"] = {"damage": 0, "ts": 1001}
    srv.RAID["boss"]["hp"] = 1
    srv._raid_hit("winner", 1, None, now=1002)
    assert srv._raid_award("whiff") is None
    assert srv._raid_award("old_whiff") is None
    assert srv._raid_award("winner")["rank"] == 1


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_duel_card_is_clamped(value):
    card = _clamp_card({"num": 0, "strength": value, "battles": value})
    assert card["strength"] == 4 and card["battles"] == 0


def test_nonfinite_raid_damage_does_not_crash(monkeypatch, tmp_path):
    srv = raid_server(monkeypatch, tmp_path)
    response = srv._raid_hit("joel", float("inf"), None, now=1001)
    assert response["ok"] and response["dealt"] == 0
    assert srv._raid_attempts("joel", now=1001)["left"] == 2


def test_cup_key_refreshes_schedule_before_entry(monkeypatch):
    old, new = cup(), dict(cup(), id=12346)
    monkeypatch.setattr(data, "load_tournies", lambda: [old, new])
    monkeypatch.setattr(tournament, "_rand_trophy_ids", lambda p: [old["id"]] * 24)
    p = pet()
    panel = TournamentPanel(p)
    p.fought_hours = [0]
    p.world_seconds += DAY_LENGTH
    monkeypatch.setattr(tournament, "_rand_trophy_ids", lambda p: [new["id"]] * 24)
    panel.key("enter")  # no text() refresh between rollover and input
    assert panel.tourney is not None
    assert panel.tourney.trophy["id"] == new["id"]
    assert p.fought_hours == [0]


def test_next_winnable_does_not_advertise_unaffordable_cup(monkeypatch):
    t = cup()
    monkeypatch.setattr(data, "load_tournies", lambda: [t])
    monkeypatch.setattr(tournament, "_rand_trophy_ids", lambda p: [t["id"]] * 24)
    p = pet()
    p.bits = 0
    assert tournament.next_winnable(p) is None


def test_cup_preview_includes_title_defense_purse(monkeypatch):
    t = cup()
    monkeypatch.setattr(data, "load_tournies", lambda: [t])
    monkeypatch.setattr(tournament, "_rand_trophy_ids", lambda p: [t["id"]] * 24)
    p = pet()
    p.trophies_won = {t["id"]: "day 1"}
    panel = TournamentPanel(p)
    text = panel.text().plain
    tm = tournament.Tournament(p, t)
    assert tm._calc_bits() == 1312
    assert "purse ~1312b" in text


def test_mega_bracket_preview_uses_mega_pet_payout(monkeypatch):
    t = dict(cup(), age_limit="Mega", bit_mod=1.1)
    monkeypatch.setattr(data, "load_tournies", lambda: [t])
    monkeypatch.setattr(tournament, "_rand_trophy_ids", lambda p: [t["id"]] * 24)
    num = next(n for n, r in data.load_sprites()[1].items()
               if r["stage"] == "Mega" and not data.is_placeholder(n))
    p = Pet.from_num(num)
    p.bits = 10000
    text = TournamentPanel(p).text().plain
    tm = tournament.Tournament(p, t)
    assert tm.stake == 385 and tm._calc_bits() == 1729
    assert "purse ~1729b" in text


def test_battle_readme_matches_progression_and_training():
    from pathlib import Path
    text = Path("README.md").read_text(encoding="utf-8")
    assert "adventure, raids and\ncups feed the same record" not in text
    assert "drilled attribute power grow with clean rounds" not in text


def test_help_describes_live_battle_lock():
    from tuipet.helpscreen import HELP
    text = "\n".join(line for line, _style in HELP)
    assert "locks the power form your lobby" not in text
    assert "battles lock their own bar" in text


def test_battle_module_documents_the_approved_miss_damage():
    assert "miss: 20%" not in battle.__doc__
    assert "normal/miss: 50%" in battle.__doc__


def test_raid_calendar_text_describes_end_day_bonus(monkeypatch):
    panel = RaidPanel(pet(), None, client=SimpleNamespace(raid={
        "boss": {"start": 0, "hp": 1, "end": 864000}, "now": 3 * 86400}))
    panel.frame_i = 40
    text = panel._context_line(panel.view, panel._boss())
    assert "weekend claims pay" not in text
    assert "weekend finishes pay 1.5x" in text


def test_initiative_is_a_coin_and_even_bouts_are_even():
    """Battle call #20 = A (Joel 2026-10-15): the first striker won ~56% of
    even bouts and home fights always handed it to the player."""
    import random as _r
    from tuipet import battle
    rng = _r.Random(7)

    def share(first_of):
        won = lost = 0
        for _ in range(4000):
            _seq, mh, fh = battle.generate(battle.Side.wild(29), battle.Side.wild(29),
                                           rng=rng.random, me_first=first_of())
            won += mh > fh
            lost += fh > mh
        return won / (won + lost)
    assert share(lambda: True) > 0.53                 # the edge is real...
    assert abs(share(lambda: rng.random() < 0.5) - 0.5) < 0.03   # ...the coin evens it


def test_a_side_felled_by_the_first_volley_never_fires_back():
    from tuipet import battle

    class _S:
        def __init__(self):
            self.hit_type = "mega"
        def hit_chance(self, other):
            return 1.0
        def roll_damage(self, rng):
            return 5
    seq, mh, fh = battle.generate(_S(), _S(), rng=lambda: 0.0, me_first=False)
    assert seq == [(False, 5, True, 5)] and mh == 0 and fh == 5
    seq, mh, fh = battle.generate(_S(), _S(), rng=lambda: 0.0, me_first=True)
    assert seq == [(True, 5, False, 5)] and mh == 5 and fh == 0


def test_a_home_battle_rolls_initiative():
    from tuipet import battle
    from tuipet.pet import Pet
    seen = set()
    for s in range(40):
        import random as _r
        b = battle.Battle(Pet(num=29, stage="Rookie", attribute="Vaccine"),
                          rng=_r.Random(s).random)
        seen.add(b.player_first)
    assert seen == {True, False}


def test_powers_and_trained_hp_fight_now():
    """Battle call #21 = B (Joel 2026-10-15): power vs the FOE's attribute
    adds hit (+0.2%/pt, cap +5%); trained HP 20+ fights with +1 HP."""
    from tuipet.pet import Pet
    p = Pet(num=29, stage="Rookie", attribute="Vaccine")
    foe = battle.Side.wild(29)
    base = battle.Side.of_pet(p).hit_chance(foe)
    setattr(p, {"Vaccine": "vaccine", "Data": "data_power", "Virus": "virus"}[foe.attribute], 10)
    assert abs(battle.Side.of_pet(p).hit_chance(foe) - base - 0.02) < 1e-9
    setattr(p, {"Vaccine": "vaccine", "Data": "data_power", "Virus": "virus"}[foe.attribute], 500)
    assert abs(battle.Side.of_pet(p).hit_chance(foe) - base - 0.05) < 1e-9   # capped
    assert battle.Side.of_pet(p).hp == 5
    p.full_health = 20
    b = battle.Battle(p)
    assert b.pet_hp == b.pet_max == 6 and b.enemy_max == 5


def test_a_forged_card_cannot_claim_more_hp_or_power_than_the_game_awards():
    card = _clamp_card({"num": 29, "hp": 99, "powers": {"Virus": 10 ** 6, "Data": -4}})
    assert card["hp"] == 6
    assert card["powers"] == {"Vaccine": 0, "Data": 0, "Virus": 25}
    side = battle.Side.of_card(card)
    assert side.hp == 6 and side.power_edge(battle.Side.wild(29)) <= battle.POWER_HIT_CAP
    old = _clamp_card({"num": 29})                  # a pre-0.6.20 peer: no bonus
    assert old["hp"] == 5 and not any(old["powers"].values())
