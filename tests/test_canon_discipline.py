"""CANON RESTORATION B — DISCIPLINE (2026-07-23, Joel: "it was
wrongfully stripped ... whatever is canon bring back").

The device pair restored on today's tree: the obedience gauge (0..100)
is live again, the tantrum call fires and costs when ignored, SCOLD
answers it (+25), PRAISE answers a proud moment (+10, windows opened by
battle wins and mega drills, never farmable).  Refusals stay SOFT (the
standing recalibration) — discipline is the tantrum economy.
"""
from tuipet import petbody
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=50)
    p.world_seconds = 600.0
    p._set_energy(p.max_energy)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_gauge_is_live_and_clamped():
    p = _pet()
    p._set_obedience(500)
    assert p.obedience == 100
    p._set_obedience(-50)
    assert p.obedience == 0


def test_the_tantrum_fires_on_an_awake_home_pet(monkeypatch):
    p = _pet()
    monkeypatch.setattr(petbody.random, "random", lambda: 0.0)
    p.tick(1.0)
    assert p.discipline_call and p.scold_window > p.world_seconds


def test_the_tantrum_never_fires_on_the_road_or_asleep(monkeypatch):
    monkeypatch.setattr(petbody.random, "random", lambda: 0.0)
    road = _pet(away=True)
    road.tick(1.0)
    assert not road.discipline_call


def test_an_ignored_tantrum_costs(monkeypatch):
    p = _pet(discipline_call=True)
    p.scold_window = p.world_seconds - 1.0            # the window has passed
    monkeypatch.setattr(petbody.random, "random", lambda: 0.99)
    m0, o0 = p.care_mistakes, p.obedience
    p.tick(1.0)
    assert not p.discipline_call
    assert p.care_mistakes == m0 + 1                  # canon: ignored calls cost
    assert p.obedience == o0 - 5


def test_scold_answers_the_call_and_wrong_scold_lands_nothing():
    p = _pet(discipline_call=True)
    p.scold_window = p.world_seconds + 600.0
    assert "lesson" in p.scold()
    assert not p.discipline_call and p.obedience == 75
    p2 = _pet()
    assert "sulks" in p2.scold()
    assert p2.obedience == 50                         # no gain, no loss


def test_praise_pays_only_in_a_proud_window():
    p = _pet()
    p.record_battle(True, {"num": 4, "stage": "Champion", "attribute": "Data"})
    assert p.world_seconds <= p.praise_window         # a win opens the window
    assert "pride" in p.praise()
    assert p.obedience == 60 and p.praise_window == 0.0
    assert "unsure" in p.praise()                     # farming lands nothing
    assert p.obedience == 60


def test_a_mega_drill_is_a_proud_moment():
    p = _pet()
    p.train_result(True)
    assert p.world_seconds <= p.praise_window
    p2 = _pet()
    p2.train_result(False)
    assert p2.praise_window == 0.0                    # a whiff is not


def test_bedtime_placates_without_reward_or_cost():
    p = _pet(discipline_call=True)
    p.scold_window = p.world_seconds + 600.0
    m0, o0 = p.care_mistakes, p.obedience
    p._calm_discipline_call()
    assert not p.discipline_call
    assert (p.care_mistakes, p.obedience) == (m0, o0)


def test_clean_pays_the_canon_obedience_reward_again():
    p = _pet(poop=2)
    o0 = p.obedience
    p.clean()
    assert p.obedience > o0                           # the inert citation is live


def test_the_panel_picks_scold_on_an_open_call_and_applies():
    from tuipet.disciplinescreen import DisciplinePanel
    p = _pet(discipline_call=True)
    p.scold_window = p.world_seconds + 600.0
    pan = DisciplinePanel(p)
    assert pan.cursor == 1                            # Scold preselected
    for line in pan.text().plain.splitlines():
        assert len(line) <= 40
    done = pan.key("enter")
    assert done[0] == "done" and "lesson" in done[1]
    assert p.obedience == 75


def test_the_panel_wears_its_own_card():
    from tuipet import statusbox
    from tuipet.disciplinescreen import DisciplinePanel
    fn = statusbox.painter_for(DisciplinePanel(_pet()))
    assert fn is statusbox.discipline
