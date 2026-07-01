"""Guard against the v0.2.0-0.2.1 regression: re-running tools/extract_effects.py
clobbered curated sprites (the MultiVPet poop, the st_injury skull) because they're
authored directly in effects.json.gz, not by the script.  The extractor now merges
instead of overwriting; this pins the curated set so a future clobber fails CI
instead of shipping silently.

The v0.2.93 icon sweep pared the atlas to the glyphs DM20 actually shows beside the
pet or on the floor: poop, grave, the injury skull, and the wash spray.  The floating
`dying` emote was dropped -- DM20's dying song is shown through the pet's own pose, not
an overlay glyph (and wayland, the sprite source of truth, has no death glyph)."""
from tuipet import data


def test_curated_effect_sprites_are_present():
    e = data.load_effects()
    curated = ("poop", "grave", "st_injury", "wash")
    missing = [k for k in curated if not e.get(k)]
    assert not missing, f"curated effect sprites missing (clobbered?): {missing}"


def test_dropped_glyphs_stay_dropped():
    # the icon sweep pulled these; keep them out (no floating `!`, no dead copymon,
    # no `dying` emote overlay -- see the module docstring).
    e = data.load_effects()
    for k in ("attention", "copymon", "dying"):
        assert k not in e, f"{k!r} was dropped in the v0.2.93 sweep but is back in the atlas"


def test_poop_is_the_authentic_two_frame_sprite():
    # the real MultiVPet spr_poop_vpet is 2 frames, 8x8 -- NOT the 1-frame filth.png crop
    poop = data.load_effects()["poop"]
    assert len(poop) == 2, "poop must be the 2-frame MultiVPet sprite, not the filth.png crop"
    assert len(poop[0][0]) == 8 and len(poop[0]) == 8, "poop frame must be 8x8"


# (The battle_overlays.json banner + hit_explosion were the DVPet orb-clash spectacle;
# the battle is now a clean pose-animation, so those overlays + orbs.json were dropped.)
