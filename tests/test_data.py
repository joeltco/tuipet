"""The DVPet CSV loaders parse cleanly and return the shapes the game relies on.

These guard against a data refresh (re-running setup_assets.sh) silently dropping
a column or changing a format — the kind of break that wouldn't surface until the
egg screen or Futon misbehaved in play.
"""
from tuipet import data, egg


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
    """The authentic growth rank (Egg, Baby I .. Super Ultimate); unknown = fully grown."""
    assert data.STAGE_RANK == ["Egg"] + data.STAGE_ORDER
    assert data.stage_rank("Egg") == 0
    assert data.stage_rank("Baby I") == 1
    assert data.stage_rank(data.STAGE_ORDER[-1]) == len(data.STAGE_RANK) - 1
    assert data.stage_rank("Bogus") == len(data.STAGE_RANK)
    # the rank must be monotonic in growth order
    ranks = [data.stage_rank(s) for s in data.STAGE_RANK]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
