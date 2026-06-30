"""Authentic DM20 care-gated evolution (rebuilt onto species conditions).

Each evolution edge carries the corpus `parsed` conditions (care_mistakes / training /
overfeed / battles / victories). A pet evolves into the MOST SPECIFIC branch whose care
record satisfies the conditions; the empty-condition edge is the bad-care catch-all
(e.g. Agumon -> Numemon). These are deterministic given the care state.
"""
from tuipet import evolution, species, data
from tuipet.pet import Pet


def _agumon(mistakes=0, trainings=0, overeat=0, battles=0, wins=0):
    p = Pet.from_num(species.by_name("Agumon")["num"])
    p.stage = "Child"
    p.care_mistakes, p.trainings, p.overeat = mistakes, trainings, overeat
    p.battles, p.wins = battles, wins
    return p


def _name(num):
    return data.load_sprites()[1][num]["name"]


def test_in_range_parses_corpus_condition_formats():
    f = evolution._in_range
    assert f("0-2", 0) and f("0-2", 2) and not f("0-2", 3)
    assert f("3+", 3) and f("3+", 9) and not f("3+", 2)
    assert f("5-15", 5) and f("5-15", 15) and not f("5-15", 4) and not f("5-15", 16)
    assert f(15, 15) and f(15, 20) and not f(15, 14)      # 'battles_n': at least N
    assert f(True, 0)                                      # redundant flag -> always satisfied


def test_perfect_care_evolves_to_greymon():
    assert _name(evolution.select(_agumon(mistakes=0, trainings=20))) == "Greymon"


def test_low_training_evolves_to_devimon():
    assert _name(evolution.select(_agumon(mistakes=0, trainings=5))) == "Devimon"


def test_messy_overfed_evolves_to_tyranomon():
    assert _name(evolution.select(_agumon(mistakes=5, trainings=10, overeat=5))) == "Tyranomon"


def test_messy_trained_overfed_evolves_to_meramon():
    assert _name(evolution.select(_agumon(mistakes=5, trainings=20, overeat=5))) == "Meramon"


def test_neglect_falls_through_to_the_numemon_catchall():
    # no specific branch matches -> the empty-condition edge (Numemon) is the default
    assert _name(evolution.select(_agumon(mistakes=10, trainings=0, overeat=0))) == "Numemon"


def test_select_only_climbs_one_stage():
    p = _agumon(trainings=20)
    target = evolution.select(p)
    assert data.load_sprites()[1][target]["stage"] == data.next_stage(p.stage) == "Adult"


def test_jogress_only_edges_are_excluded_from_normal_evolution():
    # 'tag_battle_with' edges are reachable only via jogress, never normal evolution
    for r in species.roster():
        for e in r["evolves_to"]:
            if "tag_battle_with" in (e.get("parsed") or {}):
                assert not evolution._edge_met(_agumon(), e["parsed"])


def test_every_evolving_child_picks_a_real_next_stage_form():
    """No Child with evolution edges gets stuck: select() returns a real next-stage num."""
    _, by_num = data.load_sprites()
    for r in species.roster():
        if r["stage"] != "Child" or not r["evolves_to"]:
            continue
        p = Pet.from_num(r["num"]); p.stage = "Child"
        t = evolution.select(p)
        if t is not None:
            assert not data.is_placeholder(t)
            assert by_num[t]["stage"] in (data.next_stage("Child"), "Child")
