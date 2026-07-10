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


def test_bank_is_78_and_every_egg_is_gated():
    n = egg.count()
    assert n == 78
    rules = data.load_egg_unlock()
    for i in range(n):
        assert i in rules or i in egg._WIN_EGGS, i


def test_frameless_content_is_gone():
    names = {egg.hatch_name(i) for i in range(egg.count())}
    assert not (names & {"Version 6 Egg", "Nightmare Soldiers Ver.20th Egg",
                         "Digitama X", "Digitama X2", "Vorvomon Egg",
                         "Nature Spirits Egg"})
    _, by = data.load_sprites()
    assert 1574 not in by                       # Bubbmon cut
    assert "ver6" not in lines.load_lines()
    assert 1574 not in set(egg.hatch_targets(47))


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
    for i in range(49, 78):
        for t in egg.hatch_targets(i):
            assert t in roots, (i, t)
    order = [egg.hatch_name(i) for i in range(49, 78)]
    assert order[:5] == ["Version 1 Egg", "Version 2 Egg", "Version 3 Egg",
                         "Version 4 Egg", "Version 5 Egg"]
    assert order[5:10] == ["Deep Savers Egg", "Nightmare Soldiers Egg",
                           "Wind Guardians Egg", "Metal Empire Egg",
                           "Virus Busters Egg"]      # Pendulum device order
    assert order[-2:] == ["Digitama X3", "Kera Digitama"]
    # distinct art except the design-true shares: the Terrier/Lop/X3 trio
    # (Cocomon digitama) and Draco/Slayerdra (Petitmon digitama)
    seen = {"".join(egg.frames(i)[0]) for i in range(49, 78)}
    assert len(seen) == 26


def test_fresh_save_starters_are_classic_five_plus_fields():
    st = egg.egg_states(_prog(), owned=set())
    owned = {egg.hatch_name(i) for i, (s, _) in st.items() if s == "owned"}
    assert owned == {"Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon",
                     "Deep Savers Egg", "Nightmare Soldiers Egg",
                     "Wind Guardians Egg", "Metal Empire Egg",
                     "Virus Busters Egg"}


def test_connection_gate_locks_then_opens():
    idx = _by_name()["Corona Egg"]
    assert data.load_egg_unlock()[idx]["connections"] == 3
    assert egg.egg_state(idx, _prog(), owned=set())[0] == "locked"
    assert egg.egg_state(idx, _prog(connections=3), owned=set()) == ("owned", 0)


def test_progression_tiers_read_the_right_signals():
    by = _by_name()
    assert egg.egg_state(by["Version 1 Egg"], _prog(), set()) == ("buyable", 750)
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"], _prog(), set())[0] == "locked"
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"],
                         _prog(max_gen=5), set()) == ("buyable", 2500)
    assert egg.egg_state(by["V Egg"], _prog(wins=25), set()) == ("owned", 0)
    assert egg.egg_state(by["Kera Digitama"], _prog(mega_kills=10), set()) == ("owned", 0)
    assert egg.egg_state(by["Digitama X3"], _prog(xanti_ever=True), set())[0] == "locked"
    assert egg.egg_state(by["Digitama X3"],
                         _prog(xanti_ever=True, wins=60), set()) == ("owned", 0)
    assert egg.egg_state(by["Ludo Egg"], _prog(max_stage=4), set()) == ("buyable", 1500)
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


def test_v401_save_migration():
    """Indices from the shipped 84-egg builds translate by name; cut eggs fall
    back; live ver6 pets grow past Bubbmon into Motimon."""
    by = _by_name()
    assert persistence._migrate_egg_index(1) == 1              # classic: fixed
    assert persistence._migrate_egg_index(50) == by["Corona Egg"]
    assert persistence._migrate_egg_index(83) == by["Zuba Egg"]
    assert persistence._migrate_egg_index(56) == 8             # Vorvomon -> Mokumon egg
    assert persistence._migrate_egg_index(79) == 1             # Version 6 -> Botamon egg
    save = {"num": 1574, "line_id": "ver6", "egg_type": 74, "stage": "Fresh"}
    persistence._migrate_v401_save(save)
    assert save["num"] == 19 and save["line_id"] == "choromon"
    assert save["egg_type"] == by["Version 1 Egg"]
    # already-migrated saves must NOT re-translate
    again = dict(save)
    persistence._migrate_v401_save(again)
    assert again["egg_type"] == save["egg_type"]


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
