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
    # Agumon (29) declares '10:-1:-1' -- the special rides ONLY the Vaccine slot
    special = data.load_orbs()["special"]
    generic = data.load_orbs()["generic"]
    assert data.attack_orb(29, "Vaccine", 0) == special["10"]
    assert data.attack_orb(29, "Data", 0) == generic["Data"][0]
    # Goburimon (25) declares '-1:-1:96' -- the special rides ONLY the Virus slot
    assert data.attack_orb(25, "Virus", 0) == special["96"]
    assert data.attack_orb(25, "Vaccine", 0) == generic["Vaccine"][0]


def test_power_tiers_floor_by_25_and_clamp_at_600():
    # num=-1 carries no species data -> always the generic path
    generic = data.load_orbs()["generic"]
    assert data.attack_orb(-1, "Data", 0) == generic["Data"][0]
    assert data.attack_orb(-1, "Data", 24) == generic["Data"][0]
    assert data.attack_orb(-1, "Data", 25) == generic["Data"][1]
    assert data.attack_orb(-1, "Data", 600) == generic["Data"][24]
    assert data.attack_orb(-1, "Data", 9999) == generic["Data"][24]
