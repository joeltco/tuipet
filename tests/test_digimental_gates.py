"""The Digimental waves (Joel 2026-07-17: "do it. wire the gates") -- the
canon discovery order on the egg-carousel rule: a sealed Digimental is
simply not on the shelf.  Courage & Hope from day one; the crest seven
after the FIRST armor evolution; Light/Kindness at 25 wins; Miracles at 2
felled raids; Destiny at generation 5."""
from tuipet import persistence, shop
from tuipet.pet import Pet


def _shelf_keys():
    return {e["key"] for e in shop.catalog() if e["category"] == shop.ARMOR_CATEGORY}


def test_day_one_shelf_is_courage_and_hope():
    assert _shelf_keys() == {"egg_of_courage", "egg_of_hope"}


def test_first_armor_evolution_opens_the_crest_seven():
    persistence.armor_add(1)
    assert {"egg_of_friendship", "egg_of_love", "egg_of_knowledge",
            "egg_of_sincerity", "egg_of_reliability"} <= _shelf_keys()
    assert "egg_of_light" not in _shelf_keys()


def test_the_later_waves_ride_wins_raids_and_generation():
    persistence.wins_add(25)
    assert {"egg_of_light", "egg_of_kindness"} <= _shelf_keys()
    assert "egg_of_miracles" not in _shelf_keys()
    persistence.raid_add(); persistence.raid_add()
    assert "egg_of_miracles" in _shelf_keys()
    assert "egg_of_destiny" not in _shelf_keys()
    persistence._note_max("max_gen", 5)
    assert "egg_of_destiny" in _shelf_keys()


def test_every_wave_key_is_a_real_crest():
    assert set(shop.DIGIMENTAL_GATES) == set(Pet._CREST_IDS)


def test_a_sealed_digimental_still_renders_in_the_bag():
    """entry() must resolve an owned-but-sealed one (bought before the wave
    system, or the wave regressed) -- the bag never hides property."""
    e = shop.entry("egg_of_destiny")
    assert e and e["name"] == "Destiny Egg"


def test_the_armor_evolution_counts_itself():
    """Pet._crest_egg pays the armor_evos signal the friendship wave reads."""
    before = persistence.get_progress()["armor_evos"]
    persistence.armor_add(1)
    assert persistence.get_progress()["armor_evos"] == before + 1
