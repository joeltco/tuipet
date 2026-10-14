"""Bug report 2026-10-14 (afif, 0.5.350 on Termux): `ValueError: unknown rule
atom: 'FRAG'`.  The self-updater installs the next release over the package
while the old build runs; the old build then read 0.6's evolution chart lazily
and died on a rule it had never heard of."""
from tuipet import lines
from tuipet.appboot import warm_data
from tuipet.pet import Pet


def test_an_unknown_rule_atom_is_a_closed_door_not_a_crash():
    rule = lines.parse_rule("ZORP 3+, CM 0-2")
    assert rule == [[("unknown", "ZORP", None), ("cm", 0, 2)]]
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    assert not lines.check_rule(p, rule)


def test_the_shipped_chart_has_no_unknown_atoms():
    for lid, line in lines.load_lines().items():
        for rows in line["children"].values():
            for row in rows:
                for alt in row["rule"]:
                    assert all(a[0] != "unknown" for a in alt), (lid, row["rule_text"])


def test_launch_pins_every_data_table_before_the_updater():
    lines.load_lines.cache_clear()
    warm_data()
    assert lines.load_lines.cache_info().currsize == 1
    from tuipet import data_core, data_world
    assert data_core.load_sprites.cache_info().currsize == 1
    assert data_world.load_orbs.cache_info().currsize == 1
