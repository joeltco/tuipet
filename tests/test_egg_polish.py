"""Regression probes for egg audit 2026-10-14; all persistence is sandboxed."""
import pytest

from tuipet import egg, persistence, shop
from tuipet.pet import Pet


class _App:
    def __init__(self, pet):
        from tuipet.app import TuiPetApp
        self.pet = pet
        self._grant_digimemory = TuiPetApp._grant_digimemory.__get__(self)
        self._hatch_new = TuiPetApp._hatch_new.__get__(self)

    def _do(self, msg):
        self.msg = msg


def _godzilla():
    return next(i for i in range(egg.count())
                if egg.hatch_name(i) == egg.GODZILLA_EGG)


def test_live_retirement_preserves_unused_memory():
    p = Pet(num=100, stage="Champion", generation=2)
    mem = {"name": "Elder", "num": 100, "vaccine": 5, "data": 3, "virus": 2}
    p.digimemory = dict(mem)
    p.inventory["digimemory"] = 1
    app = _App(p)
    app._hatch_new(1, 3)
    assert app.pet.digimemory == mem
    assert app.pet.inventory["digimemory"] == 1
    assert persistence.peek_digimemory() is None
    assert persistence.load()[0].digimemory == mem


@pytest.mark.parametrize("other_first", [False, True])
def test_fragment_survives_unhatched_repick(other_first):
    idx = _godzilla()
    p = Pet.new_egg(egg_type=idx)
    p.gcell_fragment = True
    app = _App(p)
    app._hatch_new(1 if other_first else idx, 2)
    if other_first:
        assert not app.pet.gcell_fragment
        assert persistence.gcell_fragment_waiting()
        app._hatch_new(idx, 2)
    assert app.pet.gcell_fragment
    assert not persistence.gcell_fragment_waiting()
    assert app.pet.generation == 1
    assert persistence.load()[0].gcell_fragment


@pytest.mark.parametrize("surface", ["memorial", "hall", "legacy"])
def test_every_lifespan_reads_real_time(surface):
    """4.5 real days of age_seconds reads 4d12h on every surface (the STATUS
    Age row's unit, petbase.AGE_DAY) -- never the 60x '270d'."""
    from tuipet.deathscreen import _age_str
    from tuipet.digicore import _legacy_rows
    from tuipet.hallscreen import HallPanel
    p = Pet(num=100, name="Elder", stage="Champion", age_seconds=388800.0, dead=True)
    persistence.snapshot_prev_gen(p)
    if surface == "memorial":
        shown = _age_str(p.age_seconds)
    elif surface == "hall":
        hall = HallPanel()
        shown = hall._epitaph(hall.elders[0])
    else:
        shown = _legacy_rows()[0][1]
    assert "4d" in shown and "12h" in shown and "270d" not in shown


@pytest.mark.parametrize("idx", [-1, 100000, "guide", 1.5])
def test_invalid_egg_purchase_does_not_charge_or_own(idx):
    p = Pet(num=100, stage="Champion", bits=20000)
    msg, sfx = shop.town_egg_buy(p, idx)
    assert sfx == "error", msg
    assert p.bits == 20000
    assert persistence.get_eggs_owned() == set()
    assert p.town_bought == {}


def test_help_explains_estate_and_unhatched_repick():
    from tuipet.helpscreen import HELP
    text = "\n".join(line for line, _ in HELP)
    assert "Bits, inventory, trophies and" in text
    assert "Unhatched re-picks keep the gen." in text


def test_retirement_cannot_reset_profile_daily_egg_limit():
    p = Pet(num=100, stage="Champion", generation=2, bits=50000)
    first, second = shop._sellable_eggs()[:2]
    assert shop.town_egg_buy(p, first)[1] == "reward"
    ledger = dict(p.town_bought)
    app = _App(p)
    app._hatch_new(1, 3)
    msg, sfx = shop.town_egg_buy(app.pet, second)
    assert sfx == "error", msg
    assert app.pet.bits == 40000
    assert app.pet.town_bought == ledger
    assert second not in persistence.get_eggs_owned()


def test_volcanic_beat_egg_hatches_its_own_line_and_opens_on_the_volcano_road():
    """Joel 2026-10-15: the official Volcanic Beat DIM card as an egg line,
    earned by clearing the Volcano road (map 26, index 25)."""
    from tuipet import adventure, data, egg, lines
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Volcanic Beat Egg")
    assert adventure.MAPS[25]["scene"] == "volcano"
    rule = data.load_egg_unlock()[idx]
    base = {"maps": set(), "maps_cleared": set(), "raids": 0}
    prog = dict(persistence.get_progress(), **base)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {25}
    assert egg._conditions_met(rule, prog)
    prog.update(persistence.migrate_road({"maps": [3]}))  # old area includes Volcano
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1603 and p.line_id == "vbe" and lines.active(p)
    v = lines.load_lines()["vbe"]
    assert len(v["members"]) == 17


def test_infinite_tide_egg_hatches_its_own_line_and_opens_on_seafloor_deep():
    """Joel 2026-10-15: the official Infinite Tide DIM card as an egg line,
    earned by clearing the Seafloor Deep road (map 28, index 27)."""
    from tuipet import adventure, data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Infinite Tide Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {27}
    assert egg._conditions_met(rule, prog)
    assert adventure.ZONES[27]["scene"] == "seafloor"
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1602 and p.line_id == "iti"
    deep = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Deep Savers Egg")
    q = Pet.new_egg(egg_type=deep)
    q._hatch_into_fresh()
    assert q.num == 1602 and q.line_id == "dsv"          # the shared baby keeps its own line
    assert len(lines.load_lines()["iti"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"   # earned, never sold


def test_nu_metal_empire_egg_hatches_bommon_into_its_line_on_the_factory_road():
    """Joel 2026-10-15: the official Nu Metal Empire DIM card as an egg line,
    earned on the Factory road (map 24, index 23) -- Machinedramon's road,
    the line's own Mugendramon."""
    from tuipet import adventure, data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Nu Metal Empire Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {23}
    assert egg._conditions_met(rule, prog)
    assert adventure.ZONES[23]["bosses"][0]["num"] == 276      # Mugendramon/Machinedramon
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 960 and p.line_id == "nme"
    assert len(lines.load_lines()["nme"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_blizzard_fang_egg_hatches_yukimibotamon_into_its_line_on_frozen_peak():
    """Joel 2026-10-15: the official Blizzard Fang DIM card as an egg line,
    earned on the Frozen Peak road (map 25, index 24); Daipenmon keeps the
    card's Ultimate slot while playing as its global Mega."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Blizzard Fang Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {24}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1410 and p.line_id == "bfa"
    meicoo = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Meicoo Egg")
    q = Pet.new_egg(egg_type=meicoo)
    q._hatch_into_fresh()
    assert q.num == 1410 and q.line_id != "bfa"        # the shared baby keeps its line
    line = lines.load_lines()["bfa"]
    assert len(line["members"]) == 17 and 696 in line["members"]
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_hermit_in_the_jungle_egg_hatches_yuramon_into_its_line_on_the_jungle_road():
    """Joel 2026-10-15: the official Hermit in the Jungle DIM card as an egg
    line, earned on the Jungle road (map 20, index 19)."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Hermit in the Jungle Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {19}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1414 and p.line_id == "hju"
    q = Pet.new_egg(egg_type=3)                          # the Yuramon starter egg
    q._hatch_into_fresh()
    assert q.num == 1414 and q.line_id == "ver4"         # the shared baby keeps its line
    assert len(lines.load_lines()["hju"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_mad_black_roar_egg_hatches_botamon_into_its_line_on_teal_hollow():
    """Joel 2026-10-15: the official Mad Black Roar DIM card as an egg line,
    earned on the Teal Hollow road (map 15, index 14) -- SkullGreymon's road,
    one of the line's own Ultimates."""
    from tuipet import adventure, data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Mad Black Roar Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {14}
    assert egg._conditions_met(rule, prog)
    assert adventure.ZONES[14]["bosses"][0]["num"] in lines.load_lines()["mbr"]["members"]
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1411 and p.line_id == "mbr"
    q = Pet.new_egg(egg_type=0)                          # the Botamon starter egg
    q._hatch_into_fresh()
    assert q.num == 1411 and q.line_id == "ver1"
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_true_shadow_howl_egg_hatches_punimon_into_its_line_on_moonlit_meadow():
    """Joel 2026-10-15: the official True Shadow Howl DIM card as an egg line,
    earned on the Moonlit Meadow road (map 7, index 6); Rhinomon keeps the
    card's Ultimate slot while playing as its global Champion."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "True Shadow Howl Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {6}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1412 and p.line_id == "tsh"
    q = Pet.new_egg(egg_type=1)                          # the Punimon starter egg
    q._hatch_into_fresh()
    assert q.num == 1412 and q.line_id == "ver2"
    line = lines.load_lines()["tsh"]
    assert len(line["members"]) == 17 and 570 in line["members"]
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_every_vb_card_egg_sits_on_the_shared_egg_grid():
    """Joel 2026-10-15: "The shape on the bounce isnt the same shape as the
    other eggs bounce" -- every VB egg sat a row high (still + wobble), and the
    hatch shells were cut from that shifted shell.  A card egg's still and
    wobble OUTLINES must be the shapes the original eggs share."""
    import gzip
    import json
    import os
    from collections import Counter
    from tuipet import egg, lines
    path = os.path.join(os.path.dirname(egg.__file__), "data", "eggs.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        bank = json.load(fh)

    def outline(fr):
        rows = []
        for r in fr:
            ink = [i for i, c in enumerate(r) if c == "1"]
            rows.append((ink[0], ink[-1]) if ink else None)
        return tuple(rows)
    # (older eggs keep a provenance NOTE in hatch_line; a card egg names a line)
    cards = [e for e in bank if e.get("hatch_line") in lines.load_lines()
             and e["hatch_line"] != "godzilla"]
    originals = [e for e in bank if e not in cards]
    assert len(cards) >= 7
    for k in (0, 1):
        shared = Counter(outline(e["frames"][k]) for e in originals).most_common(1)[0][0]
        for e in cards:
            assert outline(e["frames"][k]) == shared, (e["hatch_name"], k)
    # (the hatch shell rule moved to the template test: our shell where the
    #  original hatch leaves its shell untouched -- Joel 2026-10-15)


def test_impulse_city_egg_hatches_dokimon_into_its_line_on_city_sunset():
    """Joel 2026-10-15: the official Impulse City DIM card as an egg line,
    earned on the City Sunset road (map 11, index 10)."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Impulse City Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {10}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1429 and p.line_id == "ici"
    q = Pet.new_egg(egg_type=12)                         # the Dokimon egg
    q._hatch_into_fresh()
    assert q.num == 1429 and q.line_id == "dokimon"
    assert len(lines.load_lines()["ici"]["members"]) == 17
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_the_godzilla_egg_opens_on_monster_island():
    """Joel 2026-10-15: the Godzilla egg unlocks by clearing Monster Island
    (map 23, index 22) -- the kaiju road, Godzilla 1994's -- instead of
    raising any Digimon to Mega."""
    from tuipet import adventure, data, egg
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Godzilla Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0,
                max_stage=6)
    assert not egg._conditions_met(rule, prog)         # a Mega alone no longer opens it
    prog["maps_cleared"] = {22}
    assert egg._conditions_met(rule, prog)
    assert data.record_for(adventure.ZONES[22]["bosses"][0]["num"])["name"].startswith("Godzilla")


def test_the_egg_template_builds_on_grid_frames_for_every_card_egg():
    """Joel 2026-10-15: "Just make a permanent template" -- tools/egg_template.py
    turns one approved still design + the baby's dex into the wobble and hatch
    frames by fixed rules: both outlines exact, the baby never clipped, the
    hatch keeping the still egg's own shell."""
    import importlib.util
    import os
    from tuipet import data, lines
    spec = importlib.util.spec_from_file_location(
        "egg_template", os.path.join(os.path.dirname(__file__), "..", "tools", "egg_template.py"))
    tmpl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tmpl)
    bank = tmpl._bank()
    cards = [e for e in bank if e.get("hatch_line") in lines.load_lines()
             and e["hatch_line"] != "godzilla"]
    assert len(cards) >= 8
    for e in cards:
        still, wobble, hatch = tmpl.build(e["frames"][0], e["hatch"][0])
        assert tmpl.on_grid(still, tmpl.STILL) and tmpl.on_grid(wobble, tmpl.WOBBLE)
        donor = tmpl.donor_egg(e["hatch"][0])
        if donor is None or tmpl.donor_scattered(donor):  # seated baby on our own shell
            assert hatch[11:] == still[11:]                # (hatch rules v2, Joel 2026-10-15:
        else:                                            # a dot-scatter donor seats too)
            assert hatch[:11] == donor["frames"][2][:11]
        if e["hatch_name"] != "Godzilla Egg":            # (+ Botamon G's two pixels)
            assert e["frames"][2] == hatch, e["hatch_name"]
        for k, frame in ((0, still), (1, wobble)):       # the originals' exact shape
            ink, blank = tmpl.template_shape(k)
            assert all(frame[y][x] == "1" for y, x in ink), (e["hatch_name"], k)
            assert all(frame[y][x] == "0" for y, x in blank), (e["hatch_name"], k)
            shipped = e["frames"][k]                       # ...and the shipped egg too
            assert all(shipped[y][x] == "1" for y, x in ink), (e["hatch_name"], k)
    # a baby no egg hatches is seated whole: every pixel of Curimon survives
    top = tmpl.seated_hatch(1137, ["0" * 16] * 16)[:11]
    _, by_num = data.load_sprites()
    baby = [r for r in by_num[1137]["frames"][0] if "1" in r]
    assert sum(r.count("1") for r in top) >= sum(r.count("1") for r in baby)


def test_gammamon_egg_hatches_curimon_into_its_line_on_the_mountains_road():
    """Joel 2026-10-15: the official Gammamon DIM card as an egg line,
    earned on the Mountains road (map 16, index 15) -- dragon Wingdramon's."""
    from tuipet import data, egg, lines, shop
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Gammamon Egg")
    rule = data.load_egg_unlock()[idx]
    prog = dict(persistence.get_progress(), maps=set(), maps_cleared=set(), raids=0)
    assert not egg._conditions_met(rule, prog)
    prog["maps_cleared"] = {15}
    assert egg._conditions_met(rule, prog)
    p = Pet.new_egg(egg_type=idx)
    p._hatch_into_fresh()
    assert p.num == 1137 and p.line_id == "gam"
    assert len(lines.load_lines()["gam"]["members"]) == 14
    assert shop.town_egg_buy(Pet(num=29), idx)[1] == "error"


def test_the_godzilla_hatch_shows_botamon_g_not_plain_botamon():
    """Egg audit 2026-10-15 (Joel: A): the breakout was plain Botamon's; Botamon
    G's two distinguishing pixels belong at (9,4) and (9,11)."""
    from tuipet import egg
    idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == "Godzilla Egg")
    hatch = egg.frames(idx)[2]
    assert hatch[9][4] == "1" and hatch[9][11] == "1"


def test_a_baby_no_original_hatches_is_seated_the_originals_way():
    """Measured on the 46 originals (Joel 2026-10-15): the breakout shows the
    baby's full-size frame 5, feet on row 12 -- inside the shell, which is
    drawn in front of its lower body."""
    import importlib.util
    import os
    from tuipet import data, egg
    spec = importlib.util.spec_from_file_location(
        "egg_template", os.path.join(os.path.dirname(__file__), "..", "tools", "egg_template.py"))
    tmpl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tmpl)
    _, by_num = data.load_sprites()
    for name in ("Nu Metal Empire Egg", "Gammamon Egg"):
        idx = next(i for i in range(egg.count()) if egg.hatch_name(i) == name)
        still, _, hatch = egg.frames(idx)
        assert hatch[11:] == still[11:]                  # the shell is in front
        rim_y, rim = tmpl.SEAT_RIM
        assert hatch[rim_y] == rim                       # its broken top line (Joel)
        dex = egg.hatch_targets(idx)[0]
        pose = by_num[dex]["frames"][tmpl.SEAT_FRAME]
        ink = [y for y, r in enumerate(pose) if "1" in r]
        lift = ink[-1] - max(tmpl.SEAT_FEET_ROW, ink[-1] - ink[0])
        for y in ink:                                    # every pixel above the shell is shown
            if y - lift < tmpl.SEAT_RIM[0]:
                for x, c in enumerate(pose[y]):
                    if c == "1":
                        assert hatch[y - lift][x] == "1", (name, y, x)
