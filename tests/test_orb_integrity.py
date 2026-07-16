"""Every Digimon must fire the correct attack orb (2026-07-14 audit pin).

The orb chain is DVPet checkAttackSprite (SpriteAnim.java:14809): a species
with a special-orb index (digimon.csv 'SpecialAttacksVaccineDataVirus',
parsed vaccine:data:virus per EvolutionInfo info[54]) fires that exact cell
of attackSpritesSpecial.png; everyone else fires the generic per-attribute
orb at power tier floor(min(power,600)/25).  The full audit (roster x
original-DVPet-csv diff x sheet re-extraction) came back clean -- these pins
keep it that way without needing the gitignored _extract/raw_resources."""
import csv
import os

from tuipet import data


def _roster_attack_indices():
    path = os.path.join(os.path.dirname(data.__file__), "data", "digimon.csv")
    for r in csv.DictReader(open(path)):
        if not (r.get("DigimonNum") or "").strip().lstrip("-").isdigit():
            continue
        yield int(r["DigimonNum"]), r.get("Name"), (r.get("SpecialAttacksVaccineDataVirus") or "")


def test_every_declared_special_orb_index_has_real_ink():
    special = data.load_orbs()["special"]
    bad = []
    for num, name, raw in _roster_attack_indices():
        for part in raw.split(":"):
            part = part.strip()
            if not part.lstrip("-").isdigit():
                bad.append(f"{num} {name}: malformed {raw!r}")
                continue
            idx = int(part)
            if idx == -1:
                continue
            frame = special.get(str(idx))
            if not (0 <= idx < 100) or not frame or not any("1" in row for row in frame):
                bad.append(f"{num} {name}: idx {idx} -> no sprite")
    assert not bad, bad[:10]


def test_generic_orbs_cover_all_25_tiers_of_all_3_attributes():
    generic = data.load_orbs()["generic"]
    for attr in ("Vaccine", "Data", "Virus"):
        tiers = generic[attr]
        assert len(tiers) == 25, f"{attr}: {len(tiers)} tiers"
        holes = [t for t, fr in enumerate(tiers) if not fr or not any("1" in r for r in fr)]
        assert not holes, f"{attr}: empty tiers {holes}"


def test_attack_orb_yields_ink_for_the_whole_roster_at_every_power():
    silent = []
    for num, name, _raw in _roster_attack_indices():
        for attr in ("Vaccine", "Data", "Virus"):
            for power in (0, 300, 600):
                orb = data.attack_orb(num, attr, power)
                if not orb or not any("1" in row for row in orb):
                    silent.append(f"{num} {name} {attr}@{power}")
    assert not silent, silent[:10]


def test_the_column_order_is_vaccine_data_virus():
    # SnowAgumon (26) declares '91:-1:-1' -- the special rides ONLY the Vaccine
    # slot (device-uncovered species; Agumon itself now fires its DEVICE attack)
    special = data.load_orbs()["special"]
    generic = data.load_orbs()["generic"]
    assert data.attack_orb(26, "Vaccine", 0) == special["91"]
    assert data.attack_orb(26, "Data", 0) == generic["Data"][0]
    # Goburimon (25) declares '-1:-1:96' -- the special rides ONLY the Virus slot
    assert data.attack_orb(25, "Virus", 0) == special["96"]
    assert data.attack_orb(25, "Vaccine", 0) == generic["Vaccine"][0]


def test_device_species_fire_their_own_attack_for_every_attribute():
    """Device-accurate attacks (Joel 2026-07-14): a real-hardware species fires
    ITS attack no matter the attribute or power -- like the original V-Pet.
    Agumon (29) is covered (DU weapon rip; the 2026-07 orb fix -- the old
    MultiVPet spr_*_attack_vpet frames were attack POSES, not projectiles)."""
    dev = data.load_orbs()["device"]
    ag = dev["agumon"][0]
    assert data.attack_orb(29, "Vaccine", 0) == ag
    assert data.attack_orb(29, "Data", 600) == ag
    assert data.attack_orb(29, "Virus", 300) == ag


def test_device_attacks_are_static_and_frame_i_safe():
    """The device projectiles are single static frames (the hardware's attack
    sprite doesn't animate in flight); frame_i must be safe to pass anyway.
    The old '27 animated' pin covered MultiVPet POSE anims -- retired with
    the orb fix."""
    dev = data.load_orbs()["device"]
    assert all(len(v) == 1 for v in dev.values())
    ag = dev["agumon"][0]
    assert data.attack_orb(29, "Vaccine", 0, frame_i=0) == ag
    assert data.attack_orb(29, "Vaccine", 0, frame_i=7) == ag


def test_the_device_bank_is_complete_and_in_band():
    """deviceAttacks.csv rows must all resolve: a real roster species, a device
    bank entry with ink, and frames that fit the 16px battle band.  Also guards
    the bank against an extractor clobber (the effects.json.gz lesson)."""
    import csv as _csv
    dev = data.load_orbs()["device"]
    assert len(dev) == 75, len(dev)      # 6 species have no DU weapon: DVPet fallback
    ddir = os.path.join(os.path.dirname(data.__file__), "data")
    roster = {"".join(c for c in r["Name"].lower() if c.isalnum())
              for r in _csv.DictReader(open(os.path.join(ddir, "digimon.csv")))}
    rows = list(_csv.DictReader(open(os.path.join(ddir, "deviceAttacks.csv"))))
    assert len(rows) == 75
    for r in rows:
        nm = "".join(c for c in r["Name"].lower() if c.isalnum())
        assert nm in roster, f"{r['Name']} not in roster"
        frames = dev.get(r["AttackKey"])
        assert frames, f"{r['AttackKey']} missing from device bank"
        assert len(frames) == int(r["Frames"])
        for f in frames:
            assert len(f) <= 16 and len(f[0]) <= 16, f"{r['AttackKey']} exceeds the band"
            assert any("1" in row for row in f), f"{r['AttackKey']} has a blank frame"


def test_power_tiers_floor_by_25_and_clamp_at_600():
    # num=-1 carries no species data -> always the generic path
    generic = data.load_orbs()["generic"]
    assert data.attack_orb(-1, "Data", 0) == generic["Data"][0]
    assert data.attack_orb(-1, "Data", 24) == generic["Data"][0]
    assert data.attack_orb(-1, "Data", 25) == generic["Data"][1]
    assert data.attack_orb(-1, "Data", 600) == generic["Data"][24]
    assert data.attack_orb(-1, "Data", 9999) == generic["Data"][24]
