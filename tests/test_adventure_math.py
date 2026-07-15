"""Adventure/discover math audit (2026-07): canon re-verification vs
Zone.checkBattle / checkInvestigate / checkItem, WorldMap.checkEnergyDec /
checkSickInj / lossPenalty / applyLifePenalty, PhysicalState.canEscape +
config.csv column 1.

Verified matching: the encounter chance composition (7000 day-walk 10500 /
night 7000), the investigate seed (night +15000, walk -5000, -(obed+mood)),
checkItem's draw-then-1/3-ambush order and staple exclusion, the boss
exact-step gates, the town spans, flee knockback + the life penalty
retreat, the drain threshold (80 x fullHP).  All 462 enemies carry
AppearanceChance 100, so canon's roll-each-then-uniform pick and tuipet's
weighted draw coincide exactly (noted).

Fixed (canon divergences):
 * ESCAPING WAS FREE: canEscape is a power-weighted roll (mine vs theirs
   +50 boss / +10 random); failing it FORCES a round and the fight goes
   on.  Wild battles now roll it; surrender stays for the rest.
 * Enemy Location is a POINT territory ([loc,loc]), not a floor: placed
   randoms are SET AMBUSHERS at their exact step (swept by the stride),
   not permanent pool members from there on.
 * The travel drain lacked canon's companions: walking UNWELL sours (-1)
   and risks worsening (1%), injuries can worsen on the road, and
   marching through the pet's hated hour costs mood -10 / spirit -1."""
import random

from tuipet.pet import Pet
from tuipet.adventure import Adventure


def _pet(**kw):
    p = Pet(num=100, stage="Adult", attribute="Vaccine")

    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_placed_randoms_are_set_ambushers():
    p = _pet()
    adv = Adventure(p)
    saved = adv.zone["randoms"]                # load_maps is CACHED: restore or pollute
    try:
        adv.zone["randoms"] = [{"num": 29, "name": "A", "location": 0, "chance": 100},
                               {"num": 33, "name": "B", "location": 5000, "chance": 100}]
        adv.location = 1000
        assert [e["name"] for e in adv._wilds(prev=900)] == ["A"]   # B not in the pool yet
        adv.location = 5100
        assert {e["name"] for e in adv._wilds(prev=4900)} == {"A", "B"}  # the stride swept 5000
        adv.location = 9000
        assert [e["name"] for e in adv._wilds(prev=8800)] == ["A"]  # ...and B stays BEHIND
    finally:
        adv.zone["randoms"] = saved


