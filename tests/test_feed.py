"""The DSprite feed menu (BASIC VPET 2026-07-16): MEAT and PILL, free and
infinite -- the DVPet food catalog left with the item system."""
from tuipet.pet import Pet, FULL_HUNGER, PILL_WEIGHT_GAIN
from tuipet.feedscreen import FeedPanel, ROWS_MENU


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_the_menu_is_meat_or_pill():
    assert [k for k, _ in ROWS_MENU] == ["meat", "pill"]


def test_meat_fills_a_heart_and_weighs():
    p = _pet(hunger=1, weight=20)
    msg = p.feed_meat()
    assert p.hunger == 2 and p.weight == 21 and "Meat" in msg


def test_meat_refused_at_a_full_belly_counts_the_overeat():
    # canon gates 2026-07-18: a PURE refuse -- the counter ticks (the
    # evolution OF gates read it) but no weight, no mistake, no bowel shove
    p = _pet(hunger=FULL_HUNGER, weight=20)
    of0, m0 = p.overeat, p.mistake_day
    msg = p.feed_meat()
    assert "full" in msg and p.overeat == of0 + 1
    assert p.weight == 20 and p.mistake_day == m0
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



def test_the_pill_is_eaten_through_its_own_menu_glyph():
    """Pill-anim fix arc (Joel 2026-07-20): the source has NO heal anim -- its
    pill rides the same EATING action as meat (animation truth).  The FRAMES
    are the pill's OWN menu glyph, the DSprite way (EatingAnimationScreen
    setSprites(SYMBOL_PILL, SYMBOL_HALF_PILL, SYMBOL_EMPTY) -- main.cpp case 1):
    full -> half -> gone, so the picked pill IS the eaten pill.  This replaces
    the DVPet f:41 capsule that never matched the picker (Joel: "those are not
    the same sprites").  Pin the whole road: panel verdict -> eat anim -> the
    sym:pill key -> the PILL/HALF_PILL strip -> the heal fx kind stays gone."""
    from tuipet.app import Screen
    from tuipet.arenafx import FxMixin
    from tuipet.feedscreen import FeedPanel, PILL, HALF_PILL, PILL_FRAMES
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.sick = True
    pan = FeedPanel(p)
    pan.cursor = 1                                   # the pill row
    done, (outcome, item, msg) = pan.key("enter")
    assert (done, outcome) == ("done", "healed")
    assert item["key"] == "sym:pill" and "Cured" in msg  # the picker's own pill,
    #                                                  not the f:41 capsule
    assert p.anim == "eat"                           # EATING, not the old heal
    # the eat fx resolves sym:pill to the pill's OWN glyph strip -- full, full,
    # half-eaten, then None (the eaten-away frame blit() tolerates)
    strip = FxMixin._food_frames(None, "sym:pill")
    assert strip is PILL_FRAMES
    # the picker's PILL glyph and the FIRST eat frame are the SAME sprite;
    # it bites down to HALF_PILL, then None (gone)
    assert strip[0] is PILL and strip[2] is HALF_PILL and strip[-1] is None
    # and the heal fx kind is STILL gone root and branch
    assert not hasattr(Screen, "_fxk_heal")

    class _S:
        pass
    _probe = _S()
    _probe.fx = None
    _probe.frame_i = 0
    Screen.start_fx(_probe, "heal")
    assert _probe.fx["steps"] == 12                  # the unknown-kind default


def test_the_source_refusal_gates_hold():
    """Canon gates 2026-07-18 (decompile L11676/11677/11697/11746): sick or
    filth-flanked pets refuse meat; filth refuses the pill too; the drill
    refuses starving/sick/filthy; the fight refuses starving/drained/sick/
    filthy.  Every refusal wears the head-shake pose."""
    p = _pet(hunger=1, sick=True)
    assert "sick" in p.feed_meat().lower() and p.anim == "refuse"
    p = _pet(hunger=1)
    p.poop, p.poop_sizes = 2, [1, 2]
    assert "clean" in p.feed_meat().lower()
    assert "clean" in p.feed_pill().lower()
    assert "clean" in p.can_train().lower()
    assert "clean" in p.can_battle().lower()
    p = _pet(hunger=0)
    assert "hungry" in p.can_train().lower()
    assert "hungry" in p.can_battle().lower()
    p = _pet(sick=True)
    assert "sick" in p.can_train().lower()
    assert "sick" in p.can_battle().lower()


def test_the_feed_card_discloses_weight_on_both_rows():
    """Full disclosure both rows (feed audit 2026-07-19): the meat row used
    to hide its weight +1 while the pill admitted its +5."""
    from tuipet.feedscreen import FeedPanel
    from tuipet import statusbox

    class _App:
        pass

    lines = {}
    app = _App()
    app.pet = _pet()
    app.mode = FeedPanel(app.pet)

    class _W:
        border_subtitle = ""
        def update(self, text):
            lines["txt"] = text
    app.stats_w = _W()
    app.mode.cursor = 0
    statusbox.feed(app)
    assert "weight +1" in lines["txt"]
    app.mode.cursor = 1
    statusbox.feed(app)
    assert "weight +5" in lines["txt"]
