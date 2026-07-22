"""Shop-dossier truth audit (2026-07-22, the help-audit method): every
catalog blurb exercised against its handler.  Verdict: the shelf tells
the truth -- every dial, timer and refusal matches its words.  The one
lie found was a COMMENT, not a blurb: the X-Antibody chip claimed the
unmarked-pet death roulette ran "below" -- that roulette belonged to the
removed X-PROGRAM item (strict-DSprite shelf cut 2026-07-17) and its
orphan constants are retired with it.  The chip is, and always was, the
safe path."""
from tuipet.pet import Pet, FULL_HUNGER
from tuipet import petbase


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
    _use(p, "cheese_burger")
    assert p.hunger == FULL_HUNGER and p.care_mistakes == 1   # "a care mistake"
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
    p = _pet(care_mistakes=7)
    _use(p, "textbook")
    assert p.care_mistakes == 0                               # "erase ALL"
    p = _pet(poop=2)
    p.poop_sizes = [1, 2]
    _use(p, "port_potty")
    assert p.poop == 0                                        # "clean +
    assert p.auto_clean_until == p.world_seconds + 24 * 3600.0  # auto-clean 24h"
    p = _pet()
    _use(p, "sleeping_pill")
    assert p.asleep                                           # "sleep now"
    _use(p, "music_player")
    assert not p.asleep and p.care_mistakes == 0              # "wake now, no grudge"


def test_growth_shelf_matches_its_blurbs():
    p = _pet()
    _use(p, "dumbbell")
    assert p.stage_trainings == 10                            # "training +10"
    p = _pet()
    s0 = p.stage_seconds
    _use(p, "grow_capsule")
    assert p.stage_seconds - s0 == 7200.0                     # "+120min", real
    p = _pet()
    _use(p, "anti_evo_chip")
    assert p.evo_blocked
    _use(p, "anti_evo_chip")
    assert not p.evo_blocked                                  # "toggle"
    p = _pet()
    p.dna_owned = {}
    _use(p, "dna_crystal")
    assert p.dna_owned.get(p.field) == 10                     # "+10 own-Field"


def test_the_x_chip_is_safe_and_the_roulette_stayed_buried():
    """The chip takes hold, full stop -- the death roulette belonged to the
    REMOVED X-Program item, and its orphan constants are gone."""
    p = _pet()
    out = _use(p, "x_antibody")
    assert "takes hold" in out and p.x_antibody == "Permanent" and not p.dead
    assert "already runs" in _use(p, "x_antibody")            # marked: refuse
    for orphan in ("X_SURVIVAL_TARGET", "X_SURVIVAL_BOUND", "X_SAVE_BLOCK"):
        assert not hasattr(petbase, orphan)


def test_toys_and_adventure_shelf_match_their_blurbs():
    for key, dw, de in (("ball", -1, 0), ("skateboard", -2, -1),
                        ("xylophone", 0, 2), ("video_game", 1, 2),
                        ("television", 1, 3), ("cold_shower", 0, 2)):
        p = _pet()
        w0, e0 = p.weight, p.energy
        _use(p, key)
        assert (p.weight - w0, p.energy - e0) == (dw, de), key
    p = _pet(poop=2)
    p.poop_sizes = [1, 1]
    _use(p, "bubble_bath")
    assert p.poop == 0                                        # "washes the filth"
    for key in ("town_transport", "disaster_transport", "life_recovery"):
        p = _pet()
        out = _use(p, key)
        assert "road" in out                                  # home bag refuses
        assert p.inventory[key] == 1                          # refusal keeps it
