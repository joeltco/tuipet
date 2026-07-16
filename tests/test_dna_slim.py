"""The DNA slim (BASIC VPET 2026-07-16): Generate/Charge/Stats/Divergence
survive; the gate-forgiveness and the Requirements page left; the charge
bill rides ENERGY (the mood/spirit bills left with their systems)."""
from tuipet.pet import Pet, DNA_SAME_FIELD_ENERGY, DNA_DIFF_FIELD_ENERGY
from tuipet.dnascreen import DNAPanel, _HOME


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 10 * 60.0
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_charging_bills_energy_doubled_off_field():
    p = _pet(energy=24, max_energy=24)
    p.dna_owned[p.field] = 10
    assert p.apply_dna(p.field, 4)
    assert p.energy == 24 - DNA_SAME_FIELD_ENERGY * 4
    q = _pet(energy=24, max_energy=24)
    off = next(f for f in q.dna_owned if f != q.field)
    q.dna_owned[off] = 10
    assert q.apply_dna(off, 4)
    assert q.energy == 24 - DNA_DIFF_FIELD_ENERGY * 4


def test_the_home_menu_lost_the_requirements_page():
    assert [k for k, _ in _HOME] == ["charge", "generate", "stats", "roads"]
    pan = DNAPanel(_pet())
    assert "Requirements" not in pan.text().plain


def test_dna_panel_smoke_walk():
    pan = DNAPanel(_pet(bits=500))
    for _ in range(len(_HOME) + 1):        # walk the whole home menu
        assert pan.text().plain
        pan.key("down")
        pan.anim()
    pan.key("enter")                        # open whichever page is under the cursor
    assert pan.text().plain
    pan.key("escape")
