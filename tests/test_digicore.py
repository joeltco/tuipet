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


def test_backdrop_follows_highest_charged_dna():
    p = _pet()
    p.field = "MetalEmpire"
    assert core_background(p) == data.load_backgrounds()["digicoreMe"][0]
    p.dna_applied = dict(p.dna_applied, DragonsRoar=5)   # CHARGED DNA outranks own field
    assert core_background(p) == data.load_backgrounds()["digicoreDr"][0]
    p.dna_applied = dict(p.dna_applied, DeepSaver=5)     # a TIE yields none -> own field
    assert core_background(p) == data.load_backgrounds()["digicoreMe"][0]


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


# ---- mode change (PhysicalState.modeChange / Evolution.canModeChange) --------

def _mode_pet():
    from tuipet import evolution
    p = Pet(num=100, name="Gatomon", stage="Champion", attribute="Vaccine")
    p.obedience = 500
    p.vaccine = p.data_power = p.virus = 500
    p.evol_bonus = 100000                     # deterministic requirement pass
    p.wins = p.battles = 100
    p.energy = p.max_energy
    return p


def test_mode_change_round_trip_shares_the_life():
    p = _mode_pet()
    p.stage_seconds = 321.0
    st0 = (p.vaccine, p.data_power, p.virus)
    old, msg = p.mode_change()
    assert old == 100 and p.num != 100        # became the Mode form
    assert p.stage_seconds == 321.0           # digivolve skips the clock for Mode
    p._set_energy(p.max_energy)
    p.mode_change()                           # revert to the first pre-evolution
    assert p.num == 100
    assert (p.vaccine, p.data_power, p.virus) == st0   # changes un-applied exactly


def test_mode_change_demands_a_full_bar():
    # checkRefused reads ModeChangeEnergyChange as a FRACTION (-1 x maxEnergy):
    # anything under a full bar auto-refuses; the applied cost is 1 point
    p = _mode_pet()
    p._set_energy(p.max_energy - 1)
    old, msg = p.mode_change()
    assert old is None and "refuses" in msg
    p._set_energy(p.max_energy)
    old, _ = p.mode_change()
    assert old is not None and p.energy == p.max_energy - 1


def test_can_mode_change_gates():
    from tuipet import evolution
    assert _mode_pet().can_mode_change()
    plain = Pet(num=4, name="A", stage="Rookie", attribute="Vaccine")
    assert plain.can_mode_change() == evolution.can_mode_change(plain)


def test_dna_charge_overflow_lands_one_short_of_the_cap():
    # applyDNA: setExercise(getExerciseLimit() - 1) on overflow -- canon quirk
    p = _pet()
    p.strength = 3
    p.dna_owned["DragonsRoar"] = 10
    p.apply_dna("DragonsRoar", 5)                    # 3 + 5 overflows the gauge
    assert p.strength == 3                           # lands at limit-1, not 4
    p2 = _pet()
    p2.strength = 1
    p2.dna_owned["DragonsRoar"] = 10
    p2.apply_dna("DragonsRoar", 1)
    assert p2.strength == 2                          # a fitting charge adds normally
