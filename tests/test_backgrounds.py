"""The Great Simplification (Joel 2026-07-15): weather, temperature, habitats
and the day/night cycle are gone.  The scene behind the mon is a picked
cosmetic from the DSprite official-art catalog -- basic scenes free, fancy
ones priced in bits; townBack survives for adventure town events only."""
from tuipet import backgrounds as bgs
from tuipet import data, persistence
from tuipet.pet import Pet


def _pet(**kw):
    # a dex-consistent identity (Goburimon), so save round-trips never take
    # the repair path and clobber the migration message
    p = Pet(num=25, name="Goburimon", stage="Rookie", attribute="Virus",
            obedience=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_every_catalog_scene_ships_a_frame():
    sheets = data.load_backgrounds()
    for key in bgs.CATALOG:
        assert key in sheets and sheets[key], key
        fr = sheets[key][0]
        assert len(fr) == 24 and all(len(r) == 240 for r in fr), key


def test_the_whole_catalog_is_free_for_now():
    # Joel 2026-07-16: price walls removed (the price column stays for later)
    assert set(bgs.FREE) == set(bgs.CATALOG)
    assert bgs.DEFAULT in bgs.CATALOG


def test_the_dmc_device_set_is_pickable():
    # the Digital Monster COLOR backgrounds (tile re-audit 2026-07-16)
    for key in ("greenhills", "desert", "lakeside", "mountains", "cove"):
        assert key in bgs.CATALOG, key


def test_godzilla_range_is_data_not_picks():
    """The Godzilla-range tiles stay shipped (roads/special rooms wear them)
    but are not choosable home scenes (Joel 2026-07-16)."""
    sheets = data.load_backgrounds()
    # (the Digital Monster COLOR device set -- greenhills/desert/lakeside/
    # mountains/cove, gbg37-41 -- is the verified EXCEPTION and stays picked)
    for key in ("city", "cityday", "citysunset", "jungle", "factory",
                "factorynight", "fileisland", "islandsea", "islandnight",
                "boulevard", "boulevardusk"):
        assert key not in bgs.CATALOG, key
        assert sheets.get(key), key                # ...but the art still ships


def test_town_survives_for_adventures_only():
    assert bgs.TOWN == "townBack"
    assert bgs.TOWN not in bgs.CATALOG              # never a home pick
    assert data.load_backgrounds().get(bgs.TOWN)
    assert bgs.ARENA in bgs.CATALOG                 # the cup floor is real art


def test_every_zone_biome_wears_a_real_scene():
    sheets = data.load_backgrounds()
    for hid in data.load_habitats():
        key = bgs.biome_frame_key(hid)
        assert key in sheets, (hid, key)


def test_background_returns_the_picked_scene():
    p = _pet()
    assert p.background() == data.load_backgrounds()[bgs.DEFAULT][0]
    p.bg_current = "underwater"
    assert p.background() == data.load_backgrounds()["underwater"][0]
    assert p.background(file="volcano") == data.load_backgrounds()["volcano"][0]
    # off-catalog data scenes still render when a road asks by file
    assert p.background(file="city") == data.load_backgrounds()["city"][0]
    assert p.background(file="nope") is None


def test_free_scenes_hang_without_paying():
    p = _pet(bits=0)
    assert p.owns_background("volcano")
    assert "it is" in p.pick_background("volcano")
    assert p.bg_current == "volcano" and p.bits == 0
    assert p.pick_background("city") == "?"          # off-catalog: not a pick


def test_the_pick_persists_and_old_picks_normalize():
    p = _pet()
    p.pick_background("volcano")
    d = persistence.to_save_dict(p)
    p2, _ = persistence.pet_from_save(d, catch_up=False)
    assert p2.bg_current == "volcano"
    # a save whose pick left the catalog (a retired scene) resets to the
    # default rather than wearing data-art
    d["bg_current"] = "city"
    d["bg_owned"] = ["city", "volcano"]
    p3, _ = persistence.pet_from_save(d, catch_up=False)
    assert p3.bg_current == bgs.DEFAULT
    assert p3.bg_owned == ["volcano"]


def test_old_saves_get_their_habitat_bits_back():
    """A pre-rebuild save owns habitats -- the retired economy refunds every
    PURCHASED home at full price (the starter pair 0/2 came free)."""
    p = _pet(bits=42)
    d = persistence.to_save_dict(p)
    d.pop("bg_owned", None)
    d.pop("bg_current", None)
    d["habitats"] = [0, 2, 14, 15]                 # bought Volcano + Desert homes
    d["habitat"] = 14
    d["weather"] = "HeavyRain"                     # stale fields must not crash
    d["temp"] = 12.5
    p2, msg = persistence.pet_from_save(d, catch_up=False)
    habs = data.load_habitats()
    want = habs[14]["price"] + habs[15]["price"]
    assert p2.bits == 42 + want
    assert "refunded" in msg
    assert p2.bg_current == bgs.DEFAULT
    # an unbought old save migrates silently
    d["habitats"] = [0, 2]
    p3, msg3 = persistence.pet_from_save(d, catch_up=False)
    assert p3.bits == 42 and "refunded" not in (msg3 or "")


def test_picker_panel_hangs_scenes():
    from tuipet.backgroundscreen import BackgroundPanel
    p = _pet()
    pan = BackgroundPanel(p)
    assert "here" in pan.strip()
    pan.cursor = pan.rows.index("volcano")
    pan.key("enter")
    assert p.bg_current == "volcano"
    assert "it is" in pan.msg
    pan.key("enter")
    assert "Already up" in pan.msg
    done = pan.key("escape")
    assert done and done[0] == "done"
