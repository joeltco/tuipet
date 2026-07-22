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
    """BINARY since the X slim (2026-07-16): none or the Permanent badge."""
    p = _pet()
    assert core_badge_key(p) == "core_xnone"
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
    # flood-fill mask (2026-07-04): ENCLOSED interior blacks out...
    assert silhouette(["0110", "1001", "0110"]) == ["0110", "1111", "0110"]
    # ...but a bay open to the edge stays clear (the old scanline fill bridged
    # every concavity into one melted blob -- "the shape is out of resolution")
    assert silhouette(["1001", "1001", "1111"]) == ["1001", "1001", "1111"]


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


# ---- EVOLVES page: the requirement checklist (data-book polish 2026-07) ------

def _champ():
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 600.0
    p.vaccine, p.data_power, p.virus = 140, 40, 60
    return p


def test_requirement_report_mirrors_check():
    from tuipet import evolution
    p = _champ()
    for num, name, ready, _ in evolution.candidates(p):
        rows = evolution.requirement_report(p, num)
        assert rows
        hard = [met for met, _ in rows if met is not None]
        if ready:
            # every displayable gate met (the probability row is informational)
            assert all(hard), f"{name}: ready but the checklist shows unmet gates"
        # (not-ready with all gates met is possible: the probability roll failed)


def test_requirement_report_skips_unconstrained_gates():
    from tuipet import evolution
    p = _champ()
    num = evolution.candidates(p)[0][0]
    for met, txt in evolution.requirement_report(p, num):
        assert "None" not in txt.split("  ")[0] or "DNA" in txt   # no bare None gates leak


def test_evolves_page_selects_and_opens_the_checklist():
    p = _champ()
    pan = DigiCorePanel(p)
    while pan.pages[pan.i][0] != "EVOLVES":
        pan.key("right")
    t = pan.text().plain
    assert "to go" in t or "ready" in t
    assert t.count("\n") <= 12                       # fits the LCD
    pan.key("down")
    sel = pan.evo_sel
    pan.key("enter")
    assert pan.detail is not None and pan.detail[0] == pan.pages[pan.i][1][sel][0]
    d = pan.text().plain
    assert ("✓" in d or "✗" in d) and d.count("\n") <= 12
    pan.key("escape")
    assert pan.detail is None                        # back to the list, not out


def test_evolves_page_edges():
    # canon: the chart never gates on age -- an egg teases its hatchling
    # (setupDigicore counts Egg->Fresh as an evolution; fixed 2026-07-10,
    # the old "(too young)" stonewall was a tuipet invention)
    egg = Pet(num=-1, stage="Egg", attribute="None")
    egg.world_seconds = 600.0
    pan = DigiCorePanel(egg)
    while pan.pages[pan.i][0] != "EVOLVES":
        pan.key("right")
    assert "(too young)" not in pan.text().plain
    assert "Botamon" in pan.text().plain             # egg_type 0 hatchling


def test_teaser_zooms_in_then_holds_a_still_silhouette():
    """Canon EvolSilhouetteTransition (audit 2026-07-04): digicoreExpand zooms
    the core badge in over the opening beats, then the silhouette holds as a
    STILL frame-0 shape (the old teaser flickered idle poses at 10Hz), and the
    way back is the evolSilhouetteBack dark blink."""
    from tuipet.digicorescreen import EXPAND_T, MON_T
    p = _pet()
    panel = DigiCorePanel(p)
    panel.key("space")
    for _ in range(MON_T):                           # beat one: the mon itself
        panel.anim()
    early = panel.text().markup
    for _ in range(EXPAND_T // 2):                   # k steps 1x -> 2x at half-beat
        panel.anim()
    grown = panel.text().markup
    assert early != grown                            # the badge grows through the beats
    for _ in range(EXPAND_T):
        panel.anim()
    frames = []
    for _ in range(21):                              # the ghost SHIMMERS between
        frames.append(panel.text().markup)           # exactly two dither phases
        panel.anim()                                 # (no pose flicker)
    assert len(set(frames)) == 2
    panel.key("escape")
    assert panel._back_t > 0
    assert "000000" in panel.text().markup           # the dark blink out
    for _ in range(10):
        panel.anim()
    assert panel._back_t == 0
    assert "CORE" == panel.pages[panel.i][0]         # home again


def test_core_page_keeps_native_pixels_and_separates_the_badge():
    """Joel's Devimon report (2026-07-04): grid.center(ph=16) box-mushed every
    16px-tall mon to 14 rows AND the badge overlay drew dead-centre on top of
    it -- the two merged into a broken-looking mass.  Native pixels, pet in
    the LEFT cell, badge in the RIGHT."""
    from tuipet import grid
    p = _pet(num=102, stage="Champion")          # Devimon: a full 16px sprite
    panel = DigiCorePanel(p)
    rows, x, _mirror = panel._core_place(panel._pet_rows(102, idx=0), cell=0)
    assert len(rows) == 16                       # NOT shrunk to 14
    assert x + grid.width(rows) <= grid.X0 + grid.CELL   # stays in the left cell
    panel.text()                                 # the scene composes without error


# ---- digicore polish 2026-07-05 (Joel: "still very sloppy... cant tell theres
# other pages... symbol sprites messed up... everything crammed") ---------------

def test_badges_are_real_symbols_not_specks():
    """fields.png is 1x-authored art: the /3 block-mean crushed the ~16px
    field badges to 5x5 specks (and the 28px cores to 9x9).  Extraction is
    1x / half-res now -- every badge must stay >= 12px."""
    from tuipet import data
    E = data.load_effects()
    for k, f in E.items():
        if k.startswith("field_") or k.startswith("core_"):
            w, h = max(len(r) for r in f[0]), len(f[0])
            assert w >= 12 and h >= 12, f"{k} is {w}x{h}: the speck regression"


def test_every_digicore_page_speaks_the_menu_language():
    """Joel 2026-07-05 round 2: one layout for the whole data book -- the CORE
    landing page is a header/rows/footer MENU page like every other, the page
    dots live in EVERY header (core included).  2026-07-11 (visual sweep):
    Joel brought digicore into the v0.2.399 hint convention -- the idle strip
    speaks the hint language; the gaze teaser still owns the box."""
    import random
    from tuipet.pet import Pet
    from tuipet.digicorescreen import DigiCorePanel
    random.seed(2)
    p = Pet(num=102, name="Devimon", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    pan = DigiCorePanel(p)
    strip = pan.strip()                 # idle strip = hints (Joel 2026-07-11)
    assert "SPACE" in strip and "ESC" in strip
    first = pan.text().plain
    assert "DIGICORE  CORE" in first and chr(0x25CF) in first    # title + dots
    assert "SPACE gaze" in first                                 # in-page footer
    lines = first.split("\n")
    assert len(lines) <= 12 and all(len(l) <= 40 for l in lines)
    for _ in range(len(pan.pages) - 1):
        pan.key("right")
        page = pan.text().plain
        assert chr(0x25CF) in page                               # dots everywhere
        L = page.split("\n")
        assert len(L) <= 12 and all(len(x) <= 40 for x in L)


def test_the_core_gaze_looms_over_the_core_background():
    """The gaze (round 3): three full-LCD beats -- the mon, the circle, the
    silhouette -- over the core backdrop, narrated through the message box,
    with no key hints anywhere."""
    import random
    from tuipet.pet import Pet
    from tuipet import digicorescreen as dc
    random.seed(2)
    p = Pet(num=102, name="Devimon", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    pan = dc.DigiCorePanel(p)
    cap = []
    real = dc.render_scene

    def spy(placements, cols, rows, on, bg, overlay=None, bgimg=None, **kw):
        cap.append(bgimg)
        return real(placements, cols, rows, on, bg, overlay=overlay, bgimg=bgimg, **kw)

    dc.render_scene = spy
    try:
        pan.key("space")
        msgs = []
        for _ in range(24):
            pan.anim()
            t = pan.text()
            assert len(t.plain.split("\n")) == 12       # the WHOLE arena, no chrome
            assert "SPACE" not in t.plain                # ...and no hints
            m = pan.strip()
            if not msgs or msgs[-1] != m:
                msgs.append(m)
    finally:
        dc.render_scene = real
    assert cap and all(b is not None for b in cap)   # every gaze frame carries it
    assert msgs == ["the core stirs…", "the core opens…",
                    "A shape looms in the core…"]  # the message box narrates


def test_evolves_page_windows_instead_of_overflowing():
    """Refactor 2026-07-05: EVOLVES/detail ride menu.list_window/scroll_window
    (visuals byte-identical, proven by markup snapshot).  The old hand-rolled
    EVOLVES loop drew EVERY row -- 9+ candidates overflowed the physical LCD;
    the shared window scrolls with the cursor instead."""
    p = _champ()
    pan = DigiCorePanel(p)
    while pan.pages[pan.i][0] != "EVOLVES":
        pan.key("right")
    fake = [(100 + j, f"Cand{j}", False, j + 1) for j in range(11)]
    pan.pages[pan.i] = ("EVOLVES", fake)
    pan.evo_sel = 10
    t = pan.text().plain
    assert t.count("\n") <= 12                       # fits the LCD
    assert "Cand10" in t and "Cand0" not in t        # windowed onto the cursor


def test_egg_gaze_shows_the_egg_and_teases_the_hatchling():
    """Digicore during Egg (audit 2026-07-05): canon setupDigicore counts the
    hatch as the egg's next evolution -- the gaze said 'final form' over an
    egg and its first beat rendered an EMPTY LCD (num -1 has no roster sheet;
    the egg's art lives in egg data)."""
    from tuipet import theme
    from tuipet.digicorescreen import next_evolution
    egg = Pet(num=-1, stage="Egg", attribute="None")
    egg.world_seconds = 600.0
    nxt = next_evolution(egg)
    assert isinstance(nxt, int) and nxt >= 0          # the hatch target, never None
    pan = DigiCorePanel(egg)
    pan.key("space")
    pan.teaser_t = 0                                   # beat one: the egg itself
    assert pan._pet_rows(-1), "the egg sprite must render (not an empty core)"
    assert theme.SIL_SCENE in str(pan.text().markup), "no sprite ink on the LCD"
    pan.teaser_t = 20                                  # beat three: the tease
    assert "A shape looms" in pan.strip(), pan.strip()


def test_egg_data_pages_leak_no_sentinels_and_labels_never_collide():
    """Egg-stage data-page audit (2026-07-05): STATUS showed 'No. #-1' (the
    internal egg sentinel) and TROPHIES rendered 'This lifenone yet' -- a
    9-char label filling the whole label column, flush against its value
    (that one hit EVERY stage).  A real egg is named Digitama; No. is a dash
    until it hatches."""
    egg = Pet.new_egg()
    pan = DigiCorePanel(egg)
    for i, (title, _rows) in enumerate(pan.pages):
        pan.i = i
        plain = pan.text().plain
        assert "#-1" not in plain, f"{title} leaked the egg sentinel"
        assert "lifenone" not in plain, f"{title} label/value collision"
    pan.i = next(i for i, (t, _r) in enumerate(pan.pages) if t == "STATUS")
    t = pan.text().plain
    assert "Digitama" in t and "—" in t
    pan.i = next(i for i, (t2, _r) in enumerate(pan.pages) if t2 == "TROPHIES")
    assert "This pet  none yet" in pan.text().plain or "This pet none yet" in pan.text().plain


def test_hidden_evolutions_mask_until_first_reached():
    """HiddenEvolution (digicore audit 2026-07-06): 130 forms are concealed in
    canon's tree until reached; the album (Evolution.setUnlocked) reveals."""
    from tuipet import data, persistence, digicorescreen
    from tuipet.pet import Pet
    reqs = data.load_requirements()
    evo = data.load_evolutions()
    _, by = data.load_sprites()
    pick = next(((src, t) for src, targets in evo.items() for t in targets
                 if reqs.get(t, {}).get("hidden_evo") and t in by and src in by
                 and by[src]["stage"] not in ("Egg", "Fresh")
                 and not data.is_placeholder(t) and not data.is_placeholder(src)
                 and by[t]["stage"] != by[src]["stage"]), None)
    if pick is None:
        import pytest
        pytest.skip("no reachable hidden target")
    src, hidden_t = pick
    p = Pet(num=src, name=by[src]["name"], stage=by[src]["stage"],
            attribute=by[src]["attribute"])
    p.world_seconds = 10 * 60.0
    p.line_id = ""                                    # the corpus path (lines = Joel's charts)
    rows = digicorescreen._evo_rows(p)
    if isinstance(rows, str):
        import pytest
        pytest.skip("no candidates surfaced for this pick")
    named = {n: nm for n, nm, *_ in rows}
    if hidden_t in named:
        assert named[hidden_t] == "???"               # concealed until reached
        persistence.album_add(hidden_t)               # ...a generation gets there
        rows = digicorescreen._evo_rows(p)
        named = {n: nm for n, nm, *_ in rows}
        assert named[hidden_t] == by[hidden_t]["name"]   # revealed for good


def test_evolves_page_shows_next_form_at_every_age():
    """Canon shows the chart at EVERY stage (DVPet drawEvolutionMenu never
    gates on age; setupDigicore counts hatching as the egg\x27s evolution).
    The "(too young)" stonewall was a tuipet invention -- Joel 2026-07-10."""
    from tuipet.digicorescreen import _evo_rows
    egg_pet = Pet(num=-1, stage="Egg", attribute="None", egg_type=1)
    rows = _evo_rows(egg_pet)
    assert isinstance(rows, list) and rows, rows          # the hatchling shows
    assert rows[0][0] in data.load_sprites()[1]
    # the multi-target digitama (X3 hatches both dmx ver.3 babies) keeps
    # its surprise ("???" -- the mystery eggs left with the fake-egg cut)
    from tuipet import egg as _egg
    egg_pet.egg_type = next(i for i in range(_egg.count())
                            if len(_egg.hatch_targets(i)) > 1)
    rows = _evo_rows(egg_pet)
    assert isinstance(rows, list) and rows[0][1] == "???"
    # a Fresh line pet sees its next form, not a stonewall
    fresh = Pet(num=1411, name="Botamon", stage="Fresh", attribute="None")
    fresh.line_id = "ver1"
    rows = _evo_rows(fresh)
    assert isinstance(rows, list) and rows, rows


def test_the_data_model_is_modular_and_live():
    """Modularize 2026-07-17: digicore.py owns every page/row computation;
    digicorescreen only renders (old names stay as aliases).  The liveness
    law holds: no dead-system rows (Spirit label, injury fragment, Nutri)."""
    from tuipet import digicore, digicorescreen
    assert digicorescreen.build_pages is digicore.build_pages
    assert digicorescreen._evo_rows is digicore._evo_rows
    assert digicorescreen.next_evolution is digicore.next_evolution
    p = Pet(num=100, stage="Champion", attribute="Vaccine")
    p.world_seconds = 600.0
    flat = [(t, r[0], r[1]) for t, rows in digicore.build_pages(p)
            if isinstance(rows, list)
            for r in rows if isinstance(r, tuple) and len(r) == 2
            and isinstance(r[0], str)]
    labels = {lab for _, lab, _ in flat}
    assert "Nature" in labels and "Spirit" not in labels
    assert "Nutri" not in labels
    ailing = next(val for _, lab, val in flat if lab == "Ailing")
    assert ailing in ("sick", "no")                  # the injury fragment is gone
    # the household page (the staple stock rows left with the props:
    # strict-DSprite items, 2026-07-17)
    assert "Helper" in labels
    assert not {"Toilet", "Potty", "Futon", "Trained"} & labels
    # the power page carries the live gate-drivers
    assert {"Form", "Level", "KO6"} <= labels


def test_the_meter_and_the_core_page_agree_on_line_pets():
    """Digicore audit 2026-07-18: core_number read the CORPUS graph alone,
    so line parents whose onward roads are line-only (the jogress/X Megas)
    showed the life meter while the Meter row said an evolution neared.
    One predicate (has_next) drives both now."""
    from tuipet import digicore, lines
    # Aegisdramon (ver4): its onward row (RustTyrannomon) is line-only
    p = Pet(num=396, name="Aegisdramon", stage="Mega", attribute="Vaccine")
    p.line_id = "ver4"
    p.world_seconds = 600.0
    p.stage_seconds = 10.0
    assert not data.load_evolutions().get(396)      # the corpus is silent...
    assert lines.evo_rows(p)                        # ...the line is not
    assert digicore.has_next(p)
    growth = p.STAGE_DURATION.get(p.stage)
    if growth:                                      # a Mega with growth: countdown
        assert digicore.core_number(p) <= digicore.DIGICORE_BASE_RATE


def test_the_none_dna_field_is_load_bearing():
    """DNA audit 2026-07-18: the 'None' field looked like a dud-bank sink,
    but 387 corpus requirement gates key on it -- its charge/stats rows are
    LIVE and must never be 'cleaned up' as dead."""
    reqs = data.load_requirements()
    gates = sum(1 for r in reqs.values()
                for f, g in r.get("dna", {}).items()
                if f == "None" and g[0] != "None")
    assert gates > 300
    assert "None" in data.DNA_FIELDS


def test_requirement_checklist_page_jumps():
    """PageUp/PageDown page the requirement scroll, lobby-chat style
    (grammar sweep 2026-07-18); pageup clamps at the head."""
    from tuipet.digicorescreen import DET_VIS
    pan = DigiCorePanel(_pet())
    pan.detail = (100, "X")
    pan.key("pagedown")
    assert pan.det_off == DET_VIS - 1
    pan.key("pageup")
    assert pan.det_off == 0
    pan.key("pageup")
    assert pan.det_off == 0                      # clamped at the head


def test_legacy_headstones_speak_real_time(tmp_path, monkeypatch):
    """One day unit across the book (digicore audit 2026-07-19): the LEGACY
    page formats an elder's age through _mins — the same real-time unit as
    the STATUS Age row and the memorial epitaph.  The old //1440 mis-cited
    the clock law and inflated every headstone 60x ('270d' for a 4.5-day
    life)."""
    from tuipet import digicore, persistence
    p = _pet(name="Vetmon", stage="Champion")
    p.age_seconds = 388800.0                    # 4.5 real days of ticks
    persistence.snapshot_prev_gen(p)
    label, val = digicore._legacy_rows()[0]
    assert "4d12h" in val, val                  # the Age row's own reading
    assert "270d" not in val                    # the 60x fantasy is dead


def test_mega_core_number_is_the_lifespan_meter(monkeypatch):
    """M9 (gameplay audit 2026-07-19): Mega's 9e9 STAGE_DURATION sentinel
    read as a pending evolution for any Mega with onward (jogress/X) rows,
    freezing the meter at 14 forever -- the lifespan count-up the docstring
    promises a final form never appeared."""
    from tuipet import digicore
    p = _pet(stage="Mega")
    monkeypatch.setattr(digicore, "has_next", lambda pet: True)
    p.age_seconds = p.lifespan * 0.5
    assert core_number(p) == 7                     # halfway through life
    p.age_seconds = p.lifespan * 0.99
    assert core_number(p) > 7                      # it MOVES


def test_book_sorts_closest_first(monkeypatch):
    """M10 (gameplay audit 2026-07-19): the corpus book sorted ASCENDING by
    fulfilled score -- the top 'closest' row was the form the engine was
    LEAST likely to pick, disagreeing with the silhouette beside it."""
    from tuipet import digicore
    from tuipet import evolution
    p = _pet()
    monkeypatch.setattr(evolution, "candidates",
                        lambda pet: [(1, "Far", False, 0.2),
                                     (2, "Near", False, 0.9),
                                     (3, "Ready", True, 0.5)])
    monkeypatch.setattr(evolution, "requirement_report", lambda pet, num: [])
    rows = digicore._evo_rows(p)
    assert [r[1] for r in rows] == ["Ready", "Near", "Far"]


def test_item_row_reads_the_named_bag_key():
    """M10's other half: the checklist checked the raw 'i:N' icon key
    against a bag that stores NAMED keys, so a held Digimental's row always
    read unmet."""
    from tuipet import evolution
    p = _pet(stage="Champion")
    target = 492                                   # evol_item 15 (Courage)
    unmet = dict((label, met) for met, label in
                 evolution.requirement_report(p, target))
    item_row = next(l for l in unmet if l.startswith("use "))
    assert unmet[item_row] is False                # empty bag: honest unmet
    p.inventory["egg_of_courage"] = 1              # the named crest key
    met = dict((label, met) for met, label in
               evolution.requirement_report(p, target))
    assert met[item_row] is True


def test_core_page_teaches_the_gaze_in_bold():
    """The gaze door wears its key in the note slot (menu polish 2026-07-21:
    dim prose alone was easy to look over) — the EVOLVES/TROPHIES teaching
    pattern.  A pending gaze verdict still owns the slot."""
    from tuipet.digicorescreen import DigiCorePanel
    pan = DigiCorePanel(_pet())
    assert "SPACE: gaze into the core" in pan.text().plain
    pan.note = "Nothing stirs — this is its final form."
    plain = pan.text().plain
    assert "Nothing stirs" in plain
    assert "SPACE: gaze into the core" not in plain
