"""Adventure polish — CONDITION WALKS + TRAVEL REFUSALS (restored 2026-07-21).

Pins pass 3 + the canTravel port on the CURRENT build: a sick pet trudges the
idleUnwell poses at half march pace, a geriatric one walks the +9 aged
frames, a sleeping traveller halts the whole journey as the roadside nap,
and a pet pushed PAST EMPTY plants its feet (today's deliberately-soft
calibration: negative energy only — never chance-based).
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES
from tuipet.adventurescreen import AdventurePanel, REFUSE_T, TRAVEL_TICKS
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _on_the_road(monkeypatch, p=None):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    pan = AdventurePanel(p or _pet(), zone=ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    return pan


def test_a_sick_pet_trudges_at_half_pace(monkeypatch):
    from tuipet import menu
    pan = _on_the_road(monkeypatch)
    pan.pet.sick = True
    x0 = pan._wx
    for _ in range(10):
        pan.anim()
    assert pan._wx - x0 == 10 * 0.5 * 0.5              # MARCH_PX halved
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append(pl), real(pl, *a, **k))[1])
    pan.frame_i = 5                                    # mid-cycle: the collapse pose
    assert pan.text()
    assert calls[-1][0][0] == pan._rows(10)            # idleUnwell collapse, not the walk


def test_a_geriatric_pet_walks_the_aged_shuffle(monkeypatch):
    from tuipet import menu
    pan = _on_the_road(monkeypatch)
    p = pan.pet
    p.age_seconds = 16 * 86400.0                       # past the elder line
    assert p.is_geriatric
    calls = []
    real = menu.paint
    monkeypatch.setattr(menu, "paint",
                        lambda pl, *a, **k: (calls.append(pl), real(pl, *a, **k))[1])
    pan.frame_i = 0
    assert pan.text()
    assert calls[-1][0][0] == pan._rows(9)             # walk frame 0 -> aged 9


def test_a_sleeping_traveller_naps_by_the_road(monkeypatch):
    pan = _on_the_road(monkeypatch)
    pan.pet.asleep = True
    loc0, wx0 = pan.adv.loc, pan._wx
    for _ in range(TRAVEL_TICKS * 3):
        pan.anim()
        assert pan.text()                              # the Zzz scene renders
    assert pan.adv.loc == loc0 and pan._wx == wx0      # the whole journey waits
    assert "nap" in pan.strip()
    pan.pet.asleep = False                             # it wakes: the march resumes
    for _ in range(TRAVEL_TICKS + 1):
        pan.anim()
    assert pan.adv.loc > loc0


def test_only_a_pet_pushed_past_empty_refuses(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    p = _pet()
    a = Adventure(p, zone=ZONES[0])
    assert a.travel() == "step"                        # rested: never refuses
    p._set_energy(-3)                                  # pushed past empty
    r = a.travel()
    assert isinstance(r, tuple) and r[0] == "refused"
    assert "refuses to walk" in a.last


def test_the_panel_plants_its_feet_and_space_re_issues(monkeypatch):
    pan = _on_the_road(monkeypatch)
    p = pan.pet
    p._set_energy(-3)
    for _ in range(TRAVEL_TICKS + 1):                  # the next leg refuses
        pan.anim()
    assert pan._refused and 0 < pan._refuse_t <= REFUSE_T
    assert pan.sfx == "refuse"
    loc0 = pan.adv.loc
    for _ in range(REFUSE_T + TRAVEL_TICKS * 2):       # the shake, then planted
        pan.anim()
        assert pan.text()
    assert pan.adv.loc == loc0                         # the march is halted
    # the strip says WHY (past-empty is the only trigger) instead of the
    # bare "SPACE urge" that invited a dead mash (QOL sweep 2026-07-23);
    # honest outs only (energy audit 2026-07-23): no false "rest refills"
    # promise -- energy cannot rise on the road, town warp or home are it
    assert "Refuses" in pan.strip() and "spent" in pan.strip()
    assert "ESC home" in pan.strip()
    assert "rest refills" not in pan.strip()
    pan.key("space")                                   # urge it on: still spent
    assert pan._refused and pan._refuse_t == REFUSE_T  # ...it refuses again
    p._set_energy(p.max_energy)                        # rested (a town would do this)
    for _ in range(REFUSE_T + 1):
        pan.anim()                                     # let the shake finish
    pan.key("space")                                   # urge it on, rested
    assert not pan._refused and pan.adv.loc > loc0     # the walk re-issued


def test_a_sleep_pill_cannot_freeze_the_march(monkeypatch):
    """SOFTLOCK (energy audit 2026-07-23): the roadside-nap branch waits
    out pet.asleep, but the life sim is PAUSED in every mode (the TIME
    LAW's one-law freeze) -- a Sleep Pill used on the road put the pet
    to sleep FOREVER, march frozen, ESC home the only exit.  The pill
    is refused on the road now (and kept -- the _Refused contract)."""
    pan = _on_the_road(monkeypatch)
    p = pan.pet
    p.away = True          # the teleport's flag (the harness skips the landing)
    p.add_item("sleeping_pill")
    msg = p.use_item("sleeping_pill")
    assert "road" in str(msg)
    assert not p.asleep
    assert p.inventory.get("sleeping_pill") == 1   # refusal keeps the pill
    loc0 = pan.adv.loc
    for _ in range(TRAVEL_TICKS * 3):
        pan.anim()
    assert pan.adv.loc > loc0                      # the march still marches
