"""Digicore vs DVPet setupDigicore / getDigicoreBackground / EvolSilhouette."""
from tuipet.pet import Pet
from tuipet import data
from tuipet.digicorescreen import (DigiCorePanel, core_number, core_badge_key,
                                   core_background, silhouette, DIGICORE_BASE_RATE)


def _pet(**kw):
    p = Pet(num=4, name="A", stage="Rookie", attribute="Vaccine")
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def test_core_number_counts_down_to_evolution():
    p = _pet(stage_seconds=0.0)
    assert core_number(p) == DIGICORE_BASE_RATE == 14
    p.stage_seconds = p.STAGE_DURATION["Rookie"] * 0.99
    assert core_number(p) == 1


def test_core_number_counts_up_past_growth():
    p = _pet()
    p.stage_seconds = p.STAGE_DURATION["Rookie"] + 1
    p.age_seconds = p.lifespan * 0.5
    assert core_number(p) == 7                      # halfway through life
    p.age_seconds = 0.0
    assert core_number(p) == 1                      # floors at 1


def test_badge_follows_x_antibody_state():
    p = _pet()
    assert core_badge_key(p) == "core_xnone"
    p.x_antibody = "Temporary"
    assert core_badge_key(p) == "core_xtemp"
    p.x_antibody = "Permanent"
    assert core_badge_key(p) == "core_xreq"


def test_special_core_and_null_hiding(monkeypatch):
    cfg = data.load_digicore_config()
    burst = next(n for n, c in cfg.items() if c["icon"] == "core_burst")
    assert core_badge_key(_pet(num=burst)) == "core_burst"
    # a literal "null" icon hides the badge (setupDigicore setVisible(false));
    # in the shipped csv every null row is superseded by a later real row
    # (getDigicoreConfig keeps the LAST match), so synthesize one
    monkeypatch.setattr(data, "load_digicore_config",
                        lambda: {4: {"label": None, "icon": "hidden", "icon_x": None}})
    assert core_badge_key(_pet(num=4)) is None


def test_backdrop_follows_highest_dna_field():
    p = _pet()
    p.field = "MetalEmpire"
    assert core_background(p) == data.load_backgrounds()["digicoreMe"][0]
    p.dna_owned = dict(p.dna_owned, DragonsRoar=5)   # banked DNA outranks own field
    assert core_background(p) == data.load_backgrounds()["digicoreDr"][0]


def test_silhouette_blacks_out_the_body():
    assert silhouette(["0110", "1001", "0000"]) == ["0110", "1111", "0000"]


def test_panel_core_page_and_teaser_flow():
    p = _pet()
    panel = DigiCorePanel(p)
    assert panel.pages[0][0] == "CORE"
    panel.text()                                    # core page renders
    panel.key("space")
    assert panel.teaser
    panel.text()                                    # silhouette renders
    panel.key("space")
    assert not panel.teaser
    panel.key("right")
    assert panel.pages[panel.i][0] == "STATUS"      # the data book survives
