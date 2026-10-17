"""Approved October cup fixes: entry, durability, availability and terms."""
import datetime
import json

import pytest
from rich.cells import cell_len

from tuipet import data, persistence, tournament as T
from tuipet.pet import Pet, DAY_LENGTH
from tuipet.tournamentscreen import TournamentPanel


def pet():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500,
            bits=100_000)
    p.energy = p.max_energy
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    return p


def cup(p):
    return next(t for t in data.load_tournies() if T._eligibility_rest(p, t) is None)


@pytest.mark.parametrize("energy", [10, 15, 19, 20])
def test_three_bout_energy(monkeypatch, energy):
    p = pet()
    p.energy = energy
    monkeypatch.setattr(T, "festival", lambda: True)
    err = T.eligibility_at(p, cup(p), 0)
    assert (err is None) == (energy >= 20)
    if err:
        assert "20 energy" in err


def test_entry_checkpoint_and_reload_no_second_stake():
    p = pet()
    T.schedule(p)
    tr = cup(p)
    before = p.bits
    T.Tournament(p, tr, featured=True)
    q, _ = persistence.load()
    assert q.bits == before - T.entry_fee(p, tr)
    assert T.featured_done(q)
    panel = TournamentPanel(q)
    panel.key("f")
    panel.key("y")
    assert panel.tourney is None and q.bits == p.bits


def test_verdict_atomic_progress_and_idempotency(monkeypatch):
    p = pet()
    t = T.Tournament(p, cup(p))
    t.record(True)
    t.record(True)
    real_merge = persistence.merge_progress

    def interrupted(_):
        raise OSError("interrupted settings projection")

    monkeypatch.setattr(persistence, "merge_progress", interrupted)
    with pytest.raises(OSError):
        t.record(True)
    with open(persistence.SAVE_PATH, encoding="utf-8") as f:
        payload = json.load(f)
    assert payload["bits"] == p.bits and payload["inventory"] == p.inventory
    assert payload["trophies"] == 1
    assert t.trophy["id"] in payload["progress"]["tourneys"]
    monkeypatch.setattr(persistence, "merge_progress", real_merge)
    q, _ = persistence.load()
    assert t.trophy["id"] in persistence.get_progress()["tourneys"]
    old = p.bits
    t.record(True)
    assert p.bits == old and q.trophies == 1
    assert T.eligibility_at(q, t.trophy, 0)


def test_festival_next_hint_includes_earlier_slot_and_body(monkeypatch):
    p = pet()
    p.world_seconds = DAY_LENGTH * 23.5 / 24
    T.schedule(p)
    p.tourney_schedule = [cup(p)["id"]] * 24
    p.fought_hours = list(range(1, 24))
    monkeypatch.setattr(T, "festival", lambda: True)
    assert T.next_winnable(p)[0] == 0
    p.injured = True
    assert T.next_winnable(p) is None


def test_rival_must_belong_to_filtered_pool(monkeypatch):
    p = pet()
    tr = cup(p)
    pool = T._eligible_forms(p, tr)
    rival = next(r for r in data.load_sprites()[1].values()
                 if r["stage"] == pool[0]["stage"] and r["num"] != pool[0]["num"]
                 and not data.is_placeholder(r["num"]))
    monkeypatch.setattr(T, "_eligible_forms", lambda *_: [pool[0]])
    p.rival_num = rival["num"]
    t = T.Tournament(p, tr)
    assert not t.rival_in
    assert all(e["num"] == pool[0]["num"] for e in t.entrants)


def test_bracket_cell_width_all_rounds():
    p = pet()
    p.name = "龍" * 10
    panel = TournamentPanel(p)
    t = panel.tourney = T.Tournament(p, cup(p))
    panel.phase, panel.tree_view = "bracket", True
    for _ in range(4):
        assert max(map(cell_len, panel._render_tree().plain.splitlines())) <= 40
        if not t.over:
            t.record(True)


def test_featured_restrictions_prereqs_and_date_determinism():
    p = pet()
    for offset in range(365):
        day = datetime.date(2026, 1, 1) + datetime.timedelta(days=offset)
        tr = T.featured_now(p, day)
        assert tr == T.featured_now(p, day)
        assert T._eligibility_rest(p, tr) is None
        assert tr["season"] == T.real_season(day)


def test_terms_featured_confirmation_and_lcd(monkeypatch):
    p = pet()
    panel = TournamentPanel(p)
    tr = dict(cup(p), age_limit="Mega", enemy_stage="Mega")
    monkeypatch.setattr(T, "featured_now", lambda _: tr)
    before = p.bits
    panel.key("f")
    assert panel.tourney is None and p.bits == before
    terms = "\n".join(panel.detail_lines(tr))
    for word in ("Mega", "WARNING", "Rules", "Stake", "Loss Q/S/F", "Prize", "20 energy", "Reload"):
        assert word in terms
    rows = panel.text().plain.splitlines()
    assert len(rows) <= 12 and max(map(cell_len, rows)) <= 40
    panel.key("enter")
    assert p.bits == before
    panel.key("y")
    assert panel.tourney is not None
    panel.key("y")
    assert p.bits == before - T.entry_fee(p, tr)


def test_selected_price_tags_and_egg_paths(monkeypatch):
    p = pet()
    panel = TournamentPanel(p)
    tr = cup(p)
    p.tourney_schedule = [tr["id"]] * 24
    panel.sched = p.tourney_schedule
    panel.cursor = 1
    monkeypatch.setattr(T, "festival", lambda: False)
    text = panel.text().plain
    assert "CURRENT" in text and "CLOSED" in text
    assert "stake %db" % T.entry_fee(p, tr) in text
    p.fought_hours = [0]
    assert "RUN" in panel.text().plain
    p.fought_hours = []
    p.injured = True
    assert "BLOCKED" in panel.text().plain
    paths = "\n".join(panel.target_lines())
    assert "Summer #147" in paths and "Fall #188" in paths
    for tid in (146, 187):
        assert T.trophy_by_id(tid)["season"] in paths


def test_entry_write_failure_does_not_pay_or_unlock_bracket(monkeypatch):
    p = pet()
    panel = TournamentPanel(p)
    panel.key("f")
    before = p.bits

    def fail(*a, **kw):
        raise OSError("disk full")

    monkeypatch.setattr(persistence, "_atomic_write_json", fail)
    panel.key("y")
    assert panel.tourney is None and p.bits == before
    assert not T.featured_done(p)


def test_strict_commit_keeps_main_until_replace(monkeypatch):
    from tuipet import persistio
    p = pet()
    persistence.save(p)
    before = open(persistence.SAVE_PATH, encoding="utf-8").read()
    real_replace = persistio.os.replace

    def stop_commit(src, dst):
        if dst == persistence.SAVE_PATH:
            raise OSError("interrupted commit")
        return real_replace(src, dst)

    monkeypatch.setattr(persistio.os, "replace", stop_commit)
    p.bits += 100
    with pytest.raises(OSError):
        persistence.cup_checkpoint(p)
    assert open(persistence.SAVE_PATH, encoding="utf-8").read() == before


def test_old_save_and_sync_progress_remain_compatible():
    p = pet()
    persistence.save(p)
    q, _ = persistence.load()
    t = T.Tournament(q, cup(q), featured=True)
    for _ in range(3):
        t.record(True)
    wire = persistence.to_save_dict(q)
    persistence.save_settings({})
    persistence.write_save_dict(wire)
    r, _ = persistence.load()
    assert r.bits == q.bits and r.trophies_won == q.trophies_won
    assert t.trophy["id"] in persistence.get_progress()["tourneys"]
    assert T.featured_done(r)


def test_details_reject_changed_board(monkeypatch):
    p = pet()
    panel = TournamentPanel(p)
    panel.key("f")
    before = p.bits
    monkeypatch.setattr(T, "_today", lambda: datetime.date(2030, 1, 1))
    panel.key("y")
    assert panel.tourney is None and p.bits == before
    assert "Board changed" in panel.msg


def test_selected_price_changes_with_cursor_and_prerequisite_path(monkeypatch):
    p = pet()
    panel = TournamentPanel(p)
    a, b = dict(cup(p)), dict(cup(p))
    a["id"], b["id"] = 500, 501
    b["bit_mod"] = a["bit_mod"] + 1
    monkeypatch.setattr(T, "trophy_by_id", lambda tid: {500: a, 501: b}.get(tid))
    p.tourney_schedule = [500, 501] * 12
    panel.cursor = 1
    text = panel.text().plain
    assert "stake %db" % T.entry_fee(p, b) in text
    assert "stake %db" % T.entry_fee(p, a) not in text


@pytest.mark.parametrize("wins", [0, 1, 2])
def test_loss_verdict_is_durable(wins):
    p = pet()
    t = T.Tournament(p, cup(p), featured=True)
    for _ in range(wins):
        t.record(True)
    t.record(False)
    q, _ = persistence.load()
    assert q.bits == p.bits and q.trophies == 0
    assert q.featured_day == p.featured_day
    before = p.bits
    t.record(False)
    assert p.bits == before


def test_existing_trophy_save_repairs_split_progress():
    p = pet()
    p.trophies_won = {146: "day 1"}
    payload = persistence.to_save_dict(p)
    payload.pop("progress", None)  # old save with the historical split write
    persistence.write_save_dict(payload)
    q, _ = persistence.load()
    assert q.trophies_won == p.trophies_won
    assert 146 in persistence.get_progress()["tourneys"]


def test_authored_prizes_and_cross_season_prerequisites():
    p = pet()
    panel = TournamentPanel(p)
    prize = next(t for t in data.load_tournies() if t["item"] >= 0)
    key = T._prize_key("i", prize["item"])
    assert T.shop.entry(key)["name"] in "\n".join(panel.detail_lines(prize))
    food = next(t for t in data.load_tournies() if t["food_id"] >= 0 and t["food_amt"] > 0)
    key = T._prize_key("f", food["food_id"])
    assert "%s x%d" % (T.shop.entry(key)["name"], food["food_amt"]) in "\n".join(panel.detail_lines(food))
    path = panel.prerequisite_path(T.trophy_by_id(248))
    assert path == "Spring #15 > Summer #93 > Fall #171"
    assert "Prerequisites: none" in "\n".join(panel.target_lines())


@pytest.mark.parametrize("state", ["select", "detail", "bracket", "intro", "advance", "ceremony", "bout", "result"])
def test_opening_key_closes_every_cup_state(state):
    from unittest.mock import Mock

    panel = TournamentPanel(pet())
    if state == "detail":
        panel.key("enter")
        assert panel.detail is not None
    elif state != "select":
        panel.phase = "bracket"
        panel.tourney = Mock(over=state == "result", last="Cup ended", champion=False)
        if state in ("intro", "advance", "ceremony"):
            setattr(panel, "_" + state, {"t": 0})
        elif state == "bout":
            panel.sub = Mock()
    result = panel.key("u")
    assert result[0] == "done"
    if panel.tourney is not None:
        if state == "result":
            panel.tourney.record.assert_not_called()
        else:
            panel.tourney.record.assert_called_once_with(False)
    if state == "bout":
        panel.sub.key.assert_not_called()
