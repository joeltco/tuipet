"""Tier-1 split (2026-07-17): data.py is a FAÇADE over four domain modules.
Pins: every public loader resolves through the façade to the same object as
its owner; no loader body remains in data.py; the domains hold what the
plan assigned them."""
import inspect

from tuipet import data, data_core, data_meta, data_shop, data_world


def test_facade_is_thin_and_complete():
    src = inspect.getsource(data)
    assert "def load_" not in src                # no loader bodies in the façade
    owners = {
        data_core: ("load_sprites", "load_evolutions", "load_requirements",
                    "canonical_num", "stage_rank", "bob_frame", "DNA_FIELDS"),
        data_shop: ("load_foods", "load_vitems", "consumable_by_key",
                    "home_shop_pool", "load_loot_tables", "item_is_functional"),
        data_world: ("load_backgrounds", "load_effects", "load_icons",
                     "load_battle_fx", "load_enemies", "load_tournies",
                     "attack_orb", "load_orbs"),
        data_meta: ("load_egg_unlock", "load_titles",
                    "load_digicore_config", "title_name"),
    }
    for mod, names in owners.items():
        for n in names:
            assert getattr(data, n) is getattr(mod, n), (mod.__name__, n)


def test_every_domain_loader_actually_loads():
    assert len(data_core.load_sprites()[1]) > 1500
    assert data_shop.load_foods()
    assert data_world.load_backgrounds()
    assert data_meta.load_egg_unlock()


def test_no_module_swallowed_anothers_domain():
    for mod, foreign in ((data_shop, "load_sprites"),
                         (data_world, "load_egg_unlock"),
                         (data_meta, "load_foods")):
        src = inspect.getsource(mod)
        assert f"def {foreign}" not in src, (mod.__name__, foreign)
