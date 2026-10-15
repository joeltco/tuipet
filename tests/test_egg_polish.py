"""Regression probes for egg audit 2026-10-14; all persistence is sandboxed."""
import pytest

from tuipet import egg, persistence, shop
from tuipet.pet import Pet


class _App:
    def __init__(self, pet):
        from tuipet.app import TuiPetApp
        self.pet = pet
        self._grant_digimemory = TuiPetApp._grant_digimemory.__get__(self)
        self._hatch_new = TuiPetApp._hatch_new.__get__(self)

    def _do(self, msg):
        self.msg = msg


def _godzilla():
    return next(i for i in range(egg.count())
                if egg.hatch_name(i) == egg.GODZILLA_EGG)


def test_live_retirement_preserves_unused_memory():
    p = Pet(num=100, stage="Champion", generation=2)
    mem = {"name": "Elder", "num": 100, "vaccine": 5, "data": 3, "virus": 2}
    p.digimemory = dict(mem)
    p.inventory["digimemory"] = 1
    app = _App(p)
    app._hatch_new(1, 3)
    assert app.pet.digimemory == mem
    assert app.pet.inventory["digimemory"] == 1
    assert persistence.peek_digimemory() is None
    assert persistence.load()[0].digimemory == mem


@pytest.mark.parametrize("other_first", [False, True])
def test_fragment_survives_unhatched_repick(other_first):
    idx = _godzilla()
    p = Pet.new_egg(egg_type=idx)
    p.gcell_fragment = True
    app = _App(p)
    app._hatch_new(1 if other_first else idx, 2)
    if other_first:
        assert not app.pet.gcell_fragment
        assert persistence.gcell_fragment_waiting()
        app._hatch_new(idx, 2)
    assert app.pet.gcell_fragment
    assert not persistence.gcell_fragment_waiting()
    assert app.pet.generation == 1
    assert persistence.load()[0].gcell_fragment


@pytest.mark.parametrize("surface", ["memorial", "hall", "legacy"])
def test_every_lifespan_reads_real_time(surface):
    """4.5 real days of age_seconds reads 4d12h on every surface (the STATUS
    Age row's unit, petbase.AGE_DAY) -- never the 60x '270d'."""
    from tuipet.deathscreen import _age_str
    from tuipet.digicore import _legacy_rows
    from tuipet.hallscreen import HallPanel
    p = Pet(num=100, name="Elder", stage="Champion", age_seconds=388800.0, dead=True)
    persistence.snapshot_prev_gen(p)
    if surface == "memorial":
        shown = _age_str(p.age_seconds)
    elif surface == "hall":
        hall = HallPanel()
        shown = hall._epitaph(hall.elders[0])
    else:
        shown = _legacy_rows()[0][1]
    assert "4d" in shown and "12h" in shown and "270d" not in shown


@pytest.mark.parametrize("idx", [-1, 100000, "guide", 1.5])
def test_invalid_egg_purchase_does_not_charge_or_own(idx):
    p = Pet(num=100, stage="Champion", bits=20000)
    msg, sfx = shop.town_egg_buy(p, idx)
    assert sfx == "error", msg
    assert p.bits == 20000
    assert persistence.get_eggs_owned() == set()
    assert p.town_bought == {}


def test_help_explains_estate_and_unhatched_repick():
    from tuipet.helpscreen import HELP
    text = "\n".join(line for line, _ in HELP)
    assert "Bits, inventory, trophies and" in text
    assert "Unhatched re-picks keep the gen." in text


def test_retirement_cannot_reset_profile_daily_egg_limit():
    p = Pet(num=100, stage="Champion", generation=2, bits=50000)
    first, second = shop._sellable_eggs()[:2]
    assert shop.town_egg_buy(p, first)[1] == "reward"
    ledger = dict(p.town_bought)
    app = _App(p)
    app._hatch_new(1, 3)
    msg, sfx = shop.town_egg_buy(app.pet, second)
    assert sfx == "error", msg
    assert app.pet.bits == 40000
    assert app.pet.town_bought == ledger
    assert second not in persistence.get_eggs_owned()


def test_volcanic_beat_egg_hatches_its_own_line_and_opens_on_the_volcano_road():
    """Joel 2026-10-15: the official Volcanic Beat DIM card as an egg line,
    earned by clearing the Volcano road (map 21, index 20)."""
    from tuipet import adventure, data, egg, lines
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Volcanic Beat Egg")
    assert adventure.MAPS[20]["scene"] == "volcano"
    rule = data.load_egg_unlock()[idx]
    base = {"maps": set(), "maps_cleared": set(), "raids": 0}
    prog = dict(persistence.get_progress(), **base)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {20}
    assert egg._conditions_met(rule, prog)
    prog.update(maps_cleared=set(), maps={3})          # area 4 cleared = maps 19-24
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1603 and p.line_id == "vbe" and lines.active(p)
    v = lines.load_lines()["vbe"]
    assert len(v["members"]) == 17


def test_infinite_tide_egg_hatches_its_own_line_and_opens_on_seafloor_deep():
    """Joel 2026-10-15: the official Infinite Tide DIM card as an egg line,
    earned by clearing the Seafloor Deep road (map 16, index 15) -- the road
    whose boss is the line's own Plesiomon."""
    from tuipet import adventure, data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Infinite Tide Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {15}
    assert egg._conditions_met(rule, prog)
    assert data.record_for(adventure.ZONES[15]["bosses"][0]["num"])["name"] == "Plesiomon"
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1602 and p.line_id == "iti"
    deep = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Deep Savers Egg")
    q = Pet.new_egg(egg_type=deep)
    q._hatch_into_fresh()
    assert q.num == 1602 and q.line_id == "dsv"          # the shared baby keeps its own line
    assert len(lines.load_lines()["iti"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"   # earned, never sold


def test_nu_metal_empire_egg_hatches_bommon_into_its_line_on_the_factory_road():
    """Joel 2026-10-15: the official Nu Metal Empire DIM card as an egg line,
    earned on the Factory road (map 28, index 27) -- Machinedramon's road,
    the line's own Mugendramon."""
    from tuipet import adventure, data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Nu Metal Empire Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {27}
    assert egg._conditions_met(rule, prog)
    assert adventure.ZONES[27]["bosses"][0]["num"] == 276      # Mugendramon/Machinedramon
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 960 and p.line_id == "nme"
    assert len(lines.load_lines()["nme"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_blizzard_fang_egg_hatches_yukimibotamon_into_its_line_on_frozen_peak():
    """Joel 2026-10-15: the official Blizzard Fang DIM card as an egg line,
    earned on the Frozen Peak road (map 17, index 16); Daipenmon keeps the
    card's Ultimate slot while playing as its global Mega."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Blizzard Fang Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {16}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1410 and p.line_id == "bfa"
    meicoo = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Meicoo Egg")
    q = Pet.new_egg(egg_type=meicoo)
    q._hatch_into_fresh()
    assert q.num == 1410 and q.line_id != "bfa"        # the shared baby keeps its line
    line = lines.load_lines()["bfa"]
    assert len(line["members"]) == 17 and 696 in line["members"]
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"
