"""Shop-dossier truth audit (2026-07-22, the help-audit method): every
catalog blurb exercised against its handler.  Verdict: the shelf tells
the truth -- every dial, timer and refusal matches its words.  The one
lie found was a COMMENT, not a blurb: the X-Antibody chip claimed the
unmarked-pet death roulette ran "below" -- that roulette belonged to the
removed X-PROGRAM item (strict-DSprite shelf cut 2026-07-17) and its
orphan constants are retired with it.  The chip is, and always was, the
safe path."""
from tuipet.pet import Pet, FULL_HUNGER


def _pet(**kw):
    p = Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 10 * 60.0
    p.hunger, p.strength = 2, 2
    p._set_energy(10)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _use(p, key, n=1):
    p.inventory[key] = p.inventory.get(key, 0) + n
    return p.use_item(key)


def test_food_dials_match_their_blurbs():
    for key, dh, de, dw in (("fish", 1, 0, 0), ("vegetable", 1, 0, -1),
                            ("tuna", 2, 1, 0), ("cake", 1, 2, 2),
                            ("cupcake", 1, 1, 0), ("cookie", 1, 1, 0),
                            ("candy", 1, 1, 0)):
        p = _pet()
        h0, e0, w0 = p.hunger, p.energy, p.weight
        _use(p, key)
        assert (p.hunger - h0, p.energy - e0, p.weight - w0) == (dh, de, dw), key


def test_the_big_meals_and_the_mushroom():
    p = _pet()
    w0 = p.weight
    _use(p, "cheese_burger")
    # "fills the belly · weight +4" -- and NOT a care mistake since the
    # canonization (2026-08-01): the Bandai record names overfeeding as
    # explicitly not one, so the blurb no longer promises it either
    assert p.hunger == FULL_HUNGER and p.weight - w0 == 4
    assert p.care_mistakes == 0
    p = _pet()
    w0, e0 = p.weight, p.energy
    _use(p, "giga_meal")
    assert p.hunger == FULL_HUNGER and p.energy - e0 == 4 and p.weight - w0 == 6
    p = _pet()
    _use(p, "steak")
    assert p.full_until == p.world_seconds + 12 * 3600.0      # "12h satiety"
    p = _pet()
    _use(p, "poison_mushroom")
    assert p.dead                                             # "DO NOT FEED"


def test_care_shelf_matches_its_blurbs():
    p = _pet()
    _use(p, "energy_drink")
    assert p.energy == p.max_energy                           # "energy to FULL"
    assert "already full" in _use(p, "energy_drink")          # refuse, keep item
    p = _pet(weight=30)
    _use(p, "slim_drink")
    assert p.weight == 20                                     # "weight -10"
    p = _pet()
    _use(p, "vitamin")
    assert p.strength == 4                                    # "effort to FULL"
    p = _pet()
    p.obedience = 40
    _use(p, "textbook")
    assert p.obedience == 60                                  # "obedience +20"
    # ⭐the care shelf was repointed 2026-08-02 (item refactor): the drink
    # WARDS instead of scrubbing, and the Elixir does the wiping
    p = _pet(care_mistakes=7)
    _use(p, "elixir")                           # "NO care slips for a day"
    assert p.care_mistakes == 7 and p.pardon_lapse > 0
    p._inc_mistake("the lights left on")
    assert p.care_mistakes == 7                        # warded: nothing lands
    p = _pet(care_mistakes=7)
    _use(p, "miracle_drink")             # "wipes the WHOLE slate · energy +12"
    assert p.care_mistakes == 0 and p.mistake_day == 0
    p = _pet()
    _use(p, "gold_pill")                 # "energy FULL · nothing tires it"
    assert p.energy == p.max_energy and p.tonic_lapse > 0
    p = _pet()
    _use(p, "vitamin_g")                 # "effort FULL · CANNOT be wounded"
    assert p.strength == 4 and p.ward_lapse > 0
    p = _pet()
    _use(p, "book")                      # "obedience +5 · manners HOLD"
    assert p.manners_lapse > 0
    # (the bubble bath retired 2026-07-27: strictly less than the free C
    # key, which also pays obedience -- its dossier leg retired with it)
    for key in ("town_transport", "disaster_transport", "life_recovery"):
        p = _pet()
        out = _use(p, key)
        assert "road" in out                                  # home bag refuses
        assert p.inventory[key] == 1                          # refusal keeps it
