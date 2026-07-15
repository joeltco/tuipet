"""Jogress — the exact-pair table: my species + the partner's species look
up the sorted pair key; a hit is the fusion, a miss is no resonance."""
import pytest

from tuipet.pet import Pet
from tuipet import data, jogress


def _any_pair():
    pairs = data.load_jogress_pairs()
    byp = data.num_by_path()
    for key, result in pairs.items():
        a, b = key.split("|", 1)
        if a in byp and b in byp and result in byp:
            return a, b, result
    return None


def test_pair_lookup_is_exact_and_symmetric():
    hit = _any_pair()
    if hit is None:
        pytest.skip("no resolvable pairs in the atlas")
    a, b, result = hit
    byp = data.num_by_path()
    _, by = data.load_sprites()
    pa = Pet(num=byp[a], stage=by[byp[a]]["stage"], attribute="Free")
    pb = Pet(num=byp[b], stage=by[byp[b]]["stage"], attribute="Free")
    assert jogress.resolve_pair(pa, b) == byp[result]
    assert jogress.resolve_pair(pb, a) == byp[result]   # both-or-neither
    # and via the lobby payload path
    got = jogress.resolve_online(pa, {"num": byp[b]})
    assert got and got["num"] == byp[result]


def test_wrong_partner_gets_no_fusion():
    hit = _any_pair()
    if hit is None:
        pytest.skip("no resolvable pairs in the atlas")
    a, _b, _r = hit
    byp = data.num_by_path()
    pa = Pet(num=byp[a], stage="Child", attribute="Free")
    assert jogress.resolve_pair(pa, "database/Child/NoSuchMon.json") is None


def test_fuse_evolves_and_costs():
    hit = _any_pair()
    if hit is None:
        pytest.skip("no resolvable pairs in the atlas")
    a, b, result = hit
    byp = data.num_by_path()
    _, by = data.load_sprites()
    p = Pet(num=byp[a], stage=by[byp[a]]["stage"], attribute="Free")
    p.energy = 20
    p.weight = 30
    target = jogress.resolve_pair(p, b)
    msg = jogress.fuse(p, target)
    assert p.num == byp[result]
    assert "Jogress" in msg
    assert p.energy == 15 and p.weight == 26      # battle-scale costs
