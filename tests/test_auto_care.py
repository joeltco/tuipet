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
    # (the CleanMoodInc/bond mood assert left with the mood system)
    # (the obedience bond cost left with the discipline system)
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
    # (the !isFuton() shield walk left with the Futon's careEffect runtime:
    # strict-DSprite items, 2026-07-17 -- a lit night is always dimmed now)


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




def test_the_assistant_feeds_a_sick_pet_and_never_bills_a_headshake():
    """assistantFeed = the AI Food Pill (AutoCareHungerFoodID 44): a SICK
    pet accepts it.  The plain-meat route refused sickness and billed
    400b/visit for head-shakes until the wallet it emptied fired it
    (assistant audit 2026-07-19: 4,800b torched in ~34 game-min, hunger
    never moved)."""
    p = _pet(bits=5000)
    p.auto_care, p.assistant_num = True, 4
    p.sick, p.hunger, p.strength, p.poop = True, 0, 2, 0
    b0 = p.bits
    for _ in range(6):                       # one visit + spacing
        p.tick(1.0)
        if getattr(p, "assist_event", None):
            break
    assert p.assist_event and p.assist_event[0] == "feed"
    assert p.hunger == 1                     # the serving LANDED
    assert p.anim == "eat"                   # no head-shake
    assert p.sick                            # the assistant feeds; curing is yours
    from tuipet.pet import AUTO_CARE_VISIT_PRICE
    assert b0 - p.bits == AUTO_CARE_VISIT_PRICE[p.stage]   # one honest fee
    assert p.auto_care                       # still on duty


# ---- round 32 pins (assist screen tidy, 2026-07-19) -------------------------

def test_assist_keys_ride_the_strip_only():
    """The in-LCD 'ENTER toggle' footer doubled the strip's keys -- gone,
    like raid/DM/shop before it (one hint surface per family)."""
    from tuipet.assistscreen import AssistPanel
    p = _pet(bits=1000)
    pan = AssistPanel(p)
    t = pan.text().plain
    assert "ENTER" not in t                        # no key footer in the LCD
    assert "hire helper" in pan.strip()
    assert len(t.rstrip("\n").split("\n")) <= 12


def test_the_contract_names_its_quit_clause():
    """Full disclosure (the feed-card precedent): the helper walks off duty
    when the bits run dry -- the card says so BEFORE you hire, not only
    via the after-the-fact quit note."""
    from tuipet.assistscreen import AssistPanel
    t = AssistPanel(_pet(bits=1000)).text().plain
    assert "quits if they run dry" in t


def test_only_an_earned_verdict_rides_home():
    """ESC used to return the standing blurb every time (and the app
    discarded it -- dead on both ends).  A toggle's verdict now rides
    home; a look-and-leave returns None."""
    from tuipet.assistscreen import AssistPanel
    p = _pet(bits=1000)
    pan = AssistPanel(p)
    assert pan.key("escape") == ("done", None)     # looked, left: no noise
    pan2 = AssistPanel(p)
    pan2.key("enter")                              # hired
    done, msg = pan2.key("escape")
    assert done == "done" and "on duty" in msg
