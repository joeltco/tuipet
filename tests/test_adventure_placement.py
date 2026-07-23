"""Adventure PLACEMENT sweep — the pixel pin (anim audit D1, 2026-07-22).

No test ever asserted non-overlap or in-window for any adventure scene, and
the window clip hides placement bugs from every observer (the contact sheet
prints the POST-clip buffer, so an accidentally-clipped sprite just looks
absent).  This sweep intercepts menu.paint PRE-clip and asserts the actual
ink: beats fully inside the 32-col window, actor ink-sets disjoint, the
ambusher visible at impact, the teleport reveal standing where the march
will continue.  Driven at FOUR march positions — the old tooling fixed
_wx=14, the exact spot where none of the right-half defects manifest.
"""
import pytest

from tuipet import adventure, grid, menu
from tuipet.adventurescreen import (AdventurePanel, HZ_TELE_T, HZ_LUNGE_T,
                                    INV_HOLD_T, PARADE_T, TOWN_HOLD)
from tuipet.pet import Pet

WXS = (4.0, 14.0, 20.0, 32.0)
PH = 24                                       # ROWS * 2: the LCD pixel height


def _pet():
    return Pet(num=29, stage="Champion", attribute="Vaccine", obedience=500)


def _on_road(wx, zone=None):
    pan = AdventurePanel(_pet(), zone=zone or adventure.ZONES[0])
    pan._trans = None
    pan._landed = True
    pan.travelling = True
    pan._wx = wx
    return pan


def _capture(pan, monkeypatch):
    """One rendered frame's (placements, overlay) BEFORE the clip."""
    cap = {}
    real = menu.paint

    def spy(placements, bgimg, **kw):
        cap["placements"] = list(placements)
        cap["overlay"] = list(kw.get("overlay") or [])
        cap["clip"] = kw.get("clip")
        return real(placements, bgimg, **kw)

    monkeypatch.setattr(menu, "paint", spy)
    pan.text()
    monkeypatch.setattr(menu, "paint", real)
    return cap


def _ink(placement):
    """A placement's lit pixels, render_scene's own math (baseline + mirror)."""
    rows, x, mirror = placement
    src = [r[::-1] for r in rows] if mirror else rows
    oy = max(0, PH - len(src) - 2)
    return {(x + cx, oy + cy) for cy, row in enumerate(src)
            for cx, ch in enumerate(row) if ch == "1"}


def _in_window(pts):
    return all(grid.X0 <= x < grid.X1 and grid.TOP <= y < grid.FLOOR
               for x, y in pts)


# ---- beats: one mon, fully inside, marks off the sprite ---------------------

@pytest.mark.parametrize("wx", WXS)
def test_standing_beats_keep_the_mon_fully_in_window(wx, monkeypatch):
    pan = _on_road(wx)
    pan._town_prompt = True
    cap = _capture(pan, monkeypatch)
    assert len(cap["placements"]) == 1
    assert _in_window(_ink(cap["placements"][0]))
    assert cap["clip"] == grid.WINDOW


@pytest.mark.parametrize("wx", WXS)
def test_the_nap_zzz_never_merges_into_the_sleeper(wx, monkeypatch):
    pan = _on_road(wx)
    pan.pet.asleep = True
    cap = _capture(pan, monkeypatch)
    pet = _ink(cap["placements"][0])
    assert _in_window(pet)
    zzz = set(cap["overlay"])
    assert zzz, "the Zzz overlay must render"
    assert not (zzz & pet), "audit A7: the Zzz sat inside the sleeper"


@pytest.mark.parametrize("wx", WXS)
def test_the_glint_mark_stays_off_the_sprite(wx, monkeypatch):
    pan = _on_road(wx)
    pan._find = adventure.ZONES[0]["find_keys"][0]
    pan.frame_i = 6
    cap = _capture(pan, monkeypatch)
    pet = _ink(cap["placements"][0])
    assert _in_window(pet)
    assert not (set(cap["overlay"]) & pet)


@pytest.mark.parametrize("wx", WXS)
def test_the_carried_find_never_smears_over_the_pet(wx, monkeypatch):
    """Audit A2: at right-side digs the old X1-pin dropped the icon INTO
    the returning sprite."""
    pan = _on_road(wx)
    pan._find = adventure.ZONES[0]["find_keys"][0]
    pan.key("enter")
    pan.key("space")                          # lock the meter immediately
    while pan._scene and pan._scene["t"] < INV_HOLD_T + 5:
        pan.anim()
    assert pan._scene is not None
    cap = _capture(pan, monkeypatch)
    pet = _ink(cap["placements"][0])
    icon = set(cap["overlay"])
    assert icon, "the carried find must render"
    assert not (icon & pet), "audit A2: icon ink on the sprite"


# ---- the ambush: visible at impact, pet at the wall, disjoint ---------------

@pytest.mark.parametrize("wx", WXS)
def test_the_pouncer_is_visible_at_impact(wx, monkeypatch):
    """Audit A1: anchored at the march x the ambusher rendered half-cut or
    fully OFF-window at the moment it struck.  The pet scrambles to X0
    during the telegraph, so the pounce always has the right half."""
    pan = _on_road(wx)
    pan._hazard = {"t": HZ_TELE_T + HZ_LUNGE_T - 1,
                   "enemy": adventure.ZONES[0]["randoms"][0],
                   "dodged": False, "hit": False}
    cap = _capture(pan, monkeypatch)
    pet = _ink(cap["placements"][0])
    pet_xs = {x for x, _y in pet}
    assert min(pet_xs) == grid.X0             # scrambled to the wall
    pounce = set(cap["overlay"])
    assert pounce, "the pouncer must render at impact"
    visible = {p for p in pounce if _in_window({p})}
    assert len(visible) >= len(pounce) * 0.9, "audit A1: pouncer clipped away"
    assert not (pounce & pet), "pet and pouncer ink must stay disjoint"


@pytest.mark.parametrize("wx", WXS)
def test_the_telegraph_mark_never_covers_the_scrambler(wx, monkeypatch):
    pan = _on_road(wx)
    pan._hazard = {"t": 1, "enemy": adventure.ZONES[0]["randoms"][0],
                   "dodged": False, "hit": False}
    cap = _capture(pan, monkeypatch)
    pet = _ink(cap["placements"][0])
    assert not (set(cap["overlay"]) & pet), "audit A8: ! over the pet's head"


# ---- faceoffs and parades ---------------------------------------------------

def test_the_gate_faceoff_actors_never_share_ink(monkeypatch):
    z = next(z for z in adventure.ZONES if z["bosses"])
    pan = _on_road(14.0, zone=z)
    pan.adv.loc = pan.adv.total
    pan._at_gate = True
    pan.travelling = False
    cap = _capture(pan, monkeypatch)
    assert len(cap["placements"]) == 2
    a, b = (_ink(p) for p in cap["placements"])
    assert not (a & b), "gate faceoff: pet and boss ink overlap"


def test_the_parade_enters_and_exits_through_the_edges(monkeypatch):
    """Audit A10: marchers popped in at x=20 and vanished at x=4 mid-window."""
    z = next(z for z in adventure.ZONES
             if z["bosses"] and z["bosses"][0].get("parade_msg"))
    pan = _on_road(14.0, zone=z)
    pan.travelling = False
    nums = [b["num"] for b in z["bosses"]][:1]
    pan._parade = {"t": 0, "nums": nums, "msg": None}
    first = _capture(pan, monkeypatch)["placements"][0]
    assert first[1] >= grid.X1                # enters OFF the right edge
    pan._parade["t"] = PARADE_T - 1
    last = _capture(pan, monkeypatch)["placements"][0]
    w = max(len(r) for r in last[0])
    assert last[1] <= grid.X0 - w + 1         # exits off the left edge


# ---- the teleport reveal continues into the march ---------------------------

def test_the_arrive_reveal_stands_where_the_march_continues(monkeypatch):
    """Audit A4: the centred reveal popped ~8px + flipped facing into the
    first march frame at every run start."""
    pan = AdventurePanel(_pet(), zone=adventure.ZONES[0])
    pan._trans = {"dir": "in", "phase": "arrive", "t": 23 + 15}
    cap = _capture(pan, monkeypatch)
    assert cap["placements"], "the reveal frame must show the pet"
    rows, x, mirror = cap["placements"][0]
    assert mirror is True                     # facing the way it will walk
    assert x == pan._jx(rows)                 # standing AT the march spot
    assert cap["clip"] == grid.WINDOW         # audit C1: no more unclipped paint


def test_the_heal_beat_renders_a_celebration(monkeypatch):
    """Audit A3: Life Recovery used to heal with no visual at all."""
    pan = _on_road(14.0)
    pan.pet.add_item("life_recovery")
    pan.adv.lives = 1
    pan._transport, pan._transport_cursor = ["life_recovery"], 0
    pan.key("enter")
    assert pan.adv.lives == 3
    assert pan._heal_t == TOWN_HOLD
    cap = _capture(pan, monkeypatch)
    assert _in_window(_ink(cap["placements"][0]))
    assert "second wind" in pan.strip()


@pytest.mark.parametrize("wx", WXS)
def test_a_clean_dodge_keeps_the_whiffing_pouncer_visible(wx, monkeypatch):
    """The dodge fix (2026-07-22, Joel: 'the space to dodge mechanic was
    glitchy'): the old sail-past hid the pouncer behind the pet's columns
    for the whole tail — a successful duck read as the attacker blinking
    out of existence.  The whiff retreats out the RIGHT edge: visible at
    every tail tick, never sharing ink with the croucher."""
    from tuipet.adventurescreen import HZ_END_T
    impact = HZ_TELE_T + HZ_LUNGE_T
    for k in range(HZ_END_T - 2):             # the tail (the last ticks clip
        pan = _on_road(wx)                    #  out through the edge, lawful)
        pan._hazard = {"t": impact + k,
                       "enemy": adventure.ZONES[0]["randoms"][0],
                       "dodged": True, "hit": False}
        cap = _capture(pan, monkeypatch)
        pet = _ink(cap["placements"][0])
        pounce = set(cap["overlay"])
        assert pounce, f"tail tick {k}: the whiffing pouncer must render"
        assert {p for p in pounce if _in_window({p})}, \
            f"tail tick {k}: pouncer fully clipped"
        assert not (pounce & pet), f"tail tick {k}: shared ink"
