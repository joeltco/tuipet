"""The DVPet CSV loaders parse cleanly and return the shapes the game relies on.

These guard against a data refresh (re-running setup_assets.sh) silently dropping
a column or changing a format — the kind of break that wouldn't surface until the
egg screen or Futon misbehaved in play.
"""
from tuipet import data, egg


def test_care_effects_load():
    eff = data.load_care_effects()
    assert isinstance(eff, dict) and eff, "careEffect.csv produced no effects"
    for e in eff.values():
        for k in ("name", "duration", "mood", "energy", "hunger", "strength",
                  "end_on_sleep", "pause_temp", "pause_call", "can_reapply"):
            assert k in e
        # rate fields are (amount, every_n_ticks) pairs
        assert len(e["mood"]) == 2 and len(e["energy"]) == 2


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
    needed = {"start", "price", "map", "stage", "xanti", "tourney", "zone", "gen",
              "prev_field", "prev_attr", "prev_elem", "history", "food", "item",
              "habitat", "password", "obedience", "mood", "desc", "can_perm"}
    for rule in rules.values():
        assert needed <= set(rule)
    # at least one starter egg, and at least one egg behind a price (a real bits sink)
    assert any(r["start"] for r in rules.values())
    assert any(r["price"] > 0 for r in rules.values())


def test_egg_count_sane():
    assert egg.count() >= 5, "expected the base egg roster to load"
