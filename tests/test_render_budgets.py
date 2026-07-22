"""RENDER BUDGETS — the night hardening sweep (2026-07-21).

Every state today's arcs shipped, driven through the REAL panels and held
to the physical laws: text() fits the 12-row LCD, no line exceeds the
40-col box, and every strip stays within its 40-char lane.  pytest never
sees the pixels (the UI-render law) — but it CAN count rows and columns,
which is exactly where clipped footers and overflowing strips hide.
(tools/adventure_sheet.py is this sweep's human-eyeball twin.)
"""
import datetime

import pytest
from rich.text import Text

from tuipet import adventure, tournament
from tuipet.adventurescreen import (AdventurePanel, ZonePickPanel,
                                    HZ_TELE_T, HZ_LUNGE_T, INV_WALK_T,
                                    INV_REVEAL_T, INV_HOLD_T)
from tuipet.pet import Pet

D = datetime.date(2026, 3, 3)
MAX_ROWS, MAX_COLS = 12, 40


def _pet():
    return Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)


def _road(monkeypatch, zone=None):
    monkeypatch.setattr(adventure, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "HAZARD_CHANCE", 0.0)
    monkeypatch.setattr(adventure, "FIND_CHANCE", 0.0)
    monkeypatch.setattr(tournament, "_today", lambda: D)
    pan = AdventurePanel(_pet(), zone=zone or adventure.ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan._wx = 14.0
    return pan


def _boss_zone():
    return next(z for z in adventure.ZONES if z["bosses"])


def _parade_zone():
    return next(z for z in adventure.ZONES
                if z["bosses"] and z["bosses"][0].get("parade_msg"))


def _states(monkeypatch):
    """(name, panel) for every shipped state, staged like the contact sheet."""
    out = []

    p = _road(monkeypatch)
    out.append(("march", p))
    s = _road(monkeypatch)
    s.pet.sick = True
    s.frame_i = 5
    out.append(("march-sick", s))
    a = _road(monkeypatch)
    a.pet.age_seconds = 16 * 86400.0
    out.append(("march-aged", a))
    n = _road(monkeypatch)
    n.pet.asleep = True
    out.append(("nap", n))
    r = _road(monkeypatch)
    r._refuse_t, r._refused = 12, True
    out.append(("refuse-shake", r))
    r2 = _road(monkeypatch)
    r2._refuse_t, r2._refused = 0, True
    out.append(("refuse-planted", r2))
    g = _road(monkeypatch)
    g._find = adventure.ZONES[0]["find_keys"][0]
    g.frame_i = 6
    out.append(("glint", g))

    d = _road(monkeypatch)
    d._find = adventure.ZONES[0]["find_keys"][0]
    d.key("enter")
    for _ in range(INV_WALK_T + 4):
        d.anim()
    out.append(("dig-meter", d))
    for t in ("suspense", "reveal", "carry"):
        c = _road(monkeypatch)
        c._find = adventure.ZONES[0]["find_keys"][0]
        c.key("enter")
        goal = {"suspense": INV_WALK_T + 4, "reveal": INV_REVEAL_T + 3,
                "carry": INV_HOLD_T + 5}[t]
        for _ in range(INV_WALK_T + 2):
            c.anim()
        c.key("space")
        while c._scene and c._scene["t"] < goal:
            c.anim()
        out.append((f"dig-{t}", c))

    for name, tt, dodged, hit in (
            ("hazard-telegraph", 3, False, False),
            ("hazard-charge", HZ_TELE_T + HZ_LUNGE_T // 2, False, False),
            ("hazard-duck", HZ_TELE_T + HZ_LUNGE_T + 4, True, False),
            ("hazard-eaten", HZ_TELE_T + HZ_LUNGE_T + 2, False, True)):
        h = _road(monkeypatch)
        h._hazard = {"t": tt, "enemy": adventure.ZONES[0]["randoms"][0],
                     "dodged": dodged, "hit": hit}
        out.append((name, h))

    gt = _road(monkeypatch, zone=_boss_zone())
    gt.adv.loc = gt.adv.total
    gt._at_gate, gt.travelling = True, False
    out.append(("gate-faceoff", gt))

    pu = _road(monkeypatch)
    pu.travelling = False
    pu._pulse = {"t": 6, "parade": [], "msg": None}
    out.append(("pulse", pu))

    pz = _parade_zone()
    pa = _road(monkeypatch, zone=pz)
    pa.travelling = False
    pa._parade = {"t": 10, "nums": [b["num"] for b in pz["bosses"]][:3],
                  "msg": pz["bosses"][0]["parade_msg"]}
    out.append(("parade", pa))

    sm = _road(monkeypatch)
    sm.adv.done = True
    sm.adv.bits_earned, sm.adv.wins, sm.adv.fights = 264, 5, 5
    sm.adv.finds, sm.adv.lives, sm.adv.best_streak = 3, 2, 4
    sm.adv.holiday = "Odaiba Memorial Day"
    sm._new_best, sm._summary, sm.travelling = True, True, False
    out.append(("summary-full", sm))

    tp = AdventurePanel(_pet(), zone=adventure.ZONES[0])
    for _ in range(30):
        tp.anim()
    out.append(("teleport", tp))

    from tuipet import persistence
    persistence.zone_best_set(0, 264)
    pk = _pet()
    pk.adv_progress = 3
    out.append(("picker", ZonePickPanel(pk)))

    from tuipet.townscreen import TownPanel
    out.append(("town-hub", TownPanel(_pet(), town_id=4)))

    from tuipet.shopscreen import ShopPanel
    tb = _pet()
    tb.bits = 9999
    sp = ShopPanel(tb, town_id=4)
    out.append(("town-shop-food", sp))
    sp2 = ShopPanel(tb, town_id=4)
    sp2.tab = 1
    out.append(("town-shop-items", sp2))
    for _ in range(3):
        sp.key("enter")                         # drain the cap: the out row
    out.append(("town-shop-out", sp))
    out.append(("town-bag", ShopPanel(tb, start_mode="bag", bag_only=True,
                                      town_id=0)))
    return out


def test_every_state_respects_the_physical_lcd(monkeypatch):
    failures = []
    for name, pan in _states(monkeypatch):
        txt = pan.text()
        lines = txt.plain.split("\n")
        if len(lines) > MAX_ROWS + 1:            # +1: a trailing newline split
            failures.append(f"{name}: {len(lines)} rows")
        for i, ln in enumerate(lines):
            if len(ln) > MAX_COLS:
                failures.append(f"{name}: row {i} is {len(ln)} cols: {ln!r}")
        strip = getattr(pan, "strip", lambda: "")()
        if strip and len(Text.from_markup(strip).plain) > MAX_COLS:
            failures.append(f"{name}: strip {len(Text.from_markup(strip).plain)}")
    assert not failures, "\n".join(failures)


def test_every_state_animates_ten_ticks_clean(monkeypatch):
    """The liveness sweep: each staged state survives ten anim+render+strip
    cycles without raising -- the crash class the one-frame sheet misses."""
    for name, pan in _states(monkeypatch):
        for _ in range(10):
            pan.anim()
            assert pan.text() is not None, name
            pan.strip()


@pytest.mark.parametrize("k", ["escape", "space", "enter", "tab", "up",
                               "down", "left", "right", "r", "t", "n", "q"])
def test_every_state_eats_any_key_without_crashing(monkeypatch, k):
    """The key-mash sweep: no staged state may crash on any input."""
    for name, pan in _states(monkeypatch):
        try:
            pan.key(k)
            pan.anim()
            pan.text()
        except Exception as ex:                  # pragma: no cover
            raise AssertionError(f"{name} crashed on {k!r}: {ex}") from ex


def test_the_cup_board_respects_the_lcd_too(monkeypatch):
    """The cup audit's overflow (the featured row ran 44 cols): the board is
    in the net now, browsed across a dozen keys."""
    from tuipet.tournamentscreen import TournamentPanel
    p = _pet()
    p.strength = p.hunger = 4
    p._set_energy(p.max_energy)
    p.bits = 99999
    pan = TournamentPanel(p)
    for k in (None, "down", "down", "up", "pagedown", "pageup"):
        if k:
            pan.key(k)
        pan.anim()
        lines = pan.text().plain.split("\n")
        assert len(lines) <= MAX_ROWS + 1
        for i, ln in enumerate(lines):
            assert len(ln) <= MAX_COLS, (k, i, ln)
        s = pan.strip()
        if s:
            assert len(Text.from_markup(s).plain) <= MAX_COLS
