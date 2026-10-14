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
