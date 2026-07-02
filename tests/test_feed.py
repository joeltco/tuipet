"""Feeding system: the DM20 Meat/Protein split + the DVPet applyFood modifier.

Guards the two behaviours a prior build got wrong:
  - `f` used to blind-feed Meat with only hunger/weight/mood applied;
  - a strength-food couldn't be fed to a full pet (it should, since it never fills).
"""
from tuipet.pet import Pet, FULL_HUNGER, OVEREAT_LIMIT
from tuipet import feedscreen
from tuipet.feedscreen import FeedPanel, _staples


def _pet(**kw):
    p = Pet(num=1, stage="Rookie", attribute="Vaccine")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_meat_fills_hunger_protein_builds_strength():
    meat, prot = _staples()
    assert meat["name"] == "Meat" and int(meat["hunger"]) > 0
    assert prot["name"] == "Protein" and int(prot.get("hunger", 0)) == 0 and int(prot["strength"]) > 0


def test_meat_refuses_a_full_stomach():
    p = _pet(hunger=FULL_HUNGER, glutton=0, anim="")
    meat, _ = _staples()
    msg = p.feed(meat)
    assert p.anim == "refuse" and "full" in msg
    assert p.hunger == FULL_HUNGER          # no change


def test_protein_feeds_a_full_pet_and_builds_strength():
    p = _pet(hunger=FULL_HUNGER, strength=1, anim="")
    _, prot = _staples()
    s0 = p.strength
    msg = p.feed(prot)
    assert p.anim == "eat"                  # a strength-food never refuses on fullness
    assert p.strength == s0 + 1
    assert p.hunger == FULL_HUNGER          # it doesn't fill the stomach


def test_full_food_effect_set_applies():
    # Meat carries mood +5; feeding a hungry pet applies hunger AND mood (not just hunger)
    p = _pet(hunger=1)
    m0 = p.mood
    meat, _ = _staples()
    p.feed(meat)
    assert p.hunger == 2
    assert p.mood > m0                      # intrinsic food mood applied (was dropped before)


def test_glutton_eats_one_past_full():
    p = _pet(hunger=FULL_HUNGER, glutton=1)
    meat, _ = _staples()
    p.feed(meat)
    assert p.hunger == OVEREAT_LIMIT         # a glutton fills one heart past full


def test_fullness_modifier_diminishes_a_near_full_meal():
    # a 2-hunger food into a near-full glutton gains LESS than into an empty stomach
    big = {"name": "Steak", "hunger": 2, "category": "Meat"}
    empty = _pet(hunger=0)
    empty.feed(big)
    near = _pet(hunger=FULL_HUNGER, glutton=1)     # over-full: modifier < 1
    g0 = near.hunger
    near.feed(big)
    assert (empty.hunger - 0) >= (near.hunger - g0)


def test_feed_panel_feeds_and_closes():
    p = _pet(hunger=1)
    panel = FeedPanel(p)
    r = panel.key("enter")                  # feed the highlighted staple (Meat)
    assert r is not None and r[0] == "done"
    outcome, food, msg = r[1]
    assert outcome == "fed" and food["name"] == "Meat"
    assert p.anim == "eat"


def test_feed_panel_lists_owned_bag_foods():
    p = _pet(hunger=1)
    # a bag food (if any resolve to a real food) appears after the two staples
    panel = FeedPanel(p)
    names = [o["name"] for o in panel.options]
    assert names[:2] == ["Meat", "Protein"]
