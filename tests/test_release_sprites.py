"""Release gate for monster art (2026-10-14).  0.6.0 shipped the Godzilla line
with no projectiles, joy frames that were attack frames, and a solid-black
shot.  deploy.sh runs pytest, so these block a release.

KNOWN lists are cases that already exist and wait on Joel's call; anything
new fails."""
import gzip
import json
import os

from tuipet import data

_P = os.path.join(os.path.dirname(__file__), "..", "src", "tuipet", "data", "sprites.json.gz")
with gzip.open(_P, "rt", encoding="utf-8") as _f:
    SPRITES = json.load(_f)

HAPPY, ATTACK = 5, 6
KNOWN_HAPPY_IS_ATTACK = {118, 168}        # Nanimon, BomberNanimon (DVPet data)
KNOWN_SOLID_SHOT = set()
# legacy DVPet sprites whose attack frame repeats another slot (untouched art)
KNOWN_ATTACK_REPEATS = {12, 16, 31, 33, 34, 36, 45, 56, 78, 79, 82, 88, 90, 91, 94, 97, 103, 104, 108, 109, 111, 112, 114, 115, 117, 118, 168, 179, 180, 186, 187, 197, 213, 262, 269, 295, 338, 358, 360, 430, 583, 689, 812, 1455, 1459, 1624}
FIRST_OWN_SHOT_NUM = 1623                 # the Godzilla line on: every new species fires its own shot


def test_every_monster_has_eleven_real_frames():
    for e in SPRITES:
        assert len(e["frames"]) == 11, e["name"]
        for i, f in enumerate(e["frames"]):
            assert any("1" in r for r in f), (e["name"], i)
            assert {c for r in f for c in r} <= {"0", "1"}, (e["name"], i)


def test_joy_is_not_the_attack_frame():
    same = {e["num"] for e in SPRITES if e["frames"][HAPPY] == e["frames"][ATTACK]}
    assert same <= KNOWN_HAPPY_IS_ATTACK, sorted(same - KNOWN_HAPPY_IS_ATTACK)


def test_the_attack_frame_is_its_own_pose():
    """0.6.0.post2 shipped Botamon G with Attack == Eat (slots shuffled)."""
    rep = {e["num"] for e in SPRITES
           if any(e["frames"][ATTACK] == e["frames"][j] for j in range(11) if j != ATTACK)}
    assert rep <= KNOWN_ATTACK_REPEATS, sorted(rep - KNOWN_ATTACK_REPEATS)


def test_new_species_fire_their_own_shot():
    """0.6.0 shipped 28 kaiju on the generic orb: no deviceAttacks row."""
    own = data.load_device_attacks()
    for e in SPRITES:
        if e["num"] >= FIRST_OWN_SHOT_NUM:
            nm = "".join(c for c in e["name"].lower() if c.isalnum())
            assert nm in own, e["name"]


def test_every_monster_fires_a_real_shot():
    solid = set()
    for e in SPRITES:
        for attr in ("Vaccine", "Data", "Virus"):
            shot = data.attack_orb(e["num"], attr, 0)
            assert shot and any("1" in r for r in shot), (e["name"], attr)
            flat = "".join(shot)
            if flat.count("1") / len(flat) > 0.85:
                solid.add(e["num"])
    assert solid <= KNOWN_SOLID_SHOT, sorted(solid - KNOWN_SOLID_SHOT)
