"""The humulos dot-matrix egg pull + the frames-or-cut pass (Joel 2026-07-10):
29 device digitama with real dot sprites and REAL frame animations (DVPet/DU
sourced, design-verified), the connection unlock signal, and the .400/.401
save migration. Frameless eggs and frameless digimon were CUT."""
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


def test_bank_is_68_and_every_egg_is_gated():
    n = egg.count()
    assert n == 68
    rules = data.load_egg_unlock()
    for i in range(n):
        assert i in rules or i in egg._WIN_EGGS, i
    # the two ??? mystery eggs sit at the end of the classic block
    assert [i for i in range(n) if egg.hatch_name(i) == "???"] \
        == sorted(egg._WIN_EGGS) == [41, 42]


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
    # the NSp egg now hatches its pen20 Bubbmon root; the any-root
    # mystery egg follows the eggs (device-chart rebuild 2026-07-10)
    nsp = lines.load_lines()["nsp"]["root"]
    assert nsp in set(egg.hatch_targets(max(egg._WIN_EGGS)))


def test_no_egg_is_strictly_dominated():
    """The audit invariant: no two eggs share art AND baby where one is a
    free starter / free same-gate while the other merely charges bits."""
    rules = data.load_egg_unlock()
    byroot = {}
    for i in range(egg.count()):
        if i in egg._WIN_EGGS:
            continue
        byroot.setdefault(tuple(egg.hatch_targets(i)), []).append(i)
    for idxs in byroot.values():
        for a in idxs:
            for b in idxs:
                if a == b:
                    continue
                fa = "".join("".join(f) for f in egg.frames(a))
                fb = "".join("".join(f) for f in egg.frames(b))
                if fa != fb:
                    continue
                ra, rb = rules[a], rules[b]
                achieve = ("wins", "album_n", "mega", "connections",
                           "gen", "map", "tourney")
                plain_buy = rb["price"] and not any(rb[k] for k in achieve) \
                    and not rb["xanti"] and not rb["stage"]
                assert not (ra["start"] and plain_buy), \
                    (egg.hatch_name(a), egg.hatch_name(b))
                assert not (ra["stage"] and ra["stage"] == rb["stage"]
                            and not ra["price"] and rb["price"]), \
                    (egg.hatch_name(a), egg.hatch_name(b))


def test_win_ladder_is_staggered():
    """Each new win-gated egg gets its own moment: 25/40/50/60/75/100
    (50 belongs to classic Sakumon + the first ??? egg; 100 to the second)."""
    rules = data.load_egg_unlock()
    wins = sorted((r["wins"], r["name"]) for r in rules.values() if r.get("wins"))
    assert wins == [(25, "V Egg"), (40, "Hack Egg"), (50, "Sakumon"),
                    (60, "Digitama X3"), (75, "Zuba Egg")]


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
    for i in range(44, 68):
        for t in egg.hatch_targets(i):
            assert t in roots, (i, t)
    order = [egg.hatch_name(i) for i in range(44, 68)]
    assert order[:6] == ["Nature Spirits Egg", "Deep Savers Egg",
                         "Nightmare Soldiers Egg", "Wind Guardians Egg",
                         "Metal Empire Egg", "Virus Busters Egg"]  # Pen 1-5+Zero
    assert order[-2:] == ["Digitama X3", "Kera Digitama"]


def test_fresh_save_starters_are_classic_five_plus_fields():
    st = egg.egg_states(_prog(), owned=set())
    owned = {egg.hatch_name(i) for i, (s, _) in st.items() if s == "owned"}
    assert owned == {"Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon",
                     "Nature Spirits Egg", "Deep Savers Egg",
                     "Nightmare Soldiers Egg", "Wind Guardians Egg",
                     "Metal Empire Egg", "Virus Busters Egg"}


def test_connection_gate_locks_then_opens():
    idx = _by_name()["Corona Egg"]
    assert data.load_egg_unlock()[idx]["connections"] == 3
    assert egg.egg_state(idx, _prog(), owned=set())[0] == "locked"
    assert egg.egg_state(idx, _prog(connections=3), owned=set()) == ("owned", 0)


def test_progression_tiers_read_the_right_signals():
    by = _by_name()
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"], _prog(), set())[0] == "locked"
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"],
                         _prog(max_gen=5), set()) == ("buyable", 2500)
    assert egg.egg_state(by["V Egg"], _prog(wins=25), set()) == ("owned", 0)
    assert egg.egg_state(by["Kera Digitama"], _prog(mega_kills=10), set()) == ("owned", 0)
    assert egg.egg_state(by["Digitama X3"], _prog(xanti_ever=True), set())[0] == "locked"
    assert egg.egg_state(by["Digitama X3"],
                         _prog(xanti_ever=True, wins=60), set()) == ("owned", 0)
    assert egg.egg_state(by["Hack Egg"], _prog(wins=40), set()) == ("owned", 0)
    assert egg.egg_state(by["Zuba Egg"], _prog(wins=75), set()) == ("owned", 0)
    # lineage eggs are TEMPORARY, following the previous generation
    assert egg.egg_state(by["Ryuda Egg"],
                         _prog(last_field="DragonsRoar"), set()) == ("temp", 0)
    assert egg.egg_state(by["Lalamon Egg"],
                         _prog(last_obed=120), set()) == ("temp", 0)
    assert egg.egg_state(by["Meicoomon Egg"],
                         _prog(last_mood=200), set()) == ("temp", 0)
    assert egg.egg_state(by["Meicoomon Egg"],
                         _prog(last_mood=199), set())[0] == "locked"


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
    # the twin ??? eggs translate by occurrence, not name collision
    assert persistence._migrate_egg_index(46) == 41
    assert persistence._migrate_egg_index(47) == 42
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
    assert d3["progress"]["eggs_owned"] == [by["Babumon"]]  # license kept, temps purged
    assert d3["egg_order_v"] == persistence.EGG_ORDER_V


def test_every_egg_renders_a_shop_icon():
    from tuipet import menu
    for i in range(egg.count()):
        cell = menu.item_icon(egg.shop_egg_entry(i, 100))
        assert any(ch.strip() for ln in cell for ch in ln), (i, egg.hatch_name(i))


def test_locked_hints_reach_town_shelves():
    """The goal board: some town teases a locked egg with an actionable hint."""
    hints = {}
    for t in range(26):
        for i, hint in egg.locked_town_eggs(t, _prog(), set()):
            hints[egg.hatch_name(i)] = hint
    assert hints, "no town shows any locked-egg hint"
    for hint in hints.values():
        assert hint and len(hint) <= 45


def test_twins_egg_has_a_town_shelf():
    prog = _prog(album=set(range(0, 4000)), wins=99999, mega_kills=99999,
                 max_gen=99, max_stage=5, xanti_ever=True,
                 maps=set(range(200)), tourneys=set(range(200)),
                 last_mood=99999, last_obed=99999, last_xanti=True,
                 connections=99999)
    buyable = {i for i, _ in egg.buyable_eggs(prog, set())}
    covered = set().union(*(set(i for i, _ in egg.eggs_for_town(t, prog, set()))
                            for t in range(26)))
    assert buyable <= covered
