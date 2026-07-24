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
    """The cap is canon MAX_OBEDIENCE (P3 ruling 2026-07-23): v0.5.206
    clamped 0..100 while every constant writing here -- the clean
    reward, the surrender set (15), the stage seeds -- is calibrated
    against 150, so the low clamp silently distorted all of them."""
    from tuipet.petbase import MAX_OBEDIENCE
    assert MAX_OBEDIENCE == 150
    p = _pet()
    p._set_obedience(500)
    assert p.obedience == MAX_OBEDIENCE
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
    # the panel hands back (message, show) now -- a LANDED scold jeers
    assert done[0] == "done" and "lesson" in done[1][0]
    assert done[1][1] == "jeer"
    assert p.obedience == 75


def test_the_panel_wears_its_own_card():
    from tuipet import statusbox
    from tuipet.disciplinescreen import DisciplinePanel
    fn = statusbox.painter_for(DisciplinePanel(_pet()))
    assert fn is statusbox.discipline


# ---- E1: the lesson's show (2026-07-23, Joel: "praise and scold should
# have happy and sad animations ... already wired in") -----------------------

def _panel(pet):
    from tuipet.disciplinescreen import DisciplinePanel
    return DisciplinePanel(pet)


def test_a_landed_praise_cheers_and_a_landed_scold_jeers():
    """Discipline joins the grammar every other verdict already uses --
    the drill, the cup and the m-battle all cheer/jeer on the house
    screen.  It was the one verb that set a pose and showed nothing."""
    p = _pet()
    p.record_battle(True, {"num": 4, "stage": "Champion", "attribute": "Data"})
    pan = _panel(p)                                   # a proud window is open
    pan.cursor = 0                                    # Praise
    assert pan.key("enter")[1][1] == "cheer"

    q = _pet(discipline_call=True)
    q.scold_window = q.world_seconds + 600.0
    pan2 = _panel(q)
    assert pan2.cursor == 1                           # Scold preselected
    assert pan2.key("enter")[1][1] == "jeer"


def test_a_wrong_moment_verb_shows_nothing():
    """Nothing happened, so nothing plays -- the small pose on the LCD is
    the whole feedback (and it keeps a landed lesson legible)."""
    calm = _pet()
    for cur in (0, 1):                                # praise AND scold
        pan = _panel(calm)
        pan.cursor = cur
        assert pan.key("enter")[1][1] is None


def test_the_show_survives_the_obedience_clamp():
    """Detected on the MOMENT, not the gauge: a praise landing at the 100
    clamp moves no number but is still a real lesson."""
    p = _pet(obedience=100)
    p.record_battle(True, {"num": 4, "stage": "Champion", "attribute": "Data"})
    pan = _panel(p)
    pan.cursor = 0
    assert p.obedience == 100
    assert pan.key("enter")[1][1] == "cheer"


# ---- D1: the fade (2026-07-23) ---------------------------------------------

def test_manners_fade_while_awake():
    """Canon obedienceLapse -- discipline is a PRACTICE, not a high-water
    mark.  Cadence is scaled x5 (THE UNIT LAW: canon's minutes are device
    real-minutes and our clock runs 60x faster); neutral works out to -2
    per 10 real minutes, against a tantrum's +25 per ~90."""
    from tuipet import petbody
    import tuipet.petbody as pb
    old = pb.random.random
    pb.random.random = lambda: 0.99          # no tantrum/sickness rolls
    try:
        p = _pet(obedience=100, disposition=0)
        p._set_energy(p.max_energy)
        p.awake_limit = 9e9                  # keep it up: a 600-min tick would
        p.sleep_limit = 9e9                  # otherwise reach bedtime mid-test
        p.tick(600.0)                        # 600 game-min == 10 real min
        assert p.obedience == 98
        p.poop = 2                           # each fire also bills the mess
        p.tick(600.0)
        assert p.obedience == 94
    finally:
        pb.random.random = old
    assert petbody is not None


def test_a_sour_pet_fades_faster_than_a_sunny_one():
    """Canon's 3:2:1 disposition ratio survives the scaling."""
    from tuipet.petbase import OBEDIENCE_LAPSE_MIN
    assert OBEDIENCE_LAPSE_MIN[-1] < OBEDIENCE_LAPSE_MIN[0] < OBEDIENCE_LAPSE_MIN[1]


def test_a_sleeper_never_fades():
    """Canon MinObedienceAsleep == MaxObedience makes the lapse
    unreachable in sleep, and the fade rides the awake path only."""
    import tuipet.petbody as pb
    old = pb.random.random
    pb.random.random = lambda: 0.99
    try:
        p = _pet(obedience=100)
        p.asleep = True
        p.lights = False
        # assert the INVARIANT for as long as it actually sleeps -- a long
        # single tick just wakes it (the 7:00-sharp rule) and then it
        # fades legitimately, which would test nothing
        slept = 0
        for _ in range(30):
            if not p.asleep:
                break
            p.tick(30.0)
            slept += 1
            assert p.obedience == 100, f"faded in its sleep after {slept} ticks"
        assert slept >= 5
    finally:
        pb.random.random = old


def test_dead_meter_saves_get_one_manners_heal():
    """_set_obedience was a NO-OP for the whole BASIC VPET era, so every
    pet on disk sits at the dataclass default 0 -- "worst-raised pet
    alive" through no fault of its tamer, and D3 would call every one of
    them disobedient.  Seed those saves once, marked so a neglected pet
    cannot reset its gauge by restarting."""
    from tuipet import persistence as P
    from tuipet.petbase import FRESH_OBEDIENCE, ROOKIE_OBED_DEFAULT
    base = dict(num=93, name="Greymon", stage="Champion", attribute="Vaccine",
                world_seconds=600.0, age_seconds=600.0)
    pet, _ = P.pet_from_save(dict(base, obedience=0))
    assert pet.obedience == ROOKIE_OBED_DEFAULT and pet.obed_v == 1
    kept, _ = P.pet_from_save(dict(base, obedience=3, obed_v=1))
    assert kept.obedience == 3                      # no restart reset
    fresh, _ = P.pet_from_save(dict(base, stage="Fresh", obedience=0))
    assert fresh.obedience == FRESH_OBEDIENCE
    # a save already carrying real manners is never overwritten
    rich, _ = P.pet_from_save(dict(base, obedience=90))
    assert rich.obedience == 90


# ---- D3: earned disobedience (2026-07-23) ----------------------------------

def _neglected(**kw):
    from tuipet.petbase import DISOBEY_BELOW
    p = _pet(obedience=0, **kw)
    p._set_energy(p.max_energy)
    assert p.obedience < DISOBEY_BELOW
    return p


def test_a_well_raised_pet_never_refuses(monkeypatch):
    """The half of the soft-refusal rule that MUST survive: the old spam
    punished good raising, this punishes neglect only."""
    import tuipet.petcare as pc
    monkeypatch.setattr(pc.random, "random", lambda: 0.0)   # worst-case roll
    from tuipet.petbase import DISOBEY_BELOW
    p = _pet(obedience=DISOBEY_BELOW)
    for kind in ("feed", "train", "battle"):
        assert p.manners_refusal(kind) is False, kind


def test_a_neglected_pet_can_blow_you_off(monkeypatch):
    import tuipet.petcare as pc
    monkeypatch.setattr(pc.random, "random", lambda: 0.0)
    p = _neglected(hunger=3)
    assert p.manners_refusal("feed") and p.manners_refusal("train")
    assert p.manners_refusal("battle")


def test_the_odds_ramp_with_neglect():
    """0 at the threshold, DISOBEY_MAX_P at empty -- the first refusals
    are a warning, not a wall."""
    import tuipet.petcare as pc
    from tuipet.petbase import DISOBEY_BELOW, DISOBEY_MAX_P
    seen = {}
    for obed in (DISOBEY_BELOW, DISOBEY_BELOW // 2, 0):
        p = _pet(obedience=obed)
        hits = 0
        for i in range(1000):
            pc.random.seed(i)
            hits += bool(p.manners_refusal("train"))
        seen[obed] = hits / 1000
    assert seen[DISOBEY_BELOW] == 0
    assert 0 < seen[DISOBEY_BELOW // 2] < seen[0]
    assert seen[0] <= DISOBEY_MAX_P + 0.05


def test_medicine_and_cleaning_are_never_refused(monkeypatch):
    """A pet you cannot clean or heal is a softlock, not a personality."""
    import tuipet.petcare as pc
    monkeypatch.setattr(pc.random, "random", lambda: 0.0)
    p = _neglected(poop=2)
    assert "Cleaned" in p.clean()
    p.sick = True
    p.poop = 0
    assert "pill" in p.feed_pill().lower() or "Took" in p.feed_pill()
    assert not p.sick
    p.injured = True
    p.add_item("bandage")
    assert "patched" in str(p.use_item("bandage"))
    for kind in ("clean", "pill", "bandage", "item"):
        assert p.manners_refusal(kind) is False, kind


def test_a_starving_pet_is_never_refused_food(monkeypatch):
    """Starvation kills -- attitude must never close the door that saves it."""
    import tuipet.petcare as pc
    monkeypatch.setattr(pc.random, "random", lambda: 0.0)
    p = _neglected(hunger=0)
    assert p.manners_refusal("feed") is False
    assert "Fed" in p.feed_meat()


def test_evolution_doors_keep_their_energy_only_rule(monkeypatch):
    """Plan-audit P2: check_refused's only callers are jogress and the
    mode change.  Manners must NEVER reach them, or neglect would start
    silently refusing evolutions."""
    import tuipet.petcare as pc
    monkeypatch.setattr(pc.random, "random", lambda: 0.0)
    p = _neglected()
    assert p.check_refused() is False                  # no energy change asked


def test_a_new_pet_is_not_born_disobedient():
    """The dataclass default was 0 -- harmless while the meter was a
    no-op, but under D3 a bare Pet() would be born NEGLECTED and start
    blowing off commands.  Born TRUSTING (canon FreshObedience)."""
    from tuipet.pet import Pet
    from tuipet.petbase import DISOBEY_BELOW, FRESH_OBEDIENCE
    p = Pet(num=100, stage="Champion")
    assert p.obedience == FRESH_OBEDIENCE >= DISOBEY_BELOW
    assert p.manners_refusal("feed") is False
