"""Guard against the v0.2.0-0.2.1 regression: re-running tools/extract_effects.py
clobbered curated sprites (the MultiVPet poop, the st_* status icons, the dying
emote) because they're authored directly in effects.json.gz, not by the script.
The extractor now merges instead of overwriting; this pins the curated set so a
future clobber fails CI instead of shipping silently."""
from tuipet import data


def test_curated_effect_sprites_are_present():
    e = data.load_effects()
    curated = ("poop", "unhappy", "dying",
               "st_sick", "st_vitamin", "st_bandage", "st_fatigue",
               "st_injury", "st_medicine", "st_teach")
    missing = [k for k in curated if not e.get(k)]
    assert not missing, f"curated effect sprites missing (clobbered?): {missing}"


def test_poop_is_the_authentic_two_frame_sprite():
    # the real MultiVPet spr_poop_vpet is 2 frames, 8x8 -- NOT the 1-frame filth.png crop
    poop = data.load_effects()["poop"]
    assert len(poop) == 2, "poop must be the 2-frame MultiVPet sprite, not the filth.png crop"
    assert len(poop[0][0]) == 8 and len(poop[0]) == 8, "poop frame must be 8x8"
