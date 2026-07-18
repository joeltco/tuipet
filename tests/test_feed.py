"""The DSprite feed menu (BASIC VPET 2026-07-16): MEAT and PILL, free and
infinite -- the DVPet food catalog left with the item system."""
from tuipet.pet import Pet, FULL_HUNGER, PILL_ENERGY_GAIN, PILL_WEIGHT_GAIN
from tuipet.feedscreen import FeedPanel, ROWS_MENU


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_menu_is_meat_or_pill():
    assert [k for k, _, _ in ROWS_MENU] == ["meat", "pill"]


def test_meat_fills_a_heart_and_weighs():
    p = _pet(hunger=1, weight=20)
    msg = p.feed_meat()
    assert p.hunger == 2 and p.weight == 21 and "Meat" in msg


def test_meat_refused_at_a_full_belly_counts_the_overeat():
    p = _pet(hunger=FULL_HUNGER, weight=20)
    of0 = p.overeat
    msg = p.feed_meat()
    assert "full" in msg and p.overeat == of0 + 1 and p.weight == 21
    assert p.hunger == FULL_HUNGER


def test_pill_is_a_tonic():
    """(the cure leg left with the sickness system -- BASIC VPET 2026-07-17)"""
    p = _pet(strength=1, energy=0, weight=20)
    msg = p.feed_pill()
    assert p.strength == 2 and p.weight == 20 + PILL_WEIGHT_GAIN
    assert p.energy > 0


def test_pill_refused_when_nothing_to_top_up():
    p = _pet(sick=False, strength=4)
    p.energy = p.max_energy
    msg = p.feed_pill()
    assert "doesn" in msg and p.weight == _pet().weight


def test_panel_walks_and_feeds():
    p = _pet(hunger=1)
    pan = FeedPanel(p)
    assert pan.text().plain
    pan.key("down")
    pan.key("up")
    r = pan.key("enter")
    assert r and r[0] == "done" and r[1][0] in ("fed", "full", "refused")


def test_feed_alias_keeps_old_callers_fed():
    p = _pet(hunger=0)
    p.feed()                       # the assistant path
    assert p.hunger == 1


def test_the_meat_eats_through_the_dvpet_meat_strip():
    """Meat is EATEN (the source's action) through the DVPet f:0 Meat strip
    (art truth, Joel 2026-07-18: "all sprites must come from dvpet")."""
    from tuipet import data
    p = _pet(hunger=1)
    pan = FeedPanel(p)
    done, (outcome, item, _msg) = pan.key("enter")
    assert (done, outcome) == ("done", "fed")
    assert item["key"] == "f:0"
    strip = data.load_icons()["f:0"]
    assert len(strip) == 4
    assert len({(len(f[0]), len(f)) for f in strip if f}) == 1   # uniform frames



def test_the_pill_is_eaten_through_the_dvpet_med_strip():
    """Pill-anim fix arc (Joel 2026-07-18): the source has NO heal anim --
    its pill rides the same EATING action as meat (animation truth), and the
    frames are the DVPet f:4 Med strip (art truth: "all sprites must come
    from dvpet. the dsprite ones suck").  The old bandage route drew i:80 at
    y0-4, above the window top (y6): a clipped sliver.  Pin the whole road:
    panel verdict -> eat anim -> the f:4 key -> a real uniform strip -> the
    heal fx kind stays gone."""
    from tuipet import data
    from tuipet.app import Screen
    from tuipet.feedscreen import FeedPanel
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.sick = True
    pan = FeedPanel(p)
    pan.cursor = 1                                   # the pill row
    done, (outcome, item, msg) = pan.key("enter")
    assert (done, outcome) == ("done", "healed")
    assert item["key"] == "f:4" and "Cured" in msg
    assert p.anim == "eat"                           # EATING, not the old heal
    strip = data.load_icons()["f:4"]
    assert len(strip) == 4
    assert len({(len(f[0]), len(f)) for f in strip if f}) == 1   # uniform frames
    # and the heal fx kind is STILL gone root and branch
    assert not hasattr(Screen, "_fxk_heal")

    class _S:
        pass
    _probe = _S()
    _probe.fx = None
    _probe.frame_i = 0
    Screen.start_fx(_probe, "heal")
    assert _probe.fx["steps"] == 12                  # the unknown-kind default
