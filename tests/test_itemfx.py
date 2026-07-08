"""Item-use animation scripts (item-anim audit 2026-07-07: "balloons and
futons have broken in game animations" — every toy funneled into canon's
Trampoline hop).  Each AnimationType now plays its own canon table (itemfx);
this pins the tables' shapes, the routing, and the end chains."""
from tuipet import data, itemfx
from tuipet.app import Screen
from tuipet.pet import Pet
from tuipet.shopscreen import ShopPanel


class _FakeScreen:
    fx = None
    frame_i = 0
_FakeScreen.start_fx = Screen.start_fx
_FakeScreen.advance_fx = Screen.advance_fx


def test_every_script_is_well_formed():
    for act, sc in itemfx.SCRIPTS.items():
        assert sc["end"] in ("cheer", "jeer"), act
        assert max(sc.get("rows", {}), default=0) < sc["steps"], act
        assert all(b < sc["steps"] for b in sc["snds"]), act
        for row in sc.get("rows", {}).values():
            assert 0 <= row.get("i", 0) <= 3, act          # 4 extracted frames
        # replay every step: geometry math must never crash, and the item
        # must never sink through the floor
        for step in range(sc["steps"]):
            _f, _p, _ix, iy, _dx, _dy = itemfx.state(act, step, 8, 8, 24)
            assert iy <= 24 - 8 - 1, (act, step)


def test_play_is_canon_not_the_trampoline_hop():
    """playing(): pet flips 1<->5 while the toy runs frames, wash stings at
    the excited beats, and the fx resolves into cheer."""
    sc = itemfx.SCRIPTS["Play"]
    assert sc["snds"] == {6: "wash", 18: "wash", 30: "wash"}
    assert itemfx.state("Play", 0, 8, 8, 24)[1] == 1
    assert itemfx.state("Play", 6, 8, 8, 24)[1] == 5
    assert itemfx.state("Play", 12, 8, 8, 24)[1] == 1
    assert sc["end"] == "cheer"


def test_angry_surprise_ends_angry_and_jeers():
    assert itemfx.state("AngrySurprise", 30, 8, 8, 24)[1] == 4
    assert itemfx.state("AngrySurprise", 42, 8, 8, 24)[1] == 4
    assert itemfx.SCRIPTS["AngrySurprise"]["end"] == "jeer"


def test_bounce_ball_drops_hits_and_exits_left():
    top = itemfx.state("Bounce", 0, 8, 8, 24)
    assert top[3] < 0                                   # in from above the arena
    down = itemfx.state("Bounce", 13, 8, 8, 24)
    assert down[3] > top[3]                             # it fell
    hit = itemfx.state("Bounce", 14, 8, 8, 24)
    assert hit[1] == 5                                  # the pet lights up
    assert itemfx.SCRIPTS["Bounce"]["snds"][14] == "click"   # hitBall
    end = itemfx.state("Bounce", 30, 8, 8, 24)
    assert end[2] < hit[2]                              # carried away left


def test_lift_toggles_the_dumbbell_and_the_strain_pose():
    floor = 24 - 8 - 1
    up = itemfx.state("Lift", 6, 8, 8, 24)
    assert up[3] == floor - 6 and up[1] == 8
    dn = itemfx.state("Lift", 12, 8, 8, 24)
    assert dn[3] == floor and dn[1] == 1


def test_ride_carries_the_pet_off_left():
    mid = itemfx.state("Ride", 20, 8, 8, 24)
    assert mid[1] == 5 and mid[4] < 0                   # riding happy, moving left
    end = itemfx.state("Ride", 29, 8, 8, 24)
    assert end[4] < mid[4]                              # still sliding


def _bag_use(name):
    """Drive a real bag use of the named item; return the panel's verdict."""
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus", obedience=500)
    p.world_seconds = 12 * 60.0
    e = next(x for x in [data.consumable_by_key(k) for k in data.load_icons()]
             if x and x.get("name") == name)
    p.add_item(e["key"])
    pan = ShopPanel(p, start_mode="bag")
    rows = pan._rows()
    for i, r in enumerate(rows):
        if r.get("key") == e["key"]:
            pan.cursor = i
            break
    else:
        for t in range(6):                              # find its tab
            pan.key("right")
            rows = pan._rows()
            hit = next((i for i, r in enumerate(rows) if r.get("key") == e["key"]), None)
            if hit is not None:
                pan.cursor = hit
                break
    return pan.key("enter"), e


def test_bag_routes_each_animation_type_correctly():
    r, e = _bag_use("Balloon")                          # Play -> its own script
    assert r == ("done", ("item_use", e["key"], "Play")), r
    r, e = _bag_use("Trampoline")                       # Jump -> the ported hop
    assert r == ("done", ("play", e["key"])), r
    r, e = _bag_use("Futon")                            # Idling -> effect only
    assert r is None, r


def test_item_fx_plays_the_script_and_chains():
    s = _FakeScreen()
    s.start_fx("item", icon="i:0", script="Play")
    assert s.fx["steps"] == itemfx.SCRIPTS["Play"]["steps"]
    assert s.fx["snds"] == itemfx.SCRIPTS["Play"]["snds"]
    for _ in range(s.fx["steps"]):
        s.advance_fx()
    assert s.fx is not None and s.fx["kind"] == "cheer"   # canon: resolves into cheer
    s2 = _FakeScreen()
    s2.start_fx("item", icon="i:0", script="AngrySurprise")
    for _ in range(s2.fx["steps"]):
        s2.advance_fx()
    assert s2.fx is not None and s2.fx["kind"] == "jeer"
