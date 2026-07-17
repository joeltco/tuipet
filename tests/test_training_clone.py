"""The 0.5 timing drill (ported 2026-07-17, "replace training system with
0.5 system we made").  One bar, SPACE locks it: mega zone = clean strike,
±5 shoulder = solid hit, wide = whiff.  The lock saves the battle form
(`saved_hit_type`), train_result feeds the LINES TR gates (energy -2), and
the strike plays on battle's own strikefx rails against the 0.5 BRICK
WALL (the clone's battle_fx rips — DSprite is the ultimate truth for
animations and mechanics).  Attribute powers grow only through battle
wins now.
"""
from tuipet import training
from tuipet.pet import Pet, TRAIN_ENERGY_COST


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _panel(p=None):
    return training.TrainingPanel(p or _pet())


def _lock_at(pan, pos):
    pan.bar = pos
    pan.key("space")


# ---- grades + the saved form -----------------------------------------------------

def test_the_three_grades_read_the_window():
    pan = _panel()
    mid = (pan.mega_lo + pan.mega_hi) // 2
    _lock_at(pan, mid)
    assert pan.grade == "mega" and pan.success
    pan2 = _panel()
    _lock_at(pan2, pan2.mega_lo - 3)              # inside the ±5 shoulder
    assert pan2.grade == "normal" and pan2.success
    pan3 = _panel()
    _lock_at(pan3, 0 if pan3.mega_lo - 5 > 0 else 24)
    assert pan3.grade == "miss" and not pan3.success


def test_the_lock_saves_the_battle_form():
    p = _pet()
    pan = training.TrainingPanel(p)
    _lock_at(pan, (pan.mega_lo + pan.mega_hi) // 2)
    assert p.saved_hit_type == "mega"
    pan2 = training.TrainingPanel(p)
    _lock_at(pan2, 0 if pan2.mega_lo - 5 > 0 else 24)
    assert p.saved_hit_type == "miss"             # a whiff overwrites: today's form


def test_a_999_battle_veteran_always_strikes_mega():
    p = _pet(battles=999)
    pan = training.TrainingPanel(p)
    _lock_at(pan, 0)                              # the worst possible timing
    assert pan.grade == "mega"                    # the clone's veteran quirk


# ---- train_result (the sim side) ---------------------------------------------------

def test_every_attempt_counts_and_costs():
    p = _pet()
    e0, t0, x0 = p.energy, p.stage_trainings, p.exercise_today
    p.train_result(False)
    assert p.energy == e0 - TRAIN_ENERGY_COST
    assert p.stage_trainings == t0 + 1            # LINES TR gate: win or lose
    assert p.exercise_today == x0 + 1
    assert p.anim == "sad"
    p.train_result(True)
    assert p.anim == "happy"


def test_a_clean_strike_sheds_toward_base_never_below():
    p = _pet()
    p.weight = p._base_weight() + 3
    p.train_result(True)
    assert p.weight == p._base_weight() + 2
    q = _pet()
    q.weight = q._base_weight() - 5               # a light runner
    q.train_result(True)
    assert q.weight == q._base_weight() - 5       # the shed never fattens


def test_powers_do_not_grow_at_the_bar():
    p = _pet(vaccine=5, data_power=3, virus=2)
    pan = training.TrainingPanel(p)
    _lock_at(pan, (pan.mega_lo + pan.mega_hi) // 2)
    assert (p.vaccine, p.data_power, p.virus) == (5, 3, 2)


def test_the_energy_gate_is_the_one_hard_gate():
    p = _pet()
    p.energy = TRAIN_ENERGY_COST - 1
    assert "tired" in p.can_train().lower()
    p.energy = TRAIN_ENERGY_COST
    assert p.can_train() is None


# ---- the show ---------------------------------------------------------------------

def test_the_drill_plays_through_bar_strike_done():
    pan = _panel()
    for _ in range(10):
        pan.anim()
        assert pan.text().plain                    # the bar renders
    assert pan.strip()
    _lock_at(pan, (pan.mega_lo + pan.mega_hi) // 2)
    assert pan.phase == "shoot"
    for _ in range(200):
        pan.anim()
        assert pan.text().plain is not None        # every strike beat renders
        if pan.phase == "done":
            break
    assert pan.phase == "done"
    assert "PERFECT" in pan.text().plain
    assert pan.key("space") == ("done", pan.result)


def test_wall_one_stands_through_everything_but_a_mega_break():
    """The clone's wall rule, verbatim: Wall_1 through the whole volley --
    a whiff, a normal break, the incoming orb -- and ONLY a mega break
    crumbles it to Wall_2."""
    import json, os
    import tuipet.training as tr
    wall = json.load(open(os.path.join(os.path.dirname(tr.__file__),
                                       "data", "train_wall.json")))
    pan = _panel()
    _lock_at(pan, 0 if pan.mega_lo - 5 > 0 else 24)
    assert pan.grade == "miss"
    standing = set(pan._wall_overlay("miss"))
    assert standing == set(pan._wall_overlay("fire_in"))
    assert standing == set(pan._wall_overlay("break"))   # a miss never crumbles
    assert len(standing) == sum(r.count("1") for r in wall["Wall_1"])
    pan2 = _panel()
    _lock_at(pan2, (pan2.mega_lo + pan2.mega_hi) // 2)
    assert pan2.grade == "mega"
    crumbled = set(pan2._wall_overlay("break"))
    assert crumbled != standing                          # Wall_2: the crumble rip
    assert len(crumbled) == sum(r.count("1") for r in wall["Wall_2"])
    assert set(pan2._wall_overlay("fire_in")) == standing  # it stood to take the shot


def test_the_bar_escape_trains_nothing():
    p = _pet()
    t0, e0 = p.stage_trainings, p.energy
    pan = training.TrainingPanel(p)
    assert pan.key("escape") == ("done", None)
    assert p.stage_trainings == t0 and p.energy == e0
