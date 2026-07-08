"""Filth placement law (Joel, 2026-07-03): the max 4 poop piles occupy ONE
creature cell -- a 16x16 block of 8x8 slots on the grid's left edge, inside the
band -- and the mon (and its descending food) must NEVER overlap them, in any
state: roaming, sleeping, sick, or mid care-fx.

Verified at the PIXEL level: render_screen's blit math is replicated to get the
pet's lit pixels each frame, and they are intersected with the pile pixels."""
import random

import pytest

from tuipet import app as A
from tuipet import arena as AR          # Screen resolves render_screen here
from tuipet import data, grid
from tuipet.pet import Pet


def _live_num():
    _, by = data.load_sprites()
    return next((n for n, r in by.items()
                 if r["stage"] == "Rookie" and not data.is_placeholder(n)), None)


def _pet(poop, sizes):
    p = Pet(num=_live_num(), stage="Rookie", attribute="Vaccine")
    p.poop, p.poop_sizes = poop, list(sizes)
    return p


def _pile_union(pet, count=None):
    """Pile pixels across BOTH anim frames (they share the same slots)."""
    pts = set(A._filth_pts(pet, 0, count=count)) | set(A._filth_pts(pet, 7, count=count))
    return pts


def _pet_pixels(rows, xshift, mirror, cols=40, px_h=24):
    """Replicate render_screen's baseline blit: centred, grounded 2px up."""
    if not rows:
        return set()
    src = [r[::-1] for r in rows] if mirror else rows
    sw = max(len(r) for r in src)
    ox = (cols - sw) // 2 + xshift
    oy = max(0, px_h - len(src) - 2)
    return {(ox + x, oy + y) for y, line in enumerate(src)
            for x, ch in enumerate(line) if ch == "1"}


class _Cap:
    def __call__(self, r):
        self.val = r


def _screen():
    s = A.Screen.__new__(A.Screen)
    s.update = _Cap()
    s.on_mount()
    return s


@pytest.fixture(autouse=True)
def _seed():
    random.seed(99)


def test_four_piles_fill_exactly_one_creature_cell():
    if _live_num() is None:
        pytest.skip("sprite assets not installed")
    p = _pet(4, [3, 3, 3, 3])                     # the biggest generated size everywhere
    assert A._filth_right(4) - grid.X0 == 16, "4 poops span one 16-wide cell"
    pts = _pile_union(p)
    assert pts, "piles render"
    xs = {x for x, _ in pts}; ys = {y for _, y in pts}
    assert min(xs) >= grid.X0 and max(xs) < grid.X0 + 16, "block inside the 16-wide cell"
    assert min(ys) >= grid.TOP and max(ys) < grid.FLOOR, "block inside the 16px band"


@pytest.mark.parametrize("poop,sizes", [(1, [2]), (2, [3, 1]), (3, [2, 3, 1]), (4, [3, 3, 2, 1])])
def test_mon_never_walks_over_the_piles(poop, sizes, monkeypatch):
    if _live_num() is None:
        pytest.skip("sprite assets not installed")
    pet = _pet(poop, sizes)
    piles = _pile_union(pet)
    seen = []
    real = AR.render_screen

    def spy(rows, cols, rows_n, on, bg, baseline=True, mirror=False, xshift=0,
            yshift=0, overlay=None, bgimg=None):
        seen.append(_pet_pixels(rows, xshift, mirror))
        return real(rows, cols, rows_n, on, bg, baseline=baseline, mirror=mirror,
                    xshift=xshift, yshift=yshift, overlay=overlay, bgimg=bgimg)

    monkeypatch.setattr(AR, "render_screen", spy)
    s = _screen()
    for _ in range(200):                              # roam the full walkable width
        s.advance(pet)
        s.paint(pet)
    pet.sick = True                                   # sick shuffle state
    for _ in range(30):
        s.advance(pet)
        s.paint(pet)
    pet.sick = False
    pet.asleep, pet.anim = True, "sleep"              # sleeping (centred + clamped)
    for _ in range(30):
        s.advance(pet)
        s.paint(pet)
    assert seen
    for px in seen:
        assert px.isdisjoint(piles), "the mon stood on a pile"


def test_eat_fx_keeps_food_and_pet_clear_of_piles(monkeypatch):
    if _live_num() is None:
        pytest.skip("sprite assets not installed")
    pet = _pet(4, [3, 3, 2, 1])
    piles = _pile_union(pet)
    edge = A._filth_right(4)
    seen = []
    real = AR.render_screen

    def spy(rows, cols, rows_n, on, bg, baseline=True, mirror=False, xshift=0,
            yshift=0, overlay=None, bgimg=None):
        seen.append((_pet_pixels(rows, xshift, mirror), set(overlay or [])))
        return real(rows, cols, rows_n, on, bg, baseline=baseline, mirror=mirror,
                    xshift=xshift, yshift=yshift, overlay=overlay, bgimg=bgimg)

    monkeypatch.setattr(AR, "render_screen", spy)
    s = _screen()
    s.start_fx("eat", "f:0", pet=pet)
    for _ in range(s.fx["steps"] - 1):
        s.fx["step"] += 1
        s._paint_fx(pet)
    assert seen
    for petpx, overlay in seen:
        assert petpx.isdisjoint(piles), "the mon ate standing on a pile"
        extras = overlay - piles                      # everything else (the food) stays right of the block
        assert all(x >= edge for x, _ in extras), "the food descended onto the piles"


def test_poop_costs_weight_not_hunger():
    """Joel 2026-07-05: 'isnt pooping supposed to take away one hunger?' —
    canon says NO (PhysicalState.poop: mood relief + weight shed + gauge +
    filth; hunger is untouched — it falls on its own decay clock).  Even the
    floor-poop obedience change is 0 in the shipped difficulty column."""
    from tuipet.pet import Pet, POOP_MOOD_INC
    p = Pet(num=102, name="D", stage="Champion", attribute="Virus")
    p.world_seconds = 12 * 60.0
    p.hunger, p.weight, p.mood = 3, 20, 0
    o0 = p.obedience
    p._do_poop()
    assert p.hunger == 3                     # NEVER touched by pooping
    assert p.weight < 20                     # the canon cost is WEIGHT
    assert p.mood == POOP_MOOD_INC or p.mood > 0   # relief
    assert p.obedience == o0                 # FloorPoopObedienceChange = 0 (shipped)
