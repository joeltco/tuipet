"""Legacy town trophies remain readable after the town cup is retired."""
from tuipet import tournament
from tuipet.pet import Pet


def test_the_trophy_room_names_town_cups():
    """trophy_name speaks every id space: home labels, Town Cup #N for the
    900+ road trophies, the raw fallback only for truly unknown ids."""
    from tuipet import data
    home = data.load_tournies()[0]
    assert tournament.trophy_name(home["id"]) == tournament.trophy_label(home)
    assert tournament.trophy_name(tournament.TOWN_TROPHY_BASE + 11) == "Town Cup #12"
    assert tournament.trophy_name(899) == "cup 899"   # not a town, not a cup
    from tuipet import digicore
    p = Pet(num=100, stage="Champion")
    p.trophies_won = {tournament.TOWN_TROPHY_BASE + 3: "day 2"}
    rows = digicore._trophy_rows(p)
    assert any("Town Cup #4" in name for name, _v in rows)   # the room reads it
    assert not any(name.startswith("cup ") for name, _v in rows)
