"""DNA charge mechanics (pet.apply_dna).

The strength clamp folds DVPet's setExercise(limit-1) onto tuipet's four-heart
gauge: charging DNA nudges Effort UP toward a ceiling of limit-1 (=3, "DNA
can't top you off"), but it is a CEILING, never a penalty -- a pet already
trained to full 4 keeps its heart (DNA audit 2026-07-08).
"""
from tuipet import data
from tuipet.pet import Pet


def _pet():
    p = Pet(num=-1, stage="Rookie")
    p.field = data.DNA_FIELDS[0]
    p.dna_owned = {f: 10 for f in data.DNA_FIELDS}
    p.dna_applied = {f: 0 for f in data.DNA_FIELDS}
    return p


def test_charge_never_drops_a_maxed_pet():
    p = _pet()
    p.strength = 4                                   # trained to full
    assert p.apply_dna(p.field, 1)
    assert p.strength == 4, "DNA charge must not knock a heart off a maxed pet"


def test_charge_ceils_at_limit_minus_one():
    # from below the ceiling DNA raises you, but only up to 3 -- never to 4
    for start, expected in ((0, 1), (1, 2), (2, 3), (3, 3)):
        p = _pet()
        p.strength = start
        assert p.apply_dna(p.field, 1)
        assert p.strength == expected, (start, p.strength)


def test_bulk_charge_still_ceils_at_three():
    p = _pet()
    p.strength = 0
    assert p.apply_dna(p.field, 5)                   # gain 5, but ceiling holds
    assert p.strength == 3


# ---- high-stakes wagers (bit-sink design 2026-07-14) --------------------------

def test_classic_wager_is_untouched():
    p = _pet()
    p.bits = 0
    assert p.dna_minigame_award(10, 48) == "DragonsRoar"     # rate 48 band
    assert p.dna_owned["DragonsRoar"] == 20                  # 10 owned + 10
    assert p.bits == 0                                       # no refund below the cap


def test_premium_volume_caps_at_the_bank_and_never_refunds():
    from tuipet.pet import MAX_DNA_INVENTORY
    p = _pet()
    p.bits = 0
    p.dna_owned["DragonsRoar"] = 0
    p.dna_minigame_award(9999, 48)
    assert p.dna_owned["DragonsRoar"] == MAX_DNA_INVENTORY   # 99, not 9999
    assert p.bits == 0, "the premium is lab work, not a refundable overflow"


def test_owned_overflow_still_refunds_like_the_device():
    from tuipet.pet import MAX_DNA_INVENTORY
    p = _pet()
    p.bits = 0
    p.dna_owned["DragonsRoar"] = 90
    p.dna_minigame_award(99, 48)
    assert p.dna_owned["DragonsRoar"] == MAX_DNA_INVENTORY
    assert p.bits == 90                                      # owned + 99 - cap


def test_stabilized_wager_never_spoils():
    from tuipet.pet import DNA_STABILIZER_BET
    p = _pet()
    # an over-mash (>80) and an under-mash (<=8) both clamp into the edge bands
    assert p.dna_minigame_award(DNA_STABILIZER_BET, 95) == "DarkArea"
    assert p.dna_minigame_award(DNA_STABILIZER_BET, 3) == "DeepSaver"
    # below the tier the same rates spoil, exactly as before
    q = _pet()
    assert q.dna_minigame_award(DNA_STABILIZER_BET - 1, 95) == "None"
    assert q.dna_minigame_award(1, 3) == "None"


def test_resonant_wager_splashes_the_neighbors():
    from tuipet.pet import DNA_RESONANT_BET, MAX_DNA_INVENTORY
    p = _pet()
    p.dna_owned = {f: 0 for f in data.DNA_FIELDS}
    p.dna_minigame_award(DNA_RESONANT_BET, 48)               # DragonsRoar
    assert p.dna_owned["DragonsRoar"] == MAX_DNA_INVENTORY
    splash = DNA_RESONANT_BET // 5
    assert p.dna_owned["WindGuardian"] == min(splash, MAX_DNA_INVENTORY)
    assert p.dna_owned["MetalEmpire"] == min(splash, MAX_DNA_INVENTORY)
    # an EDGE band splashes only its one real neighbor
    q = _pet()
    q.dna_owned = {f: 0 for f in data.DNA_FIELDS}
    q.dna_minigame_award(DNA_RESONANT_BET, 12)               # DeepSaver, the first band
    assert q.dna_owned["JungleTrooper"] == min(splash, MAX_DNA_INVENTORY)


def test_bet_screen_walks_only_the_wagers_that_buy_something():
    """Joel 2026-10-15 (DNA call #3 = A): 100-499 all paid 99 DNA, 501-2499
    the same as 500, 2501+ the same as 2500 -- the picker offers 1..99, 500
    and 2500 only."""
    from tuipet.dnascreen import DNAPanel
    p = _pet()
    p.bits = 50_000
    pan = DNAPanel(p)
    pan.phase, pan.bet = "bet", 1
    seen = {1}
    for _ in range(200):
        pan.key("right")
        seen.add(pan.bet)
    assert seen == set(range(1, 100)) | {500, 2500}
    assert pan.bet == 2500                                   # the top tier caps
    pan.key("left")
    assert pan.bet == 500
    pan.key("left")
    assert pan.bet == 99
    pan.bet = 1
    pan.key("up")
    assert pan.bet == 99                                     # ↑ jumps tier to tier
    pan.key("up")
    assert pan.bet == 500
    pan.key("up")
    pan.key("up")
    assert pan.bet == 2500
    pan.key("down")
    assert pan.bet == 500
    pan.key("down")
    pan.key("down")
    assert pan.bet == 1


def test_the_result_page_reports_what_actually_banked():
    """DNA review 2026-07-18: near the 99 cap the overflow refunds as bits,
    and the result page said "Got 99" while 9 landed.  It now reports the
    true banked delta and the refund."""
    from tuipet import dnascreen
    from tuipet.pet import Pet
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.world_seconds = 12 * 60.0
    p.bits = 5000
    p.dna_owned["DragonsRoar"] = 90                  # 9 slots left
    pan = dnascreen.DNAPanel(p)
    pan.phase, pan.bet, pan.mash_f = "mash", 99, 0
    pan.hits = 48                                    # lands in the DragonsRoar band
    pan.mash_f = dnascreen.MASH_TICKS                # the clock expires this tick
    pan.anim()
    field, wager, rate, banked, refund = pan.won
    assert field == "DragonsRoar" and wager == 99
    assert banked == 9 and refund == 90              # truth, not the wager
    page = pan.text().plain
    assert "Got 9 Dragons Roar" in page and "Refund: 90b" in page


def test_a_spoiled_mash_refunds_half_and_banks_no_dud_dna():
    """Joel 2026-10-15 (DNA call #4 = A): None DNA could never be spent."""
    p = _pet()
    p.bits = 1000
    dud = p.dna_owned.get("None", 0)
    assert p.dna_bet(80)
    assert p.dna_minigame_award(80, 0) == "None"
    assert p.bits == 1000 - 80 + 40
    assert p.dna_owned.get("None", 0) == dud


def test_legacy_dud_dna_cashes_out_on_load():
    from tuipet import persistence
    p = _pet()
    p.bits = 100
    p.dna_owned["None"] = 60
    loaded, msg = persistence.pet_from_save(persistence.to_save_dict(p))
    assert loaded.bits == 130 and loaded.dna_owned["None"] == 0
    assert "dud DNA" in msg


def test_a_charge_never_outruns_the_energy_that_pays_for_it():
    """Joel 2026-10-15 (DNA call #5 = A): past empty energy the old bill kept
    charging and drained obedience; now the charge stops at what energy pays."""
    p = _pet()
    off = next(f for f in p.dna_owned if f not in ("None", p.field))
    p.dna_owned[off] = 99
    p.energy, ob = 10, p.obedience
    assert p.dna_affordable(off) == 5                       # 2 energy per off-Field unit
    assert not p.apply_dna(off, 6)
    assert p.dna_owned[off] == 99 and p.energy == 10
    assert p.apply_dna(off, 5)
    assert p.energy == 0 and p.obedience == ob
    assert p.dna_affordable(off) == 0 and not p.apply_dna(off, 1)


def test_the_dna_crystal_costs_150b():
    """Joel 2026-10-15 (DNA call #6 = A): 1500b for 10 DNA vs ~10b by the
    mash; 150b keeps a 15x premium for no mash and a sure Field."""
    from tuipet import shop
    assert shop.CATALOG["dna_crystal"].price == 150
