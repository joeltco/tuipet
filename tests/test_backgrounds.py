"""The DSprite background catalog, wired to the eggs (BASIC VPET 2026-07-17).

Habitats left; the scene behind the mon is decided by the EGG the pet
hatched from and never moves.  Pins: total egg coverage, every wired scene
really exists in backgrounds.json.gz (a typo'd key would render a silent
black arena), the arena keeps its 5-frame sheet, and the manifest holds in
both directions like the icon/sound audits.
"""
from tuipet import backgrounds, data, egg
from tuipet.pet import Pet


def test_every_egg_is_wired_to_a_real_scene():
    sheets = data.load_backgrounds()
    for i in range(egg.count()):
        key = backgrounds.scene_for_egg(i)
        assert key in backgrounds.EGG_BG.values()
        assert key in sheets, f"egg {i} ({egg.hatch_name(i)}) wired to missing scene {key!r}"
        assert backgrounds.name(key) != key          # every pick has a display name


def test_egg_bg_covers_exactly_the_egg_roster():
    assert set(backgrounds.EGG_BG) == set(range(egg.count()))


def test_unknown_egg_falls_back_to_the_default():
    assert backgrounds.scene_for_egg(9999) == backgrounds.DEFAULT
    assert backgrounds.scene_for_egg(None) == backgrounds.DEFAULT
    assert backgrounds.DEFAULT in data.load_backgrounds()


def test_every_sheet_is_single_frame():
    """The DSprite look: one frame per scene -- the arena's day/night sheet
    flattened when the day/night system left (BASIC VPET 2026-07-17)."""
    sheets = data.load_backgrounds()
    for key, fr in sheets.items():
        assert len(fr) == 1, key


def test_every_sheet_is_wired_or_allowlisted():
    """Both directions, like the icon manifest: every shipped sheet is an
    egg scene, a special room, a digicore plate, or carries a reason."""
    ALLOWED_SILENT = {
        # off-catalog DSprite data scenes: no egg picked them (yet) -- kept
        # as real rips a future egg/system can wear without a data rebuild
        "boulevard", "boulevardusk", "citysunset", "fileisland",
        "islandnight", "jungle", "seafloor",
        # sunsetshore came BACK 2026-07-19: it briefly wore the cliffside
        # eggs, then Joel's bug report + a full-res look proved it SEABED
        # art (the warm band is sunlight through the water) -- renamed
        # Sunset Seafloor, pick-only again
        "sunsetshore",
        # their wearers (Sunamon / the Meicoomon egg skin) left with the
        # fake-egg cut (2026-07-17); the rips stay for a future wearer
        "desert", "tealhollow",
        # pick-only since the cliffside rewire (scene audit 2026-07-19):
        # cove's art is SEABED, not a coast -- the two Cliffside eggs moved
        # to sunsetshore; the sandy shallows stay on the E-picker shelf
        "cove",
    }
    wired = set(backgrounds.EGG_BG.values()) | {"tourneyBack"}
    plates = {k for k in data.load_backgrounds() if k.startswith("digicore")}
    dark = set(data.load_backgrounds()) - wired - plates - ALLOWED_SILENT
    assert not dark, f"shipped sheets nothing wears (and no reason on file): {sorted(dark)}"
    stale = {k for k in ALLOWED_SILENT
             if k in wired or k not in data.load_backgrounds()}
    assert not stale, f"allowlisted sheets that ARE wired (or gone): {sorted(stale)}"


def test_the_pet_wears_its_egg_scene_for_life():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.egg_type = 40                                  # baybridge (the movie twin)
    fr = p.background()
    assert fr == data.load_backgrounds()["baybridge"][0]
    p.evolve_to(101) if hasattr(p, "evolve_to") else None
    assert p.background() == fr                      # evolution never moves the home


def test_scene_display_names_follow_the_family_law():
    """Recolours of one composition share a family word (scene-name audit
    2026-07-20, done by LOOKING at the pixels).  Corrections: cove is a BEACH,
    not a seafloor (zero structural correlation with them); the real seafloor
    is ONE undersea scene at three lightings -- underwater/seafloor/sunsetshore.
    Display names stay unique; keys never change (saves carry them)."""
    from tuipet import backgrounds as bgs
    for k in ("forestgate", "goldenwood", "tealhollow"):
        assert "Hollow" in bgs.NAMES[k], k
    # the seafloor trio is one undersea scene, day/deep/sunset -- NOT cove
    for k in ("underwater", "seafloor", "sunsetshore"):
        assert "Seafloor" in bgs.NAMES[k], k
    assert bgs.NAMES["cove"] == "Beach"                # a shore, not a seafloor
    for k in ("islandsea", "fileisland", "islandnight"):
        assert bgs.NAMES[k].startswith("Island"), k   # one island, three times
    assert bgs.NAMES["blossom"].startswith("Flower Field")
    for k in ("baybridge", "bridgenight"):
        assert bgs.NAMES[k].startswith("Bay Bridge"), k
    names = list(bgs.NAMES.values())
    assert len(names) == len(set(names))        # no two scenes share a name


def test_cliffside_eggs_stand_on_the_shore_not_the_seabed():
    """TWICE re-homed (scene audits 2026-07-19): 'cove' was seabed art,
    then 'sunsetshore' proved seabed TOO (Joel's bug report — the warm
    band is sunlight through the water).  The island's rock-over-sea is
    the one true coast in the set; the water lines stay submerged on
    purpose."""
    from tuipet import backgrounds as bgs
    assert bgs.EGG_BG[3] == "islandsea"          # Yuramon (Cliffside)
    assert bgs.EGG_BG[14] == "islandsea"         # Ketomon (Cliffside)
    for i in (13, 18, 24):                       # the water lines: seabed is HOME
        assert "Seafloor" in bgs.NAMES[bgs.EGG_BG[i]], i
