"""The DVPet CSV loaders parse cleanly and return the shapes the game relies on.

These guard against a data refresh (re-running setup_assets.sh) silently dropping
a column or changing a format — the kind of break that wouldn't surface until the
egg screen misbehaved in play.
"""
from tuipet import data, egg


# (test_care_effects_load left with the careEffect runtime:
# strict-DSprite items, 2026-07-17)


def test_digicore_icons_load():
    icons = data.load_digicore_icons()
    assert isinstance(icons, dict) and icons, "digicoreMenuConfig.csv produced no badges"
    assert set(icons.values()) <= {"Burst", "Twelve", "Two", "Dark"}
    assert all(isinstance(k, int) for k in icons)


def test_egg_unlock_load():
    rules = data.load_egg_unlock()
    assert isinstance(rules, dict) and rules, "eggUnlock.csv produced no rules"
    assert all(isinstance(k, int) for k in rules), "rules must be keyed by egg index"
    # every rule index is a real egg
    assert all(0 <= k < egg.count() for k in rules)
    # every rule carries the full evaluated condition set egg.py reads
    needed = {"start", "map", "stage", "xanti", "tourney", "zone", "gen",
              "prev_field", "prev_attr", "prev_elem", "history", "food", "item",
              "habitat", "password", "obedience", "mood", "desc", "can_perm"}
    for rule in rules.values():
        assert needed <= set(rule)
        # the licence economy is dead (2026-07-17): no rule carries a price
        assert "price" not in rule and "store" not in rule
    # at least one starter egg, and at least one earned condition gate
    assert any(r["start"] for r in rules.values())
    assert any(not r["start"] and r["desc"] for r in rules.values())


def test_egg_count_sane():
    assert egg.count() >= 5, "expected the base egg roster to load"


def test_pretty_field():
    """CamelCase Field values get spaced for display; data keys stay joined."""
    assert data.pretty_field("NightmareSoldier") == "Nightmare Soldier"
    assert data.pretty_field("DeepSaver") == "Deep Saver"
    assert data.pretty_field("MetalEmpire") == "Metal Empire"
    assert data.pretty_field("None") == "None"
    assert data.pretty_field("") == ""
    assert data.pretty_field(None) == ""
    # every real field value spaces cleanly and stays within the 17-col DNA column
    _, by = data.load_sprites()
    for f in {r.get("field", "") for r in by.values() if r.get("field")}:
        pretty = data.pretty_field(f)
        assert pretty.replace(" ", "") == f          # only spaces inserted
        assert len(pretty) <= 17


def test_stage_rank_helper():
    """The consolidated 7-stage rank (Egg..Mega); unknown stage = fully grown."""
    assert data.STAGE_RANK == ["Egg"] + data.STAGE_ORDER
    assert data.stage_rank("Egg") == 0
    assert data.stage_rank("Fresh") == 1
    assert data.stage_rank("Mega") == len(data.STAGE_RANK) - 1
    assert data.stage_rank("Bogus") == len(data.STAGE_RANK)
    # the rank must be monotonic in growth order
    ranks = [data.stage_rank(s) for s in data.STAGE_RANK]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
