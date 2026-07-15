"""The projectile pins: every species fires its OWN attack shape (the
atlas' attack_sprite index into the 50 shipped bitmaps), deterministic and
frame-safe; unknown species fall back to the legacy attribute orbs."""
from tuipet import data


def test_every_species_fires_its_own_shape():
    d, _ = data.load_sprites()
    for rec in d[:40]:
        orb = data.attack_orb(rec["num"], rec["attribute"], 0)
        assert orb and any("1" in r for r in orb), rec["name"]
        want = data._attack_shape(rec["attack_sprite"])
        if want:
            assert orb == want, "the species' own shape fires"


def test_orb_is_frame_i_safe_and_static():
    d, _ = data.load_sprites()
    n = d[0]["num"]
    a = data.attack_orb(n, "Vaccine", 0, frame_i=0)
    b = data.attack_orb(n, "Vaccine", 0, frame_i=7)
    assert a == b, "shapes are static bitmaps"


def test_unknown_species_falls_back_to_attribute_orbs():
    orb = data.attack_orb(10 ** 6, "Virus", 50)
    assert orb and any("1" in r for r in orb)
