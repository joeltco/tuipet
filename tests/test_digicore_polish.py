"""DigiCore audit 2026-10-14: readouts agree with tuipet, not imported lore."""
import inspect
import random
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.cells import cell_len
from rich.text import Text

from tuipet import data, digicore, evolution, helpscreen, lines, menu, persistence, statusbox
from tuipet.digicorescreen import DigiCorePanel
from tuipet.pet import Pet


def pet(num=29, line_id=""):
    p = Pet.from_num(num)
    p.line_id = line_id
    p.world_seconds = 600.0
    return p


def fits(panel):
    text = panel.text().plain
    assert len(text.splitlines()) <= 12, text
    assert all(cell_len(row) <= menu.W for row in text.splitlines()), text
    assert cell_len(Text.from_markup(panel.strip()).plain) <= 40
    return text


def card(panel):
    class Stats:
        def update(self, value):
            self.text = Text.from_markup(value).plain
    app = SimpleNamespace(pet=panel.pet, mode=panel, stats_w=Stats())
    statusbox.digicore(app)
    text = app.stats_w.text
    assert len(text.splitlines()) <= 16
    assert all(cell_len(row) <= statusbox.CARD_W for row in text.splitlines()), text
    return text


@pytest.mark.parametrize("egg_type", range(47))
def test_a1_eggs_count_incubation_not_elderhood(egg_type):
    p = Pet.new_egg(egg_type=egg_type)
    duration = p.EGG_DURATION
    assert digicore.core_number(p) == 14
    assert "14 until hatching" in fits(DigiCorePanel(p))
    p.stage_seconds = duration - 1
    assert digicore.core_number(p) == 1
    assert "hatches at 1" in fits(DigiCorePanel(p))
    p.stage_seconds = duration + 1
    p.hatching = True
    assert "1 until hatching" in fits(DigiCorePanel(p))
    assert "incubation complete" in fits(DigiCorePanel(p))
    assert p.EGG_DURATION == duration == 60


def test_a1_mega_fusion_meter_counts_age_and_says_so():
    p = pet(396, "ver4")
    p.age_seconds = 7.5 * 86400
    text = fits(DigiCorePanel(p))
    assert "7 of 14 to elder" in text and "counts the days" in text
    assert "to evolve" not in text and "nears at 1" not in text


def test_a1_godzilla_mega_uses_existing_finite_window():
    p = pet(1644, "godzilla")
    p.age_seconds = 7.5 * 86400
    p.stage_seconds = 0
    assert "14 until evolution" in fits(DigiCorePanel(p))
    p.stage_seconds = p._evolve_after() - 1
    assert digicore.core_number(p) == 1
    assert p._evolve_after() == 2880 and p.STAGE_DURATION["Mega"] == 9e9


@pytest.mark.parametrize("flag,label", [("evo_blocked", "anti-evo"), ("asleep", "waking")])
def test_a1_growth_holds_do_not_promise_evolution(flag, label):
    p = pet(29, "ver1")
    setattr(p, flag, True)
    text = fits(DigiCorePanel(p))
    assert label in text and "to evolve" not in text


def test_a1_elder_hold_and_growth_window_wording():
    p = pet(29, "ver1")
    assert "can evolve at 1" in fits(DigiCorePanel(p))
    p.age_seconds = 16 * 86400
    assert "growth held: elder" in fits(DigiCorePanel(p))


@pytest.mark.usefixtures("care_ok")
def test_a1_armed_off_chart_growth_counts_window_without_touching_bank():
    p = pet(192, "ver1")
    assert not lines.evo_rows(p)
    p.dna_owned["DeepSaver"] = 87
    p.dna_applied["DeepSaver"] = 1000
    blob = persistence.to_save_dict(p)
    p, _ = persistence.pet_from_save(blob, strict=True)
    assert p is not None and evolution.divergence_options(p)
    before = persistence.to_save_dict(p)
    before.pop("_saved_at")
    pan = DigiCorePanel(p)
    assert "14 until evolution" in fits(pan)
    for i in range(len(pan.pages)):
        pan.i = i
        fits(pan)
    after = persistence.to_save_dict(p)
    after.pop("_saved_at")
    assert after == before
    assert p.dna_owned["DeepSaver"] == 87 and p.dna_applied["DeepSaver"] == 1000


@pytest.mark.parametrize("lid,source", [("x3a", 1019), ("x3a", 1036), ("x3a", 230), ("x3b", 1019)])
def test_a2_line_hidden_names_follow_album_reveal(lid, source):
    p = pet(source, lid)
    target = 1238
    rows = digicore._evo_rows(p)
    assert next(r[1] for r in rows if r[0] == target) == "???"
    pan = DigiCorePanel(p, start="EVOLVES")
    pan.evo_sel = next(i for i, r in enumerate(rows) if r[0] == target)
    assert "Cherubimon" not in fits(pan)
    pan.key("enter")
    assert "Cherubimon" not in fits(pan)
    persistence.album_add(target)
    assert next(r[1] for r in digicore._evo_rows(p) if r[0] == target) == "Cherubimon X"


def test_a3_all_corpus_candidates_remain_browsable():
    p = pet(12)
    expected = {r[0] for r in evolution.candidates(p)}
    assert len(expected) > 8
    pan = DigiCorePanel(p, start="EVOLVES")
    assert {r[0] for r in pan.pages[-1][1]} == expected
    state = random.getstate()
    seen = set()
    for _ in expected:
        fits(pan)
        row = pan.pages[-1][1][pan.evo_sel]
        seen.add(row[0])
        pan.key("enter")
        fits(pan)
        pan.key("escape")
        pan.key("down")
    assert seen == expected and random.getstate() == state


def test_a4_trophies_are_inherited_exact_totals_and_distinct_cups():
    p = pet()
    p.trophies, p.trophies_won = 13, {0: "day 1"}
    persistence.tourney_add(0)
    persistence.tourney_add(0)
    persistence.snapshot_prev_gen(p)
    heir = Pet.new_egg(generation=2, egg_type=0)
    rows = dict(digicore._trophy_rows(heir))
    assert "This pet" not in rows
    assert rows["Wins"] == "13 across generations"
    assert rows["Career"] == "1 distinct cups"
    assert heir.trophies == 13 and heir.trophies_won == p.trophies_won


def test_a5_mode_door_does_not_claim_ready_or_roll_rng():
    p = pet(220)
    assert p.can_mode_change()
    assert not evolution.check(p, 1038, connecting=True, roll=False)
    state = random.getstate()
    text = fits(DigiCorePanel(p))
    assert "press M" in text and "ready" not in text
    assert random.getstate() == state


def test_a6_failed_mode_attempt_refreshes_real_disturb_and_preserves_navigation():
    p = pet(220)
    p.asleep = True
    pan = DigiCorePanel(p)
    pan.evo_sel = 1
    assert pan.key("m") is None
    assert p.disturb == 1 and pan.i == 0 and pan.evo_sel == 1
    pan.i = next(i for i, (title, _) in enumerate(pan.pages) if title == "CONDITION")
    assert dict(pan.pages[pan.i][1])["Disturb"] == "1 this stage"
    assert "Disturb  1 this stage" in fits(pan)


@pytest.mark.parametrize("source,lid,target", [(396, "ver4", 393), (297, "ver1", 399), (139, "vbu", 221)])
def test_a7_jogress_is_a_lobby_door_not_zero_care_gates(source, lid, target):
    p = pet(source, lid)
    pan = DigiCorePanel(p, start="EVOLVES")
    pan.evo_sel = next(i for i, r in enumerate(pan.pages[-1][1]) if r[0] == target)
    text = fits(pan)
    assert "lobby" in text and "0 to go" not in text
    pan.key("enter")
    assert "jogress" in fits(pan)


def test_a7_egg_requirements_describe_live_incubation():
    p = Pet.new_egg(egg_type=0)
    p.stage_seconds = 15
    pan = DigiCorePanel(p, start="EVOLVES")
    assert "hatch" in fits(pan) and "0 to go" not in fits(pan)
    pan.key("enter")
    assert "incubation: 0m45s remaining" in fits(pan)
    p.stage_seconds = 30
    assert "incubation: 0m30s remaining" in fits(pan)


def test_a8_partner_instruction_survives_wrapping():
    pan = DigiCorePanel(pet(139, "vbu"), start="EVOLVES")
    pan.detail = (221, "Megadramon")
    text = fits(pan)
    assert "partner" in text
    assert "Vaccine/Virus" in text


@pytest.mark.parametrize("page", ["STATUS", "POWER", "PERSON"])
def test_a8_large_counters_and_wide_text_are_readable_by_scrolling(page):
    p = pet()
    p.bits = 10**12
    p.battles = p.wins = 10**10
    p.total_trainings = p.stage_trainings = 10**7
    p.name = "龍" * 30
    p.rival_name = "龍" * 30
    pan = DigiCorePanel(p, start=page)
    text = fits(pan)
    collected = [text]
    for _ in range(30):
        pan.key("down")
        collected.append(fits(pan))
    shown = "\n".join(collected)
    if page == "STATUS":
        assert str(p.bits) in shown and str(p.battles) + "W" in shown
    elif page == "POWER":
        assert "this" in shown and "stage" in shown and str(p.stage_trainings) in shown
    else:
        assert "W-" in shown
    pan.key("right")
    assert pan.row_off == 0


def test_a8_long_checklist_is_scrollable_without_losing_its_tail(monkeypatch):
    message = "Dragon " * 80 + "FINAL PARTNER"
    monkeypatch.setattr(evolution, "requirement_report", lambda *args: [(False, message)])
    pan = DigiCorePanel(pet(), start="EVOLVES")
    pan.detail = (100, "Greymon")
    text = fits(pan)
    assert "FINAL PARTNER" not in text
    for _ in range(50):
        pan.key("down")
        text = fits(pan)
    assert "FINAL PARTNER" in text


def test_a8_full_trophy_and_legacy_pages_keep_note_and_footer_visible():
    p = pet()
    p.trophies_won = {i: "day 999" for i in range(5)}
    persistence.save_settings({"progress": {"legacy": [
        {"gen": i, "name": "HerculesKabuterimon", "stage": "InTraining", "age": 86400}
        for i in range(10)]}})
    for page in ("TROPHIES", "LEGACY"):
        pan = DigiCorePanel(p, start=page)
        fits(pan)                       # keys ride the strip (menus call #12 = A)
        assert "↑↓ scroll" in Text.from_markup(pan.strip()).plain
        for _ in range(3):
            pan.key("pagedown")
        assert "more" in fits(pan)
        assert "ESC back" in Text.from_markup(pan.strip()).plain


def test_a9_strip_and_card_follow_page_gaze_and_requirements():
    pan = DigiCorePanel(pet())
    assert "SPACE gaze" in Text.from_markup(pan.strip()).plain
    pan.key("space")
    assert "GAZE" in card(pan) and "ESC back" in card(pan)
    pan.key("escape")
    pan._back_t = 0
    pan.key("right")
    assert "gaze" not in pan.strip() and "←→ page" in Text.from_markup(pan.strip()).plain
    pan = DigiCorePanel(pet(), start="EVOLVES")
    pan.key("enter")
    assert "REQUIREMENTS" in card(pan) and "ESC back" in Text.from_markup(pan.strip()).plain
    assert "scroll" in pan.strip() and "gaze" not in pan.strip()


def test_a9_card_fits_wide_names_and_preserves_note_words():
    p = pet()
    p.name = "龍" * 16
    pan = DigiCorePanel(p)
    pan.note = "The mode is out of reach — press ESC to return."
    text = card(pan)
    assert "return." in text


def test_a8_mode_message_has_a_readable_tail_without_marquee():
    pan = DigiCorePanel(pet())
    pan.note = "Long mode verdict " * 8 + "FINAL VERDICT"
    fits(pan)
    assert "↑↓ scroll" in Text.from_markup(pan.strip()).plain
    for _ in range(20):
        pan.key("down")
    assert "FINAL VERDICT" in fits(pan)


def test_a9_docs_describe_tuipet_keys_and_existing_clock_truth():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    section = readme.split("**DigiCore**")[1].split("## Raids")[0]
    assert "potential next form" in section and "elderhood" in section
    assert "canon EvolutionState" not in section
    help_text = "\n".join(t for t, _ in helpscreen.HELP)
    assert "SPACE on CORE: gaze; elsewhere page" in help_text
    assert "EVOLVES: ENTER for requirements" in help_text
    src = inspect.getsource(digicore)
    assert "is_injured() is hard False" not in src and "adventure\n    # left" not in src
    assert "also ranks corpus" in src


@pytest.mark.parametrize("num", [1109, 1111, 1112, 1113, 1129])
def test_item_and_mode_only_forms_show_no_growth_countdown(num):
    """VB audit 2026-10-14: these evolve only by a Beast Spirit item, or (antibody-
    less Bolgmon) by Mode/X -- the core must not count a timer that never fires."""
    from tuipet.pet import Pet
    rec = data.load_sprites()[1][num]
    p = Pet(num=num, name=rec["name"], stage=rec["stage"], attribute="Vaccine")
    assert not digicore.has_timed_next(p)
    assert digicore.growth_clock(p) is None and not digicore.growth_pending(p)


def test_call_8_readout_labels():
    """Joel 2026-10-15 (DigiCore call #8 = A): six readout labels."""
    from tuipet import digicore
    from tuipet.pet import Pet
    p = Pet(num=29, name="Agumon", stage="Rookie", attribute="None")
    pages = dict(digicore.build_pages(p))
    status, power, cond = dict(pages["STATUS"]), dict(pages["POWER"]), dict(pages["CONDITION"])
    assert status["Attrib"] == "Free"
    assert power["Attack"].endswith(" form") and power["Level"].split()[0].endswith("/4")
    assert "Fullness" in cond and cond["Disturb"].endswith("this stage")
    p.line_id, p.gcell = "godzilla", 351
    assert dict(dict(digicore.build_pages(p))["STATUS"])["G-Cell"].split()[3] == "351pt"


def test_call_9_the_person_core_flavor_reads_as_a_badge():
    """Joel 2026-10-15 (DigiCore call #9 = A): Dark/Burst/Twelve/Two is the
    art catalog's badge name, not a stat -- labelled Badge, not Core."""
    from tuipet import data, digicore
    from tuipet.pet import Pet
    num, name = next(iter(data.load_digicore_icons().items()))
    person = dict(dict(digicore.build_pages(Pet(num=num, stage="Mega")))["PERSON"])
    assert "Core" not in person and person["Badge"].endswith(name)


def test_call_10_no_duplicate_x_row_and_trophy_days_say_world_day():
    """Joel 2026-10-15 (DigiCore call #10 = A)."""
    from tuipet import digicore
    from tuipet.pet import Pet
    p = Pet(num=29, name="Agumon", stage="Rookie", attribute="Vaccine")
    p.x_antibody = "Permanent"
    p.trophies_won = {1: "day 12"}
    pages = dict(digicore.build_pages(p))
    assert "X-Anti" not in dict(pages["POWER"])
    assert "world day 12" in [v for _, v in digicore._trophy_rows(p)]
