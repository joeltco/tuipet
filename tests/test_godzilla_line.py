"""The Godzilla line (Digital Monster COLOR Godzilla 70th Edition, wired
2026-10-13): the G-Cell meter, the four line atoms it brought (GC, RAND, FRAG,
NOAREA), the egg, and the fragment that rides into the next Godzilla Egg.

Numbers are the humulos dmgz manual's, verbatim: the meter is 14 blue cells x 8
points, 10 yellow x 12, 20 red x 12 (472); a battle win +6 / loss -4, a random
encounter +12 / -6, training +4 / +2 / -2, Protein -4, a care mistake -8."""
from tuipet import egg, lines, persistence
from tuipet.pet import Pet
from tuipet.petbase import GCELL_MAX, gcell_cells

GODZILLA_ROOT = 1623          # Botamon G


def _godzilla_pet():
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Godzilla Egg")
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    return p


# ---- the meter ---------------------------------------------------------------

def test_meter_is_the_devices_44_cells():
    assert GCELL_MAX == 472
    # every chart threshold lands on the cell boundary the icon names
    assert gcell_cells(39) == (4, 0, 0) and gcell_cells(40) == (5, 0, 0)
    assert gcell_cells(79) == (9, 0, 0) and gcell_cells(80) == (10, 0, 0)
    assert gcell_cells(111) == (13, 0, 0) and gcell_cells(112) == (14, 0, 0)
    assert gcell_cells(231) == (14, 9, 0) and gcell_cells(232) == (14, 10, 0)
    assert gcell_cells(351) == (14, 10, 9) and gcell_cells(352) == (14, 10, 10)
    assert gcell_cells(GCELL_MAX) == (14, 10, 20)


def test_meter_clamps_and_survives_evolution():
    p = _godzilla_pet()
    p.gcell_add(-50)
    assert p.gcell == 0
    p.gcell_add(10_000)
    assert p.gcell == GCELL_MAX
    p.gcell = 200
    p.evolve_to(1624)                         # the manual's reset list leaves G-Cells out
    assert p.gcell == 200


def test_training_grades_move_the_meter():
    p = _godzilla_pet()
    p.gcell = 100
    p.train_result(True, "mega")
    assert p.gcell == 104                     # success +4
    p.train_result(False, "normal")
    assert p.gcell == 106                     # phase-2 failure +2
    p.train_result(False, "miss")
    assert p.gcell == 104                     # phase-1 failure -2


def test_care_mistake_costs_eight():
    p = _godzilla_pet()
    p.gcell = 100
    p._inc_mistake("left hungry too long")
    assert p.gcell == 92


def test_local_battles_move_the_meter_and_online_ones_do_not():
    p = _godzilla_pet()
    p.evolve_to(1624)
    p.gcell = 100
    p.record_battle(True)
    assert p.gcell == 106
    p.record_battle(False)
    assert p.gcell == 102
    p.record_battle(True, online=True)        # progression-neutral (L17)
    assert p.gcell == 102


# ---- the atoms ---------------------------------------------------------------

def test_new_atoms_parse():
    assert lines.parse_rule("GC 112+") == [[("gc", 112, None)]]
    assert lines.parse_rule("GC 0-111") == [[("gc", 0, 111)]]
    assert lines.parse_rule("RAND 50-99") == [[("rand", 50, 99)]]
    assert lines.parse_rule("FRAG, CM 0-4") == [[("frag", None, None), ("cm", 0, 4)]]
    assert lines.parse_rule("NOAREA 6") == [[("noarea", "6", None)]]


def test_gc_and_frag_atoms_read_the_pet():
    p = _godzilla_pet()
    p.gcell = 111
    assert not lines.check_rule(p, lines.parse_rule("GC 112+"))
    p.gcell = 112
    assert lines.check_rule(p, lines.parse_rule("GC 112+"))
    assert not lines.check_rule(p, lines.parse_rule("FRAG"))
    p.gcell_fragment = True
    assert lines.check_rule(p, lines.parse_rule("FRAG"))


def test_the_coin_is_rolled_once_per_stage():
    """The Chibis' 50/50: re-checking the rule every tick must not re-flip it."""
    p = _godzilla_pet()
    p.evolve_to(1624)
    roll = p.stage_roll
    assert 0 <= roll <= 99
    heads = lines.parse_rule("RAND 0-49")
    first = lines.check_rule(p, heads)
    assert all(lines.check_rule(p, heads) == first for _ in range(50))
    assert p.stage_roll == roll


def test_noarea_is_the_negation_of_the_map_arm():
    p = _godzilla_pet()
    assert lines.check_rule(p, lines.parse_rule("NOAREA 6"))   # a fresh profile cleared nothing
    persistence.map_complete_add(6)
    assert not lines.check_rule(p, lines.parse_rule("NOAREA 6"))


# ---- the egg and the line ------------------------------------------------------

def test_godzilla_egg_hatches_botamon_g_into_the_line():
    p = _godzilla_pet()
    assert p.num == GODZILLA_ROOT
    assert p.line_id == "godzilla"


def test_burning_godzilla_needs_the_fragment():
    """Burning Godzilla (VI+) is fragment-only on the device."""
    line = lines.load_lines()["godzilla"]
    rows = [r for r in line["children"][1644] if r["num"] == 1650]
    assert rows and all(any(a[0] == "frag" for a in alt) for alt in rows[0]["rule"])


def _app_with(pet):
    from tuipet import app as app_mod
    app = app_mod.TuiPetApp.__new__(app_mod.TuiPetApp)
    app.pet = pet
    app._do = lambda *a, **k: None
    app._grant_digimemory = lambda p: None
    app._open_mode = lambda panel, cb=None: None
    return app, app_mod


def _dead(num):
    p = _godzilla_pet()
    p.evolve_to(num)
    p.dead = True
    return p


def test_a_fallen_g_erosion_kaiju_can_leave_a_fragment(monkeypatch):
    """dmgz manual: 15% on the death of Jr/MG-G/1954/SG-G/1994/WG-G/1999 --
    rolled ONCE per death (the ceremony is guarded by death_banked)."""
    from tuipet import app as app_mod
    persistence._note_take("gcell_frag")
    monkeypatch.setattr(app_mod.random, "random", lambda: 0.0)   # the roll hits
    app, _ = _app_with(_dead(1644))                                # Godzilla 1994
    app._death_ceremony()
    assert persistence.gcell_fragment_waiting()
    persistence._note_take("gcell_frag")
    app, _ = _app_with(_dead(1628))                                # Little Godzilla: not a dropper
    app._death_ceremony()
    assert not persistence.gcell_fragment_waiting()
    monkeypatch.setattr(app_mod.random, "random", lambda: 0.99)    # the roll misses
    app, _ = _app_with(_dead(1647))
    app._death_ceremony()
    assert not persistence.gcell_fragment_waiting()


def test_the_fragment_rides_into_the_next_godzilla_egg_only():
    gz = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Godzilla Egg")
    persistence._note_put("gcell_frag", 1)
    app, app_mod = _app_with(_dead(1644))
    app_mod.TuiPetApp._hatch_new(app, 0, 2)          # Botamon's egg: the fragment waits
    assert not app.pet.gcell_fragment
    assert persistence.gcell_fragment_waiting()
    app.pet.dead = True
    app_mod.TuiPetApp._hatch_new(app, gz, 3)         # the next Godzilla Egg takes it
    assert app.pet.gcell_fragment
    assert not persistence.gcell_fragment_waiting()


def test_the_fragment_replaces_the_grave():
    """Joel 2026-10-13: "let it replace the grave instead of next to it"."""
    from tuipet import deathscreen
    p = _dead(1644)
    assert deathscreen.marker(p) is deathscreen.GRAVE
    p.gcell_frag_left = True
    shard = deathscreen.marker(p)
    assert shard is not deathscreen.GRAVE and shard in deathscreen.FRAGMENT
    assert deathscreen.marker(p, 4) != deathscreen.marker(p, 0)      # it twinkles
    panel = deathscreen.DeathPanel(p)
    seen = ""
    for t in range(400):                       # the epitaph marquees through an 18-col window
        panel._mq = t
        seen += panel.strip()
    assert "Fragment" in seen


def test_every_godzilla_form_fires_its_own_dsprite_shot():
    """v0.6.1: 0.6.0 shipped the line on the generic orb.  Every new form now
    fires its own DSprite attack (stats.attack_sprite), e.g. the 1994 family
    shares Attack_17 and Kiryu fires Attack_32."""
    from tuipet import data
    dev = data.load_orbs()["device"]
    for num in range(1623, 1651):
        shot = data.attack_orb(num, "Virus", 0)
        assert shot in [v[0] for k, v in dev.items() if k.startswith("gz_")], num
    assert data.attack_orb(1644, "Data", 300) == data.attack_orb(1650, "Vaccine", 0)   # 1994 == Burning (#17)
    assert data.attack_orb(1640, "Data", 0) != data.attack_orb(1644, "Data", 0)        # Kiryu has its own


def test_godzilla_1994_really_reaches_burning_godzilla():
    """Mega never auto-evolves in tuipet -- 0.6.0.post1 shipped the VI -> VI+
    row unreachable.  The Godzilla line's Mega with a chart child now gets
    the Stage VI window (2880 s), like the device's 48-hour Stage VI."""
    p = _godzilla_pet()
    for n in (1624, 1625, 1629, 1635, 1644):
        p.evolve_to(n)
    p.gcell_fragment = True
    p.care_mistakes = 0
    p.stage_battles, p.battle_log = 15, [1] * 15
    p.stage_seconds = p.LATE_STAGE_WINDOW - 1
    p._maybe_evolve()
    assert p.num == 1644                      # not yet: the window isn't open
    p.stage_seconds = p.LATE_STAGE_WINDOW
    p._maybe_evolve()
    assert p.num == 1650                      # Burning Godzilla
    # Burning itself has no next form: it stays put forever
    p.stage_seconds = 9e8
    p._maybe_evolve()
    assert p.num == 1650


def test_other_megas_still_never_auto_evolve():
    p = _godzilla_pet()
    for n in (1624, 1625, 1628, 1635, 1646):  # Destoroyah: a Mega with no next form
        p.evolve_to(n)
    assert p._evolve_after() == 9e9
