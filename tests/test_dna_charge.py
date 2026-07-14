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
    from tuipet.pet import MAX_DNA_INVENTORY
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


def test_bet_screen_pages_and_caps_at_the_wager_limit():
    from tuipet.pet import MAX_DNA_WAGER
    from tuipet.dnascreen import DNAPanel
    p = _pet()
    p.bits = 50_000
    pan = DNAPanel(p)
    pan.phase, pan.bet = "bet", 1
    pan.key("up")
    assert pan.bet == 101                                    # ↑ pages +100
    for _ in range(200):
        pan.key("up")
    assert pan.bet == MAX_DNA_WAGER                          # hard cap
    pan.key("down")
    assert pan.bet == MAX_DNA_WAGER - 100
