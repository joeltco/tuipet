"""LIVE-PLAY AUDIT — the pins (2026-07-25).

Three QA personas played the game headlessly overnight (caretaker / chaos
/ grinder).  The chaos player's finds, all in the poisoned-save path —
a SUPPORTED path: load()'s contract is .bak -> quarantine -> "Starting
fresh", never a raise (a crash at load is a crash LOOP: the .bak holds the
same poison).

L1 (FIXED) — TWO MIGRATIONS CRASHED BEFORE ANY CHECK RAN.  The manners
heal (`float(data.get("obedience"))`) and the interrupted-wager settle
(`dna_wager_pending > 0`) both ran ahead of the wrong-type rejection list,
so a string in either field raised straight out of pet_from_save -- and
load() called it OUTSIDE its try, so the promised fallback never got the
chance.  Boot crash (app.py loads at startup).

L2 (FIXED) — THE 13-FIELD TYPE LIST MISSED ~20 FIELDS.  stage_seconds,
calories, strength, care_mistakes, gift_t, tourney_alarm, anim_ttl,
full_until, adv_progress, town_bought, daily_mood ... a save poisoned in
any of them loaded "fine" and crashed on the first tick or first render --
exactly the failure the list's own comment says it exists to prevent.

THE FIX, both levels: a GENERIC type gate over fields(Pet) -- every save
value must match its dataclass default's shape, checked BEFORE the
migrations; one sweep, no list to forget (a defense is only as good as
its worst consumer).  And load() wraps pet_from_save in the belt: any
raise that slips a future gate lands in the same fallback chain.
"""
import json
import os

import pytest

from tuipet import persistence
from tuipet.pet import Pet


def _healthy_save():
    p = Pet.new_egg(egg_type=1)
    p._hatch_into_fresh()
    persistence.save(p)
    d = json.load(open(persistence.SAVE_PATH))
    try:
        os.remove(persistence.SAVE_PATH + ".bak")
    except OSError:
        pass
    return d


def _write(d):
    json.dump(d, open(persistence.SAVE_PATH, "w"))


# the fields the chaos player measured crashing tick()/render on old code,
# plus the two that crashed the migrations themselves
_POISONED = ["obedience", "dna_wager_pending", "stage_seconds", "calories",
             "strength", "care_mistakes", "energy_rank", "glutton",
             "vitamin_lapse", "battles", "item_interest", "last_birthday",
             "_poop_t", "_cal_t", "_str_t", "gift_t", "tourney_alarm",
             "anim_ttl", "full_until", "auto_clean_until", "adv_progress",
             "num"]


@pytest.mark.parametrize("fld", _POISONED)
def test_a_poisoned_numeric_field_is_rejected_not_accepted(fld):
    d = _healthy_save()
    d[fld] = "banana"
    pet, _msg = persistence.pet_from_save(d)
    assert pet is None, f"{fld}='banana' built a pet that crashes later"


@pytest.mark.parametrize("fld,val", [("daily_mood", "x"), ("town_bought", 5),
                                     ("inventory", "bag"), ("poop_sizes", 3)])
def test_a_poisoned_container_field_is_rejected(fld, val):
    d = _healthy_save()
    d[fld] = val
    pet, _msg = persistence.pet_from_save(d)
    assert pet is None, (fld, val)


@pytest.mark.parametrize("fld", ["obedience", "dna_wager_pending"])
def test_load_quarantines_the_migration_crashers(fld):
    """The boot path itself: the two fields whose poison raised out of
    load() and crashed the app at startup."""
    d = _healthy_save()
    d[fld] = "banana"
    _write(d)
    pet, msg = persistence.load()          # must NOT raise
    assert pet is None
    assert "couldn't be read" in msg


def test_a_poisoned_main_save_still_falls_back_to_the_bak():
    """The .bak (one autosave behind) beats quarantine when it's healthy."""
    d = _healthy_save()
    json.dump(d, open(persistence.SAVE_PATH + ".bak", "w"))
    d2 = dict(d)
    d2["stage_seconds"] = "zzz"
    _write(d2)
    pet, msg = persistence.load()
    assert pet is not None
    assert "backup" in msg


def test_the_belt_catches_a_future_gate_slip(monkeypatch):
    """load()'s contract is fallback/quarantine, never a raise -- even if
    pet_from_save grows a new crash tomorrow."""
    _write(_healthy_save())

    def boom(_d):
        raise RuntimeError("a future migration bug")
    monkeypatch.setattr(persistence, "pet_from_save", boom)
    pet, msg = persistence.load()
    assert pet is None and "couldn't be read" in msg


def test_the_gate_rejects_no_healthy_save():
    """Over-rejection would quarantine real pets: a full healthy roundtrip
    must still load, message-free."""
    _write(_healthy_save())
    pet, msg = persistence.load()
    assert pet is not None and msg == ""


# ---- L3: the filth-sickness scaling is LIVE (the caretaker's find) -------
#
# _filth_effects' docstring always promised "chance x piles vs the bound x
# the species multiplier", but the wiring was lost: FILTH_SICK_CHANCE /
# FILTH_SICK_BOUND sat unreferenced, 232 species' PoopSickChanceBoundMultiplier
# was parsed and never read, and _tick_mortality rolled a flat SICK_POOP_P
# (0.015/min) whatever the mess -- so one unanswerable 3am pile meant a
# ~97% sick morning after flawless care.  The roll now lives where its
# docstring lives: per game-min, piles/(12000 x mult), canon's own bound.
# ⚠These pins were rewritten for 0.5.317: they used to be tuned to a bound
# of 200, the 60x-hot /60 "rescale" that made ONE pile sicken a pet in a
# median 3.3 real minutes.  The scaling and multiplier legs they check are
# unchanged -- only the rate they check them at.

def _filth_pet(num=29, lid="ver1", piles=1):
    p = Pet(num=num, stage="Champion", attribute="Vaccine")
    p.line_id = lid
    p.poop, p.poop_sizes = piles, [2] * piles
    p.hunger = p.strength = 4
    p.weight = p._base_weight()
    return p


def test_the_filth_roll_scales_with_the_pile_count(monkeypatch):
    """The pile count is the risk: a roll that a 3-pile sty catches must
    slip past a lone pile.  Threshold sits between 1/12000 and 3/12000."""
    monkeypatch.setattr("tuipet.petbody.random.random", lambda: 2 / 12000.0)
    lone = _filth_pet(piles=1)
    lone._filth_effects(1.0)
    assert not lone.sick, "one pile rolled at the 3-pile rate"
    messy = _filth_pet(piles=3)
    messy._filth_effects(1.0)
    assert messy.sick, "three piles must roll hotter than one"


def test_the_filth_roll_reads_the_species_multiplier(monkeypatch):
    """The 232 species' PoopSickChanceBoundMultiplier is finally read: a
    resistant (mult 2.0) species shrugs at half the rate."""
    monkeypatch.setattr("tuipet.petbody.random.random", lambda: 1.5 / 12000.0)
    normal = _filth_pet(num=29, piles=2)          # mult 1.0 -> p 2/12000
    normal._filth_effects(1.0)
    assert normal.sick
    tough = _filth_pet(num=116, piles=2)          # mult 2.0 -> p 1/12000
    tough._filth_effects(1.0)
    assert not tough.sick


def test_the_road_still_shields_the_home_mess(monkeypatch):
    """countFilth reads 0 away -- the canon shield survives the rewire."""
    monkeypatch.setattr("tuipet.petbody.random.random", lambda: 0.0)
    p = _filth_pet(piles=4)
    p.away = True
    for _ in range(100):
        p._filth_effects(1.0)
    assert not p.sick


def test_the_overweight_roll_still_lives_in_mortality(monkeypatch):
    """Only the FILTH half moved: the overweight sickness stays."""
    monkeypatch.setattr("tuipet.petbody.random.random", lambda: 0.0)
    p = _filth_pet(piles=0)
    p.weight = p._base_weight() * 2
    p._tick_mortality(1.0)
    assert p.sick


# ---- L4: the town cup honors the shared cup hour (the grinder's find) ----
#
# Entering ANY cup burns the pet's cup-hour slot (Tournament.__init__), but
# the town door never CHECKED it -- and adventure marches park the world
# clock (TIME LAW), so a march-and-flee loop re-entered the town cup every
# arrival: measured 100 consecutive cups, +47,632 bits, 0.0 game-seconds.
# The "~1,500b a minute" farm the hour rule exists to close, reopened
# through the road.  Each entry also silently killed that hour's HOME cup:
# the slot was spent but never checked.  One slot, both doors.

def _cup_pet(hour=10):
    p = Pet(num=1455, stage="Champion", attribute="Vaccine")
    p.line_id = "ver1"
    p.bits = 50000
    p.hunger = p.strength = 4
    p.energy = p.max_energy
    p.world_seconds = hour * 60.0
    return p


def test_the_town_cup_honors_the_shared_cup_hour():
    import tuipet.townscreen as ts
    p = _cup_pet()
    t1 = ts.TownPanel(p, town_id=0)
    t1._start_cup()
    assert t1.sub is not None, t1.msg               # the hour's cup runs
    t2 = ts.TownPanel(p, town_id=3)                 # a fresh visit, same hour
    t2._start_cup()
    assert t2.sub is None, "the same game-hour ran a second town cup"
    assert "hour" in t2.msg
    p.world_seconds = 11 * 60.0                     # the next main-view hour
    t3 = ts.TownPanel(p, town_id=3)
    t3._start_cup()
    assert t3.sub is not None, t3.msg               # cadence, not a shut door


def test_a_town_cup_entry_spends_the_home_boards_hour_too():
    """The other direction of the same slot, now symmetric: burned AND
    checked on both boards."""
    from tuipet import tournament
    import tuipet.townscreen as ts
    p = _cup_pet()
    t1 = ts.TownPanel(p, town_id=0)
    t1._start_cup()
    assert t1.sub is not None
    home = tournament.trophy_by_id(tournament.schedule(p)[10])
    assert "run" in (tournament.eligibility(p, home) or "")


# ---- L5: the rationed counter buys the LIVE row (the grinder's note) -----

def _rich_town_pet():
    p = Pet(num=1455, stage="Champion", attribute="Vaccine")
    p.line_id = "ver1"
    p.bits = 500000
    return p


def test_a_stale_row_replay_cannot_oversell_the_ration():
    from tuipet import shop
    p = _rich_town_pet()
    row = next(r for r in shop.town_stock(0, pet=p) if r["left"] > 0)
    stale = dict(row)                               # the cached copy
    sold = 0
    for _ in range(row["left"] + 5):
        _msg, sfx = shop.town_buy(p, dict(stale))   # replayed, never rebuilt
        if sfx == "confirm":
            sold += 1
    assert sold == row["left"], f"stale replay sold {sold} of {row['left']}"


def test_a_forged_price_cannot_underpay():
    from tuipet import shop
    p = _rich_town_pet()
    row = next(r for r in shop.town_stock(0, pet=p) if r["left"] > 0)
    before = p.bits
    _msg, sfx = shop.town_buy(p, dict(row, price=1))
    assert sfx == "confirm"
    assert before - p.bits == row["price"], "the forged price was honored"


def test_the_gate_covers_every_numeric_field_generically():
    """The whole-roster sweep: poison EVERY field whose default is a plain
    number -- none may build a pet.  New Pet fields join automatically."""
    from dataclasses import MISSING, fields
    base = _healthy_save()
    for f in fields(Pet):
        proto = (f.default if f.default is not MISSING
                 else f.default_factory() if f.default_factory is not MISSING
                 else 0)
        if isinstance(proto, bool) or not isinstance(proto, (int, float)):
            continue
        if f.name in ("_lights_t", "egg_type"):
            # healed, not rejected, BEFORE the gate: a stringified _lights_t
            # coerces to float('-inf'); a non-int egg_type heals to egg 0
            # ("a classic Botamon egg beats a dead app")
            continue
        d = dict(base)
        d[f.name] = "banana"
        pet, _ = persistence.pet_from_save(d)
        assert pet is None, f"{f.name} accepted a string"
