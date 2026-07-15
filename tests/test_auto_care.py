"""Auto-care (the AI Assistant) — DVPet PhysicalState.checkAutoCare / doAutoCare /
processAutoCarePrice + Evolution.getRandomAssistDigimon, config.csv AutoCare*."""
import json

from tuipet.pet import (Pet, AUTO_CARE_VISIT_PRICE, AUTO_CARE_HOUR_PRICE,
                        AUTO_CARE_PAYMENT_MIN, AUTO_CARE_VISIT_SPACING)
from tuipet import data, persistence


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=100)
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_config_values_are_the_classic_column():
    assert AUTO_CARE_VISIT_PRICE["Champion"] == 400          # AutoCareStageIVPrice
    assert AUTO_CARE_VISIT_PRICE["Mega"] == 1600
    assert AUTO_CARE_HOUR_PRICE["Fresh"] == 0                # stages I-II bill no retainer
    assert AUTO_CARE_HOUR_PRICE["Rookie"] == 100
    # the retainer ladder is HALF the visit ladder at every adult stage
    # (bit-sink design 2026-07-14: a flat 100 was pocket change past Rookie)
    for stage in ("Rookie", "Champion", "Ultimate", "Mega"):
        assert AUTO_CARE_HOUR_PRICE[stage] == AUTO_CARE_VISIT_PRICE[stage] // 2


def test_hiring_rolls_an_assistant_from_the_can_assist_pool():
    pool = data.assist_pool()
    assert pool and all(data.load_requirements()[n]["can_assist"] for n in pool)
    p = _pet(bits=5000)
    p.set_auto_care(True)
    assert p.auto_care and p.assistant_num in pool


def test_clean_visit_charges_and_costs_bond():
    p = _pet(bits=2000, poop=2, poop_sizes=[2, 3], auto_care=True, assistant_num=29)
    m0, o0, e0 = p.mood, p.obedience, p.enthusiasm
    p.tick(1.0)
    assert p.poop == 0 and p.poop_sizes == []
    assert p.bits == 2000 - 400                              # the Champion visit price
    assert p.mood == m0 + 6 - 10                             # CleanMoodInc, then the bond cost
    assert p.obedience == o0 - 1 and p.enthusiasm == e0 - 1
    act, piles, sizes = p.assist_event                       # the app's fx mailbox
    assert act == "clean" and piles == 2 and sizes == [2, 3]


def test_awake_priority_filth_then_hunger_then_strength():
    p = _pet(bits=9000, poop=1, poop_sizes=[2], hunger=0, strength=0,
             auto_care=True, assistant_num=29)
    p.tick(1.0)
    assert p.assist_event[0] == "clean"                      # filth outranks the stomach
    for _ in range(AUTO_CARE_VISIT_SPACING):
        p.tick(1.0)
    assert p.assist_event[0] == "feed" and p.hunger > 0      # then the AI Food Pill
    for _ in range(AUTO_CARE_VISIT_SPACING):
        p.tick(1.0)
    assert p.assist_event[0] == "strength" and p.strength > 0   # then the AI Supplement


def test_assisted_feed_is_never_refused():
    p = _pet(bits=9000, hunger=0, obedience=0, mood=-9000,   # would refuse anything
             auto_care=True, assistant_num=29)
    p.tick(1.0)
    assert p.assist_event[0] == "feed" and p.hunger > 0      # assistantFeed: canRefuse=false


def test_asleep_the_assistant_cleans_then_dims_the_lights():
    p = _pet(bits=9000, auto_care=True, assistant_num=29)
    p.sleep_lapse = p.sleep_limit
    p.tick(1.0)
    assert p.asleep and p.lights
    p.tick(1.0)
    assert p.assist_event[0] == "lights" and p.lights is False
    # ... but never under a Futon (DVPet !isFuton()) -- applied at bedtime,
    # once the pet is already down (the effect ends on any sleep TRANSITION)
    q = _pet(bits=9000, auto_care=True, assistant_num=29)
    q.sleep_lapse = q.sleep_limit
    q.tick(1.0)
    assert q.asleep
    q.effect_id, q.effect_t, q._eff_asleep = 0, 900.0, True
    q.tick(1.0)
    assert getattr(q, "assist_event", None) is None and q.lights


def test_unaffordable_visit_puts_the_assistant_off_duty():
    p = _pet(bits=100, poop=1, poop_sizes=[2], auto_care=True, assistant_num=29)
    p.tick(1.0)
    assert p.auto_care is False and p.poop == 1              # nothing done, nothing charged
    assert "assistant left" in p.assist_note


def test_hourly_retainer_bills_and_quits_when_broke():
    p = _pet(bits=300, auto_care=True, assistant_num=29)     # Champion retainer = 200/hour
    for _ in range(AUTO_CARE_PAYMENT_MIN):
        p.tick(1.0)
    assert p.bits == 100 and p.auto_care
    for _ in range(AUTO_CARE_PAYMENT_MIN):
        p.tick(1.0)
    assert p.auto_care is False and p.bits == 100            # can't cover hour two


def test_visits_are_spaced_like_the_assistant_anim_guard():
    p = _pet(bits=9000, hunger=0, auto_care=True, assistant_num=29)
    p.tick(1.0)
    assert p.assist_event[0] == "feed"
    p.hunger = 0
    p.assist_event = None
    p.tick(1.0)
    assert getattr(p, "assist_event", None) is None          # still inside the spacing window


def test_contract_survives_the_save_round_trip():
    p = _pet(bits=1000, auto_care=True, assistant_num=42)
    d = json.loads(json.dumps(persistence.to_save_dict(p)))
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.auto_care is True and p2.assistant_num == 42
    assert "assist_event" not in d                           # the fx mailbox is transient


def test_assist_panel_toggles_and_shows_the_stage_prices():
    from tuipet.assistscreen import AssistPanel
    p = _pet(bits=1000)
    pan = AssistPanel(p)
    t = pan.text().plain
    assert "AI ASSISTANT" in t and "400b/care" in t and "200b/hour" in t and "OFF" in t
    pan.key("enter")
    assert p.auto_care and "on duty" in pan.text().plain
    pan.key("enter")
    assert not p.auto_care


def test_the_assistant_stays_home_while_the_pet_adventures():
    """doAutoCare/checkAutoCare gate on _isHome (canon teleportArrive toggles
    it; auto-care audit 2026-07-06): OUT on the road the assistant neither
    bills the retainer nor visits -- and it hasn't quit, it resumes at home."""
    p = _pet(bits=2000, poop=2, poop_sizes=[2, 3], auto_care=True, assistant_num=29)
    p.away = True
    b0 = p.bits
    for _ in range(70):
        p._tick_auto_care(1.0)                    # past a full retainer window
    assert p.auto_care and p.bits == b0           # no visit, no billing, still hired
    assert p.poop == 2                            # the mess waits for YOU out there
    p.away = False
    p._tick_auto_care(1.0)
    assert p.poop == 0 and p.bits < b0            # home again: the visit fires


def test_the_adventure_flags_away_and_the_exit_clears_it():
    """Adventure.__init__ marks the pet OUT; leaving the panel brings it home
    (the same exit hook that restores the home climate)."""
    from tuipet import adventurescreen
    p = _pet(bits=100)
    p.stage_seconds = 1e9                          # past any gate noise
    pan = adventurescreen.AdventurePanel(p)
    assert p.away is True
    while pan._trans is not None:                  # the arrival teleport lands
        pan.anim()
    pan.key("escape")                              # starts the homecoming teleport
    while pan._trans is not None:                  # ...which swaps home mid-anim
        pan.anim()
    assert p.away is False
    assert pan.auto_close == ("done", None)
