"""The humulos dot-matrix egg pull + the frames-or-cut pass (Joel 2026-07-10),
the connection unlock signal, and the cross-bank save migration.  Frameless
eggs and frameless digimon were CUT; the provenance audit (2026-07-17) then
cut the 22 fake eggs, leaving the 46 device-verified digitama."""
from tuipet import data, egg, lines, persistence


def _prog(**over):
    p = {"album": set(), "wins": 0, "mega_kills": 0, "max_gen": 1,
         "max_stage": 0, "xanti_ever": False, "maps": set(),
         "tourneys": set(), "last_field": "None", "last_attr": "None",
         "last_elem": "None", "last_mood": 0, "last_obed": 0,
         "last_xanti": False, "connections": 0}
    p.update(over)
    return p


def _by_name():
    return {egg.hatch_name(i): i for i in range(egg.count())}


def test_bank_is_46_and_every_egg_is_gated():
    n = egg.count()
    assert n == 46
    rules = data.load_egg_unlock()
    for i in range(n):
        assert i in rules, i                       # every egg has a real rule row
    assert "???" not in {egg.hatch_name(i) for i in range(n)}


def test_frameless_and_dominated_content_is_gone():
    names = {egg.hatch_name(i) for i in range(egg.count())}
    # frameless (no official animation exists anywhere)
    assert not (names & {"Version 6 Egg", "Nightmare Soldiers Ver.20th Egg",
                         "Digitama X", "Digitama X2", "Vorvomon Egg"})
    # dominated duplicates (same art + same baby on a strictly easier path)
    assert not (names & {"Version 1 Egg", "Version 2 Egg", "Version 3 Egg",
                         "Version 4 Egg", "Version 5 Egg", "Ludo Egg",
                         "YukimiBotamon", "Pichimon", "Mokumon", "Nyokimon",
                         "Choromon"})
    # Bubbmon RETURNED with a real DU state strip (.403) -- Nature Spirits
    # lives again and the any-root mystery egg knows him
    _, by = data.load_sprites()
    assert len(by[1574]["frames"]) == 11
    assert len({"".join(f) for f in by[1574]["frames"]}) >= 5
    assert lines.load_lines()["ver6"]["root"] == 1574   # dormant, for old pets


def test_no_egg_is_strictly_dominated():
    """The audit invariant, post-licence: eggs that share a hatch root must
    at least differ in ART (a same-art same-baby twin would be a pure dupe --
    the Meicoomon Egg skin was exactly that, and it was cut)."""
    byroot = {}
    for i in range(egg.count()):
        byroot.setdefault(tuple(egg.hatch_targets(i)), []).append(i)
    for idxs in byroot.values():
        for a in idxs:
            for b in idxs:
                if a >= b:
                    continue
                fa = "".join("".join(f) for f in egg.frames(a))
                fb = "".join("".join(f) for f in egg.frames(b))
                assert fa != fb, (egg.hatch_name(a), egg.hatch_name(b))


def test_win_ladder_is_staggered():
    """Each win-gated egg gets its own moment: 10/25/30/40/50/60/75.
    30 is Slayerdra's battle route -- the dragon trio's gates were
    differentiated 2026-07-14 (Slayerdra=wins, Breakdra=Mega kills,
    Draco=album); Chibickmon's 10 replaced its licence (2026-07-17)."""
    rules = data.load_egg_unlock()
    wins = sorted((r["wins"], r["name"]) for r in rules.values() if r.get("wins"))
    assert wins == [(10, "Chibickmon"), (25, "V Egg"), (30, "Slayerdra Egg"),
                    (40, "Hack Egg"), (50, "Sakumon"), (60, "Digitama X3"),
                    (75, "Zuba Egg")]


def test_every_egg_animates_with_real_frames():
    """The frames-or-cut invariant: 3 frames each, at least 2 distinct --
    no static eggs, no invented motion, ever."""
    for i in range(egg.count()):
        fr = egg.frames(i)
        assert len(fr) == 3, i
        assert all(len(f) == 16 and all(len(r) == 16 and set(r) <= {"0", "1"}
                                        for r in f) for f in fr), i
        assert len({"".join(f) for f in fr}) >= 2, ("static egg", i, egg.hatch_name(i))
        assert "".join(fr[0]).count("1") > 20, i


def test_new_eggs_hatch_line_roots_in_device_order():
    roots = {l["root"] for l in lines.load_lines().values()}
    for i in range(23, 46):
        for t in egg.hatch_targets(i):
            assert t in roots, (i, t)
    order = [egg.hatch_name(i) for i in range(23, 46)]
    assert order[:6] == ["Nature Spirits Egg", "Deep Savers Egg",
                         "Nightmare Soldiers Egg", "Wind Guardians Egg",
                         "Metal Empire Egg", "Virus Busters Egg"]  # Pen 1-5+Zero
    assert order[-2:] == ["Digitama X3", "Kera Digitama"]


def test_fresh_save_starters_are_the_classic_five():
    # egg-ladder redesign 2026-07-12: the 6 Pendulum field eggs are earned now,
    # so a brand-new save opens with ONLY the five classic babies.
    st = egg.egg_states(_prog(), owned=set())
    owned = {egg.hatch_name(i) for i, s in st.items() if s == "owned"}
    assert owned == {"Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon"}


def test_connection_gate_locks_then_opens():
    idx = _by_name()["Corona Egg"]
    assert data.load_egg_unlock()[idx]["connections"] == 3
    assert egg.egg_state(idx, _prog(), owned=set()) == "locked"
    assert egg.egg_state(idx, _prog(connections=3), owned=set()) == "owned"


def test_progression_tiers_read_the_right_signals():
    by = _by_name()
    # the 20th-anniversary flagship: a 5th-gen lineage ENDED in Virus
    # Busters (the licence became a field-story gate, 2026-07-17)
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"], _prog(), set()) == "locked"
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"],
                         _prog(max_gen=5), set()) == "locked"
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"],
                         _prog(max_gen=5, last_field="VirusBuster"), set()) == "owned"
    assert egg.egg_state(by["V Egg"], _prog(wins=25), set()) == "owned"
    assert egg.egg_state(by["Kera Digitama"], _prog(mega_kills=10), set()) == "owned"
    assert egg.egg_state(by["Digitama X3"], _prog(xanti_ever=True), set()) == "locked"
    assert egg.egg_state(by["Digitama X3"],
                         _prog(xanti_ever=True, wins=60), set()) == "owned"
    assert egg.egg_state(by["Hack Egg"], _prog(wins=40), set()) == "owned"
    assert egg.egg_state(by["Zuba Egg"], _prog(wins=75), set()) == "owned"
    # lineage eggs are TEMPORARY, following the previous generation
    assert egg.egg_state(by["Ryuda Egg"],
                         _prog(last_field="DragonsRoar"), set()) == "temp"
    assert egg.egg_state(by["Lalamon Egg"],
                         _prog(last_obed=120), set()) == "temp"


def test_record_connection_counts_distinct_tamers():
    assert persistence.get_progress()["connections"] == 0
    persistence.record_connection("Wyldfeather")
    persistence.record_connection("Wyldfeather")    # repeat: still one tamer
    persistence.record_connection("azazel")
    persistence.record_connection("")               # no name, no count
    assert persistence.get_progress()["connections"] == 2


def test_save_migration_across_bank_versions():
    """Indices from every shipped bank (.400/.401 84-egg, .402 78, .403 79)
    translate by (name, occurrence); still-cut eggs fall back ONLY for
    incubation; live Bubbmon pets stay Bubbmon."""
    by = _by_name()
    assert persistence._migrate_egg_index(1) == by["Botamon"]
    assert persistence._migrate_egg_index(34) == by["Sakumon"]  # classic shifts -5
    assert persistence._migrate_egg_index(50) == by["Corona Egg"]
    assert persistence._migrate_egg_index(83) == by["Zuba Egg"]
    assert persistence._migrate_egg_index(67) == by["Nature Spirits Egg"]
    # the twin ??? eggs were cut (2026-07-17): both fall back to Botamon
    # for incubation only
    assert persistence._migrate_egg_index(46) == by["Botamon"]
    assert persistence._migrate_egg_index(47) == by["Botamon"]
    # incubation fallbacks: cut eggs -> the surviving egg of the same baby
    assert persistence._migrate_egg_index(56) == by["Nightmare Soldiers Egg"]  # Vorvomon
    assert persistence._migrate_egg_index(79) == by["Nature Spirits Egg"]      # Version 6
    assert persistence._migrate_egg_index(7) == by["Deep Savers Egg"]          # Pichimon lic.
    # a .403 save (v3): Ludo at 71 falls back to Cotsucomon's egg
    assert persistence._migrate_egg_index(71, persistence._V403_FULL) \
        == by["Cotsucomon"]
    save = {"num": 1574, "line_id": "ver6", "egg_type": 74, "stage": "Fresh",
            "egg_order_v": None}
    persistence._migrate_v401_save(save)
    assert save["num"] == 1574 and save["line_id"] == "ver6"   # Bubbmon lives
    assert save["egg_type"] == by["Botamon"]                   # Version 1 fallback
    again = dict(save)
    persistence._migrate_v401_save(again)                      # no re-translation
    assert again["egg_type"] == save["egg_type"]


def test_owned_eggs_never_gain_cut_or_temp_eggs():
    """The .403 Puttimon-as-starter bug: owning a cut egg must NOT become
    owning a different egg -- ownership drops cut eggs (no fallback), and the
    sanity pass strips temp eggs however they snuck in."""
    by = _by_name()
    d = {"egg_order_v": None,
         "progress": {"eggs_owned": [1, 53, 54]}}   # Botamon + X + X2 on .401
    assert persistence._migrate_v401_settings(d)
    assert d["progress"]["eggs_owned"] == [by["Botamon"]]   # cut eggs DROP
    d3 = {"egg_order_v": 3,
          "progress": {"eggs_owned": [17, 11, 6]}}  # v3 leak: Puttimon/Kuramon temp
    assert persistence._migrate_v401_settings(d3)
    # Babumon's licence DROPS with the fake-egg cut (ownership never falls
    # back), and the temp leaks purge -- a fully cleaned set
    assert d3["progress"]["eggs_owned"] == []
    assert d3["egg_order_v"] == persistence.EGG_ORDER_V


def test_every_egg_renders_an_icon():
    from tuipet import menu
    for i in range(egg.count()):
        cell = menu.item_icon({"egg_idx": i})
        assert any(ch.strip() for ln in cell for ch in ln), (i, egg.hatch_name(i))


def test_every_locked_egg_offers_a_chaseable_hint():
    """Post-licence goal surface: every locked egg's rule carries a real
    LockedDescription (the guide is the goal board now)."""
    rules = data.load_egg_unlock()
    for i in range(egg.count()):
        if egg.egg_state(i, _prog(), set()) == "locked":
            assert rules[i]["desc"], (i, egg.hatch_name(i))
    assert egg.locked_hint(_prog(), set())

