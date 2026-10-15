"""Evolution audit 2026-10-14: chart clocks and special-road anchoring."""
import pytest

from tuipet import data, digicore, evolution, lines
from tuipet.pet import Pet


def test_spec_census_and_rule_grammar_match_the_shipped_chart():
    import csv
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = (root / "LINES_SPEC.md").read_text(encoding="utf-8")
    with open(root / "src/tuipet/data/lines.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    census = re.search(r"currently (\d+) lines, (\d+) rows", spec)
    assert census and tuple(map(int, census.groups())) == (len(lines.load_lines()), len(rows))
    documented = set(re.findall(r"`([A-Z][A-Z0-9]*)(?: [^`]*)?`", spec))
    used = {k.upper() for line in lines.load_lines().values()
            for kids in line["children"].values() for row in kids
            for alt in row["rule"] for k, _, _ in alt}
    assert used <= documented


def test_help_qualifies_the_mega_route_with_branch_dead_ends():
    from tuipet.helpscreen import HELP
    grow = [text for text, _ in HELP]
    section = grow[grow.index("GROW"):grow.index("x DNA - steer the next evolution:")]
    assert any("branches stop" in text for text in section)


@pytest.mark.parametrize("lid", ["x3a", "x3b"])
def test_dmx_mega_care_road_runs_at_the_existing_late_window(lid):
    p = Pet.from_num(1290)                 # Magnadramon X -> Magnamon X
    p.line_id = lid
    p.exp = 5000
    p.care_mistakes = 0
    assert lines.select_line(p) == 1314
    assert p._evolve_after() == p.LATE_STAGE_WINDOW
    assert digicore.growth_clock(p) == p.LATE_STAGE_WINDOW
    p.stage_seconds = p.LATE_STAGE_WINDOW - 1
    p._maybe_evolve()
    assert p.num == 1290
    p.stage_seconds += 1
    p._maybe_evolve()
    assert p.num == 1314 and p.line_id == lid
    assert lines.active(p)
    assert p._evolve_after() == 9e9         # the terminal Ultra stays terminal


def test_unknown_updated_rule_is_unmet_in_the_checklist(monkeypatch):
    rule = lines.parse_rule("FUTURE 3+")
    row = {"num": 93, "rule": rule, "jogress": None}
    monkeypatch.setattr(lines, "load_lines", lambda: {
        "ver1": {"members": {29: {}, 93: row}, "children": {29: [row]}}})
    p = Pet.from_num(29)
    p.line_id = "ver1"
    assert lines.select_line(p) is None
    report = lines.requirement_report(p, 93)
    assert report and report[0][0] is False
    assert "FUTURE" in report[0][1]
    assert lines.evo_rows(p)[0][2:] == (False, 1)


def test_mode_reversion_adopts_the_chart_that_claims_its_landing(monkeypatch):
    p = Pet.from_num(1038)                 # MetalGreymon AM is off-chart
    p.line_id = ""
    p.energy = p.max_energy
    p.vaccine = p.data_power = p.virus = 10000
    monkeypatch.setattr(Pet, "check_refused", lambda self, **kw: False)
    assert evolution.pre_evolution(p.num) == 220
    old, msg = p.mode_change()
    assert old == 1038 and p.num == 220
    assert p.line_id and lines.active(p), msg


def test_off_chart_mode_keeps_the_original_chart_for_reversion(monkeypatch):
    from tuipet import persistence

    p = Pet.from_num(220)
    p.line_id = "godzilla"
    p.energy = p.max_energy
    p.vaccine = p.data_power = p.virus = 10000
    monkeypatch.setattr(Pet, "check_refused", lambda self, **kw: False)
    monkeypatch.setattr(evolution, "mode_targets", lambda pet: [1038])
    p.mode_change()
    assert p.num == 1038
    assert not lines.active(p) and p.line_id == "godzilla"
    p, msg = persistence.pet_from_save(persistence.to_save_dict(p))
    assert p is not None and p.line_id == "godzilla", msg
    p.energy = p.max_energy
    p.mode_change()
    assert p.num == 220 and p.line_id == "godzilla" and lines.active(p)


def test_jogress_only_mega_keeps_its_external_door():
    p = Pet.from_num(297)
    p.line_id = "ver1"
    assert lines.jogress_declared(p) == [(399, 398)]
    assert p._evolve_after() == 9e9
    p.stage_seconds = p.LATE_STAGE_WINDOW
    p._maybe_evolve()
    assert p.num == 297


def test_line_no_match_does_not_fall_through_to_the_corpus(monkeypatch):
    p = Pet.from_num(93)
    p.line_id = "ver1"
    p.stage_seconds = p._evolve_after()
    p.battle_log = []

    def corpus_called(pet):
        pytest.fail("an unfulfilled chart gate fell through to the corpus")

    monkeypatch.setattr(evolution, "select", corpus_called)
    p._maybe_evolve()
    assert p.num == 93 and p.line_id == "ver1"


def test_shipped_hatch_names_and_partner_checklists_have_no_hidden_name_leak():
    reqs = data.load_requirements()
    from tuipet import egg
    for idx in range(egg.count()):
        assert all(not reqs.get(n, {}).get("hidden_evo")
                   for n in egg.hatch_targets(idx))
    for line in lines.load_lines().values():
        for rows in line["children"].values():
            for row in rows:
                if isinstance(row["jogress"], int):
                    assert not reqs.get(row["jogress"], {}).get("hidden_evo")


def test_a_mode_change_never_lands_a_pet_in_a_vb_card_line():
    """MetalGreymon AM joined Mad Black Roar (2026-10-15); a pet from another
    chart that Mode-changes into it must not be captured by the card line --
    card lines are entered only through their own egg."""
    p = Pet.from_num(1038)
    p.line_id = ""
    assert lines.adopt_line(p) != "mbr"
