"""The humulos dot-matrix egg pull (Joel 2026-07-10 "pull all 84"): 35 device
digitama with real dot sprites, the DM Ver.6 line, and the DM20 connection-
battle unlock signal."""
from tuipet import data, egg, lines, persistence


def test_bank_is_84_and_every_egg_is_gated():
    n = egg.count()
    assert n == 84
    rules = data.load_egg_unlock()
    for i in range(n):
        assert i in rules or i in egg._WIN_EGGS, i


def test_new_eggs_wear_their_own_dot_sprites_and_hatch_line_roots():
    ln = lines.load_lines()
    roots = {l["root"] for l in ln.values()}
    seen = set()
    for i in range(49, 84):
        fr = egg.frames(i)
        assert len(fr) == 3 and all(len(f) == 16 for f in fr), i
        key = "".join(fr[0])
        assert key.count("1") > 20, i          # real ink, not a blank
        seen.add(key)
        for t in egg.hatch_targets(i):
            assert t in roots, (i, t)          # every hatch is a line root
    # distinct art except two source-true shares: the Terrier/Lop twins
    # digitama, and Draco/Slayerdra (identical dot art on humulos itself)
    assert len(seen) == 33


def test_ver6_line_is_the_humulos_chart():
    line = lines.load_lines()["ver6"]
    assert line["root"] == 1574                # Bubbmon
    stages = {}
    for num, row in line["members"].items():
        stages.setdefault(row["stage"], set()).add(num)
    assert stages["InTraining"] == {19}        # Motimon
    assert stages["Rookie"] == {48, 49}        # Tentomon / Otamamon
    assert stages["Champion"] == {140, 141, 113, 120, 125, 142, 159}
    assert stages["Ultimate"] == {225, 200, 251}   # the Perfect capstones


def test_ver6_hatch_canonicalizes():
    root, lid = lines.canonical_root(1574)
    assert (root, lid) == (1574, "ver6")


def test_version6_and_nature_spirits_hatch_bubbmon():
    by_name = {egg.hatch_name(i): i for i in range(egg.count())}
    for nm in ("Version 6 Egg", "Nature Spirits Egg"):
        assert egg.hatch_targets(by_name[nm]) == [1574], nm


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


def test_connection_gate_locks_then_opens():
    idx = _by_name()["Corona Egg"]
    assert data.load_egg_unlock()[idx]["connections"] == 3
    assert egg.egg_state(idx, _prog(), owned=set())[0] == "locked"
    # linking with 3 tamers EARNS it -- no bits (an achievement, not a purchase)
    assert egg.egg_state(idx, _prog(connections=3), owned=set()) == ("owned", 0)


def test_fresh_save_starters_are_classic_five_plus_fields():
    st = egg.egg_states(_prog(), owned=set())
    owned = {egg.hatch_name(i) for i, (s, _) in st.items() if s == "owned"}
    assert owned == {"Botamon", "Punimon", "Poyomon", "Yuramon", "Zurumon",
                     "Nature Spirits Egg", "Deep Savers Egg",
                     "Nightmare Soldiers Egg", "Metal Empire Egg",
                     "Wind Guardians Egg", "Virus Busters Egg"}


def test_progression_tiers_read_the_right_signals():
    by = _by_name()
    # Version eggs: cheap licenses, buyable from day one
    assert egg.egg_state(by["Version 1 Egg"], _prog(), set()) == ("buyable", 750)
    # Ver.20th: a 5th-generation lineage buys it; locked before
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"], _prog(), set())[0] == "locked"
    assert egg.egg_state(by["Virus Busters Ver. 20th Egg"],
                         _prog(max_gen=5), set()) == ("buyable", 2500)
    # trophies earn themselves
    assert egg.egg_state(by["V Egg"], _prog(wins=25), set()) == ("owned", 0)
    assert egg.egg_state(by["Kera Digitama"], _prog(mega_kills=10), set()) == ("owned", 0)
    assert egg.egg_state(by["Digitama X"], _prog(xanti_ever=True), set()) == ("owned", 0)
    assert egg.egg_state(by["Digitama X3"], _prog(xanti_ever=True), set())[0] == "locked"
    assert egg.egg_state(by["Digitama X3"],
                         _prog(xanti_ever=True, wins=60), set()) == ("owned", 0)
    # Version 6: raise a Mega, then it's a purchase
    assert egg.egg_state(by["Version 6 Egg"], _prog(max_stage=5), set()) == ("buyable", 3000)
    # lineage eggs are TEMPORARY, following the previous generation
    assert egg.egg_state(by["Ryuda Egg"],
                         _prog(last_field="DragonsRoar"), set()) == ("temp", 0)
    assert egg.egg_state(by["Vorvomon Egg"],
                         _prog(last_elem="Fire"), set()) == ("temp", 0)
    assert egg.egg_state(by["Lalamon Egg"],
                         _prog(last_obed=120), set()) == ("temp", 0)
    assert egg.egg_state(by["Meicoomon Egg"],
                         _prog(last_mood=200), set()) == ("temp", 0)
    assert egg.egg_state(by["Meicoomon Egg"],
                         _prog(last_mood=199), set())[0] == "locked"


def test_single_frame_digitama_rock_in_place():
    """Humulos device eggs carry ONE real dot frame -- the carousel animates
    their POSITION (no invented pixels); two-frame DVPet eggs keep the pixel
    pulse and hold still."""
    from tuipet.eggselectscreen import EggSelectPanel
    p = EggSelectPanel()
    names = {i: egg.hatch_name(i) for i in p.carousel}
    field = next(pos for pos, i in enumerate(p.carousel)
                 if names[i] == "Nature Spirits Egg")
    classic = next(pos for pos, i in enumerate(p.carousel)
                   if names[i] == "Botamon")
    for target, moves in ((field, True), (classic, False)):
        p.pos = p.scroll = target
        offs = set()
        for t in range(20):
            p.frame_i = t
            offs.add(p._wobble(target, True))
        assert (offs != {0}) == moves, (names[p.carousel[target]], offs)


def test_every_egg_renders_a_shop_icon():
    """Every egg -- classic and humulos -- must draw a non-blank icon cell in
    the shop/bag/town views (item_icon rides the real egg frames)."""
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
    # the field-named eggs land on field-matched shelves via named_field
    assert any("Ver" in n or "Egg" in n for n in hints)


def test_record_connection_counts_distinct_tamers():
    assert persistence.get_progress()["connections"] == 0
    persistence.record_connection("Wyldfeather")
    persistence.record_connection("Wyldfeather")    # repeat: still one tamer
    persistence.record_connection("azazel")
    persistence.record_connection("")               # no name, no count
    assert persistence.get_progress()["connections"] == 2


def test_twins_egg_has_a_town_shelf():
    """The Terrier/Lop twins digitama hatches two roots; the union-theme rule
    must still land it on some town's shelf."""
    prog = {"album": set(range(0, 4000)), "wins": 99999, "mega_kills": 99999,
            "max_gen": 99, "max_stage": 5, "xanti_ever": True,
            "maps": set(range(200)), "tourneys": set(range(200)),
            "last_field": "None", "last_attr": "None", "last_elem": "None",
            "last_mood": 99999, "last_obed": 99999, "last_xanti": True,
            "connections": 99999}
    buyable = {i for i, _ in egg.buyable_eggs(prog, set())}
    covered = set().union(*(set(i for i, _ in egg.eggs_for_town(t, prog, set()))
                            for t in range(26)))
    assert buyable <= covered
