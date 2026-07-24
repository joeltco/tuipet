"""CANON RESTORATION — INJURY, the second ailment (2026-07-23, Joel:
"it was wrongfully stripped ... whatever is canon bring back").

The real hardware has two ailments with two meds: sickness (the pill)
and battle injury (the Bandage).  The 2026-07-16 strip took injury
whole; this restores it to the device rules on today's tree — the
decompile's BattleInjury table adapted (fatigue/mood coefficients left
with their dead systems), LOCAL bouts only, the vitamin as the canon
guard, one-dose cure in the pill's own grammar.
"""
from tuipet import petbattle, petbody
from tuipet.pet import Pet
from tuipet.petbase import BATTLE_INJ_TABLE


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p._set_energy(p.max_energy)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _fight(p, won=True, roll=0.5, monkeypatch=None):
    monkeypatch.setattr(petbattle.random, "random", lambda: roll)
    p.record_battle(won, {"num": 4, "stage": "Champion", "attribute": "Data"})


def test_a_bad_condition_loss_can_wound(monkeypatch):
    p = _pet()
    p._set_weight(p._base_weight() + 10)       # 8g+ off base = bad condition
    _fight(p, won=False, roll=0.10, monkeypatch=monkeypatch)   # < 150/1000
    assert p.injured and p.injuries == 1


def test_a_healthy_winner_virtually_never_wounds(monkeypatch):
    p = _pet()
    _fight(p, won=True, roll=0.05, monkeypatch=monkeypatch)    # good_nv = 3/1000
    assert not p.injured


def test_the_vitamin_is_the_canon_guard(monkeypatch):
    assert BATTLE_INJ_TABLE["good_v"] == 0                     # a guarded healthy pet: immune
    p = _pet()
    p._set_weight(p._base_weight() + 10)
    p.vitamin_lapse = 100.0                                    # guard live
    _fight(p, won=False, roll=0.076, monkeypatch=monkeypatch)  # bad_v 25+50=75/1000 < roll
    assert not p.injured
    p2 = _pet()
    p2._set_weight(p2._base_weight() + 10)
    _fight(p2, won=False, roll=0.076, monkeypatch=monkeypatch)  # bad_nv 100+50=150/1000
    assert p2.injured


def test_online_bouts_never_wound(monkeypatch):
    p = _pet()
    p._set_weight(p._base_weight() + 10)
    monkeypatch.setattr(petbattle.random, "random", lambda: 0.0)
    p.record_battle(False, online=True)                        # L17: body billing only
    assert not p.injured


def test_the_bandage_cures_and_the_pill_does_not():
    p = _pet(injured=True, injuries=1)
    assert p.battle_condition() == "Too hurt to fight."        # the gate
    assert p.status_word() == "injured"                        # the word
    p.add_item("bandage")
    assert "patched" in p.use_item("bandage")
    assert not p.injured and p.injuries == 1                   # cured; the count keeps
    # the pill stays sick-only: it cannot have been the cure
    p2 = _pet(injured=True)
    p2._set_energy(0)                                          # so the pill isn't refused
    p2.strength = 0
    p2.feed_pill()
    assert p2.injured                                          # two ailments, two meds


def test_the_bandage_refuses_a_healthy_pet():
    p = _pet()
    p.add_item("bandage")
    assert "Nothing" in str(p.use_item("bandage"))
    assert p.inventory.get("bandage") == 1                     # refusal keeps the item


def test_an_injured_pet_still_eats():
    p = _pet(injured=True, hunger=2)
    assert "sick" not in str(p.feed_meat())                    # only SICK blocks meat


def test_the_bandage_is_in_the_catalog():
    from tuipet import shop
    e = shop.entry("bandage")
    assert e and e["name"] == "Bandage" and e["category"] == "Medicine"


def test_the_vitamin_guard_burns_at_one_per_game_minute(monkeypatch):
    """P0a (plan audit 2026-07-23): the guard decayed `dt / 60.0` -- 60x
    too slow under THE UNIT LAW (dt IS game-minutes) -- so one 500b
    capsule bought ~24 REAL HOURS of immunity and silently disarmed the
    whole injury system shipped a release earlier.

    The pin this replaces ticked 60 and asserted "< 1440.0", which
    passed with the bug present.  This one pins the RATE, so a 60x
    regression cannot hide."""
    monkeypatch.setattr(petbody.random, "random", lambda: 0.99)   # no other rolls fire
    p = _pet()
    p.strength = 0
    p.add_item("vitamin")
    p.use_item("vitamin")
    assert p.vitamin_lapse == 1440.0        # one game DAY of protection
    p.tick(10.0)
    assert p.vitamin_lapse == 1430.0        # 1:1 with game-min (the bug gave 1439.83)


def test_a_wound_heals_on_its_own_clock(monkeypatch):
    """P4 ruling (plan audit 2026-07-23): v0.5.205 shipped injury with NO
    canon recovery, leaving a 300b shop-only Bandage as the only cure
    while sickness has a free infinite one.  Canon heals a wound on a
    clock (randint(1,12) lapses); the Bandage now buys off the WAIT
    rather than being the only door."""
    p = _pet()
    p._set_weight(p._base_weight() + 10)
    monkeypatch.setattr(petbattle.random, "random", lambda: 0.0)
    monkeypatch.setattr(petbattle.random, "randint", lambda a, b: a)   # shortest wound
    p.record_battle(False, {"num": 4, "stage": "Champion", "attribute": "Data"})
    assert p.injured and p.inj_length > 0
    monkeypatch.setattr(petbody.random, "random", lambda: 0.99)        # no new rolls
    p.tick(p.inj_length / 2)
    assert p.injured                                   # still hurt halfway
    p.tick(p.inj_length + 1)
    assert not p.injured and p.inj_length == 0         # time closed it


def test_the_bandage_buys_off_the_wait():
    p = _pet(injured=True, inj_length=999.0)
    p.add_item("bandage")
    p.use_item("bandage")
    assert not p.injured and p.inj_length == 0.0
