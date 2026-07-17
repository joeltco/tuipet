"""Jogress doors vs humulos canon (audit 2026-07-17, the LV-fix treatment).

Verified this audit: Omnimon (WarGreymon+MetalGarurumon), Omnimon Alter-S
(BlitzGreymon+CresGarurumon), RustTyrannomon (Machinedramon+Aegisdramon),
Examon (Slayerdramon+Breakdramon), GraceNovamon (Apollomon+Dianamon),
Mastemon (Angewomon+LadyDevimon), Boltboutamon (Piemon+Vamdemon -- wikimon
confirms, the pair looked wrong and wasn't).  FIXED: Chaosmon's BanchoLeomon
side and Rafflesimon's Lotusmon side were missing their doors (symmetric
canon); the name-intersection channel let two WarGreymons mirror-fuse
(exact doors now bind to the peer's NUM); and Jesmon GX is canon ONE-SIDED
("only Jesmon X ... can be used to evolve Gankoomon X"), which the
both-or-neither lobby could never open -- the COMPANION role fixes it.
(Alphamon Ouryuken stays out: Ouryuken isn't in the DVPet roster.)
"""
from tuipet import data, jogress, lines
from tuipet.pet import Pet, DP_MAX

# canon one-sided doors: the companion never evolves (wikimon/humulos DMX3)
ONE_SIDED = {(863, 1)}          # Jesmon X companion -> Jesmon GX (x3a/x3b)


def _pet(num, stage="Mega", line_id=""):
    rec = data.record_for(num)
    p = Pet(num=num, name=rec.get("name", "?"), stage=stage,
            attribute=rec.get("attribute", "Vaccine"), obedience=500)
    p.world_seconds = 600.0
    p.dp = DP_MAX
    p.energy = p.max_energy
    p.line_id = line_id
    return p


def test_every_exact_door_is_mutual_or_declared_one_sided():
    """The lobby fusion channel needs the partner to resonate: every exact
    door must have its mirror row in SOME line, or be on the canon one-sided
    list (where the companion role answers instead)."""
    L = lines.load_lines()
    one_way = []
    for lid, line in L.items():
        for parent, rows in line["children"].items():
            for row in rows:
                j = row["jogress"]
                if j is None or isinstance(j, tuple):
                    continue
                mutual = any(r2["jogress"] == parent and r2["num"] == row["num"]
                             for l2 in L.values()
                             for r2 in l2["children"].get(j, []))
                if not mutual:
                    one_way.append((lid, parent, row["num"], j))
    allowed = {j for j, _ in ONE_SIDED}
    stray = [w for w in one_way if w[3] not in allowed]
    assert not stray, f"one-way doors with no canon exemption: {stray}"
    assert one_way, "the one-sided family vanished -- update ONE_SIDED"


def test_chaosmon_opens_from_both_sides():
    """FIXED this audit: BanchoLeomon's side (jyarimon) was missing."""
    L = lines.load_lines()
    assert any(r["num"] == 348 and r["jogress"] == 349
               for r in L["jyarimon"]["children"].get(350, []))
    assert any(r["num"] == 348 and r["jogress"] == 350
               for r in L["draco"]["children"].get(349, []))


def test_rafflesimon_opens_from_both_sides():
    """FIXED this audit: Lotusmon's side (dokimon) was missing."""
    L = lines.load_lines()
    assert any(r["num"] == 508 and r["jogress"] == 285
               for r in L["dokimon"]["children"].get(374, []))
    assert any(r["num"] == 508 and r["jogress"] == 374
               for r in L["wgu"]["children"].get(285, []))


def test_exact_doors_bind_to_the_peers_num():
    """Two WarGreymons must never mirror-fuse into Omnimon: the exact door
    wants MetalGarurumon (279), and the name intersection alone no longer
    opens it."""
    war = _pet(280, line_id="mem")
    twin_payload = {"num": 280, "name": "WarGreymon", "stage": "Mega",
                    "fusions": ["Omnimon"], "attrs": [], "wants": [279]}
    assert jogress.resolve_online(war, twin_payload) is None or \
        not (jogress.resolve_online(war, twin_payload) or {}).get("num") == \
        next(n for n, r in data.load_sprites()[1].items() if r["name"] == "Omnimon")
    partner_payload = {"num": 279, "name": "MetalGarurumon", "stage": "Mega",
                       "fusions": ["Omnimon"], "attrs": [], "wants": [280]}
    r = jogress.resolve_online(war, partner_payload)
    assert r and data.record_for(r["num"])["name"] == "Omnimon"


def test_jesmon_gx_is_one_sided_with_a_companion():
    ganko = _pet(next(n for n, r in data.load_sprites()[1].items()
                      if r["name"] == "Gankoomon X"), line_id="x3a")
    jes = _pet(863, line_id="x3a")
    # the evolving side: the exact door matches the companion's num
    r = jogress.resolve_online(ganko, {"num": 863, "name": "Jesmon X",
                                       "stage": "Mega", "fusions": [],
                                       "attrs": [], "wants": []})
    assert r and data.record_for(r["num"])["name"] == "Jesmon GX"
    # the companion side: no door of its own, but the peer WANTS it
    r2 = jogress.resolve_online(jes, {"num": ganko.num, "name": "Gankoomon X",
                                      "stage": "Mega", "fusions": ["Jesmon GX"],
                                      "attrs": [], "wants": [863]})
    assert r2 and r2.get("companion")
    # ...and can_jogress lets the companion enter the session at full DP
    assert jogress.can_jogress(jes) is None
