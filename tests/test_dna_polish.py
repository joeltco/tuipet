"""DNA audit 2026-10-14: poisoned saves and player readouts, without balance changes."""
import inspect
import json
import random
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import data, digicore, evolution, persistence, statusbox
from tuipet.app import TuiPetApp
from tuipet.digicorescreen import DigiCorePanel, MON_T, EXPAND_T
from tuipet.dnascreen import DNAPanel, MASH_TICKS
from tuipet.pet import Pet


def pet(num=29):
    rec = data.load_sprites()[1][num]
    p = Pet(num=num, name=rec["name"], stage=rec["stage"], bits=10000)
    p.world_seconds = 600.0
    return p


def card(panel):
    class Stats:
        def update(self, text):
            self.text = Text.from_markup(text).plain
    app = SimpleNamespace(pet=panel.pet, mode=panel, stats_w=Stats())
    statusbox.dna(app)
    return app.stats_w.text


@pytest.mark.parametrize("field", ["dna_owned", "dna_applied", "dna_wager_pending"])
def test_null_dna_save_normalizes_before_any_consumer(field):
    blob = persistence.to_save_dict(pet())
    blob[field] = None
    p, _ = persistence.pet_from_save(blob, strict=True)
    assert p is not None
    panel = DNAPanel(p)
    assert panel.text().plain and card(panel)
    assert p.highest_dna() == ""
    assert p.dna_wager_pending == 0


@pytest.mark.parametrize("field,value", [
    ("dna_owned", {"DeepSaver": "8"}),
    ("dna_owned", {"DeepSaver": -1}),
    ("dna_owned", {"DeepSaver": 100}),
    ("dna_owned", {"UnknownField": 5}),
    ("dna_owned", {"DeepSaver": True}),
    ("dna_applied", {"DeepSaver": "8"}),
    ("dna_applied", {"DeepSaver": float("nan")}),
    ("dna_applied", {"DeepSaver": float("inf")}),
    ("dna_applied", {"DeepSaver": -8}),
    ("dna_applied", {"DeepSaver": 1.5}),
    ("dna_wager_pending", 1.5),
    ("dna_wager_pending", -5),
    ("dna_wager_pending", 10000),
    ("dna_wager_pending", float("inf")),
])
def test_malformed_dna_cloud_probe_rejects_without_raising(field, value):
    blob = persistence.to_save_dict(pet())
    blob[field] = value
    assert persistence.pet_from_save(blob, strict=True)[0] is None


def test_malformed_local_dna_is_quarantined_with_original_bank(tmp_path):
    blob = persistence.to_save_dict(pet())
    blob["dna_owned"] = {"DeepSaver": 87, "DarkArea": "bad"}
    path = tmp_path / "save.json"
    path.write_text(json.dumps(blob), encoding="utf-8")
    p, message = persistence.load(str(path))
    assert p is None and "damaged file was kept" in message
    archived = next(tmp_path.glob("save.corrupt.*.json"))
    assert json.loads(archived.read_text(encoding="utf-8"))["dna_owned"] == blob["dna_owned"]


def test_estate_salvages_valid_slots_and_archives_poisoned_slot(tmp_path):
    persistence.save_settings({"progress": {"last_gen": {
        "dna_owned": {"NatureSpirit": 87, "DeepSaver": "bad"}}}})
    p = Pet.new_egg(generation=2, egg_type=0)
    assert p.dna_owned["NatureSpirit"] == 87
    assert p.dna_owned["DeepSaver"] == 0
    archived = next(tmp_path.glob("save.corrupt.*.json"))
    assert json.loads(archived.read_text(encoding="utf-8"))["progress"]["last_gen"]["dna_owned"]["NatureSpirit"] == 87


def test_backup_recovery_archives_poisoned_main_before_next_save(tmp_path):
    blob = persistence.to_save_dict(pet())
    path = tmp_path / "save.json"
    Path(str(path) + ".bak").write_text(json.dumps(blob), encoding="utf-8")
    blob["dna_owned"] = {"DeepSaver": 87, "DarkArea": "bad"}
    path.write_text(json.dumps(blob), encoding="utf-8")
    p, message = persistence.load(str(path))
    assert p is not None and "recovered from the backup" in message
    archived = next(tmp_path.glob("save.corrupt.*.json"))
    persistence.save(p, str(path))
    assert json.loads(archived.read_text(encoding="utf-8"))["dna_owned"]["DeepSaver"] == 87


def test_legacy_integral_counts_keep_all_bank_and_uncapped_charge():
    blob = persistence.to_save_dict(pet())
    blob["dna_owned"] = {"DeepSaver": 87.0, "None": 99}
    blob["dna_applied"] = {"DeepSaver": 1000.0}
    p, _ = persistence.pet_from_save(blob)
    assert p.dna_owned["DeepSaver"] == 87 and type(p.dna_owned["DeepSaver"]) is int
    assert p.dna_owned["None"] == 0                  # legacy dud DNA cashed in (2026-10-15)
    assert p.dna_applied["DeepSaver"] == 1000
    assert set(p.dna_owned) == set(data.DNA_FIELDS)


@pytest.mark.usefixtures("care_ok")
def test_every_armed_preview_is_stable_and_does_not_consume_rng():
    p = pet()
    p.line_id = "ver1"
    p.dna_applied["DragonsRoar"] = 8
    expected = sorted(set(evolution.divergence_roads(p)["DragonsRoar"]))
    state = random.getstate()
    for _ in range(3):
        assert evolution.divergence_options(p) == expected
        assert digicore.next_evolution(p) == expected[0]
        rows = digicore._evo_rows(p)
        assert [r[0] for r in rows[:len(expected)]] == expected
        panel = DigiCorePanel(p, start="EVOLVES")
        assert panel.text().plain.count("✓ road") == len(expected)
        panel.detail = rows[0][:2]
        assert "road option; final pick at growth" in panel.text().plain
        assert TuiPetApp._armed_field(None, p) == "DragonsRoar"
    assert random.getstate() == state
    panel.teaser = True
    panel.teaser_t = MON_T + EXPAND_T
    assert "One of" in panel.strip() and "DNA road forms" in panel.strip()
    assert cell_len(panel.strip()) <= 40


def test_off_chart_preview_also_preserves_rng():
    p = pet()
    p.dna_applied["DragonsRoar"] = 8
    state = random.getstate()
    assert digicore._evo_rows(p)
    assert random.getstate() == state


def test_dna_respects_care_and_still_rolls_the_final_choice(monkeypatch):
    """Joel 2026-10-14, design call #1 "B": DNA steers only among forms the
    pet's care qualifies for; none qualify -> no steer (it used to fall back
    to the best-fulfilled edge anyway)."""
    p = pet()
    p.dna_applied["DragonsRoar"] = 8
    monkeypatch.setattr(evolution, "check", lambda *a, **kw: False)
    assert evolution.divergence_target(p) is None
    assert evolution.divergence_options(p) == []
    calls = []
    monkeypatch.setattr(evolution, "check", lambda *a, **kw: True)
    monkeypatch.setattr(evolution, "fulfilled", lambda *a: 0)
    monkeypatch.setattr(evolution, "deviation", lambda *a: 0)
    def choose(options):
        calls.append(list(options))
        return options[-1]
    monkeypatch.setattr(evolution.random, "choice", choose)
    assert evolution.divergence_target(p) == 90
    assert calls == [evolution.divergence_roads(p)["DragonsRoar"]]


def test_stats_none_to_charge_card_matches_committed_field():
    p = pet()
    p.dna_owned["VirusBuster"] = 3
    panel = DNAPanel(p)
    panel.phase, panel.cursor = "stats", 9
    panel.key("escape")
    panel.key("enter")
    assert panel.cursor == 0 and panel.field == "VirusBuster"
    assert "Field    Virus Buster" in card(panel)
    assert panel.key("enter") == ("done", ("charged", "VirusBuster", 1))


@pytest.mark.usefixtures("care_ok")
def test_dna_card_has_road_progress_instead_of_fake_unlocks():
    p = pet()
    p.dna_applied["DeepSaver"] = 8
    panel = DNAPanel(p)
    panel.phase, panel.cursor = "charge", panel.charge_fields.index("DeepSaver")
    text = card(panel)
    assert "Unlocks" not in text
    assert "Armed Deep Saver" in text and "Road 8/8 · 1 forms" in text


def test_dna_conditions_are_informational_bonuses_not_unmet_requirements():
    rows = evolution.requirement_report(pet(), 88)
    bonus = [(met, text) for met, text in rows if text.startswith("DNA")]
    assert bonus and all(met is None and text.startswith("DNA bonus ") for met, text in bonus)
    assert all(cell_len(text) <= 35 for _, text in bonus)
    assert "bypass" not in inspect.getdoc(evolution._dna_ok).split("\n")[0].replace("not a care-gate bypass", "")
    readme = Path(__file__).resolve().parents[1] / "README.md"
    dna = readme.read_text(encoding="utf-8").split("**DNA**")[1].split("**DigiCore**")[0]
    assert "not unlock gates" in dna and "*entire*" not in dna


def test_resonance_reports_actual_partial_and_zero_neighbor_gains():
    p = pet()
    p.dna_owned["JungleTrooper"] = 95
    p.dna_owned["WindGuardian"] = 99
    panel = DNAPanel(p)
    panel.phase, panel.bet = "bet", 2500
    panel.key("enter")
    panel.hits = 30
    for _ in range(MASH_TICKS - 1):
        panel.anim()
    assert panel.phase == "mash"
    panel.anim()
    assert panel.phase == "result" and MASH_TICKS == 100
    text = panel.text().plain
    assert "+4 Jungle Trooper DNA" in text and "+0 Wind Guardian DNA" in text
    assert "+500" not in text
    assert "continue" in panel.strip() and "bank it" not in panel.strip()


@pytest.mark.parametrize("bet,hits,field", [(500, 0, "Deep"), (500, 90, "Dark"), (1, 0, "None")])
def test_stabilized_strip_previews_effective_award(bet, hits, field):
    panel = DNAPanel(pet())
    panel.phase, panel.bet, panel.hits, panel.mash_f = "mash", bet, hits, 100
    assert field in Text.from_markup(panel.strip()).plain


def test_wager_tiers_report_capped_gain_not_uncapped_splash():
    panel = DNAPanel(pet())
    panel.phase, panel.bet = "bet", 2500
    text = panel.text().plain
    assert "up to 99/adjacent Field" in text
    assert "+500" not in text and "rarer" not in text


def test_charge_cost_uses_actual_bank_and_explains_existing_penalties():
    p = pet()
    p.dna_owned["DeepSaver"] = 3
    panel = DNAPanel(p)
    panel.phase, panel.cursor, panel.amount = "charge", panel.charge_fields.index("DeepSaver"), 99
    text = panel.text().plain
    assert "x3/99 energy -6" in text
    assert "Charges clear at every evolution" in text and "ties disarm" in text
    text = card(panel)
    assert "Charge x3/99: energy -6" in text
    assert "Effort +1/ea, up to 3" in text and "Stops at empty energy" in text
    from tuipet import helpscreen
    guide = "\n".join(text for text, _ in helpscreen.HELP)
    assert "ties disarm" in guide and "stops at empty energy" in guide


def test_no_road_form_does_not_suggest_charging_to_arm():
    p = Pet.new_egg(egg_type=0)
    p._hatch_into_fresh()
    panel = DNAPanel(p)
    panel.phase = "roads"
    text = panel.text().plain
    assert "Charging now cannot arm a road" in text
    assert "Charge a Field to its threshold" not in text


def test_crystal_uses_the_display_field_name():
    p = pet()
    assert p._dna_crystal() == "+10 Nature Spirit DNA banked!"


def test_roads_browse_every_destination_and_mask_hidden_names(monkeypatch):
    p = pet()
    reqs = {n: dict(r) for n, r in data.load_requirements().items()}
    reqs[85]["hidden_evo"] = True
    monkeypatch.setattr(data, "load_requirements", lambda: reqs)
    monkeypatch.setattr(persistence, "album_seen", lambda num: False)
    panel = DNAPanel(p)
    panel.phase = "roads"
    panel.road_i = sorted(panel._roads).index("DragonsRoar")
    assert "ENTER lists all forms" in panel.text().plain
    panel.key("enter")
    assert panel.phase == "road_detail"
    targets = sorted(set(panel._roads["DragonsRoar"]))
    shown = set()
    for i in range(len(targets)):
        shown.add(targets[panel.target_i])
        text = panel.text().plain
        assert panel._target_name(targets[panel.target_i]) in text
        assert "Growmon" not in text
        panel.key("down")
    assert shown == set(targets) and len(shown) > 2
    monkeypatch.setattr(persistence, "album_seen", lambda num: True)
    assert panel._target_name(85) == "Growmon"
    panel.key("escape")
    assert panel.phase == "roads"


def test_dna_text_fits_without_marquee_or_clipped_guidance(monkeypatch):
    from tuipet import menu
    def stationary(msg, tick=None):
        assert cell_len(msg) <= menu.W, msg
        return Text(msg + "\n")
    monkeypatch.setattr(menu, "note", stationary)
    panel = DNAPanel(pet())
    panel.pet.dna_owned = {f: 99 for f in data.DNA_FIELDS}
    panel.won = ("NightmareSoldier", 9999, 64, 0, 99)
    panel.splashed = {"MetalEmpire": 0, "VirusBuster": 3}
    for phase in ("home", "charge", "stats", "roads", "road_detail", "bet", "result"):
        panel.phase = phase
        for cursor in range(10):
            panel.cursor = cursor
            panel.bet = 9999
            lines = panel.text().plain.splitlines()
            assert len(lines) <= 12, (phase, lines)
            assert all(cell_len(line) <= menu.W for line in lines)
            assert cell_len(Text.from_markup(panel.strip()).plain) <= 40
            lines = card(panel).splitlines()
            assert len(lines) <= 16 and all(cell_len(line) <= 26 for line in lines)
    panel.phase, panel.hits, panel.mash_f = "mash", 99999, 1
    assert cell_len(Text.from_markup(panel.strip()).plain) <= 40


def test_dead_dna_sickness_constants_and_chargeable_none_claim_are_gone():
    from tuipet import petbase, data_shop
    for name in ("DNA_SAME_FIELD_SICK", "DNA_DIFF_FIELD_SICK", "DNA_SICK_BOUND"):
        assert not hasattr(petbase, name)
    assert "bankable/chargeable" not in inspect.getsource(data_shop)
