"""Device-chart fidelity: every new egg (44-67) hatches a line built from ITS
OWN device's evolution chart (humulos pen20/dm20/dmx), not a borrowed tree.
Born from Joel's 2026-07-10 bug report: the Deep Savers egg hatched the
DM20th Corona/Luna tree because the eggs had been name-joined onto whatever
classic line shared their baby."""
from tuipet import data, egg, lines


def _names(lid):
    _, by = data.load_sprites()
    return {by[n]["name"] for n in lines.load_lines()[lid]["members"]}


def _by_name():
    return {egg.hatch_name(i): i for i in range(egg.count())}


def _root_line(i):
    L = lines.load_lines()
    return [lid for lid, l in L.items()
            for t in egg.hatch_targets(i) if l["root"] == t]


def test_every_new_egg_hatches_its_own_device_line():
    """No two eggs share a root unless their device charts are identical
    (WG+Lalamon -- humulos pen20 says so)."""
    by = _by_name()
    L = lines.load_lines()
    roots = {}
    for name, lid in [("Nature Spirits Egg", "nsp"), ("Deep Savers Egg", "dsv"),
                      ("Nightmare Soldiers Egg", "nso"),
                      ("Wind Guardians Egg", "wgu"), ("Metal Empire Egg", "mem"),
                      ("Virus Busters Egg", "vbu"), ("Corona Egg", "corona"),
                      ("Luna Egg", "luna"), ("Zuba Egg", "zuba"),
                      ("Hack Egg", "hack"), ("DORU Egg", "doru20"),
                      ("Slayerdra Egg", "slayerdra"),
                      ("Breakdra Egg", "breakdra"), ("Ryuda Egg", "ryuda"),
                      ("Draco Egg", "draco"), ("Terrier Egg", "terrier"),
                      ("Lop Egg", "lop"), ("V Egg", "vegg"),
                      ("Virus Busters Ver. 20th Egg", "vb20"),
                      ("Kera Digitama", "kera")]:
        assert egg.hatch_targets(by[name]) == [L[lid]["root"]], (name, lid)
        roots[name] = L[lid]["root"]
    # the pen20 twin that legitimately shares a chart (the Meicoomon egg
    # skin, VB's other twin, left with the fake-egg cut 2026-07-17)
    assert egg.hatch_targets(by["Lalamon Egg"]) == [L["wgu"]["root"]]
    assert "Meicoomon Egg" not in by
    # X3 multi-hatches BOTH dmx ver.3 babies (Zerimon & Cocomon sides)
    assert egg.hatch_targets(by["Digitama X3"]) == \
        sorted([L["x3a"]["root"], L["x3b"]["root"]])


def test_deep_savers_is_the_deep_savers_chart():
    """The bug that started it all: Deep Savers must be ocean Digimon,
    not the Corona/Luna tree."""
    n = _names("dsv")
    assert {"Gomamon", "Ikkakumon", "Zudomon", "Plesiomon",
            "Seadramon", "MegaSeadramon", "MetalSeadramon"} <= n
    assert not ({"Apollomon", "Dianamon", "Lunamon", "Coronamon",
                 "Bearmon", "Dobermon"} & n)


def test_field_eggs_wear_their_pen20_charts():
    assert {"Devimon", "Bakemon", "Piedmon", "LadyDevimon"} <= _names("nso")
    assert {"Biyomon", "Kiwimon", "Lilymon", "Phoenixmon"} <= _names("wgu")
    assert {"Hagurumon", "Guardromon", "Andromon", "Machinedramon"} <= _names("mem")
    # pen20's VB egg raises Nyaromon roads (NOT Pendulum Zero's Patamon)
    assert {"Nyaromon", "Agumon", "Gabumon", "Salamon", "MagnaAngemon",
            "Seraphimon", "Omnimon"} <= _names("vbu")
    assert {"Tentomon", "Kabuterimon", "MegaKabuterimon",
            "HerculesKabuterimon"} <= _names("nsp")
    # NSp still roots at Bubbmon (pen20 agrees with the old DM6 line there)
    _, by = data.load_sprites()
    assert by[lines.load_lines()["nsp"]["root"]]["name"] == "Bubbmon"


def test_corona_luna_split_and_gracenovamon_doors():
    """dm20: Corona raises Coronamon, Luna raises Lunamon; each capstone is
    the Tag-Battle GraceNovamon door with the OTHER mascot as partner."""
    co, lu = _names("corona"), _names("luna")
    assert {"Coronamon", "Firamon", "Flaremon", "Apollomon"} <= co
    assert {"Lunamon", "Lekismon", "Crescemon", "Dianamon"} <= lu
    assert "Lunamon" not in co and "Coronamon" not in lu
    L = lines.load_lines()
    apollo = L["corona"]["members"][394]
    diana = L["luna"]["members"][377]
    assert any(r["jogress"] == 377 for r in L["corona"]["children"][394])
    assert any(r["jogress"] == 394 for r in L["luna"]["children"][377])
    assert apollo and diana


def test_dragon_eggs_and_examon_doors():
    """dm20: Slayerdra/Breakdra split at Dracomon's colour roads; Examon is
    the Tag-Battle capstone with the twin dragon as partner."""
    L = lines.load_lines()
    assert {"Dracomon", "Coredramon", "Wingdramon", "Slayerdramon"} \
        <= _names("slayerdra")
    assert {"Dracomon", "Coredramon", "Groundramon", "Breakdramon"} \
        <= _names("breakdra") or {"Dracomon"} <= _names("breakdra")
    assert any(r["jogress"] == 316 for r in L["slayerdra"]["children"][315])
    assert any(r["jogress"] == 315 for r in L["breakdra"]["children"][316])


def test_twin_eggs_take_their_own_side():
    t, l = _names("terrier"), _names("lop")
    assert {"Terriermon", "Gargomon", "Rapidmon", "MegaGargomon"} <= t
    assert {"Lopmon", "Turuiemon", "Antylamon", "Cherubimon"} <= l or \
           {"Lopmon", "Turuiemon", "Cherubimon"} <= l
    assert "Lopmon" not in t and "Terriermon" not in l


def test_attribute_jogress_doors_parse_and_open():
    """pen20 Pendulum jogress: 'Jogress with X Adult' becomes an attribute
    door the fusion channel can open (engine extension 2026-07-10)."""
    L = lines.load_lines()
    specs = [r["jogress"] for line in L.values()
             for rows in line["children"].values() for r in rows
             if isinstance(r["jogress"], tuple)]
    assert specs, "no attribute jogress doors loaded"
    assert all(set(s) <= {"Vaccine", "Data", "Virus", "None"} for s in specs)
    # a Veedramon on the V line offers its device fusions via attributes
    from tuipet import jogress

    class _P:
        num, line_id, stage, attribute = 144, "vegg", "Champion", "Vaccine"
        battle_log, mega_kills, dp = [], 0, 0
        care_mistakes = stage_trainings = overeat = stage_battles = 0
        battles = wins = disturb = exp = 0
        injuries = sick_count = weight = 0
        _base_weight = staticmethod(lambda: 0)
        levels_fought = []
        vaccine = data_power = virus = 34
        full_health = 5
        name = "t"
    opts = {o["name"]: o for o in jogress.options(_P())}
    assert "Garudamon" in opts and set(opts["Garudamon"]["partners"]) \
        == {"Vaccine", "Data"}


def test_doru_and_ryuda_are_the_small_dm20_pen20_charts():
    assert _names("doru20") == {"Dodomon", "Dorimon", "Dorumon", "Dorugamon",
                                "DoruGreymon", "Alphamon"}
    assert {"Fufumon", "Kyokyomon", "Ryudamon", "Ginryumon",
            "Hisyaryumon", "Ouryumon"} <= _names("ryuda")


def test_kera_is_the_dmx_keramon_line():
    """dmx: Kuramon -> Tsumemon -> Keramon X -> Diaboromon X (the canon
    rapid-evolution skip, 'Wait 24 hours')."""
    assert _names("kera") == {"Kuramon", "Tsumemon", "Keramon X",
                              "Diaboromon X"}


def test_old_wrong_lines_stay_dormant_for_existing_pets():
    """ver6 (and the classic lines the eggs used to borrow) still load, so a
    pet mid-journey keeps its tree; they just aren't hatched anymore."""
    L = lines.load_lines()
    assert L["ver6"]["root"] == 1574
    hatched = {t for i in range(egg.count()) for t in egg.hatch_targets(i)}
    assert 1574 not in hatched
