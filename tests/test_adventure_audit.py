"""THE ADVENTURE AUDIT — the pins (2026-07-25).

Joel: "lets do a full blown adventure audit next."

Two findings and the invariants a run must hold, measured by RUNNING the
road rather than reading it:

  * F1 (hotfixed v0.5.250, pinned in test_battle_audit) — the boss gate
    inherited the HOME energy clause and refused every honest arrival.
  * F2 — the Town Transport past the last town: every zone has exactly
    ONE town span, so once you walk past it the 500b ticket bought a rest
    in place while announcing "Warped to a town" — no hub, no shop, no
    visit-or-walk-on choice.  Late, drained and past the town is exactly
    when a tamer reaches for that ticket.
  * the run invariants: lives, progress, the weight floor, the effort
    cap, the streak, and loot that the bag can actually use.
"""
import random

import pytest

from tuipet import adventure as A, shop
from tuipet.adventurescreen import AdventurePanel
from tuipet.pet import Pet


def _pet(**kw):
    p = Pet(num=100, stage="Champion", attribute="Vaccine", obedience=500)
    p.energy, p.hunger, p.strength = p.max_energy, 4, 4
    p.weight = p._base_weight() + 6
    p.bits, p.adv_progress = 0, 3
    for k, v in kw.items():
        setattr(p, k, v)
    return p


def _zone_with_town():
    return next(z for z in A.ZONES if z.get("town_legs"))


# ---- F2: the Town Transport --------------------------------------------


# ---- the run's invariants ----------------------------------------------

@pytest.mark.parametrize("seed", [11, 12, 13])
def test_a_whole_run_holds_its_invariants(seed):
    random.seed(seed)
    p = _pet()
    adv = A.Adventure(p, zone=A.ZONES[A.PROGRESSION[seed % len(A.PROGRESSION)]])
    base = p._base_weight()
    for _ in range(4000):
        r = adv.travel()
        if r is None:
            break
        tag = r[0] if isinstance(r, tuple) else r
        if tag == "encounter":
            won = random.random() < 0.7
            p.record_battle(won, r[1])
            adv.chain(won)
            if won:
                adv.award_bits(r[1])
            if adv.resolve(won) == "failed":
                break
        elif tag == "boss":
            p.record_battle(True, r[1])
            adv.resolve_boss(True)
            break
        elif tag == "find":
            assert r[1] in shop.CATALOG or r[2], "found loot the bag can't use"
            adv.finds += 1
        elif tag == "hazard":
            adv.hazard_hit()
        elif tag == "refused":
            break
        assert 0 <= adv.lives <= A.MAX_LIVES
        assert 0 <= adv.loc <= adv.total
        assert p.weight >= base, "the march ground the pet under its base weight"
        assert p.strength <= A.TRAVEL_EFFORT_CAP
        assert adv.streak <= adv.best_streak
    assert adv.bits_earned >= 0


def test_a_town_rest_fills_the_tank_breaks_the_chain_and_fires_ONCE(monkeypatch):
    # a quiet road: this pin is about the REST, not about what jumps out
    for knob in ("ENCOUNTER_CHANCE", "HAZARD_CHANCE", "FIND_CHANCE"):
        monkeypatch.setattr(A, knob, 0.0)
    z = _zone_with_town()
    a, _b, _t = z["town_legs"][0]
    p = _pet(energy=1)
    adv = A.Adventure(p, zone=z)
    adv.loc, adv.lives, adv.streak = a - 1, 1, 4
    adv.best_streak = 4
    assert adv.travel() == "town"                       # stepped in: rested
    assert adv.lives == A.MAX_LIVES
    assert p.energy >= p.max_energy // 2                 # at least half a tank (D1)
    assert adv.streak == 0 and adv.best_streak == 4      # the chain pays the price
    p.energy = 1
    adv.travel()                                         # the NEXT leg in town
    assert p.energy == 1, "the rest re-fired inside the same town span"


# ---- progression --------------------------------------------------------

def test_only_the_frontier_advances_the_road():
    p = _pet()
    p.adv_progress = 3
    assert A.record_win(p, A.ZONES[A.PROGRESSION[3]]) and p.adv_progress == 4
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[3]])      # a replay
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[10]])     # out of order
    assert p.adv_progress == 4
    p.adv_progress = len(A.PROGRESSION)
    assert not A.record_win(p, A.ZONES[A.PROGRESSION[-1]])     # the end holds
    assert len(A.unlocked_indices(p)) == len(A.PROGRESSION)


# ---- every road state renders (the panel smoke law) ---------------------

def _panel(**kw):
    p = _pet(**kw)
    pan = AdventurePanel(p, zone=A.ZONES[A.PROGRESSION[2]])
    pan._trans = pan._pulse = None
    pan.travelling = pan._landed = True
    return p, pan


ROAD_STATES = {
    "march": lambda pan: None,
    "glint": lambda pan: setattr(pan, "_find", "fish"),
    "ambush": lambda pan: setattr(pan, "_hazard",
                                  {"t": 1, "enemy": {"num": 120, "name": "K"},
                                   "dodged": False, "hit": False}),
    "town prompt": lambda pan: setattr(pan, "_town_prompt", True),
    "town rest": lambda pan: setattr(pan, "_rest_t", 3),
    "life recovery": lambda pan: setattr(pan, "_heal_t", 3),
    "at the gate": lambda pan: setattr(pan, "_at_gate", True),
    "summary": lambda pan: setattr(pan, "_summary", True),
    "parade": lambda pan: setattr(pan, "_parade",
                                  {"t": 1, "nums": [120], "msg": "The gate falls!"}),
    "pulse": lambda pan: setattr(pan, "_pulse", {"t": 1, "parade": [], "msg": None}),
}


@pytest.mark.parametrize("state", sorted(ROAD_STATES))
def test_every_road_state_renders_inside_the_arena(state):
    _p, pan = _panel()
    ROAD_STATES[state](pan)
    txt = pan.text()
    plain = txt.plain if hasattr(txt, "plain") else str(txt)
    rows = plain.split("\n")
    assert len(rows) <= 12, f"{state}: {len(rows)} rows"
    assert max(len(r) for r in rows) <= 40, f"{state}: too wide"
    pan.strip()                                   # the hint line renders too


# ==== THE 2026-07-25 FULL GAMEPLAY AUDIT — the batch pins =================
# Six parallel sweeps (engine / panel / town / cross-system / balance sim /
# live-play); every fix below verified failing on the pre-fix tree.

from rich.cells import cell_len as _cl
import re as _re


def _plain(s):
    return _re.sub(r"\[[^]]*]", "", s)


def _frontier_replay(p):
    """A pet standing on a conquered road position 0 (replay=True there)."""
    p.adv_progress = 1
    return A.Adventure(p, zone=A.ZONES[A.PROGRESSION[0]])


def test_danger_rolls_before_treasure(monkeypatch):
    """A festival doubles finds; finds must not shadow hazards -- the old
    order made the road ~14% SAFER on a holiday."""
    p = _pet()
    adv = A.Adventure(p, zone=A.ZONES[A.PROGRESSION[0]])
    monkeypatch.setattr(A, "ENCOUNTER_CHANCE", 0.0)
    monkeypatch.setattr(adv, "_roll_hazard", lambda: {"name": "X"})
    monkeypatch.setattr(adv, "_roll_find", lambda: ("fish", False))
    out = adv.travel()
    assert out[0] == "hazard"


def test_the_towns_safe_ground_covers_the_walk_in_not_the_walk_out(monkeypatch):
    z = next(x for x in A.ZONES if x.get("town_legs"))
    a, b, _t = z["town_legs"][0]
    p = _pet()
    adv = A.Adventure(p, zone=z)
    monkeypatch.setattr(A, "ENCOUNTER_CHANCE", 1.0)   # every off-town leg rolls
    monkeypatch.setattr(A, "FIND_CHANCE", 0.0)
    monkeypatch.setattr(A, "HAZARD_CHANCE", 0.0)
    adv.loc = a - 1                          # destination a: town ground
    assert adv._roll_encounter() is None     # no ambush on the doorstep
    adv._immunity = 0
    adv.loc = b                              # destination b+1: outside
    assert adv._roll_encounter() is not None  # the walk OUT rolls again


def test_grace_spends_on_town_legs_too():
    z = next(x for x in A.ZONES if x.get("town_legs"))
    a, _b, _t = z["town_legs"][0]
    p = _pet()
    adv = A.Adventure(p, zone=z)
    adv.loc, adv._immunity = a, 3
    adv._roll_encounter()
    assert adv._immunity == 2                # legs, not fights dodged


def test_the_replay_bounty_pays_once_a_day_per_zone():
    boss = {"name": "B", "bits": (100, 100), "boss": True}
    wild = {"name": "w", "bits": (10, 10)}
    p = _pet(bits=0)
    adv = _frontier_replay(p)
    assert adv.award_bits(boss) > 0          # first replay bounty of the day
    adv2 = _frontier_replay(p)               # the back-to-back loop
    assert adv2.award_bits(boss) == 0        # rationed
    assert adv2.bounty_spent
    assert adv2.award_bits(wild) > 0         # wilds still pay
    q = _pet(bits=0, adv_progress=0)
    fresh = A.Adventure(q, zone=A.ZONES[A.PROGRESSION[0]])
    assert not fresh.replay
    assert fresh.award_bits(boss) > 0        # a FIRST conquest is untouched


def test_the_front_door_refuses_what_the_road_cannot_cure():
    assert "hungry" in _pet(hunger=0).can_adventure()
    assert "Clean" in _pet(poop=3).can_adventure()
    assert _pet(sick=True).can_adventure() is None      # the pilgrimage embarks
    hurt = _pet()
    hurt.injured, hurt.inj_length = True, 999.0
    assert hurt.can_adventure() is None


def test_the_town_rest_is_the_roads_sickbed():
    p = _pet(sick=True)
    p.injured, p.inj_length = True, 999.0
    adv = A.Adventure(p, zone=A.ZONES[A.PROGRESSION[0]])
    adv._rest_up()
    assert not p.sick and not p.injured and p.inj_length == 0.0


def test_an_unfit_body_balks_at_a_wild(monkeypatch):
    p = _pet()
    p.injured, p.inj_length = True, 999.0
    pan = AdventurePanel(p, zone=A.ZONES[A.PROGRESSION[0]])
    pan._trans = None
    pan.travelling = True
    pan._start_battle({"name": "w", "bits": (1, 1)})
    assert pan.sub is None                   # no bout with a hurt body
    assert pan.travelling                    # the march keeps flowing
    assert "slipped away" in pan._note
    assert pan.adv.fights == 0               # nothing recorded


def test_the_second_wind_works_on_the_knocked_back_gate():
    """The retry arm (no body refusal) left a held Life Recovery inert at
    the exact moment it exists for."""
    p = _pet()
    p.add_item("life_recovery")
    pan = AdventurePanel(p, zone=A.ZONES[A.PROGRESSION[0]])
    pan._trans = None
    pan.travelling = False
    pan._at_gate, pan._gate_refusal = True, None
    pan.adv.lives = 1
    pan.key("t")
    assert pan._transport                    # the menu opens on the retry arm
    pan.key("enter")
    assert pan.adv.lives == A.MAX_LIVES
    assert pan._heal_t > 0
    s = _plain(pan.strip())
    assert "second wind" in s                # the beat SPEAKS at the gate
    for _ in range(200):
        pan.anim()                           # ...and DRAINS at the gate
    assert pan._heal_t == 0


def test_a_road_death_ends_the_run_now():
    p = _pet()
    pan = AdventurePanel(p, zone=A.ZONES[A.PROGRESSION[0]])
    pan._trans = None
    pan.travelling = True
    p.dead = True
    pan.anim()
    assert pan._trans is not None            # straight to the homecoming
    assert pan._summary_shown                # a grave outranks a score card


def test_the_town_hub_speaks_the_item_verdicts_and_closes_over_a_corpse():
    from tuipet.townscreen import TownPanel
    p = _pet()
    t = TownPanel(p, 0)
    t._sub_done(("eat", "f:13", "...it was DELICIOUS. And fatal."))
    assert "fatal" in t.msg                  # the verdict SPEAKS
    t._sub_done(("evolve", 100))
    assert "evolved" in t.msg
    p.dead = True
    assert t.key("enter") == ("done", None)  # any key closes over a corpse


@pytest.mark.parametrize("zi", range(len(A.ZONES)))
def test_every_gate_strip_fits_the_box(zi):
    """Ten boss names ran 41-45 cells and marqueed the REQUIRED keys; the
    pulse line ran to 71.  Cells, not chars (bug-#32 law)."""
    p = _pet()
    p.add_item("life_recovery")
    pan = AdventurePanel(p, zone=A.ZONES[zi])
    pan._trans = None
    pan.travelling = False
    pan._at_gate = True
    pan.adv.lives = 1                        # life recovery held -> T shown
    assert _cl(_plain(pan.strip())) <= 40
    pan._gate_refusal = "Too hungry to fight."   # the widest refusal clause
    assert _cl(_plain(pan.strip())) <= 40
    pan._gate_refusal = None
    pan._pulse = {"t": 0, "parade": [], "msg": None,
                  "line": f"{pan.adv.name} — cleared!"}
    assert _cl(_plain(pan.strip())) <= 40


def test_the_zone_picker_holds_its_shape_and_trims_with_ellipsis(monkeypatch):
    from tuipet.adventurescreen import ZonePickPanel
    from tuipet import persistence
    p = _pet()
    p.adv_progress = len(A.PROGRESSION)          # the whole road: the longest
    long_zi = max(A.PROGRESSION, key=lambda i: len(A.ZONES[i]["name"]))
    monkeypatch.setattr(persistence, "zone_bests", lambda: {long_zi: 123})
    pan = ZonePickPanel(p)
    rows = []
    for cur in range(len(pan.indices)):
        pan.cursor = cur
        rows.append(len(pan.text().plain.rstrip("\n").split("\n")))
    assert len(set(rows)) == 1               # the footer never hops a row
    pan.cursor = pan.indices.index(long_zi)
    assert A.ZONES[long_zi]["name"] in pan.text().plain   # map names fit whole


def test_the_picker_tells_you_the_bounty_is_claimed():
    from tuipet.adventurescreen import ZonePickPanel
    p = _pet()
    p.adv_progress = 1
    p.road_bounty = {"day": shop._today_ordinal(), str(A.PROGRESSION[0]): 1}
    pan = ZonePickPanel(p)
    pan.cursor = pan.indices.index(A.PROGRESSION[0])
    assert "bounty claimed today" in pan.text().plain


def test_the_area_atom_reads_the_device_lifetime(monkeypatch):
    from tuipet import lines, persistence
    p = _pet()
    p.adv_progress = 0
    monkeypatch.setattr(persistence, "get_progress",
                        lambda: {"maps": {3}, "raids": 0})
    assert lines.check_rule(p, lines.parse_rule("AREA 3"))   # lifetime maps open it
    met, txt = lines._atom_row(p, ("area", "3", None))
    assert "map 4" in txt                    # the row speaks the road door


def test_the_vitals_stay_live_on_the_road():
    import inspect
    from tuipet.app import TuiPetApp
    src = inspect.getsource(TuiPetApp.on_frame)
    assert "self.stats_w.paint(self.pet)" in src   # the liveness fallback


def test_the_bug_report_wears_the_running_version():
    import inspect
    from tuipet.app import TuiPetApp
    assert "_boot_version" in inspect.getsource(TuiPetApp._bug_meta)
    assert "_boot_version" in inspect.getsource(TuiPetApp.__init__)


def test_the_repick_carries_the_antiprinter_ledgers():
    import inspect
    from tuipet.app import TuiPetApp
    src = inspect.getsource(TuiPetApp._hatch_new)   # the re-pick estate copy
    assert "town_bought" in src and "road_bounty" in src
