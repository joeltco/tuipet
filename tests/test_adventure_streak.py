"""Adventure polish — the WIN STREAK bonus (arcade arc, 2026-07-21).

Pins the chain: consecutive won fights grow a run-local streak that scales
bounties (+25%/win past the first, capped at double); a loss or flee breaks
it, and so does ANY town rest (waypoint or warp) — the push-on gamble.
"""
from tuipet import adventure
from tuipet.adventure import Adventure, ZONES, STREAK_CAP
from tuipet.adventurescreen import AdventurePanel
from tuipet.pet import Pet


def _pet():
    return Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)


def _wild_zone():
    return next(z for z in ZONES if z["randoms"])


class _Win:
    won = True


class _Loss:
    won = False


def test_the_chain_grows_on_wins_and_breaks_on_anything_else():
    a = Adventure(_pet(), zone=_wild_zone())
    for _ in range(3):
        a.chain(True)
    assert a.streak == 3 and a.best_streak == 3
    a.chain(False)                                     # a loss (or flee) breaks it
    assert a.streak == 0 and a.best_streak == 3        # the best survives


def test_the_streak_scales_the_bounty_to_the_cap():
    a = Adventure(_pet(), zone=_wild_zone())
    a.holiday = None                                   # isolate the streak math
    e = {"name": "W", "bits": (8, 8)}                  # fixed: 8 * mult, exact
    a.chain(True)
    assert a.award_bits(e) == 8                        # first win: no bonus yet
    a.chain(True)
    assert a.award_bits(e) == 10                       # x1.25
    for _ in range(3):                                 # streak 5: past the cap
        a.chain(True)
    assert a.streak_mult() == STREAK_CAP
    assert a.award_bits(e) == 16                       # capped at double


def test_any_town_rest_breaks_the_chain(monkeypatch):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    z = _wild_zone()
    a = Adventure(_pet(), zone=z)
    a.chain(True), a.chain(True)
    a.loc = z["town_legs"][0][0] - 1                   # one leg shy of the town
    assert a.travel() == "town"                        # step in: the rest fires
    assert a.streak == 0                               # ...and the chain is gone
    p = _pet()
    p.add_item("town_transport")                       # the warp rest breaks it too
    b = Adventure(p, zone=z)
    b.chain(True), b.chain(True)
    assert b.use_transport("town_transport") == "town-warp"
    assert b.streak == 0


def test_the_panel_chains_fights_and_wears_the_marker(monkeypatch):
    """_battle_done feeds the chain BEFORE the bounty (a win pays its own
    streak), the march strip wears the xN marker from 2 up, a loss strips
    it, and the summary brags the run's best."""
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    p = _pet()
    pan = AdventurePanel(p, zone=_wild_zone())
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan.adv.holiday = None
    fixed = {"name": "W", "bits": (8, 8), "num": 100}
    p.bits = 0
    for _ in range(2):
        pan._fighting_enemy = dict(fixed)
        pan._battle_done(_Win())
    assert pan.adv.streak == 2 and p.bits == 8 + 10    # the 2nd win paid x1.25
    assert "×2" in pan.strip()                         # the marker rides the strip
    pan._fighting_enemy = dict(fixed)
    pan._battle_done(_Loss())
    assert pan.adv.streak == 0 and "×" not in pan.strip()
    card = pan._summary_frame().plain
    assert "Streak" in card and "×2 best" in card      # the brag line
