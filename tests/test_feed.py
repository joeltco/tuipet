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


def test_the_meat_eats_through_its_own_bite_strip():
    """Meat joins the pill on the source's bite strips (2026-07-18): the
    panel hands the "meat" key, the fx resolves it to the ripped me/ge/_e
    shrink; the DVPet f:0 icon stays with the bag consumables."""
    from tuipet.app import Screen
    from tuipet.feedscreen import FeedPanel, MEAT_BITES
    p = _pet(hunger=1)
    pan = FeedPanel(p)
    done, (outcome, item, _msg) = pan.key("enter")
    assert (done, outcome) == ("done", "fed")
    assert item["key"] == "meat"

    class _S:
        pass
    _S._food_frames = Screen._food_frames
    frames = _S()._food_frames("meat")
    assert frames is MEAT_BITES
    assert len(frames) == 4 and frames[-1] is None
    inks = [sum(r.count("1") for r in f) for f in frames[:3]]
    assert inks[0] > inks[1] > inks[2] > 0            # a strict shrink


def test_the_pill_is_eaten_on_its_own_bite_strip():
    """Pill-anim fix (Joel 2026-07-18: "the pill eating animation is broken...
    dsprite is the animation truth"): the source has NO heal anim -- its pill
    rides the same EATING action as meat, on the ripped he/ve/ye bite strip.
    The old route (the DVPet bandage() port) drew the i:80 medicine strip at
    y0-4, above the window top (y6): a clipped sliver.  Pin the whole road:
    panel verdict -> eat anim -> the "pill" key -> the strip the fx steps."""
    from tuipet.app import Screen
    from tuipet.feedscreen import FeedPanel, PILL_BITES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.sick = True
    pan = FeedPanel(p)
    pan.cursor = 1                                   # the pill row
    done, (outcome, item, msg) = pan.key("enter")
    assert (done, outcome) == ("done", "healed")
    assert item["key"] == "pill" and "Cured" in msg
    assert p.anim == "eat"                           # EATING, not the old heal
    # the fx resolves "pill" to the ripped strip: 3 bites + the eaten-away None
    class _S:
        pass
    _S._food_frames = Screen._food_frames
    frames = _S()._food_frames("pill")
    assert frames is PILL_BITES
    assert len(frames) == 4 and frames[-1] is None
    assert all(len(f) == 8 and all(len(r) == 8 for r in f) for f in frames[:3])
    # the strip is a strict shrink: full -> bitten -> nearly gone
    inks = [sum(r.count("1") for r in f) for f in frames[:3]]
    assert inks[0] > inks[1] > inks[2] > 0
    # and the heal fx kind is GONE root and branch
    assert not hasattr(Screen, "_fxk_heal")
    _probe = _S()
    _probe.fx = None
    _probe.frame_i = 0
    Screen.start_fx(_probe, "heal")
    assert _probe.fx["steps"] == 12                  # the unknown-kind default
